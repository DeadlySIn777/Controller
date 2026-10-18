"""Nominate a bounded redundant VS loop withdrawal plus real VDD join.

This is not a native/current acceptance. Every retained VS physical contact
and source endpoint is explicitly compared before any sparse nomination.
"""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import complete_geometry_r2 as G
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
R=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
O=H/'U10009-exact-VS-cycle-withdrawal-VDD-join-nomination-r379'
REMOVE=('cc85850d-78ba-455c-b892-3379cc0758e3','314c7ea2-285c-4616-a9c1-1667a4d561d8','013e40ba-4cc7-4b61-ad7c-2db0106d1b3f','354a6ed9-c3e6-44f8-af1c-bb5df73c88c2','59c527b2-3d63-45f2-a04f-48ea1c4757f4','b051a5a5-d030-478d-b567-4d2ebb539dcc','d1238ca3-0593-4a58-a049-b70b1f08219b','0a76e60a-f8ec-4542-bba6-a6cb551952d7','abb7a3a1-3039-4592-a4d2-e98b658a48f6','ad6cb510-3c09-455f-bf7d-6c8cc8dee85f','10ebbc58-ccf8-401b-a4de-1c33891d31dc','5eab07a1-af9d-4e3c-a0f2-bac6f13eda49','373e8c03-ad2a-41aa-851d-7f285c018108','08069409-b594-45b0-b3ac-f549b6d833c4','3351caa3-c092-4018-901d-1ccfde426563')
def main():
 assert not O.exists();O.mkdir();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,actual=pickle.loads(M.read_bytes());oldgroups=pickle.loads((R/'actual-drilled-current-groups.pkl').read_bytes());tm={t['uuid']:t for t in h['tracks']};protected=tm[REMOVE[0]]['net'];assert all(tm[u]['net']==protected and tm[u]['layer']=='B.Cu'and tm[u]['w']==.3 for u in REMOVE)
 target=next(p for p in h['pads']if(p['ref'],str(p['num']))==('U10009','4'));via=next(v for v in h['vias']if v['uuid']=='49d391b6-92ac-4024-9058-16931eb2143f');assert via['net']==target['net'];assert tuple((via['x'],via['y']))==(265.55,171.85)
 track={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/U10009/R379/VDD-direct-source')),'net':target['net'],'layer':'B.Cu','w':.20,'a':[target['x'],target['y']],'b':[via['x'],via['y']]}
 after={**actual,'tracks':[t for t in actual['tracks']if t['uuid']not in REMOVE]+[track]};rec,trees=F.build(after);axis=LineString([track['a'],track['b']]);errors=[];checks=[];vm={v['uuid']:v for v in h['vias']}
 for j in trees['B.Cu'].query(axis.buffer(.901),predicate='intersects'):
  row=rec['B.Cu'][int(j)]
  if L.norm(row['net'])==L.norm(track['net']):continue
  dist=axis.distance(row['shape'])-.1
  if row['kind']=='track'and not tm[row['uuid']].get('m'):
   t=tm[row['uuid']];dist=axis.distance(LineString([t['a'],t['b']]))-.1-t['w']/2
  elif row['kind']=='via':v=vm[row['uuid']];dist=axis.distance(Point(v['x'],v['y']))-.1-v['d']/2
  req=max(G.gap(h,track['net'],row['net']),row.get('clearance_mm',.15)if row['kind']=='fill'else 0)+.025;r={'kind':row['kind'],'UUID':row['uuid'],'raw_net':row['net'],'actual_mm':dist,'required_mm':req};checks.append(r)
  if dist<req:errors.append(r)
 for a in h['rule_areas']:
  if a.get('no_tracks')and 'B.Cu'in a['layers']and any(axis.buffer(.125).intersects(s)for s in L.poly(a['outline'])):errors.append({'kind':'native_no_track_rule','UUID':a['uuid']})
 _,pg=K.physical(after,L.norm(protected),K.hole_context(after));old=oldgroups[L.norm(protected)];relations,loss=K.contact_losses(old,pg,REMOVE);oldroot=K.root(old,'U11004','17');newroot=K.root(pg,'U11004','17');source_missing=K.keys(oldroot)-{('track',u,'B.Cu')for u in REMOVE}-K.keys(newroot)
 vs={p['uuid']for p in h['pads']if p['ref']=='U10009'and p['net']==protected};source_vs={r['uuid']for r in newroot if r['kind']=='pad'}&vs
 _,ag=K.physical(after,L.norm(target['net']),K.hole_context(after));aroot=K.root(ag,'U11017','1');vdd_root=any(r['kind']=='pad'and r['uuid']==target['uuid']for r in aroot)
 (O/'only-proposed-track-and-exact-original-VS-withdrawals.pkl').write_bytes(pickle.dumps({'tracks':[track],'vias':[],'removed':list(REMOVE),'exact_original_tracks':[tm[u]for u in REMOVE]},protocol=5))
 receipt={'verdict':'BOUNDED_VS_CYCLE_WITHDRAWAL_AND_VDD_JOIN_NOMINATION_PASS_ALL_RETAINED_CONTACTS_CURRENT_NATIVE_OPEN'if not errors and not loss and not source_missing and source_vs==vs and vdd_root else'BOUNDED_VS_CYCLE_NOMINATION_REJECTED','parent_model_sha256':sha(M),'strict_reference_audit_FAIL28_inherited':True,'new_track':track,'exact_original_VS_removed_tracks':[tm[u]for u in REMOVE],'local_track_true_guard_checks':checks,'guard_errors':errors,'all_retained_protected_physical_relations':relations,'retained_protected_relationship_losses':loss,'prior_protected_source_physical_keys_lost':[list(k)for k in sorted(source_missing)],'all_eight_VS_native_pad_UUIDs':sorted(vs),'all_eight_VS_still_actual_U11004_17_rooted':source_vs==vs,'VDD_actual_U11017_1_rooted':vdd_root,'withdrawn_parallel_path_current_redistribution_gate':'MANDATORY_OPEN; preserving contact does not prove preserved capacity or transient/drop behavior','full_four_outputs_each_A':.5,'VDD_load_planning_A':.0016,'nativeexact_delete_chunks_and_reference_allforeignfilledreplay':'OPEN; no native adoption','proposed_discrete_sha256':sha(O/'only-proposed-track-and-exact-original-VS-withdrawals.pkl'),'native_jobs':0,'source_rules_or_model_written':False,'adopted':False}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'verdict':receipt['verdict'],'guard_errors':errors,'physical_loss_count':len(loss),'source_missing':len(source_missing),'all8VS':source_vs==vs,'VDD_rooted':vdd_root}),flush=True)
if __name__=='__main__':main()
