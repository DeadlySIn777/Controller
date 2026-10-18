"""Fresh ordinary pair on the signal side; R7036 remains at its exact original pose."""
import json,pickle,hashlib,sys,time,math,traceback
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
from nominate_R371_coupled_R7036_minimal_rigid_pad_poses_r391 import moved
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
N=H/'sbc-power/CM79-R371-R7035-one-ENC-ordinary-signal-via-existing-LG-return-eligibility-r388'
O=H/'sbc-power/CM79-R371-new-ordinary-ENC-plus-LG-pair-signal-side-original-R7036-r396'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());scope=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());pose=[180,-3.4,3.0];mm=moved(scope,pose);own={p['uuid']for p in scope['pads']};net=L.norm(scope['source_pin_nets']['2']);saved=json.loads((N/'finite-ordinary-signal-via-original-source-return-old-mask-native-guard-census.json').read_text());io=next(r['successful_IO3_reconnect']for r in saved if r['host_R7035_pose']==pose);ioBody=Z.bounded_buffer(LineString(io['path']),.1);put(O/'exact-original-R7036-held-R7035-scope-and-IO3-path.json',{'host_R7035_pose':pose,'R381_receipt_sha256':sha(P/'receipt.json'),'IO3_path':io,'R7036_pose':'ORIGINAL_NATIVE_AST_EXACT','only_R7035_two_owned_pads_withdrawn_for_real_rigid_move':True})
 groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');region=box(76,22,86,33);fills={ly:[rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly]for ly in('In1.Cu','In4.Cu')};ft={ly:STRtree(ss)for ly,ss in fills.items()};refs={ly:zero(unary_union([ss for ss in fills[ly]if ss.intersects(region)]).intersection(region.buffer(2)))for ly in fills};base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};rec,trees=F.build(base);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;native=A.C.inventory((H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb').read_bytes());zones={z['uuid']:z for z in c['zones']};holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);vxy=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vxy);courts=[(f['ref'],sh)for f in h['footprints']if f['ref']!='R7035'for ps in f['courtyard'].values()for sh in L.poly(ps)]+[('actual_moved_R7035',mm['court'])];ct=STRtree([sh for r,sh in courts]);reserve,exempt=A.reservations();masks={ly:[]for ly in refs}
 for layer,rlayer in[('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]:
  for rr in rec[layer]:
   if rr['kind']=='fill'or dom.get(L.norm(rr['net']))!=dom.get('/LOGIC_GND')or not rr['shape'].intersects(region):continue
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
    if not sh.is_empty:masks[ly].append({'uuid':rr['uuid'],'kind':'actual_original_SOURCE_LG_annulus','shape':sh})
 mt={ly:STRtree([r['shape']for r in masks[ly]])for ly in refs};sigPad=next(p for p in mm['pads']if str(p['old']['num'])=='2');rows=[];sigLegal=[];pairs=[]
 def screen(xy,newnet):
  point=Point(*xy);bad=[];ops=[];referenceCuts={}
  for ly in K.LAYERS:
   for j in trees[ly].query(point.buffer(1.3),predicate='intersects'):
    rr=rec[ly][int(j)]
    if L.norm(rr['net'])==newnet:continue
    local=float(zones[rr['uuid']]['clearance_mm'])if rr['kind']=='fill'and rr['uuid']in zones else .15;req=max(local,gap(newnet,rr['net']))+.025;dd=point.distance(rr['shape'])-.25
    if rr['kind']=='fill'and rr['uuid']in native[3]and dom.get(L.norm(rr['net']))==dom.get(newnet):
     if dd<req:ops.append({'UUID':rr['uuid'],'layer':ly,'raw_net':rr['net'],'actual_native_antipad_radius_mm':.25+local,'conservative_planner_antipad_radius_mm':.25+req,'original_native_outline_settings_UUID_exact':True})
     if L.norm(rr['net'])=='/LOGIC_GND':referenceCuts[ly]=Z.bounded_buffer(point,.25+req)
     continue
    if dd<req:bad.append({'kind':'original_foreign_native_Cu','UUID':rr['uuid'],'layer':ly,'raw_net':rr['net'],'gap_mm':dd,'required_mm':req})
   for z in q:
    if z['layer']==ly and L.norm(z['net'])!=newnet and point.distance(z['shape'])-.25<max(float(z['clearance_mm']),gap(newnet,z['net']))+.025:bad.append({'kind':'all_foreign_owned_role_hard','UUID':z['uuid'],'layer':ly})
  for np in mm['pads']:
   if L.norm(np['old']['net'])!=newnet and point.distance(np['shape'])-.25<.175:bad.append({'kind':'actual_moved_R7035_foreign_pad_Cu','pin':np['old']['num']})
   if point.distance(np['shape'])-.1<.28:bad.append({'kind':'actual_moved_R7035_SMD_to_new_drill','pin':np['old']['num']})
  if newnet!='/IO_3V3'and point.distance(ioBody)-.25<.175:bad.append({'kind':'qualified_new_IO3_F_reconnect_Cu'})
  for j in ct.query(point.buffer(.275),predicate='intersects'):bad.append({'kind':'real_component_courtyard_no_D4','ref':courts[int(j)][0]})
  for j in ht.query(point.buffer(.385),predicate='intersects'):
   uid,hs=holes[int(j)]
   if point.distance(hs)-.1<.28:bad.append({'kind':'all_real_hole_new_drill_guard','UUID':uid})
  for j in vt.query(point.buffer(.825),predicate='intersects'):
   if point.distance(vxy[int(j)])<.815:bad.append({'kind':'ordinary_original_via_pitch','UUID':h['vias'][int(j)]['uuid']})
  for rules,ex in[(h['rule_areas'],False),(reserve['keepouts'],True)]:
   for rr in rules:
    if not ex and not rr.get('no_vias')or ex and newnet in exempt.get(rr['name'],set()):continue
    if any(point.distance(sh)<.275 for sh in L.poly(rr['outline'])):bad.append({'kind':'native_or_frozen_reserved_via_rule','name':rr.get('name',rr.get('uuid'))})
  for ly in refs:
   cut=referenceCuts.get(ly,point.buffer(.1,quad_segs=128))
   for j in mt[ly].query(cut,predicate='intersects'):
    rr=masks[ly][int(j)];hit=cut.intersection(rr['shape'])
    if not hit.is_empty:bad.append({'kind':'every_actual_before_supported_body_role_source_annulus_mask','UUID':rr['uuid'],'layer':ly,'hit_type':hit.geom_type,'hit_area_mm2':hit.area})
   if ly=='In1.Cu':
    for np in mm['pads']:
     hit=cut.intersection(np['shape'])
     if not hit.is_empty:bad.append({'kind':'new_whole_R7035_SMD_reference_mask','pin':np['old']['num'],'hit_mm2':hit.area})
  return bad,ops
 candidates=sorted([[round(78.2+.2*i,6),round(24.2+.2*j,6)]for i in range(26)for j in range(31)],key=lambda xy:Point(*xy).distance(Point(*sigPad['xy'])))
 for xy in candidates:
  if Point(*xy).distance(Point(*sigPad['xy']))>3:continue
  bad,ops=screen(xy,net);row={'new_SIG_xy':xy,'deficits':bad,'explicit_normal_native_same_domain_hole_operations':ops};rows.append(row)
  if bad:continue
  sigLegal.append(row)
  for a in range(0,360,10):
   angle=math.radians(a);gxy=[round(xy[0]+.95*math.cos(angle),6),round(xy[1]+.95*math.sin(angle),6)];gp=Point(*gxy);ann=gp.buffer(.25,quad_segs=128).difference(gp.buffer(.1,quad_segs=128));overlaps={ly:ann.intersection(unary_union([fills[ly][int(j)]for j in ft[ly].query(ann,predicate='intersects')])).area for ly in fills}
   if not all(v>0 for v in overlaps.values()):continue
   gbad,gops=screen(gxy,'/LOGIC_GND');pair={'new_SIG_xy':xy,'new_LG_xy':gxy,'ordinary_pair_distance_mm':Point(*xy).distance(gp),'both_sizes_drills_mm':[.5,.2],'actual_current_SOURCE_LG_annulus_plane_overlap_mm2':overlaps,'signal_hole_ops':ops,'ground_hole_ops':gops,'deficits':gbad,'exact_R7035_pose':pose,'R7036_unchanged':True}
   if not gbad:pairs.append(pair)
  if len(rows)%25==0:put(O/'finite-new-SIG-via-native-mask-guard-screen.json',rows);put(O/'eligible-new-ordinary-SIG-source-LG-pairs.json',pairs)
 put(O/'finite-new-SIG-via-native-mask-guard-screen.json',rows);put(O/'only-native-mask-eligible-new-SIG-sites.json',sigLegal);put(O/'eligible-new-ordinary-SIG-source-LG-pairs.json',pairs);(O/'exact-R7035-pose-and-existing-IO3-reconnect.pkl').write_bytes(pickle.dumps({'R7035':mm,'scope':scope,'IO3_path':io},protocol=5));put(O/'receipt.json',{'verdict':'NEW_ORDINARY_ENC_SIGNAL_LG_PAIR_ELIGIBILITY_ORIGINAL_R7036_HELD','R371_model_sha256':sha(D/'model.pkl'),'R7035_host_pose':pose,'new_SIG_candidate_count':len(rows),'new_SIG_native_mask_guard_eligible_count':len(sigLegal),'new_SIG_LG_ordinary_SOURCE_pair_eligible_count':len(pairs),'all_original_R7036_native_AST_pads_Cu_court_source_contacts_held':True,'no_D4_no_newslot_no_source_mask_waiver':True,'exact_fullsource_native_filled_both_annuli_reconnect_allmasks_current_thermal':'OPEN','model_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R396',sha(O/'receipt.json'),len(rows),len(sigLegal),len(pairs),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
