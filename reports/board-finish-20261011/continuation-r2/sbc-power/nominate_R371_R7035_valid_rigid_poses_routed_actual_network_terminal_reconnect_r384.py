"""Reconnect legal rigid poses through real F Cu groups and actual In1 reference."""
import json,pickle,hashlib,sys,time,math,uuid,traceback,copy
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
import tri_route as TR
O=H/'sbc-power/CM79-R371-R7035-valid-rigid-poses-actual-network-terminal-source-reference-route-nominations-r384'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
N=H/'sbc-power/CM79-R371-R7035-small-genuine-rigid-translation-old-terminal-stubs-new-ordinary-return-nomination-r383'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def parts(s):return []if s.is_empty else list(s.geoms)if s.geom_type=='MultiPolygon'else[s]if s.geom_type=='Polygon'else[]
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';assert sha(N/'receipt.json')=='aef70c55db2f8736825d84135706c8b9385fbc82047aacf5f6d89269f830df8e';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());scope=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());fp=scope['footprint'];pads=scope['pads'];own={p['uuid']for p in pads};poses=[r for r in json.loads((N/'finite-small-rigid-pose-ordinary-return-and-terminal-geometry-attempts.json').read_text())if r.get('terminal_stub_count',0)>0];assert len(poses)==2;base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};ctx=K.hole_context(base);_,encgroups=K.physical(base,L.norm(scope['source_pin_nets']['2']),ctx);signalOldContacts={rr['UUID']for rr in scope['old_direct_contacts'][1]['retained_old_direct_contacts']};signalComponents=[xs for xs in encgroups if any(rr['uuid']in signalOldContacts for rr in xs)];assert signalComponents;changedGroups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());ioSource=K.root(changedGroups['/IO_3V3'],'R18001','2');lg=K.root(changedGroups['/LOGIC_GND'],'J11001','2');envelope=box(78,18,94,32);ref=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']).intersection(envelope));rec,trees=F.build(base,layers={'F.Cu'});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);vmap={v['uuid']:v for v in h['vias']};tmap={t['uuid']:t for t in h['tracks']};reserve,exempt=A.reservations();attempts=[];winner=None
 def targets(xs,center):
  out=[];seen=set()
  for rr in xs:
   if rr['uuid']in own or rr['layer']!='F.Cu'or rr['shape'].distance(center)>8:continue
   if rr['kind']=='via':v=vmap[rr['uuid']];samples=[[v['x'],v['y']]]
   elif rr['kind']=='track'and rr['uuid']in tmap:
    t=tmap[rr['uuid']]
    if t.get('m'):continue
    samples=[[round(t['a'][0]+u*(t['b'][0]-t['a'][0]),6),round(t['a'][1]+u*(t['b'][1]-t['a'][1]),6)]for u in (0,.25,.5,.75,1)]
   elif rr['kind']=='pad':p=next(p for p in h['pads']if p['uuid']==rr['uuid']);samples=[[p['x'],p['y']]]
   else:continue
   for xy in samples:
    key=(rr['uuid'],tuple(xy))
    if key in seen:continue
    seen.add(key);out.append({'UUID':rr['uuid'],'kind':rr['kind'],'xy':xy,'actual_source_Cu_shape':rr['shape']})
  return sorted(out,key=lambda rr:Point(*rr['xy']).distance(center))[:40]
 for pi,pose in enumerate(poses):
  angle,dx,dy=pose['host_rigid_pose_deg_dx_dy'];rigid=lambda sh:affinity.translate(affinity.rotate(sh,angle,origin=(fp['x'],fp['y'])),dx,dy);moved={str(p['num']):{'old':p,'shape':rigid(unary_union(L.poly(p['layers']['F.Cu']))),'xy':[round(rigid(Point(p['x'],p['y'])).x,6),round(rigid(Point(p['x'],p['y'])).y,6)]}for p in pads};returnSite=pose['possible_ordinary_return'];gp=Point(*returnSite['new_LG_xy']);done=[];ok=True;requests=[('1',ioSource)]+[('2',xs)for xs in signalComponents]
  for requestIndex,(pin,component)in enumerate(requests):
   p=moved[pin];net=L.norm(p['old']['net']);end=p['xy'];candidates=targets(component,Point(*end));success=None
   for target in candidates:
    start=target['xy'];clip=envelope;obs=[];ownvia=target['UUID']if target['kind']=='via'else None;cap=None
    if ownvia:
     v=vmap[ownvia];radius=(v['d']/2 if 'In1.Cu'in v['flashed']else v['drill']/2)+.25+.025;cap=Point(v['x'],v['y']).buffer(radius,quad_segs=128)
    for j in trees['F.Cu'].query(clip.buffer(1),predicate='intersects'):
     rr=rec['F.Cu'][int(j)]
     if L.norm(rr['net'])==net or rr['kind']=='fill'and L.norm(rr['net'])=='/LOGIC_GND':continue
     local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;obs.append(Z.bounded_buffer(rr['shape'].intersection(clip.buffer(1)),.1+max(local,gap(net,rr['net']))+.025))
    for z in q:
     if z['layer']=='F.Cu'and L.norm(z['net'])!=net and z['shape'].intersects(clip.buffer(1)):obs.append(Z.bounded_buffer(z['shape'].intersection(clip.buffer(1)),.1+max(float(z['clearance_mm']),gap(net,z['net']))+.025))
    for np in moved.values():
     if L.norm(np['old']['net'])!=net:obs.append(Z.bounded_buffer(np['shape'],.275))
    for t in done:
     if L.norm(t['net'])!=net:obs.append(Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+.275))
    for j in ht.query(clip.buffer(1),predicate='intersects'):
     uid,n,sh=holes[int(j)]
     if uid!=ownvia:obs.append(Z.bounded_buffer(sh,.38))
    obs.append(Z.bounded_buffer(gp,.525))
    for rules,ex in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
     for rr in rules:
      if 'F.Cu'not in rr['layers']or(not ex and not rr.get('no_tracks'))or(ex and net in exempt.get(rr['name'],set())):continue
      obs.extend(Z.bounded_buffer(sh,.125)for sh in L.poly(rr['outline'])if sh.intersects(clip.buffer(1)))
    allowed=ref if cap is None else unary_union([ref,cap]);free=clip.difference(unary_union(obs)).intersection(allowed.buffer(-.105,quad_segs=128));face=next((sh for sh in parts(free.buffer(-.000002,quad_segs=64))if sh.covers(Point(*start))and sh.covers(Point(*end))),None);row={'pose':pose['host_rigid_pose_deg_dx_dy'],'pin':pin,'actual_old_source_component_request':requestIndex,'target_UUID':target['UUID'],'target_kind':target['kind'],'start':start,'new_pad_center':end,'ordinary_width_mm':.2,'same_actual_source_reference_and_native_Cu_free_face':face is not None,'exact_named_source_terminal_own_cap_mm':radius if cap is not None else None};attempts.append(row);put(O/'finite-actual-old-Cu-source-reference-reconnect-attempts.json',attempts)
    if face is None:continue
    direct=LineString([start,end]);path=[start,end]if face.covers(direct)else TR.route(face,start,end)[0]
    if not path:continue
    path=[(round(float(x),6),round(float(y),6))for x,y in path]
    if not all(free.covers(LineString([a,bb]))for a,bb in zip(path,path[1:])):continue
    nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R7035-R384:'+str(pi)+':'+pin+':'+str(requestIndex)+':'+str(i))),'net':p['old']['net'],'layer':'F.Cu','w':.2,'a':list(a),'b':list(bb)}for i,(a,bb)in enumerate(zip(path,path[1:]))];axisbody=zero(unary_union([Z.bounded_buffer(LineString([t['a'],t['b']]),.1)for t in nt]));actual=axisbody.difference(unary_union([sh for uid,n,sh in holes]));remaining=actual.difference(cap)if cap is not None else actual;referenceGap=remaining.difference(ref);overlap=actual.intersection(target['actual_source_Cu_shape']).area;newOverlap=actual.intersection(p['shape']).area;row.update({'reference_gap_EMPTY':referenceGap.is_empty,'target_actual_old_Cu_overlap_mm2':overlap,'actually_moved_pad_overlap_mm2':newOverlap,'path':path,'length_mm':LineString(path).length});put(O/'finite-actual-old-Cu-source-reference-reconnect-attempts.json',attempts)
    if not referenceGap.is_empty or overlap<=0 or newOverlap<=0:continue
    done+=nt;success={'target':{k:v for k,v in target.items()if k!='actual_source_Cu_shape'},'tracks':nt,'path':path,'exact_own_old_source_cap_mm':radius if cap is not None else None,'actual_source_Cu_and_moved_pad_positive_contacts':True};break
   if not success:ok=False;break
  if ok:winner={'host_rigid_pose_deg_dx_dy':pose['host_rigid_pose_deg_dx_dy'],'target_native_angle_delta':(-angle)%360,'target_root_xy':[round(fp['x']+dx,6),round(fp['y']+dy,6)],'new_tracks':done,'new_ordinary_LG_return_site':returnSite,'old_ENC_contact_component_count':len(signalComponents),'actual_source_net_terminal_preservation_masks_oldrefs_fullgraph_native_pose_current':'OPEN'};break
 if winner:(O/'only-nominated-genuine-R7035-actual-network-routed-return-packet.pkl').write_bytes(pickle.dumps(winner,protocol=5))
 put(O/'receipt.json',{'verdict':'GENUINE_R7035_RIGID_POSE_ACTUAL_NETWORK_RECONNECT_AND_ORDINARY_RETURN_NOMINATION'if winner else'NO_ACTUAL_F_SOURCE_REFERENCE_RECONNECT_IN_TWO_PAD_LEGAL_RIGID_POSES_DECLARED_WINDOW','current_R371_model_sha256':sha(D/'model.pkl'),'R383_receipt_sha256':sha(N/'receipt.json'),'pad_legal_pose_count':len(poses),'ENC_old_contact_component_count_after_owned_pad_withdrawal':len(signalComponents),'actual_network_reconnect_attempt_count':len(attempts),'winner':winner,'packet_sha256':sha(O/'only-nominated-genuine-R7035-actual-network-routed-return-packet.pkl')if winner else None,'every_older_native_Cu_mask_foreign_plane_and_part_source_value_net_pad_UUID_fixed':True,'actual_fullsource_older_contact_oldref_native_pose_profile_mask_fill_DRC_and_signed_loop_current_thermal':'OPEN','model_source_native_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R384',sha(O/'receipt.json'),bool(winner),len(attempts),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
