"""Exact local DI6 reference-aware path correction from immutable R8.

Nomination only. No native work, board emission, source or shared mutation.
All current fault copper and the original withheld barrel remain unchanged.
"""
import sys,pickle,json,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/'sbc-power'))
import guarded_power_projection_r44 as Z
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import tri_route as T
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
NET=K.NET;GND=K.GND

def main():
 started=time.monotonic();out=HERE/'di6-reference-path-correction-r10.json';assert not out.exists();A.read(__file__)
 receipt=json.loads(A.read(HERE/'di6-direct-latest-power-full-audit-r8.json'));assert C.sha(A.read(HERE/'di6-direct-latest-power-full-audit-r8.json'))=='42e250565080e9f495b0400645eda2a849618f6e1b33d2aa7ba85091d0c2cade'
 cp=pickle.loads(A.read(HERE/'di6-direct-r8-physical-checkpoint.pkl'));assert C.sha(A.read(HERE/'di6-direct-r8-physical-checkpoint.pkl'))=='134f8a35aa052075fe0ecc34a87a263fb473d2389db8a4ac9b072c99e91a0377'
 h=cp['h'];h2=cp['h2'];before=cp['before'];after=cp['after'];refs=cp['refs'];zones=cp['zones'];signal=cp['nv'][0];ret=cp['nv'][1];win=box(108,92,125,123)
 rec,trees=F.build({**h2,'zones':[]});domain=h2['domains_normalized'];holes=[]
 for v in h2['vias']:
  if Point(v['x'],v['y']).distance(win)<2:holes.append((v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for p in h2['pads']:
  for sh in L.poly(p.get('hole') or []):
   if sh.distance(win)<2:holes.append((p['uuid'],L.norm(p['net']),sh))
 reserve,exempt=A.reservations();hard=[]
 for r in h2['rule_areas']:
  if r.get('no_tracks'):
   for sh in L.poly(r['outline']):
    if sh.distance(win)<2:hard.append((r['uuid'],r['layers'],sh,set()))
 for r in reserve['keepouts']:
  for sh in L.poly(r['outline']):
   if sh.distance(win)<2:hard.append((r['name'],r['layers'],sh,exempt.get(r['name'],set())))
 free={};voids=[]
 for row in receipt['new_full_body_reference'][0]['own_voids']:
  voids.append(Point(row['at_mm']).buffer(row['radius_mm'],quad_segs=256))
 for layer in ('F.Cu','In3.Cu'):
  obs=[]
  for i in trees[layer].query(win.buffer(2),predicate='intersects'):
   q=rec[layer][int(i)];n=L.norm(q['net'])
   if n==NET:continue
   gap=.15 if domain.get(n)==domain.get(NET) else .6;obs.append(q['shape'].buffer(gap+.025+.005,quad_segs=128))
  # Existing same-domain fills may retreat legally. Proposed power meshes and
  # all cross-domain fills stay hard; native local clearance applies.
  for z in before['zones']:
   n=L.norm(z['net']);gap=.15 if domain.get(n)==domain.get(NET) else .6
   if n==NET or gap==.15:continue
   for sh in L.poly(z['fills'].get(layer,[])):
    if sh.distance(win)<2:obs.append(sh.buffer(max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  for z in zones:
   n=L.norm(z['net'])
   if z['layer']!=layer or n==NET or z['shape'].distance(win)>2:continue
   gap=.15 if domain.get(n)==domain.get(NET) else .6;obs.append(z['shape'].buffer(max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  obs += [sh.buffer(.280,quad_segs=128) for u,n,sh in holes if n!=NET]
  obs += [sh.buffer(.025,quad_segs=128) for u,ls,sh,es in hard if layer in ls and NET not in es]
  physical=win.difference(unary_union(obs)).buffer(-.105)
  actualref=refs[layer].intersection(win.buffer(1));owncut=Z.bounded_disk(signal,.525);old_reference_only_owncut=cp['oldrefs'][layer].intersection(owncut);allowed=actualref.union(old_reference_only_owncut).union(unary_union(voids)).buffer(-.105)
  free[layer]=physical.intersection(allowed)
 print('DI6_R9_EXACT_REFERENCE_FREE_CONSTRUCTED',flush=True)
 source=next(p for p in h['pads'] if p['uuid']=='8cb51ce7-ffcc-432a-90f1-6f2c2e13b06f');pad=unary_union(L.poly(source['layers']['F.Cu']));attachment=pad.buffer(-.075).intersection(free['F.Cu']);starts=K.sites(attachment,[119.136,97.3745],30)
 sourcebody=[q for q in cp['oroot'] if q['layer']=='In1.Cu' and q['kind']=='fill' and q['shape'].distance(pad)<1]
 current_di6=[t for t in h['tracks'] if L.norm(t['net'])==NET];current_source=next(v for v in h['vias'] if v['uuid']=='0ff4e506-7bc1-48ad-91fd-aeb598e74c7a')
 target_neighbors=[{'uuid':t['uuid'],'layer':t['layer'],'a':t['a'],'b':t['b'],'width_mm':t['w']} for t in current_di6 if min(math.dist(t['a'],(current_source['x'],current_source['y'])),math.dist(t['b'],(current_source['x'],current_source['y'])))<.000002]
 target=[113.95,119.35];attempts=[]
 for startrow in starts:
  attempt={'source_attachment_mm':startrow['at_mm'],'signal': [signal['x'],signal['y']],'return':[ret['x'],ret['y']],'paths':[]};attempts.append(attempt)
  for layer,a,b in [('F.Cu',startrow['at_mm'],attempt['signal']),('In3.Cu',attempt['signal'],target)]:
   pp=[p for p in K.pieces(free[layer]) if p.covers(Point(a)) and p.covers(Point(b))]
   if not pp:attempt['failed_layer']=layer;break
   pts,search=T.route(pp[0],tuple(a),tuple(b));pts=[[round(x,6),round(y,6)] for x,y in pts]
   full=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);outside=full.difference(refs[layer].union(unary_union(voids)));contact=full.intersection(pad).area if layer=='F.Cu' else None
   attempt['paths'].append({'layer':layer,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'reference_outside_exact_own_disks_mm2':outside.area,'actual_source_pad_contact_mm2':contact,'search':search})
  if len(attempt['paths'])==2:break
 result={'verdict':'EXACT_REFERENCE_AWARE_DI6_PATHS_NOMINATED_INDEPENDENT_FULL_NATIVE_OPEN' if attempts and len(attempts[-1]['paths'])==2 else'EXACT_REFERENCE_AWARE_DI6_PATHS_INCOMPLETE','preserved_R9_planner_sha256':C.sha(A.read(HERE/'construct_di6_reference_paths_r9.py')),'preserved_R9_report_sha256':C.sha(A.read(HERE/'di6-reference-path-correction-r9.json')),'R8_receipt_sha256':C.sha(A.read(HERE/'di6-direct-latest-power-full-audit-r8.json')),'physical_checkpoint_sha256':C.sha(A.read(HERE/'di6-direct-r8-physical-checkpoint.pkl')),'source_parent':cp['binding']['exact_native_discrete_board_file'],'source_parent_sha256':cp['binding']['exact_native_discrete_board_sha256'],'source_pad_exact_UUID':source['uuid'],'source_pad_exact_bounds_mm':pad.bounds,'actual_source_pad_attachment_area_mm2':attachment.area,'actual_current_target_neighbor_tracks':target_neighbors,'existing_target_via_unchanged':current_source,'new_source_pair_retained':receipt['actual_source_rooted_returns'][0],'same_layer_target_contact_requires_no_added_target_transition':bool(any(t['layer']=='In3.Cu' for t in target_neighbors)),'own_disks_unchanged':receipt['new_full_body_reference'][0]['own_voids'],'reference_free_areas_mm2':{l:f.area for l,f in free.items()},'reference_region_topology':{l:len(K.pieces(f)) for l,f in free.items()},'attempts':attempts,'all_current_fault_copper_unchanged':True,'all20_absent_original_withdrawables_not_restored':True,'original_drill_conflict114_65_119_45_withheld':True,'reference_circle_boundary_artifacts_not_waived':True,'nomination_only_own_outward_projection_strip':{'exact_new_signal_UUID':signal['uuid'],'analytic_radius_mm':.525,'bounded_projection_circumradius_mm':.525/math.cos(math.pi/512),'former_rooted_reference_intersection_only':True,'actual_analytic_disk_reference_gaps_must_remain_OPEN':True},'native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'verdict':result['verdict'],'source_attachment_area_mm2':attachment.area,'attempts':attempts,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
