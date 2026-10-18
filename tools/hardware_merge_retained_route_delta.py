"""Merge only a reviewed additive core route delta into the populated PCB."""
import argparse,copy,hashlib,json,shutil,subprocess,sys
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,dump,children,child,value
from hardware_route_logic_return import identity,pad_identity
from hardware_populate_motherboard_pcb import raw_items,verify_population,native_parts_and_nets,watchdog_clear_source_check
ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('population','before','after','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('New immutable report directory required')
    src=a.population.resolve();base=src/'motherboard-populated-candidate.kicad_pcb';receipt=read(src/'report.json')
    if sha(base)!=receipt['candidate_board_sha256']:raise ValueError('Population candidate changed')
    before=pcbnew.LoadBoard(str(a.before.resolve()));after=pcbnew.LoadBoard(str(a.after.resolve()));b=pcbnew.LoadBoard(str(base))
    old={t.m_Uuid.AsString():identity(t) for t in before.GetTracks()};new={t.m_Uuid.AsString():identity(t) for t in after.GetTracks()}
    if any(new.get(k)!=v for k,v in old.items()):raise ValueError('Delta replaces old copper')
    populated={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    if any(populated.get(k)!=v for k,v in old.items()):raise ValueError('Populated PCB differs from exact delta base')
    oldpads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in before.GetPads()}
    newpads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in after.GetPads()}
    if oldpads!=newpads:raise ValueError('Delta changed original pads')
    tree=parse(base.read_text(encoding='utf8'));additions=[]
    routed=parse(a.after.read_text(encoding='utf8'))
    for kind in ('segment','via'):
        for item in children(routed,kind):
            ident=value(child(item,'uuid')[1])
            if ident in old:continue
            if ident in populated:raise ValueError('Duplicate delta UUID')
            net=value(child(item,'net')[1])
            if b.FindNet(net) is None:raise ValueError('Delta net absent from population '+net)
            tree.append(copy.deepcopy(item));additions.append(ident)
    if len(additions)!=len(new)-len(old):raise ValueError('Incomplete route delta')
    shutil.copytree(src,out);dest=out/base.name;dest.write_text(dump(tree)+'\n',encoding='utf8')
    run=subprocess.run([str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','--output',str(out/'merged-drc.json'),str(dest)],capture_output=True,text=True,encoding='utf8',errors='replace')
    (out/'merged-drc.txt').write_text(run.stdout+run.stderr,encoding='utf8')
    drc=read(out/'merged-drc.json')
    if run.returncode or drc['violations'] or drc.get('ignored_checks'):raise ValueError('Merged geometry failed native DRC; retain attempted evidence')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
    actual={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    if any(actual.get(k)!=v for k,v in populated.items()):raise ValueError('Retained populated copper changed')
    if any(actual.get(k)!=new[k] for k in additions):raise ValueError('Delta geometry changed')
    if raw_items(base,'footprint')!=raw_items(dest,'footprint'):raise ValueError('Any populated native footprint changed')
    # Zone fills must be recalculated for new vias. Their electrical/outline
    # definitions may not change; generated filled polygons are separate data.
    def definitions(path):
        z=raw_items(path,'zone');result={}
        for key,data in z.items():
            t=parse(data)
            for f in list(children(t,'filled_polygon')):t.remove(f)
            result[key]=dump(t)
        return result
    if definitions(base)!=definitions(dest):raise ValueError('Zone definition changed')
    model=read(out/'source-inputs/motherboard-design.json');physical=model['components']
    _,nodes=native_parts_and_nets(out/'source-inputs/motherboard-netlist.xml',physical)
    padnets={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in b.GetPads() if q.GetNumber()}
    verified=verify_population(fresh,model,nodes,actual,{}, {},[])
    if not verified['ok']:raise ValueError('Independent population/copper retention failed '+repr(verified))
    verified['source_inputs_unchanged']=True
    receipt.update(revision=out.name,candidate_board_sha256=sha(dest),population=verified,
        uncapped_native_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        native_drc=dict(exit_code=run.returncode,regular_violations=0,ignored_checks=[],reported_unconnected_items=len(drc['unconnected_items'])),
        watchdog_clear_source_check=watchdog_clear_source_check(model,nodes),
        added_retained_core_copper_items=len(additions),all_previous_track_via_items_unchanged=True,
        retained_zone_definitions_unchanged=True,zone_fills_recalculated_for_added_copper=True)
    write(out/'report.json',receipt)
    write(out/'core-delta-receipt.json',dict(inputs={str(x.resolve()):sha(x) for x in (base,a.before,a.after)},added_track_via_uuids=additions,
        total_tracks_vias=len(actual),uncapped_missing_joins=receipt['uncapped_native_missing_joins'],native_regular_drc=0,ignored_checks=[],all_880_native_footprints_unchanged=True,
        all_previous_copper_unchanged=True,zone_definitions_unchanged=True,manufacturing_ready=False))
    print(json.dumps({'added_items':len(additions),'total_tracks_vias':len(actual),'uncapped_missing_joins':receipt['uncapped_native_missing_joins'],'native_regular_drc':0}))
if __name__=='__main__':main()
