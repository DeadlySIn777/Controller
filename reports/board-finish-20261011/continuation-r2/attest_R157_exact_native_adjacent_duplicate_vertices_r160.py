"""Remove exactly two zero-length expected edges; actual/native geometry stays frozen."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;S=H/'R155-known-reference-native-diagnostic-r157'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def put(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1)+'\n')
def clean(ring):
 out=[]
 for p in ring:
  if not out or p!=out[-1]:out.append(p)
 return out
assert sha(H/'R157-zone-coordinate-diagnosis-r158.json')=='e07f923441e1776d675fa3034424ea368f7ea6370af94a8e2cbc1bde4b930bcd'
board=S/'copy/board.kicad_pcb';candidate='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
assert sha(board)==candidate
original=read(S/'receipt.json');assert original['verdict']=='FAIL_JOINT_POWER_NATIVE_API'
assert original['runs']==[{'name':'source-all-Cu','exit_code':0},{'name':'all-new-zones','exit_code':1}]
assert original['all_native_discrete']['verdict']=='PASS' and original['source_API_summary']['parity_defects']==0
spec=read(S/'expected-zones.json');assert spec['candidate_sha256']==candidate
diag=read(H/'R157-zone-coordinate-diagnosis-r158.json');bound={r['uuid']:r for r in diag['rows']}
assert set(bound)=={'0929ae75-1efc-5015-af08-223abac05c5e','61cb8179-7754-5031-bbea-0da464bf816f'}
changes=[]
for e in spec['zones']:
 old=e['rings_IU'];new=[clean(r) for r in old]
 if new!=old:
  assert e['uuid'] in bound and old==bound[e['uuid']]['raw_expected_rings_IU']
  assert [len(a)-len(b)for a,b in zip(old,new)]==[1]+[0]*(len(old)-1)
  # Consecutive identical coordinates encode zero displacement; no coordinates
  # are rounded, moved, sorted away, tolerance-compared, or replaced by native data.
  for a,b in zip(old,new):
   assert set(map(tuple,a))==set(map(tuple,b))
   assert all(x==y for x,y in zip(clean(a),b))
  changes.append({'uuid':e['uuid'],'ring':0,'removed_adjacent_zero_length_vertices':1,'exact_integer_coordinate_set_preserved':True})
  e['rings_IU']=new
assert len(changes)==2
out=S/'exact-adjacent-duplicate-vertices-r160';assert not out.exists();out.mkdir()
expected=out/'expected-zones.json';put(expected,spec)
pins={str(p.resolve()):sha(p)for p in (Path(__file__),board,S/'receipt.json',S/'expected-zones.json',S/'native-parity.json',S/'inputs.json',H/'R157-zone-coordinate-diagnosis-r158.json',H/'native_declared_selected_zone_contract_r2.py',expected)}
cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(H/'native_declared_selected_zone_contract_r2.py'),str(expected),str(board),str(out/'native-zones.json')]
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
with (out/'api.log').open('w')as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
assert all(sha(p)==v for p,v in pins.items())
zr=read(out/'native-zones.json');ok=run.returncode==0 and not zr['errors'] and zr['native_zones_checked']==200
r={'verdict':'PASS_R157_NATIVE_API_WITH_EXACT_TWO_ZERO_LENGTH_EXPECTED_EDGES'if ok else'FAIL_R157_EXACT_NATIVE_DUPLICATE_EDGE_ATTESTATION','candidate_sha256':candidate,'candidate_path':str(board),'original_failed_stage_receipt_file':str(S/'receipt.json'),'original_failed_stage_receipt_sha256':sha(S/'receipt.json'),'source_all_Cu_API_pass':True,'native_zones_checked':zr['native_zones_checked'],'native_holes_checked':zr['native_holes_checked'],'native_zone_exact_contract_file':str(out/'native-zones.json'),'native_zone_exact_contract_sha256':sha(out/'native-zones.json'),'exact_integer_adjacent_duplicate_only_changes':changes,'input_sha256':pins,'strict_old_reference_gate_pass':False,'strict_old_reference_loss_count':28,'new_R7_raw_reference_failure_preserved':True,'host_all_supply_rooted':False,'native_saved_or_refilled':False,'adopted':False,'manufacturing_ready':False}
put(out/'receipt.json',r);print(json.dumps({k:v for k,v in r.items()if k!='input_sha256'}),flush=True)
raise SystemExit(0 if ok else 1)
