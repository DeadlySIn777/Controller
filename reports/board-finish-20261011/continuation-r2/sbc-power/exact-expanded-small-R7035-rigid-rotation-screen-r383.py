"""Small genuine R7035 translation, preserved old terminals, one ordinary return."""
import json,pickle,hashlib,sys,time,math,copy,uuid,traceback
from pathlib import Path
from shapely import affinity,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import audit_aux_exact_raw as A
O=H/'sbc-power/CM79-R371-R7035-small-genuine-rigid-translation-old-terminal-stubs-new-ordinary-return-nomination-r383'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=D/'model.pkl';assert sha(mp)=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';assert sha(P/'receipt.json')=='6e9b02d1de90131096cf71ba8cf59d8ee65c86dbdbed4e67d961a0fb6796ec6e';g,h,b,q,c=pickle.loads(mp.read_bytes());authority=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());fp=authority['footprint'];pads=authority['pads'];own={p['uuid']for p in pads};sourceRows=json.loads((H/'sbc-power/CM79-R371-detached-old-IO3-one-new-ordinary-actual-source-LG-return-screen-r375/all-two-plane-source-eligible-return-site-native-guard-ledger.json').read_text());returns=[r for r in sourceRows if all(x['kind']=='pad'and x['UUID']in own or x['kind']=='actual_component_courtyard_no_POWER_D4'and x['ref']=='R7035'for x in r['deficits'])];assert returns;returns.sort(key=lambda r:(abs(r['ordinary_pair_distance_mm']-.95),r['new_LG_xy']));put(O/'only-return-sites-blocked-by-movable-R7035-own-pad-or-courtyard.json',returns);groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');refFull=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']));localBox=box(79,19,90,31);ref=zero(refFull.intersection(localBox));put(O/'exact-local-source-reference-screen-envelope.json',{'source':'actual J11001.2 In1','local_clip_bounds':[79,19,90,31],'all_nomination_pad_and_terminal_shapes_strictly_inside_envelope':True,'full_source_reference_final_audit':'OPEN; local clip is only a routing screen and never a native/source replacement'});base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};rec,trees=F.build(base,layers={'F.Cu'});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);courts=[(f['ref'],s)for f in h['footprints']if f['ref']!='R7035'for side,ps in f['courtyard'].items()if side=='F'for s in L.poly(ps)];ct=STRtree([s for ref,s in courts]);owncourt=unary_union(L.poly(fp['courtyard']['F']));reserve,exempt=A.reservations();oldtracks={t['uuid']:t for t in h['tracks']};poses=sorted([(angle,round(dx*.1,6),round(dy*.1,6))for angle in (0,-90,90,180)for dx in range(-15,16)for dy in range(-18,19)if angle or dx or dy],key=lambda v:(math.hypot(v[1],v[2])+.05*abs(v[0])/90,v[2]<0,abs(v[1]),abs(v[0])));attempts=[];winner=None
 def guarded(net,shape,axis=None,width=None):
  bad=[]
  for j in trees['F.Cu'].query(shape.buffer(1),predicate='intersects'):
   rr=rec['F.Cu'][int(j)]
   if L.norm(rr['net'])==L.norm(net):continue
   if rr['kind']=='fill'and L.norm(rr['net'])=='/LOGIC_GND':continue
   local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;req=max(local,gap(net,rr['net']))+.025;distance=shape.distance(rr['shape'])
   if axis is not None:
    if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];distance=axis.distance(LineString([t['a'],t['b']]))-width/2-t['w']/2
    elif rr['kind']=='via':v=rr['source'];distance=axis.distance(Point(v['x'],v['y']))-width/2-v['d']/2
    else:distance=axis.distance(rr['shape'])-width/2
   if distance<req:bad.append({'UUID':rr['uuid'],'kind':rr['kind'],'raw_net':rr['net'],'actual_gap_mm':distance,'planner_required_mm':req})
  for z in q:
   if z['layer']!='F.Cu'or L.norm(z['net'])==L.norm(net)or not z['shape'].intersects(shape.buffer(1)):continue
   distance=shape.distance(z['shape']);req=max(float(z['clearance_mm']),gap(net,z['net']))+.025
   if distance<req:bad.append({'UUID':z['uuid'],'kind':'owned_physical_role_hard','actual_gap_mm':distance,'planner_required_mm':req})
  for j in ht.query(shape.buffer(.285),predicate='intersects'):
   uid,n,s=holes[int(j)];distance=shape.distance(s)
   if axis is not None and L.norm(net)=='/IO_3V3'and uid=='3945a1ae-f8cb-441a-ad9d-21bde31e0e9f'and axis.distance(Point(84.15,24.7))<.000001:continue
   if distance<.28:bad.append({'UUID':uid,'kind':'all-real-hole-new-SMD-or-track-guard','gap_mm':distance})
  for rules,ex in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
   for rr in rules:
    if 'F.Cu'not in rr['layers']or(not ex and not rr.get('no_pads')and not rr.get('no_tracks'))or(ex and L.norm(net)in exempt.get(rr['name'],set())):continue
    if any(shape.distance(s)<.025 for s in L.poly(rr['outline'])):bad.append({'kind':'native_or_frozen_reserved_F_rule','name':rr.get('name',rr.get('uuid'))})
  return bad
 for angle,dx,dy in poses:
  rigid=lambda sh:affinity.translate(affinity.rotate(sh,angle,origin=(fp['x'],fp['y'])),dx,dy)
  movedcourt=rigid(owncourt);legalReturn=next((r for r in returns if movedcourt.distance(Point(*r['new_LG_xy']).buffer(.25,quad_segs=128))>=.025),None)
  if not legalReturn:continue
  bad=[]
  for j in ct.query(movedcourt.buffer(.025),predicate='intersects'):bad.append({'kind':'moved-actual-courtyard-intersects-other-court','ref':courts[int(j)][0]})
  newpads=[];refs=[]
  for p in pads:
   sh=rigid(unary_union(L.poly(p['layers']['F.Cu'])));bad+=guarded(p['net'],sh);referenceGap=sh.difference(ref);refs.append({'pin':p['num'],'whole_SMD_actual_J1_In1_gap_EMPTY':referenceGap.is_empty,'gap_mm2':referenceGap.area});newpads.append({'original':p,'xy':[round(rigid(Point(p['x'],p['y'])).x,6),round(rigid(Point(p['x'],p['y'])).y,6)],'shape':sh})
   if not referenceGap.is_empty:bad.append({'kind':'moved-full-SMD-actual-In1-reference','pin':p['num'],'gap_mm2':referenceGap.area})
  row={'host_rigid_pose_deg_dx_dy':[angle,dx,dy],'translation_mm':[dx,dy],'move_length_mm':math.hypot(dx,dy),'possible_ordinary_return':legalReturn,'new_SMD_reference_rows':refs,'deficits':bad};attempts.append(row)
  if len(attempts)%25==0:put(O/'finite-small-rigid-pose-ordinary-return-and-terminal-geometry-attempts.json',attempts)
  if bad:continue
  nt=[]
  for np in newpads:
   p=np['original'];end=np['xy'];contacts=next(r for r in authority['old_direct_contacts']if r['pad_UUID']==p['uuid'])['retained_old_direct_contacts'];targets=[]
   for old in contacts:
    if old['kind']=='via':v=next(v for v in h['vias']if v['uuid']==old['UUID']);targets.append([v['x'],v['y']])
    elif old['kind']=='track':t=oldtracks[old['UUID']];targets.append(min([t['a'],t['b']],key=lambda x:math.dist(x,[p['x'],p['y']])))
   for i,start in enumerate(sorted({tuple(v)for v in targets})):
    if math.dist(start,end)<.001:continue
    width=.3 if L.norm(p['net'])=='/IO_3V3'else .2;axis=LineString([start,end]);shape=zero(Z.bounded_buffer(axis,width/2));errors=guarded(p['net'],shape,axis,width);bad+=errors;t={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R7035-R383:'+str(dx)+':'+str(dy)+':'+str(p['num'])+':'+str(i))),'net':p['net'],'layer':'F.Cu','w':width,'a':list(start),'b':end};nt.append(t)
  for t in nt:
   axis=LineString([t['a'],t['b']])
   for np in newpads:
    if L.norm(np['original']['net'])==L.norm(t['net']):continue
    dd=axis.distance(np['shape'])-t['w']/2
    if dd<.175:bad.append({'kind':'new-stub-to-other-actually-moved-pad','UUID':t['uuid'],'pin':np['original']['num'],'actual_gap_mm':dd})
   for tt in nt:
    if L.norm(tt['net'])==L.norm(t['net']):continue
    dd=axis.distance(LineString([tt['a'],tt['b']]))-t['w']/2-tt['w']/2
    if dd<.175:bad.append({'kind':'new-mutual-foreign-stub-Cu','UUID':t['uuid'],'other_UUID':tt['uuid'],'actual_gap_mm':dd})
  row['terminal_stub_count']=len(nt);row['terminal_stub_deficits']=bad;put(O/'finite-small-rigid-pose-ordinary-return-and-terminal-geometry-attempts.json',attempts)
  if bad:continue
  point=Point(*legalReturn['new_LG_xy']);retBad=[]
  for np in newpads:
   dd=point.distance(np['shape'])-.25
   if dd<.175:retBad.append({'kind':'new-return-to-actually-moved-pad','pin':np['original']['num'],'actual_gap_mm':dd})
  for t in nt:
   dd=LineString([t['a'],t['b']]).distance(point)-t['w']/2-.25
   if dd<.175:retBad.append({'kind':'new-return-to-new-reconnect-stub','UUID':t['uuid'],'actual_gap_mm':dd})
  row['new_return_to_actual_moved_geometry_deficits']=retBad
  if retBad:continue
  winner={'host_rigid_pose_deg_dx_dy':[angle,dx,dy],'translation_mm':[dx,dy],'new_footprint_xy':[round(fp['x']+dx,6),round(fp['y']+dy,6)],'native_angle_delta_degrees':(-angle)%360,'native_local_AST_unchanged':True,'new_terminal_tracks':nt,'new_ground_return_site':legalReturn,'native_FP_and_pad_masks_fresh_old_source_Cu_reference_projections_and_all3689':'OPEN','original_source_value_and_IO3_ENC3_A_P_nets_pad_UUIDs_exact':True};break
 put(O/'finite-small-rigid-pose-ordinary-return-and-terminal-geometry-attempts.json',attempts)
 if winner:(O/'only-nominated-R7035-rigid-pose-stubs-new-return.pkl').write_bytes(pickle.dumps(winner,protocol=5))
 put(O/'receipt.json',{'verdict':'SMALL_R7035_MOVE_ORDINARY_RETURN_TERMINAL_GEOMETRY_NOMINATION_PENDING_NATIVE_AND_FULLSOURCE'if winner else'NO_SMALL_R7035_TRANSLATION_NOMINATION_IN_DECLARED_FULL_REFERENCE_AND_OLD_CU_GUARDS','current_R371_model_sha256':sha(mp),'R381_source_native_scope_receipt_sha256':sha(P/'receipt.json'),'eligible_return_sites_after_only_R7035_blocker_withdrawal':len(returns),'bounded_translation_candidate_count':len(poses),'attempt_count_after_return_courtyard_prefilter':len(attempts),'winner':winner,'nomination_packet_sha256':sha(O/'only-nominated-R7035-rigid-pose-stubs-new-return.pkl')if winner else None,'source_net_native_local_AST_rule_or_courtyard_shape_changes':0,'actual_source_fullscope_older_contacts_oldrefs_native_power_loop_current_thermal':'OPEN','inherited_R371_and_CORE_failure_flags':'RETAINED','adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R383',sha(O/'receipt.json'),bool(winner),len(attempts),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
