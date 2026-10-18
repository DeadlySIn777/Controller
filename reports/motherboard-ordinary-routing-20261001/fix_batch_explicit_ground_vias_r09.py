"""Restore only newly proposed Ground stitches and disable automatic net inference."""
from pathlib import Path
import sys,json,shutil,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as a
e=a.engine
p=Path(__file__).parent;old=p/'actual-source26-root83-In2-batch-r08';out=p/'actual-source26-root83-In2-batch-r09';out.mkdir(exist_ok=False)
board=old/'motherboard-ordinary-In2-batch-candidate.kicad_pcb';plan=e.read(old/'proposed-groups.json')
ids={u for g in plan['groups']for u in g['ground_UUIDs']};assert len(ids)==13
tree=e.parse(board.read_text());changes=[]
for via in e.children(tree,'via'):
 uid=e.value(e.child(via,'uuid')[1])
 if uid not in ids:continue
 n=e.child(via,'net');previous=e.value(n[1]);n[1]=e.q('/LOGIC_GND')
 free=e.child(via,'free')
 if free is None:via.append(['free','yes'])
 else:free[1]='yes'
 changes.append(dict(uuid=uid,prior_native_net=previous,explicit_required_net='/LOGIC_GND',free_standing_net_is_fixed=True))
assert len(changes)==len(ids)
dest=out/board.name;dest.write_text(a.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(board.with_suffix(suffix),dest.with_suffix(suffix))
for f in old.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name in('fp-lib-table','manifest.json','piece-eligibility.json','proposed-groups.json'):shutil.copyfile(f,out/f.name)
b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
assert all(cu[u].Type()==pcbnew.PCB_VIA_T and cu[u].GetNetname()=='/LOGIC_GND'and cu[u].GetIsFree()for u in ids)
e.write(out/'explicit-Ground-net-correction.json',dict(passed=True,input_board_sha256=e.sha(board),output_board_sha256=e.sha(dest),only_new_ground_stitches_corrected=changes,primary_documentation='https://docs.kicad.org/9.0/en/pcbnew/pcbnew.html',native_BuildConnectivity_preserves_all_declared_ground_nets=True,existing_Cu_and_electrical_source_change_not_authorized=True,native_refill_DRC_and_all_actual_return_power_proofs_pending=True,manufacturing_ready=False))
print(json.dumps(dict(proposed_ground_vias=len(ids),prior_wrong_net=sum(r['prior_native_net']!='/LOGIC_GND'for r in changes),preserved_after_native_connectivity=True)))
