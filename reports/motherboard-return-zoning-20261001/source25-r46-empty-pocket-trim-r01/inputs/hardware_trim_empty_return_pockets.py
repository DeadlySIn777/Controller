"""Remove only proven empty generated reference-fill pockets geometrically.

No required source projection is removed. Exact source-bearing pockets need
real grounding. This native operation changes only explicitly reviewed zone
outlines, never copper tracks, pads, nets, thermal substrates or package
exclusions. Actual source-pad clusters and native DRC are checked afterward.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import ROOT,sha,write
from hardware_build_assembly import parse,children,child,value,dump
from hardware_zone_motherboard_returns import inflation,duplicate,split_polygons,dump_board,LEGACY_ZONES
from hardware_classify_unanchored_return_pockets import classify
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_route_logic_return import identity,pad_identity
from hardware_merge_bounded_pcb_delta import zone_definition
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def empty_polygons(b,mapping):
    report=classify(b,mapping)
    empty={(r['net'],r['reference_layer'],r['filled_piece'])for r in report['rows']if r['empty_reference_pocket']}
    fills={}
    for z in b.Zones():
        if z.GetIsRuleArea():continue
        for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
            if z.HasFilledPolysForLayer(layer):fills.setdefault((z.GetNetname(),layer),pcbnew.SHAPE_POLY_SET()).BooleanAdd(z.GetFilledPolysList(layer))
    cuts={}
    for (net,layer),fill in sorted(fills.items()):
        fill.Simplify()
        for i,piece in enumerate(split_polygons(fill)):
            if(net,b.GetLayerName(layer),i)in empty:cuts.setdefault((net,layer),pcbnew.SHAPE_POLY_SET()).Append(inflation(piece,.01))
    for p in cuts.values():p.Simplify()
    return cuts,report


def trim(b,cuts,allowed):
    changed=[];removed=[];added=[]
    for z in list(b.Zones()):
        uid=z.m_Uuid.AsString();key=z.GetNetname(),z.GetLayer()
        if uid not in allowed or z.GetIsRuleArea()or key not in cuts:continue
        original=duplicate(z.Outline());new=duplicate(original);new.BooleanSubtract(cuts[key]);delta=duplicate(original);delta.BooleanSubtract(new)
        if not delta.Area():continue
        pieces=sorted(split_polygons(new),key=lambda p:p.Area(),reverse=True)
        if not pieces:
            if uid in LEGACY_ZONES:raise ValueError('Original required plane cannot be deleted '+uid)
            removed.append(dict(uuid=uid,net=key[0],layer=b.GetLayerName(key[1]),reason='Entire generated reference outline has no actual source-adjacent pad/track projection'));b.Remove(z);continue
        z.Outline().RemoveAllContours();z.Outline().Append(pieces[0]);extra=[]
        for p in pieces[1:]:
            sibling=z.Duplicate();sibling.Outline().RemoveAllContours();sibling.Outline().Append(p);b.Add(sibling);extra.append(sibling.m_Uuid.AsString());added.append(sibling.m_Uuid.AsString())
        changed.append(dict(uuid=uid,net=key[0],layer=b.GetLayerName(key[1]),changed_keys=['polygon'],removed_outline_area_mm2=delta.Area()/1e12,new_same_rule_fragment_UUIDs=extra))
    return dict(changed=changed,removed=removed,new_fragment_UUIDs=added)


def clusters_survive(before,after):
    locations={p:(r['net'],set(r['pad_UUIDs']))for r in after for p in r['pad_UUIDs']}
    return all(r['net']==locations[r['pad_UUIDs'][0]][0]and set(r['pad_UUIDs'])<=locations[r['pad_UUIDs'][0]][1]for r in before)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ['board','map','generation-base','out']:ap.add_argument('--'+k,type=Path,required=True)
    a=ap.parse_args();base=a.board.resolve();out=a.out.resolve()
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('New immutable report directory required')
    m=json.loads(a.map.read_text(encoding='utf-8'));b=pcbnew.LoadBoard(str(base));generation=pcbnew.LoadBoard(str(a.generation_base.resolve()))
    old_zoneids={z.m_Uuid.AsString()for z in generation.Zones()};allowed={z.m_Uuid.AsString()for z in b.Zones()if z.m_Uuid.AsString()not in old_zoneids}|set(LEGACY_ZONES)
    out.mkdir(parents=True);inputs=out/'inputs';inputs.mkdir()
    for p in [base,a.map.resolve(),a.generation_base.resolve(),Path(__file__),ROOT/'tools/hardware_classify_unanchored_return_pockets.py']:shutil.copy2(p,inputs/p.name)
    oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};beforetree=parse(base.read_text(encoding='utf-8'));beforezones={value(child(z,'uuid')[1]):zone_definition(z)for z in children(beforetree,'zone')}
    nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
    cuts,classification=empty_polygons(b,m);write(out/'before-empty-pocket-classification.json',classification);transaction=trim(b,cuts,allowed)
    dest=out/'motherboard-empty-reference-pockets-trimmed-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
    for p in base.parent.iterdir():
        if p.is_dir()and(p.name.endswith('.pretty')or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
        elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
    if oldcu!={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}or oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in fresh.GetPads()}:raise ValueError('Actual native copper/source pads changed')
    newclusters=native_pad_clusters(fresh,nets);passed=clusters_survive(oldclusters,newclusters);write(out/'all-source-pad-cluster-proof.json',dict(before=oldclusters,after=newclusters,passed=passed))
    if not passed:raise ValueError('Empty-pocket cut disconnected an actual prior source-pad cluster')
    finaltree=parse(dest.read_text(encoding='utf-8'));afterzones={value(child(z,'uuid')[1]):zone_definition(z)for z in children(finaltree,'zone')}
    changed={r['uuid']for r in transaction['changed']}|{r['uuid']for r in transaction['removed']}
    if any(afterzones.get(uid)!=raw for uid,raw in beforezones.items()if uid not in changed):raise ValueError('Unreviewed zone definition changed')
    for row in transaction['changed']:
        first,last=beforezones[row['uuid']],afterzones[row['uuid']];row['before_definition_sha256']=hashlib.sha256(first.encode()).hexdigest();row['after_definition_sha256']=hashlib.sha256(last.encode()).hexdigest();row['before_raw_definition']=first;row['after_raw_definition']=last;row['electrical_outline_correction_reason']='Remove only native unanchored filled copper with no actual own-domain source-adjacent pad or trace projection; every actual prior source-pad cluster is preserved.'
        a0,b0=parse(first),parse(last)
        for tree in [a0,b0]:
            for p in list(children(tree,'polygon')):tree.remove(p)
        if dump(a0)!=dump(b0):raise ValueError('Zone net/rules changed outside exact empty outline '+row['uuid'])
    write(out/'exact-zone-outline-transaction.json',transaction);d=json.loads((out/'drc.json').read_text());r=dict(board_sha256=sha(dest),source_board_sha256=sha(base),all_native_Cu_and_pad_pieces_preserved=True,all_prior_actual_source_pad_clusters_preserved=True,
        empty_pockets_before=classification['empty_count'],source_bearing_unanchored_pockets_before=classification['source_bearing_count'],changed_zone_outlines=len(transaction['changed']),removed_generated_zones=len(transaction['removed']),new_same_rule_fragments=len(transaction['new_fragment_UUIDs']),native_DRC_violations=d['violations'],native_ignored=d['ignored_checks'],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,physical_qualification=False)
    write(out/'receipt.json',r);print(json.dumps({k:v for k,v in r.items()if k!='native_DRC_violations'},indent=2))


if __name__=='__main__':main()
