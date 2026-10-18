"""One signal dive port outside the actual moved part, with an existing native LG pair."""
import json,pickle,hashlib,sys,time,math,traceback,collections
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
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R371-R7035-one-ENC-ordinary-signal-via-existing-LG-return-eligibility-r388'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
N=H/'sbc-power/CM79-R371-R7035-valid-rigid-poses-actual-network-terminal-source-reference-route-nominations-r386'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';assert sha(N/'receipt.json')=='ccbffc727426336017f14a5f252ee5a09a757e6cbc7b53df2b198275aab3c18b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());scope=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());fp=scope['footprint'];pads=scope['pads'];own={p['uuid']for p in pads};net=L.norm(scope['source_pin_nets']['2']);rgroups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(rgroups['/LOGIC_GND'],'J11001','2');refs={ly:zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly]))for ly in ('In1.Cu','In4.Cu')};successful=[r for r in json.loads((N/'finite-actual-old-Cu-source-reference-reconnect-attempts.json').read_text())if r.get('pin')=='1'and r.get('reference_gap_EMPTY')and r['target_actual_old_Cu_overlap_mm2']>0 and r['actually_moved_pad_overlap_mm2']>0];unique={tuple(r['pose']):r for r in successful};poses=sorted(unique.values(),key=lambda r:math.hypot(r['pose'][1],r['pose'][2]))[:12];native=A.C.inventory((H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb').read_bytes());near=unary_union([Point(fp['x']+r['pose'][1],fp['y']+r['pose'][2]).buffer(5)for r in poses]);lfills={ly:[rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly]for ly in refs};lft={ly:STRtree(ss)for ly,ss in lfills.items()};ports=[]
 for v in h['vias']:
  if L.norm(v['net'])!='/LOGIC_GND'or v['uuid']not in native[3]or not near.covers(Point(v['x'],v['y'])):continue
  overlap={}
  for ly in refs:
   ann=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==ly]));local=unary_union([lfills[ly][int(j)]for j in lft[ly].query(ann,predicate='intersects')]);overlap[ly]=ann.intersection(local).area
  if all(a>0 for a in overlap.values()):ports.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'actual_original_two_source_plane_annulus_overlap_mm2':overlap,'native_original_chunk_sha256':hashlib.sha256(native[3][v['uuid']]).hexdigest()})
 put(O/'only-existing-original-actual-two-plane-LG-return-ports.json',ports);base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};rec,trees=F.build(base);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);vxy=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vxy);courts=[(f['ref'],s)for f in h['footprints']if f['ref']!='R7035'for ps in f['courtyard'].values()for s in L.poly(ps)];ct=STRtree([s for ref,s in courts]);reserve,exempt=A.reservations();rows=[];eligible=[];region=near.buffer(1);masks={ly:[]for ly in refs}
 for layer,rlayer in [('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]:
  for rr in rec[layer]:
   if rr['kind']=='fill'or L.norm(rr['net'])=='/LOGIC_GND'or dom.get(L.norm(rr['net']))!=dom.get('/LOGIC_GND')or not rr['shape'].intersects(region):continue
   sh=rr['shape'].intersection(refs[rlayer])
   if not sh.is_empty:masks[rlayer].append({'uuid':rr['uuid'],'kind':rr['kind'],'shape':sh})
  for z in q:
   if z['layer']==layer and L.norm(z['net'])!='/LOGIC_GND'and dom.get(L.norm(z['net']))==dom.get('/LOGIC_GND')and z['shape'].intersects(region):
    sh=z['shape'].intersection(refs[rlayer])
    if not sh.is_empty:masks[rlayer].append({'uuid':z['uuid'],'kind':'owned_before_supported_role','shape':sh})
 for ly in refs:
  for rr in lg:
   if rr['kind']=='via'and rr['layer']==ly and rr['shape'].intersects(region):
    sh=rr['shape'].intersection(refs[ly])
    if not sh.is_empty:masks[ly].append({'uuid':rr['uuid'],'kind':'actual_original_source_LG_annulus','shape':sh})
 mt={ly:STRtree([r['shape']for r in masks[ly]])for ly in refs}
 for pose in poses:
  angle,dx,dy=pose['pose'];rigid=lambda sh:affinity.translate(affinity.rotate(sh,angle,origin=(fp['x'],fp['y'])),dx,dy);newcourt=rigid(unary_union(L.poly(fp['courtyard']['F'])));newpads=[{'p':p,'shape':rigid(unary_union(L.poly(p['layers']['F.Cu']))),'xy':[round(rigid(Point(p['x'],p['y'])).x,6),round(rigid(Point(p['x'],p['y'])).y,6)]}for p in pads];sig=next(x for x in newpads if str(x['p']['num'])=='2');seen=set()
  for ret in ports:
   if Point(*ret['xy']).distance(Point(*sig['xy']))>4:continue
   for angleDegrees in range(0,360,5):
    ar=math.radians(angleDegrees);xy=[round(ret['xy'][0]+.95*math.cos(ar),6),round(ret['xy'][1]+.95*math.sin(ar),6)];key=tuple(xy)
    if key in seen or Point(*xy).distance(Point(*sig['xy']))>3:continue
    seen.add(key);point=Point(*xy);bad=[];localLGcuts={};nativeHoleOps=[]
    for ly in K.LAYERS:
     for j in trees[ly].query(point.buffer(1.25),predicate='intersects'):
      rr=rec[ly][int(j)]
      if L.norm(rr['net'])==net:continue
      local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;req=max(local,gap(net,rr['net']))+.025;distance=point.distance(rr['shape'])-.25
      if rr['kind']=='fill'and rr['uuid']in native[3]and dom.get(L.norm(rr['net']))==dom.get(net):
       if distance<req:nativeHoleOps.append({'UUID':rr['uuid'],'raw_net':rr['net'],'layer':ly,'only_normal_native_new_via_antipad_radius_mm':.25+req,'original_outline_settings_UUID_exact':True})
       if L.norm(rr['net'])=='/LOGIC_GND':localLGcuts[ly]=Z.bounded_buffer(point,.25+req)
       continue
      if distance<req:bad.append({'UUID':rr['uuid'],'kind':rr['kind'],'raw_net':rr['net'],'layer':ly,'actual_gap_mm':distance,'planner_required_mm':req})
     for z in q:
      if z['layer']!=ly or L.norm(z['net'])==net:continue
      distance=point.distance(z['shape'])-.25;req=max(float(z['clearance_mm']),gap(net,z['net']))+.025
      if distance<req:bad.append({'UUID':z['uuid'],'kind':'all_foreign_owned_physical_roles_hard','layer':ly,'actual_gap_mm':distance,'planner_required_mm':req})
    for np in newpads:
     if L.norm(np['p']['net'])!=net and point.distance(np['shape'])-.25<.175:bad.append({'kind':'actually_moved_foreign_pad_Cu','pin':np['p']['num']})
     if point.distance(np['shape'])-.1<.28:bad.append({'kind':'all_actually_moved_SMD_to_new_drill_guard','pin':np['p']['num']})
    if point.distance(newcourt)<.275:bad.append({'kind':'moved_actual_R7035_courtyard_no_D4'})
    for j in ct.query(point.buffer(.275),predicate='intersects'):bad.append({'kind':'original_other_component_courtyard_no_D4','ref':courts[int(j)][0]})
    for j in ht.query(point.buffer(.385),predicate='intersects'):
     uid,n,sh=holes[int(j)]
     if point.distance(sh)-.1<.28:bad.append({'kind':'every_real_hole_new_drill_guard','UUID':uid})
    for j in vt.query(point.buffer(.825),predicate='intersects'):
     if point.distance(vxy[int(j)])<.815:bad.append({'kind':'ordinary_all_via_pitch','UUID':h['vias'][int(j)]['uuid']})
    for rules,ex in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
     for rr in rules:
      if not ex and not rr.get('no_vias')or ex and net in exempt.get(rr['name'],set()):continue
      if any(point.distance(sh)<.275 for sh in L.poly(rr['outline'])):bad.append({'kind':'native_or_frozen_reserved_via_rule','name':rr.get('name',rr.get('uuid'))})
    for ly,cut in localLGcuts.items():
     if ly not in refs:continue
     for j in mt[ly].query(cut,predicate='intersects'):
      rr=masks[ly][int(j)];hit=cut.intersection(rr['shape'])
      if not hit.is_empty:bad.append({'kind':'exact_actual_before_supported_body_role_or_source_annulus_mask','UUID':rr['uuid'],'layer':ly,'hit_type':hit.geom_type,'hit_area_mm2':hit.area})
    row={'host_R7035_pose':pose['pose'],'successful_IO3_reconnect':pose,'new_signal_xy':xy,'raw_signal_net':scope['source_pin_nets']['2'],'size_drill_mm':[.5,.2],'existing_original_LG_return':ret,'ordinary_return_distance_mm':point.distance(Point(*ret['xy'])),'explicit_normal_native_same_domain_fill_hole_operations':nativeHoleOps,'deficits':bad,'geometry_original_mask_and_courtyard_eligibility_PASS':not bad};rows.append(row)
    if not bad:eligible.append(row)
   put(O/'finite-ordinary-signal-via-original-source-return-old-mask-native-guard-census.json',rows)
 put(O/'only-eligible-signal-dive-port-existing-source-return-pairs.json',eligible);put(O/'receipt.json',{'verdict':'ORDINARY_ENC_SIGNAL_DIVE_PORT_ELIGIBILITY_WITH_REAL_EXISTING_NATIVE_LG_RETURNS','current_R371_model_sha256':sha(D/'model.pkl'),'R386_closed_source_route_receipt_sha256':sha(N/'receipt.json'),'selected_IO3_source_route_supported_rigid_pose_count':len(poses),'original_actual_two_plane_LG_ports':len(ports),'candidate_count':len(rows),'eligible_count':len(eligible),'existing_LG_return_pair_only_no_new_return_hole_for_signal':True,'normal_native_same_domain_antipads_explicit_original_outlines_profiles_exact':True,'all_foreign_owned_roles_old_supported_bodies_and_source_annuli_hard':True,'F_to_B_or_In3_at_most_three_layer_legs_actual_source_refs_older_contacts_full68_native_pose_and_allmasks':'OPEN','model_source_native_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R388',sha(O/'receipt.json'),len(ports),len(rows),len(eligible),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
