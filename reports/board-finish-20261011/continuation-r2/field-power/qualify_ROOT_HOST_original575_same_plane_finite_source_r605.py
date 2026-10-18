"""Finite actual In4 conductor between the incoming In3 and native B sides."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route as T
import guarded_power_projection_r44 as Z
OUT=H/'ROOT-HOST-original575-exact-own-guard-same-In4-finite-source-r605'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();ad=H/'ROOT-R238-HOST-independent-actual-drilled-old-contact-return-reference-r593';assert sha(ad/'receipt.json')=='ae201321e911af3ebb93ce32b34ea7a3ff9814fc9820b575b724d3670808b3cb';groups=pickle.loads((ad/'fresh-actual-drilled-groups.pkl').read_bytes());assert sha(ad/'fresh-actual-drilled-groups.pkl')=='0478294977406e208157beb5c57fa895de83a7d5172e8b942aff675e40c81e87'
 pp=ROOT/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';assert sha(pp)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402';op=pickle.loads(pp.read_bytes());mp=ROOT/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl';assert sha(mp)=='8bc676155f72e590cc8dd77f6315f0990d60b421f54a3c7928dc8e66ba48f91d';g,h,b,q,c=pickle.loads(mp.read_bytes());v=next(x for x in h['vias']if x['uuid']==op['source_terminal_UUID']);assert (v['x'],v['y'],v['d'],v['drill'])==(206.15,146.15,.6,.3);assert set(v['flashed'])==set(K.LAYERS)
 ground=K.root(groups['/LOGIC_GND'],'J11001','2');actualplane=unary_union([x['shape']for x in ground if x['kind']=='fill'and x['layer']=='In4.Cu']);centre=Point(v['x'],v['y']);rad=op['source_terminal_exact_own_cap_mm'];assert rad==.575;own=Z.bounded_disk(v,rad);local=actualplane.intersection(centre.buffer(1.8,quad_segs=128));finite=local.difference(own).buffer(-.105,quad_segs=128)
 # Exact incoming new In3 body and retained ORIGINAL B terminal chain.
 # Probe axes are taken from actual source-bearing records, not fabricated
 # radial spokes, unrelated same-net contacts or neighboring caps.
 newids={t['uuid']for t in op['tracks']};host=next(xs for xs in groups['/motherboard_do/DOA_SDI_HOST']if any(x['kind']=='via'and x['uuid']==v['uuid']for x in xs));by={'B.Cu':[],'In3.Cu':[]};seen=set();trackrows=[]
 for x in host:
  if x['kind']!='track'or x['layer']not in by or x['uuid']in seen:continue
  t=x['source'];ly=x['layer'];isnew=x['uuid']in newids
  if (ly=='B.Cu'and isnew)or(ly=='In3.Cu'and not isnew):continue
  line=LineString([t['a'],t['b']]);same=[y['shape']for y in host if y['kind']=='track'and y['uuid']==x['uuid']and y['layer']==ly];body=unary_union(same)
  if body.distance(centre)>1.8:continue
  seen.add(x['uuid']);trackrows.append({'UUID':x['uuid'],'layer':ly,'source_native_retained':not isnew,'new_incoming_side':isnew,'exact_axis':[t['a'],t['b']],'actual_physical_drill_subtracted_body':ds(body)})
  for i in range(101):
   pt=line.interpolate(i/100,normalized=True);dist=pt.distance(centre)
   if not .575<dist<1.8 or not body.covers(pt)or not finite.covers(pt):continue
   by[ly].append({'UUID':x['uuid'],'probe_mm':list(pt.coords[0]),'distance_from_actual_terminal_mm':dist,'actual_body_contains':True,'finite_source_plane_constrained_outside_exact_own_cap_contains':True,'source_native_retained':not isnew,'new_incoming_side':isnew})
 selected=None;attempts=[]
 for part in K.RF.parts(finite):
  bs=[x for x in by['B.Cu']if part.covers(Point(x['probe_mm']))];ins=[x for x in by['In3.Cu']if part.covers(Point(x['probe_mm']))]
  if not bs or not ins:continue
  pairs=sorted(((math.dist(x['probe_mm'],y['probe_mm']),x,y)for x in bs for y in ins),key=lambda x:x[0])
  for _,pb,pi in pairs[:64]:
   path,search=T.route(part,tuple(pb['probe_mm']),tuple(pi['probe_mm']));axis=LineString(path);body=Z.bounded_buffer(axis,.1);outside=body.difference(local);hit=body.intersection(own)
   row={'B_probe':pb,'incoming_In3_probe':pi,'path':path,'path_length_mm':axis.length,'axis_covered_by_exact_eroded_source_component':part.covers(axis),'actual_full020_body_outside_real_J1_In4_source':ds(outside),'actual_full020_body_exact_own575_hit':ds(hit),'search':search};attempts.append(row)
   if part.covers(axis)and outside.is_empty and hit.is_empty:
    selected={**row,'finite_actual_conductor_width_mm':.20,'additional_source_boundary_guard_mm':.005,'same_real_source_plane':'In4.Cu','actual_stackup_adjacent_order':['B.Cu','In4.Cu','In3.Cu'],'source':'J11001.2','native_full_all6_original_terminal_geometry_retained':True,'neighbor_cap_or_ground_ring_not_used':True};(OUT/'actual-finite-same-plane-J1-source-path.wkb').write_bytes(body.wkb);break
  if selected:break
 for name,s in [('actual-J1-In4-source-plane',actualplane),('local-real-In4-source-only',local),('exact-own575-cap',own),('finite-source-eroded-outside-own575',finite)]: (OUT/(name+'.wkb')).write_bytes(s.wkb)
 put(OUT/'actual-native-B-and-new-In3-terminal-body-bindings.json',trackrows);put(OUT/'all-actual-signal-side-probes.json',by);put(OUT/'finite-path-search-attempts.json',attempts)
 put(OUT/'receipt.json',{'status':'ORIGINAL_HOST575_B_IN4_IN3_SAME_SOURCE_FINITE_CONDUCTOR_GEOMETRIC_PASS_NATIVE_SI_OPEN'if selected else'ORIGINAL_HOST575_SAME_PLANE_FINITE_SOURCE_CONDUCTOR_REPAIR_REQUIRED','R593_source_contact_receipt_SHA256':sha(ad/'receipt.json'),'actual_R238_model_SHA256':sha(mp),'actual_source_groups_SHA256':sha(ad/'fresh-actual-drilled-groups.pkl'),'original_signal_terminal_UUID':v['uuid'],'original_signal_geometry_and_all6_layer_masks_exact':True,'exact_own_cap_radius_mm':rad,'actual_stackup_adjacent_order':['B.Cu','In4.Cu','In3.Cu'],'actual_existing_native_B_body_matches':trackrows,'actual_side_probe_counts':{ly:len(xs)for ly,xs in by.items()},'finite_same_plane_witness':selected,'scope':'Explicit geometric actual-source screen of this original HOST cap, not a general SI/current minimum or full-ring rule. The raw three cap reference gaps remain bound; this supplies a finite real J1-return path outside the exact575 aperture, without cap enlargement, arbitrary ground disks or neighboring-annulus borrowing.','required_raw_fullcap_reference_checkers_not_rewritten':True,'R196_nine_FG_CLK_FLT_nomination_failures_and_newordinary_native_fullDRC':'OPEN/FAIL preserved','native_SI_electrical_edge_rate_loop_current_thermal':'OPEN','native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R605',sha(OUT/'receipt.json'),'path',selected is not None,'probes',{ly:len(xs)for ly,xs in by.items()},flush=True)
if __name__=='__main__':main()
