"""Recheck finite HOST return transfer on fresh actual R275 native source."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,time,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as R
import tri_route as T
import guarded_power_projection_r44 as Z
K=N.K;sha=N.sha
AP=H/'R275-actual-selected-native-five-net-source-body-reference-audit-r278'
OUT=H/'R275-HOST575-fresh-actual-native-In4-finite-source-transfer-r280'
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();receipt=json.loads((AP/'receipt.json').read_bytes());mf=AP/'actual-five-net-after-model.pkl';gf=AP/'actual-five-net-all-drilled-after-groups.pkl';assert sha(mf)==receipt['after_actual_model_SHA256'];assert sha(gf)==receipt['after_actual_groups_SHA256'];after=pickle.loads(mf.read_bytes());groups=pickle.loads(gf.read_bytes())
 pp=H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';assert sha(pp)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402';op=pickle.loads(pp.read_bytes());v=next(x for x in after['vias']if x['uuid']==op['source_terminal_UUID']);assert (v['x'],v['y'],v['d'],v['drill'])==(206.15,146.15,.6,.3)
 observed_all6=set(v['flashed'])==set(K.LAYERS);rad=op['source_terminal_exact_own_cap_mm'];assert rad==.575;ground=K.root(groups['/LOGIC_GND'],'J11001','2');actualplane=unary_union([r['shape']for r in ground if r['kind']=='fill'and r['layer']=='In4.Cu']);centre=Point(v['x'],v['y']);own=Z.bounded_disk(v,rad);local=actualplane.intersection(centre.buffer(1.8,quad_segs=128));finite=local.difference(own).buffer(-.105,quad_segs=128)
 host=next(gr for gr in groups['/motherboard_do/DOA_SDI_HOST']if any(r['kind']=='via'and r['uuid']==v['uuid']for r in gr));newids={t['uuid']for t in op['tracks']};by={'B.Cu':[],'In3.Cu':[]};seen=set();bindings=[]
 for r in host:
  if r['kind']!='track'or r['layer']not in by or r['uuid']in seen:continue
  isnew=r['uuid']in newids;ly=r['layer']
  if (ly=='B.Cu'and isnew)or (ly=='In3.Cu'and not isnew):continue
  body=unary_union([s['shape']for s in host if s['kind']=='track'and s['uuid']==r['uuid']and s['layer']==ly]);line=LineString([r['source']['a'],r['source']['b']])
  if body.distance(centre)>1.8:continue
  seen.add(r['uuid']);bindings.append({'UUID':r['uuid'],'layer':ly,'source_retained_native':not isnew,'incoming_new_body':isnew,'exact_axis':[r['source']['a'],r['source']['b']],'actual_all_drilled_body':R.shapeinfo(body)})
  for i in range(101):
   pt=line.interpolate(i/100,normalized=True);distance=pt.distance(centre)
   if .575<distance<1.8 and body.covers(pt)and finite.covers(pt):by[ly].append({'UUID':r['uuid'],'probe_mm':list(pt.coords[0]),'distance_mm':distance,'native_source_body_contains':True,'finite_actual_source_contains':True,'new_body':isnew})
 selected=None;attempts=[]
 for part in K.RF.parts(finite):
  bs=[r for r in by['B.Cu']if part.covers(Point(r['probe_mm']))];ins=[r for r in by['In3.Cu']if part.covers(Point(r['probe_mm']))]
  if not bs or not ins:continue
  pairs=sorted(((math.dist(b['probe_mm'],a['probe_mm']),b,a)for b in bs for a in ins),key=lambda x:x[0])
  for _,pb,pi in pairs[:64]:
   path,search=T.route(part,tuple(pb['probe_mm']),tuple(pi['probe_mm']))
   if not path:attempts.append({'B_probe':pb,'In3_probe':pi,'path':path,'search':search});continue
   axis=LineString(path);body=Z.bounded_buffer(axis,.1);outside=body.difference(local);hit=body.intersection(own);edgegap=body.distance(local.boundary);capgap=body.distance(own);row={'B_probe':pb,'In3_probe':pi,'path':path,'path_length_mm':axis.length,'axis_inside_eroded_source':part.covers(axis),'whole020_body_outside_actual_J1_In4':R.shapeinfo(outside),'whole020_body_own575_hit':R.shapeinfo(hit),'literal_body_to_source_boundary_gap_mm':edgegap,'literal_body_to_exact_own575_gap_mm':capgap,'both_literal005_guard_gaps_pass':edgegap>=.005 and capgap>=.005,'search':search};attempts.append(row)
   if part.covers(axis)and outside.is_empty and hit.is_empty and edgegap>=.005 and capgap>=.005: selected=row;(OUT/'finite-actual-native-J1-In4-return-transfer-body.wkb').write_bytes(body.wkb);break
  if selected:break
 for label,s in (('actual-J1-In4-source',actualplane),('local-actual-J1-In4-source',local),('exact-own575-cap',own),('finite-eroded-actual-source',finite)):(OUT/(label+'.wkb')).write_bytes(s.wkb)
 put('actual-terminal-native-B-and-new-In3-bindings.json',bindings);put('actual-side-probes.json',by);put('finite-source-search-attempts.json',attempts)
 put('receipt.json',{'status':'R275_ACTUAL_NATIVE_HOST575_FINITE_SAME_In4_SOURCE_GEOMETRIC_PASS_SI_CURRENT_OPEN'if selected and observed_all6 else'R275_ACTUAL_NATIVE_HOST575_FINITE_SOURCE_TRANSFER_REPAIR_REQUIRED','parent_R278_status':receipt['status'],'parent_R278_counts':receipt['counts'],'parent_source_contact_reference_failures_NOT_waived':True,'actual_R278_receipt_SHA256':sha(AP/'receipt.json'),'actual_after_model_SHA256':sha(mf),'actual_after_groups_SHA256':sha(gf),'original_terminal_UUID':v['uuid'],'original_actual_geometry_exact':True,'original_all6_FlashLayer_observed':observed_all6,'exact_own_cap_radius_mm':rad,'actual_stackup_order':['B.Cu','In4.Cu','In3.Cu'],'finite_conductor_width_mm':.20,'extra_boundary_guard_mm':.005,'actual_source':'J11001.2','finite_same_real_plane_witness':selected,'probe_counts':{ly:len(rs)for ly,rs in by.items()},'old_R605_model_NOT_substituted':True,'neighbor_caps_or_artificial_ground_disks_not_used':True,'raw_body_cap_reference_gaps_retained':True,'scope':'Finite return transfer outside this exact original own aperture, with both probes on real signal bodies and the conductor wholly on actual native source copper. No general SI/current acceptance or radius enlargement.','native_full_DRC_current_edge_rate_SI_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R280_COMPLETE',sha(OUT/'receipt.json'),'finite_path',selected is not None,'actual_all6',observed_all6,flush=True)
if __name__=='__main__':main()
