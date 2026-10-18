"""Move only a proposed transfer away from the retained OBS28 return corridor."""
from pathlib import Path
import sys,json,copy,shutil,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import hardware_route_critical_digital_wip_r05 as authority
e=authority.engine;p=Path(__file__).parent;old=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-IO3-tip-trial-r85');out=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-OBS29-repair-trial-r86');out.mkdir(exist_ok=False)
src=old/'motherboard-bounded-merged-candidate.kicad_pcb';tree=e.parse(src.read_text());plan=e.read(p/'actual-source26-root83-In2-batch-r12/proposed-groups.json');g=plan['groups'][1];assert g['source_pair']==['U17010.13','U17009.12'];allowed=set(g['new_copper_UUIDs']);changes=[]
signal_x='305.632233';ground_x='304.832233'
for node in tree:
 if not isinstance(node,list)or not node or node[0]not in('segment','via'):continue
 uid=e.value(e.child(node,'uuid')[1])
 if uid not in allowed:continue
 before=e.dump(node)
 for key in('at','start','end'):
  point=e.child(node,key)
  if point is not None and point[1]in(signal_x,ground_x):point[1]=str(round(float(point[1])-.2,6))
 if e.dump(node)!=before:changes.append(dict(uuid=uid,before=before,after=e.dump(node)))
assert len(changes)==5,changes
def shift(points):return[[round(x-.2,6)if abs(x-305.632233)<1e-8 else x,y]for x,y in points]
g['start']['position']=shift([g['start']['position']])[0];g['start']['front_path_mm']=shift(g['start']['front_path_mm']);g['back_path_mm']=shift(g['back_path_mm']);g['start']['ground']['new_position'][0]=round(g['start']['ground']['new_position'][0]-.2,6)
plan['OBS29_retained_OBS28_return_repair']=dict(parent_board_sha256=e.sha(src),translation_mm=[-.2,0],changed_only_proposed_UUIDs=changes,prior_failure_ledger_sha256=e.sha(old/'old-ordinary9-reference-conflicts.json'))
dest=out/src.name;dest.write_text(authority.dump_native_board(tree)+'\n');e.write(out/'proposed-groups.json',plan)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in old.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
shutil.copyfile(p/'actual-source26-root83-In2-batch-r12/manifest.json',out/'manifest.json')
e.write(out/'OBS29-transfer-repair-proposal.json',dict(parent_board_sha256=e.sha(src),changed_only_unadopted_route_Cu=changes,original_ROOT84_Cu_and_all_lands_unchanged=True,native_full_verification_pending=True,manufacturing_ready=False))
with(out/'drc-command.txt').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(command_exit=r.returncode,board_sha256=e.sha(dest),adopted=False)))
