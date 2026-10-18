"""Route both genuine resistor poses using original actual components and reference fills."""
import sys,json,pickle,hashlib,time,math,uuid,traceback
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
import tri_route as TR
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
Q=H/'sbc-power/CM79-R371-R7036-exact-source-native-Cu-and-local-reference-scope-r389'
N=H/'sbc-power/CM79-R371-coupled-R7036-minimal-rigid-pad-poses-ordinary-ENC-port-r391'
O=H/'sbc-power/CM79-R371-coupled-F-reconnect-joint-minimal-source-LG-support-r394'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def parts(s):return []if s.is_empty else list(s.geoms)if s.geom_type=='MultiPolygon'else[s]if s.geom_type=='Polygon'else[]
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());s35=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());s36=pickle.loads((Q/'exact-original-R7036-source-native-pose-contact-packet.pkl').read_bytes());own={p['uuid']for s in(s35,s36)for p in s['pads']};poses=pickle.loads((N/'all-pad-legal-genuine-coupled-pose-nominations.pkl').read_bytes())[:40];assert poses;base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};ctx=K.hole_context(base);minus=L.norm(s36['source_pin_nets']['1']);_,mg=K.physical(base,minus,ctx);oldminus={r['UUID']for r in next(x for x in s36['old_direct_contacts']if str(x['pin'])=='1')['retained_old_direct_contacts']}if 'pin'in s36['old_direct_contacts'][0]else{r['UUID']for r in next(x for x in s36['old_direct_contacts']if x['pad_UUID']==s36['pads'][0]['uuid'])['retained_old_direct_contacts']};minusGroups=[xs for xs in mg if any(r['uuid']in oldminus for r in xs)];assert minusGroups;groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');env=box(70,20,88,34);fullref=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']).intersection(env));rec,trees=F.build(base,layers={'F.Cu'});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for uid,sh in holes]);reserve,exempt=A.reservations();vmap={v['uuid']:v for v in h['vias']};tmap={t['uuid']:t for t in h['tracks']};attempts=[];winner=None;fixed={};holefixed={};additionalLGSupport=[]
 allrec,alltrees=F.build(base,layers={'In1.Cu'});lgcuts=[]
 for j in alltrees['In1.Cu'].query(env.buffer(1),predicate='intersects'):
  rr=allrec['In1.Cu'][int(j)]
  if L.norm(rr['net'])=='/LOGIC_GND':continue
  local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;lgcuts.append(Z.bounded_buffer(rr['shape'].intersection(env.buffer(1)),max(local,gap('/LOGIC_GND',rr['net']))+.025))
 for z in q:
  if z['layer']=='In1.Cu'and L.norm(z['net'])!='/LOGIC_GND'and z['shape'].intersects(env.buffer(1)):lgcuts.append(Z.bounded_buffer(z['shape'].intersection(env.buffer(1)),max(float(z['clearance_mm']),gap('/LOGIC_GND',z['net']))+.025))
 for j in ht.query(env.buffer(1),predicate='intersects'):lgcuts.append(Z.bounded_buffer(holes[int(j)][1],.28))
 for rules,ex in[(h['rule_areas'],False),(reserve['keepouts'],True)]:
  for rr in rules:
   if 'In1.Cu'not in rr['layers']or(ex and '/LOGIC_GND'in exempt.get(rr['name'],set())):continue
   lgcuts.extend(Z.bounded_buffer(sh,.025)for sh in L.poly(rr['outline'])if sh.intersects(env.buffer(1)))
 prospectiveLGfree=env.difference(unary_union(lgcuts))
 def targets(component,center):
  out=[];seen=set()
  for rr in component:
   if rr['uuid']in own or rr['layer']!='F.Cu'or rr['shape'].distance(center)>6:continue
   if rr['kind']=='via':v=vmap[rr['uuid']];samples=[[v['x'],v['y']]]
   elif rr['kind']=='track'and rr['uuid']in tmap:
    t=tmap[rr['uuid']]
    if t.get('m'):continue
    samples=[[round(t['a'][0]+u*(t['b'][0]-t['a'][0]),6),round(t['a'][1]+u*(t['b'][1]-t['a'][1]),6)]for u in(0,.5,1)]
   elif rr['kind']=='pad':p=next(p for p in h['pads']if p['uuid']==rr['uuid']);samples=[[p['x'],p['y']]]
   else:continue
   for xy in samples:
    key=(rr['uuid'],tuple(xy))
    if key in seen:continue
    seen.add(key);out.append({'UUID':rr['uuid'],'kind':rr['kind'],'xy':xy,'shape':rr['shape']})
  return sorted(out,key=lambda rr:Point(*rr['xy']).distance(center))[:16]
 def route(pose,request,target,done):
  pinpad=request['pad'];net=L.norm(pinpad['old']['net']);end=pinpad['xy'];start=target['xy'];sig=Point(*pose['selected_ordinary_ENC_port']['new_signal_xy']);sigUid='R394-exact-new-ENC-plus-via';ownvia=target['UUID']if target['kind']in('via','newvia')else None;cap=None
  if ownvia:
   radius=.525 if ownvia==sigUid else(vmap[ownvia]['d']/2 if 'In1.Cu'in vmap[ownvia]['flashed']else vmap[ownvia]['drill']/2)+.275;cap=Point(*start).buffer(radius,quad_segs=128)
  if net not in fixed:
   cuts=[]
   for j in trees['F.Cu'].query(env.buffer(1),predicate='intersects'):
    rr=rec['F.Cu'][int(j)]
    if L.norm(rr['net'])==net or rr['kind']=='fill'and L.norm(rr['net'])=='/LOGIC_GND':continue
    local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;cuts.append(Z.bounded_buffer(rr['shape'].intersection(env.buffer(1)),.1+max(local,gap(net,rr['net']))+.025))
   for z in q:
    if z['layer']=='F.Cu'and L.norm(z['net'])!=net and z['shape'].intersects(env.buffer(1)):cuts.append(Z.bounded_buffer(z['shape'].intersection(env.buffer(1)),.1+max(float(z['clearance_mm']),gap(net,z['net']))+.025))
   for rules,ex in[(h['rule_areas'],False),(reserve['keepouts'],True)]:
    for rr in rules:
     if 'F.Cu'not in rr['layers']or(not ex and not rr.get('no_tracks'))or(ex and net in exempt.get(rr['name'],set())):continue
     cuts.extend(Z.bounded_buffer(sh,.125)for sh in L.poly(rr['outline'])if sh.intersects(env.buffer(1)))
   fixed[net]=unary_union(cuts)
  obs=[fixed[net]]
  if ownvia not in holefixed:holefixed[ownvia]=unary_union([Z.bounded_buffer(holes[int(j)][1],.38)for j in ht.query(env.buffer(1),predicate='intersects')if holes[int(j)][0]!=ownvia])
  obs.append(holefixed[ownvia])
  if ownvia!=sigUid:obs.append(Z.bounded_buffer(sig,.48 if net==L.norm(pose['selected_ordinary_ENC_port']['raw_signal_net'])else .525))
  for mm in(pose['R7035'],pose['R7036']):
   for np in mm['pads']:
    if L.norm(np['old']['net'])!=net:obs.append(Z.bounded_buffer(np['shape'],.275))
  io=pose['selected_ordinary_ENC_port']['successful_IO3_reconnect'];obs.append(Z.bounded_buffer(LineString(io['path']),.375))
  for t in done:
   if L.norm(t['net'])!=net:obs.append(Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+.275))
  nativeLGop=next(x for x in pose['selected_ordinary_ENC_port']['explicit_normal_native_same_domain_fill_hole_operations']if L.norm(x['raw_net'])=='/LOGIC_GND'and x['layer']=='In1.Cu'); nativeZone=next(z for z in c['zones']if z['uuid']==nativeLGop['UUID']); actualNativeRadius=.25+float(nativeZone['clearance_mm']); assert abs(actualNativeRadius+.025-nativeLGop['only_normal_native_new_via_antipad_radius_mm'])<1e-9; ref=unary_union([fullref]+additionalLGSupport).difference(sig.buffer(actualNativeRadius,quad_segs=128)); lgfree=prospectiveLGfree.difference(Z.bounded_buffer(sig,.425)); referenceDomain=lgfree if request['label']=='R7035-ENC3_A_P-to-one-ordinary-dive'else ref; allowed=referenceDomain if cap is None else unary_union([referenceDomain,cap]);free=env.difference(unary_union(obs)).intersection(allowed.buffer(-.105,quad_segs=128));face=next((sh for sh in parts(free.buffer(-.000002,quad_segs=64))if sh.covers(Point(*start))and sh.covers(Point(*end))),None);row={'R7036_pose':pose['R7036']['pose'],'request':request['label'],'target_UUID':target['UUID'],'start':start,'end':end,'same_Cu_reference_free_face':face is not None,'start_in_free':free.covers(Point(*start)),'end_in_free':free.covers(Point(*end)),'actual_native_LG_antipad_radius_mm':actualNativeRadius,'same_exact_terminal_guard_radius_mm':radius if cap is not None else None,'native_LG_zone_clearance_mm':float(nativeZone['clearance_mm']),'larger_conservative_R388_old_mask_guards_retained':True};attempts.append(row)
  if face is None:return None
  direct=LineString([start,end]);path=[start,end]if face.covers(direct)else TR.route(face,start,end)[0]
  if not path:return None
  path=[[round(float(x),6),round(float(y),6)]for x,y in path]
  if not all(free.covers(LineString([a,bb]))for a,bb in zip(path,path[1:])):return None
  nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R394:'+str(pose['R7036']['pose'])+':'+request['label']+':'+str(i))),'net':pinpad['old']['net'],'layer':'F.Cu','w':.2,'a':a,'b':bb}for i,(a,bb)in enumerate(zip(path,path[1:]))];body=zero(unary_union([Z.bounded_buffer(LineString([t['a'],t['b']]),.1)for t in nt]));actual=body.difference(unary_union([sh for u,sh in holes]+[sig.buffer(.1,quad_segs=128)]));remaining=actual.difference(cap)if cap is not None else actual;rg=remaining.difference(ref);oldOverlap=actual.intersection(target['shape']).area;padOverlap=actual.intersection(pinpad['shape']).area;row.update({'path':path,'length_mm':LineString(path).length,'reference_gap_EMPTY':rg.is_empty,'target_actual_overlap_mm2':oldOverlap,'moved_pad_overlap_mm2':padOverlap})
  if request['label']=='R7035-ENC3_A_P-to-one-ordinary-dive':
   required=zero(remaining); support=zero(Z.bounded_buffer(required,.005)); contacts=[ss.intersection(ref).area for ss in parts(support)]; supportGap=support.difference(lgfree); newReferenceGap=required.difference(unary_union([ref,support])); row.update({'joint_positive_LG_support_area_mm2':support.area,'every_support_component_actual_J1_source_fill_overlap_mm2':contacts,'new_LG_support_foreign_hole_rule_gap_EMPTY':supportGap.is_empty,'new_actual_body_source_reference_gap_EMPTY':newReferenceGap.is_empty})
   if not contacts or not all(a>0 for a in contacts)or not supportGap.is_empty or not newReferenceGap.is_empty or oldOverlap<=0 or padOverlap<=0:return None
   additionalLGSupport.append(support);return nt
  return nt if rg.is_empty and oldOverlap>0 and padOverlap>0 else None
 for pose in poses:
  sig=Point(*pose['selected_ordinary_ENC_port']['new_signal_xy']);additionalLGSupport.clear();done=[];directRows=[];requests=[{'label':'R7035-ENC3_A_P-to-one-ordinary-dive','pad':next(p for p in pose['R7035']['pads']if str(p['old']['num'])=='2'),'component':None,'targets':[{'UUID':'R394-exact-new-ENC-plus-via','kind':'newvia','xy':list(sig.coords)[0],'shape':sig.buffer(.25,quad_segs=128).difference(sig.buffer(.1,quad_segs=128))}]}]+[{'label':'R7036-ENC3_A_N-original-component-'+str(i),'pad':next(p for p in pose['R7036']['pads']if str(p['old']['num'])=='1'),'component':xs}for i,xs in enumerate(minusGroups)]+[{'label':'R7036-GND-actual-J1-component','pad':next(p for p in pose['R7036']['pads']if str(p['old']['num'])=='2'),'component':lg}];ok=True
  for request in requests:
   p=request['pad'];component=request['component']
   if component is not None:
    overlaps=[{'UUID':rr['uuid'],'kind':rr['kind'],'overlap_mm2':p['shape'].intersection(rr['shape']).area}for rr in component if rr['layer']=='F.Cu'and rr['uuid']not in own and p['shape'].intersects(rr['shape'])]
    if any(rr['overlap_mm2']>0 for rr in overlaps):directRows.append({'request':request['label'],'positive_actual_original_component_contacts':overlaps,'new_tracks':0});continue
    candidates=targets(component,Point(*p['xy']))
   else:candidates=request['targets']
   success=None
   for target in candidates:
    success=route(pose,request,target,done)
    if success is not None:done+=success;break
   put(O/'finite-actual-coupled-function-F-reconnect-attempts.json',attempts)
   if success is None:ok=False;break
  if ok:winner={'exact_pad_pose_nomination':pose,'new_F_reconnect_tracks':done,'only_new_positive_source_LG_In1_support_shapes':list(additionalLGSupport),'direct_original_source_contacts':directRows,'original_ENC3_A_N_contact_component_count':len(minusGroups),'new_SIG_via_and_actual_JD12_B3_lower_leg':'OPEN','fresh_all_original_pad_source_relationships_refs_native_masks_current':'OPEN'};break
 if winner:(O/'only-coupled-genuine-poses-both-functions-F-reconnect-nomination.pkl').write_bytes(pickle.dumps(winner,protocol=5))
 put(O/'finite-actual-coupled-function-F-reconnect-attempts.json',attempts);put(O/'receipt.json',{'verdict':'COUPLED_BOTH_FUNCTIONS_F_RECONNECT_NOMINATION'if winner else'NO_COUPLED_F_RECONNECT_IN_FIRST_40_MINIMAL_PAD_LEGAL_POSES','R371_model_sha256':sha(D/'model.pkl'),'R391_receipt_sha256':sha(N/'receipt.json'),'bounded_minimal_pad_pose_count':len(poses),'old_ENC3_A_N_component_count':len(minusGroups),'route_attempt_count':len(attempts),'winner':bool(winner),'packet_sha256':sha(O/'only-coupled-genuine-poses-both-functions-F-reconnect-nomination.pkl')if winner else None,'original_all_Cu_pad_UUIDs_source_values_nets_and_courtyard_shapes_held':True,'wholebody_actual_source_refs_exact_terminal_guards_only':True,'minimal_new_LG_In1_role_all_foreign_reference_layer_Cu_holes_rules_hard':True,'new_LG_profile_emission_fresh_current_source_proof_native_fill_DRC':'OPEN','adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R394',sha(O/'receipt.json'),bool(winner),len(attempts),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
