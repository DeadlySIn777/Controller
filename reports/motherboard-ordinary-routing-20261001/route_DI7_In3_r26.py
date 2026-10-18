"""Use the already Source-reviewed In3/adjacent-In4 option for this actual DI7 path."""
from pathlib import Path
import sys,json,copy,shutil,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r05 as authority
e=o.engine;root=Path(__file__).parent
source=root/'actual-source26-root87-In2-extended-r20';src=source/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
assert e.sha(src)=='52a11507a617c76bd369163d748dda760271ebaf9aad8e74aa1c96113d479d79'
out=root/'actual-source26-root87-DI7-In3-r26';out.mkdir(exist_ok=False)
plan=e.read(source/'proposed-groups.json');manifest=e.read(source/'manifest.json');g=plan['groups'][0];assert len(plan['groups'])==1 and g['net']=='/motherboard_di/DI7_LOGIC'
row=manifest['nets'][g['net']];assert 'In3.Cu'in row['layers']and row['reference_layers']['In3.Cu']=='In4.Cu'
b=pcbnew.LoadBoard(str(src));cu={t.m_Uuid.AsString():t for t in b.GetTracks()};wire='bce4f002-c30b-46ab-8381-2582466642d8'
assert cu[wire].GetLayer()==pcbnew.In2_Cu;cu[wire].SetLayer(pcbnew.In3_Cu);b.BuildConnectivity()
o.MAPPING=e.read('reports/motherboard-domains-20261001/source26-root87-In2-r20-r01/domain-map.json')
try:
 preflight=o.actual_return_check(b,set(g['signal_UUIDs']),manifest['nets'])
 e.write(out/'actual-reference-preflight.json',preflight)
except Exception as exc:
 e.write(out/'actual-reference-preflight-rejected.json',dict(error=str(exc),adopted=False));raise
assert all(set(v['intended_reference_layers'])=={'In1.Cu','In4.Cu'}for v in preflight['actual_signal_via_reference_audits'])
tree=e.parse(src.read_text());node=next(t for t in e.children(tree,'segment')if e.value(e.child(t,'uuid')[1])==wire);assert e.value(e.child(node,'layer')[1])=='In2.Cu';e.child(node,'layer')[1]=e.q('In3.Cu')
dest=out/src.name;dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in source.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
plan['actual_signal_layers']=['F.Cu','In3.Cu'];plan['actual_common_reference']=None;plan['actual_transfer_references']=['In1.Cu','In4.Cu']
plan['exact_proposed_layer_repair']=dict(uuid=wire,before='In2.Cu',after='In3.Cu',existing_Source_review_allows_layer=True,existing_manifest_unchanged=True,no_new_vias_or_changed_ground_stitches=True)
e.write(out/'proposed-groups.json',plan);shutil.copyfile(source/'manifest.json',out/'manifest.json')
with(out/'drc-command.txt').open('w')as log:
 r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--all-track-errors','--severity-all','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
print(json.dumps(dict(command_exit=0,new_copper=7,board_sha256=e.sha(dest),adopted=False)))
