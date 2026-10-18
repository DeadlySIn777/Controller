"""Reconcile exact retained routes that enter real isolation-package gaps.

Only the enumerated native UUIDs may change geometry. Real source endpoints,
lands and nets are fixed. Added detours preserve the old same-net physical
pad clusters. This is an engineering correction, not a DRC suppression.
"""
from __future__ import annotations
import argparse,copy,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import ROOT,sha,write
from hardware_build_assembly import parse,dump,child,value,children
from hardware_route_logic_return import identity,pad_identity
from hardware_route_selected_additive import immutable_objects
from hardware_zone_motherboard_returns import functional_barrier,add_keepout
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def vec(p):return pcbnew.VECTOR2I(*(pcbnew.FromMM(x)for x in p))


def native_pad_clusters(board,nets):
    board.BuildConnectivity();out=[];seen=set()
    for p in board.GetPads():
        if not p.GetNumber() or p.GetNetname()not in nets or p.m_Uuid.AsString()in seen:continue
        items=list(board.GetConnectivity().GetConnectedItems(p))+[p]
        ids={q.m_Uuid.AsString()for q in items if isinstance(q,pcbnew.PAD)and q.GetNumber()and q.GetNetname()==p.GetNetname()}
        seen|=ids;out.append(dict(net=p.GetNetname(),pad_UUIDs=sorted(ids)))
    return out


def apply(board):
    exact={t.m_Uuid.AsString():t for t in board.GetTracks()};ledger=[];added=[]
    def edit(uid,net,start,end,old_start,old_end):
        t=exact[uid]
        if t.GetNetname()!=net or tuple(t.GetStart())!=tuple(vec(old_start))or tuple(t.GetEnd())!=tuple(vec(old_end)):
            raise ValueError('Exact reviewed retained route precondition changed '+uid)
        old=identity(t);t.SetStart(vec(start));t.SetEnd(vec(end))
        ledger.append(dict(uuid=uid,before=old,after=identity(t),net=net,reason='Exact package functional isolation gap correction'))
    def new(model_uid,start,end):
        original=exact[model_uid];t=pcbnew.PCB_TRACK(board);t.SetNet(original.GetNet())
        t.SetLayer(original.GetLayer());t.SetWidth(original.GetWidth());t.SetStart(vec(start));t.SetEnd(vec(end));board.Add(t)
        added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
    sda='/motherboard_safety_sensor/DIC_SENSOR_SDA';scl='/motherboard_safety_sensor/DIC_SENSOR_SCL'
    edit('77ce933c-03ed-49af-a643-c0d32d5b296a',sda,[117.2,175.865],[117.2,175.865],[121.325,175.865],[121.325,175.865])
    edit('9e7ea7ed-97e0-4f74-88ae-4c8dcf999903',sda,[117.2,175.865],[118.525,175.865],[121.325,175.865],[118.525,175.865])
    edit('58c55e90-7861-467f-b6a7-3f7182708bb8',sda,[121.325,167.7071],[117.2,175.865],[121.325,167.7071],[121.325,175.865])
    edit('c09a5148-4c21-49a0-8acc-1fb04ab87d19',scl,[116.2,177.135],[116.2,177.135],[121.325,177.135],[121.325,177.135])
    edit('0e12292a-3515-4893-a3cc-764dd51fc344',scl,[116.2,177.135],[118.525,177.135],[121.325,177.135],[118.525,177.135])
    edit('268ca875-9ac6-45ff-8502-c81fd7c994c6',scl,[129.675,169],[116.2,172.5],[129.675,169],[121.325,177.135])
    new('268ca875-9ac6-45ff-8502-c81fd7c994c6',[116.2,172.5],[116.2,177.135])
    chassis='0df65ce4-7666-4119-a8ea-96e783bba855'
    edit(chassis,'/CHASSIS',[420,27.5],[414,27.5],[420,28],[414,28]);new(chassis,[420,28],[420,27.5]);new(chassis,[414,27.5],[414,28])
    mpg='ae43fd60-995c-4b41-bffb-c85530d90492'
    edit(mpg,'/motherboard_operator/MPG_SEL_Y',[89.8821,301],[102.25,302],[89.8821,296.7071],[102.25,302]);new(mpg,[89.8821,296.7071],[89.8821,301])
    cond='075108d5-7295-4d62-8794-a06af67d0347'
    edit(cond,'/motherboard_operator/MPG_SEL_Y_CONDITIONED',[93.71997,288.3],[106.3375,288.3],[93.71997,291.35],[106.3375,291.35]);new(cond,[93.71997,291.35],[93.71997,288.3]);new(cond,[106.3375,288.3],[106.3375,291.35])
    fault='/motherboard_operator/PRB0_FAULT_GOOD_ISO'
    edit('d4afb6ba-ff4b-4222-8413-50264fea6d5f',fault,[102.65,294.365],[104.4,294.365],[102.65,294.365],[95.1375,294.365])
    edit('247f83ae-65ff-4227-bfd1-54e6593a66e3',fault,[104.4,302.05],[95.1375,302.05],[95.1375,294.365],[95.1375,302.05])
    new('d4afb6ba-ff4b-4222-8413-50264fea6d5f',[104.4,294.365],[104.4,302.05])
    ao='/motherboard_acc_control/AO_I2C_SDA_HOST'
    edit('0cd3817e-fb12-44b4-9f87-0a20e04bdab8',ao,[413.03003,254.87003],[409,245],[413.03003,254.87003],[413.03003,241.35997])
    edit('7f769cc1-832d-4d0c-90da-f6ec781a0190',ao,[409,245],[410.01997,241.35997],[413.03003,241.35997],[410.01997,241.35997])
    return ledger,added


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--map',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    base=a.board.resolve();out=a.out.resolve();mapping=json.loads(a.map.read_text(encoding='utf-8'))
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('New report directory required')
    if mapping['input_sha256'].get(str(base))!=sha(base):raise ValueError('Map input differs from exact board')
    out.mkdir(parents=True);(out/'inputs').mkdir()
    for f in [base,a.map.resolve(),Path(__file__)]:shutil.copy2(f,out/'inputs'/f.name)
    dest=out/'motherboard-functional-isolation-corrected-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
    for f in base.parent.iterdir():
        if f.is_dir()and(f.name.endswith('.pretty')or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
    shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    board=pcbnew.LoadBoard(str(base));old_cu={t.m_Uuid.AsString():identity(t)for t in board.GetTracks()}
    old_pads={p.m_Uuid.AsString():pad_identity(p)for p in board.GetPads()};old_zones={z.m_Uuid.AsString()for z in board.Zones()}
    net_names={t.GetNetname()for t in board.GetTracks()if t.m_Uuid.AsString()in {
        '77ce933c-03ed-49af-a643-c0d32d5b296a','c09a5148-4c21-49a0-8acc-1fb04ab87d19','0df65ce4-7666-4119-a8ea-96e783bba855',
        'ae43fd60-995c-4b41-bffb-c85530d90492','075108d5-7295-4d62-8794-a06af67d0347','d4afb6ba-ff4b-4222-8413-50264fea6d5f','7f769cc1-832d-4d0c-90da-f6ec781a0190'}}
    before_clusters=native_pad_clusters(board,net_names);ledger,added=apply(board)
    all_layers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]
    for row in mapping['barriers']:add_keepout(board,functional_barrier(row),all_layers,'ISO_FUNCTIONAL_BOUNDARY_'+row['reference'],tracks=True,vias=True)
    donor=out/'native-donor.kicad_pcb';pcbnew.SaveBoard(str(donor),board)
    old_tree=parse(base.read_text(encoding='utf-8'));new_tree=parse(donor.read_text(encoding='utf-8'))
    changed={r['uuid']for r in ledger};newids={r['uuid']for r in added}
    replacements={value(child(n,'uuid')[1]):n for n in new_tree[1:]if isinstance(n,list)and n and n[0]in ['segment','via','zone']}
    final=copy.deepcopy(old_tree)
    for i,n in enumerate(final):
        if isinstance(n,list)and n and n[0]in ['segment','via']and value(child(n,'uuid')[1])in changed:final[i]=copy.deepcopy(replacements[value(child(n,'uuid')[1])])
    final.extend(copy.deepcopy(n)for u,n in replacements.items()if u in newids or(n[0]=='zone'and u not in old_zones))
    dest.write_text(dump(final)+'\n',encoding='utf-8')
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    fresh=pcbnew.LoadBoard(str(dest));actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    if any(actual.get(u)!=v for u,v in old_cu.items()if u not in changed):raise ValueError('Unreviewed old copper changed')
    if {p.m_Uuid.AsString():pad_identity(p)for p in fresh.GetPads()}!=old_pads:raise ValueError('Source-pad lands or names changed')
    if any(actual[r['uuid']]!=r['after']for r in ledger):raise ValueError('Reviewed edited geometry differs after native save')
    if any(actual[r['uuid']]!=r['identity']for r in added):raise ValueError('New route net/geometry differs after native save')
    after_clusters=native_pad_clusters(fresh,net_names)
    if any(not any(old['net']==new['net']and set(old['pad_UUIDs'])<=set(new['pad_UUIDs'])for new in after_clusters)for old in before_clusters):raise ValueError('An old actual stationary source-pad cluster was disconnected')
    drc=json.loads((out/'drc.json').read_text(encoding='utf-8'))
    receipt=dict(board_sha256=sha(dest),input_board_sha256=sha(base),exact_native_copper_geometry_ledger=ledger,exact_new_copper=added,
        exact_added_zone_UUIDs=sorted(u for u,n in replacements.items()if n[0]=='zone'and u not in old_zones),
        old_stationary_source_pad_clusters_preserved=True,source_pad_cluster_evidence=dict(before=before_clusters,after=after_clusters),
        all_actual_source_pad_lands_and_names_preserved=True,native_errors=sum(v['severity']=='error'for v in drc['violations']),
        native_warnings=sum(v['severity']=='warning'for v in drc['violations']),native_ignored=drc.get('ignored_checks',[]),
        manufacturing_ready=False,physical_qualification=False)
    receipt['passed']=not receipt['native_errors']and not receipt['native_ignored'];write(out/'receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items()if k not in ['exact_native_copper_geometry_ledger','exact_new_copper','exact_added_zone_UUIDs','source_pad_cluster_evidence']},indent=2));raise SystemExit(not receipt['passed'])


if __name__=='__main__':main()
