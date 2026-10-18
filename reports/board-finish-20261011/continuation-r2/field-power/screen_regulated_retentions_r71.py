"""Independent prospective R41 discrete screen against exact joint R59."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,sys
from pathlib import Path
from shapely.geometry import Point
from inventory import sha
import contact_layout as C
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OUT=HERE/'regulated-retained-discrete-joint-screen-r71'
WITHDRAW={'aeb2c3c8-5214-5918-86bf-b4db2cd59377','123d0875-7228-5ee5-9a07-ae0ef5b69b53','0cae08f1-3783-5a82-959f-9d8c9cae6f0e'}
def main():
 assert not OUT.exists();OUT.mkdir()
 mp=ROOT/'sbc-power/core-protected-outward-joint-r59/model.pkl';assert sha(mp)=='a77ba8a283d9b1e856ec6e4627363f9ba413e9db5c5af4c5fa1b8e3c41c32682'
 g,h,binding,zones,after=pickle.loads(mp.read_bytes());dp=HERE/'regulated-field-source-feeds-r41/proposed-discrete.pkl';assert sha(dp)=='d4bfc0e5740ee166c220f8a1946df8a6f9ac89a7fee19d74948b4a4d2e6eb8c4';d=pickle.loads(dp.read_bytes())
 failures=[];pairs=0;minimum=1e9;dom=h['domains_normalized']
 for v in d['vias']:
  if v['uuid'] in WITHDRAW:continue
  point=Point(v['x'],v['y'])
  for q in zones:
   if q['layer'] not in v['flashed'] or q['net']==v['net']:continue
   req=max(.15 if dom.get(C.norm(q['net']))==dom.get(C.norm(v['net'])) else .6,float(q.get('clearance_mm',.15)))+.025
   distance=point.distance(q['shape'])-v['d']/2
   if distance<req:failures.append({'kind':'prospective_via_to_joint_proposed_plane','via':v,'foreign_zone_uuid':q['uuid'],'foreign_raw_net':q['net'],'layer':q['layer'],'actual_edge_gap_mm':distance,'required_gap_mm':req})
  for other in h['vias']:
   pairs+=1;gap=math.hypot(v['x']-other['x'],v['y']-other['y'])-(v['drill']+other['drill'])/2;minimum=min(minimum,gap)
   if gap<.275:failures.append({'kind':'drill_to_native_or_joint_drill','via':v,'foreign_via':other,'actual_hole_gap_mm':gap,'required_gap_mm':.275})
 for t in d['tracks']:
  if t['uuid'] in {'11a7cc38-5c1a-572d-88d1-5f9a9f9f4f6b','851a5cd5-ac72-59c7-aa54-4afc35fb1098','116ed1e7-2940-5f18-961d-4436b602ec01'}:continue
  for q in zones:
   if q['layer']!=t['layer'] or q['net']==t['net']:continue
   req=max(.15 if dom.get(C.norm(q['net']))==dom.get(C.norm(t['net'])) else .6,float(q.get('clearance_mm',.15)))+.025
   gap=C.body(t).distance(q['shape'])
   if gap<req:failures.append({'kind':'prospective_stub_to_joint_proposed_plane','stub':t,'foreign_zone_uuid':q['uuid'],'foreign_raw_net':q['net'],'layer':q['layer'],'actual_edge_gap_mm':gap,'required_gap_mm':req})
 row={'verdict':'FAIL_RELOCATE_ADDITIONAL_PROSPECTIVE_ITEMS' if failures else 'PASS_SCOPED_RETAINED17_TO_CURRENT_PROPOSALS_AND_ALL_VIA_DRILLS','R59_model_sha256':sha(mp),'original_R41_discrete_sha256':sha(dp),'explicitly_withdrawn_via_UUIDs':sorted(WITHDRAW),'retained_vias':17,'retained_stubs':17,'drill_pairs_checked':pairs,'minimum_drill_gap_mm':minimum,'failures':failures,'native_and_all_discrete_Cu_SMD_reference_source_current_gates':'NOT_CHECKED_BY_THIS_SCOPED_SCREEN','board_written':False,'native_jobs':0}
 (OUT/'receipt.json').write_text(json.dumps(row,indent=1)+'\n',encoding='utf-8');print(row['verdict'],len(failures),'failures',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
