"""Read-only ordinary power pairs with exact actual existing source LG ports."""
import hashlib,json,pickle,sys,time,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-widened-ordinary-power-with-existing-actual-source-LG-port-pairs-r314'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def buf(s,r):return set_precision(Z.bounded_buffer(s,r),0)
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());prior=H/'sbc-power/CM79-widened-retained-original-F-anchor-ordinary-port-pairs-r313';proof=json.loads((prior/'receipt.json').read_text());assert proof['model_sha256']==sha(mp)and not proof['adopted'];nom=json.loads((prior/'widened-original-anchor-finite-pair-census.json').read_text())['power_PASS_sites'];old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');axis=LineString([old['a'],old['b']]);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;ctx=K.hole_context(c);_,groups=K.physical(c,'/LOGIC_GND',ctx);root=K.root(groups,'J11001','2');native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=A.C.inventory(native.read_bytes());CM=pickle.loads((H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl').read_bytes());cmids={v['uuid']for v in CM['vias']};fills={ly:[r['shape']for r in root if r['kind']=='fill'and r['layer']==ly]for ly in('In1.Cu','In4.Cu')};ft={ly:STRtree(shs)for ly,shs in fills.items()};ports=[]
 for v in h['vias']:
  if L.norm(v['net'])!='/LOGIC_GND':continue
  ann={ly:unary_union([r['shape']for r in root if r['kind']=='via'and r['uuid']==v['uuid']and r['layer']==ly])for ly in K.LAYERS}
  if not all(not ann[ly].is_empty and ann[ly].area>0 for ly in('In1.Cu','In4.Cu')):continue
  aa={}
  for ly in('In1.Cu','In4.Cu'):
   local=unary_union([fills[ly][int(i)]for i in ft[ly].query(ann[ly],predicate='intersects')]);aa[ly]=ann[ly].intersection(local).area
  if not all(x>0 for x in aa.values()):continue
  ports.append({'via':v,'native_original_UUID':v['uuid']in iv[3],'unadopted_CM49_owned_UUID':v['uuid']in cmids,'current_actual_annuli_mm2_by_layer':{ly:s.area for ly,s in ann.items()if not s.is_empty},'current_actual_source_fill_contacts_mm2':aa,'prospective_CM_all6_native_mask_qualification':'OPEN'if v['uuid']in cmids else'ORIGINAL_ACTUAL_MASK_RETAINED'})
 put(O/'actual-source-LG-port-census.json',ports);records,trees=F.build({**c,'zones':[]},layers={'In2.Cu'});reserve,exempt=A.reservations();qon=[(z['uuid'],z['net'],set_precision(z['shape'],0),float(z['clearance_mm']))for z in q if z['layer']=='In2.Cu'];holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];matched={};rejected={}
 for label,pps in nom.items():
  good=[];bad=[]
  for pp in pps:
   for port in ports:
    vv=port['via'];d=math.hypot(pp['x']-vv['x'],pp['y']-vv['y'])
    if not .9<=d<=1.0:continue
    centre=Point(vv['x'],vv['y']);localaxis=LineString([[pp['x'],202.35],[116.2 if label=='left'else 120.1,202.35]]);req=gap(old['net'],vv['net'])+.025003;actual=centre.distance(localaxis)-.625-vv['d']/2;hole=centre.distance(localaxis)-.625-vv['drill']/2-.005;rr={'power':pp,'existing_actual_source_ground_port':port,'ordinary_centre_distance_mm':d,'full1p25_In2_candidate_to_existing_ground_via_actual_Cu_gap_mm':actual,'planner_required_mm':req,'foreign_ground_hole_guarded_edge_mm':hole,'foreign_ground_hole_required_mm':.275,'no_new_ground_hole_or_CM49_port_move':True}
    if actual<req or hole<.275:bad.append(rr);continue
    good.append(rr)
   if len(good)>=80:break
  matched[label]=good;rejected[label]=bad;print('R314_SIDE',label,len(good),len(bad),flush=True)
 put(O/'ordinary-existing-source-port-pair-matrix.json',{'matched':matched,'mutual_fullwidth_rejected':rejected});proposals=[]
 for left in matched.get('left',[])[:30]:
  for right in matched.get('right',[])[:30]:
   a=[left['power']['x'],202.35];bb=[right['power']['x'],202.35];line=LineString([a,bb]);body=buf(line,.625);bad=[]
   for j in trees['In2.Cu'].query(body.buffer(1),predicate='intersects'):
    rr=records['In2.Cu'][int(j)]
    if L.norm(rr['net'])==L.norm(old['net']):continue
    if rr['kind']=='track'and not rr['source'].get('m'):tt=rr['source'];dd=line.distance(LineString([tt['a'],tt['b']]))-.625-tt['w']/2
    elif rr['kind']=='via':vv=rr['source'];dd=line.distance(Point(vv['x'],vv['y']))-.625-vv['d']/2
    else:dd=line.distance(rr['shape'])-.625
    required=gap(old['net'],rr['net'])+.025003
    if dd<required:bad.append({'kind':rr['kind'],'uuid':rr['uuid'],'net':rr['net'],'actual_gap_mm':dd,'planner_required_mm':required})
   for u,n,sh,local in qon:
    if L.norm(n)==L.norm(old['net']):continue
    dd=body.distance(sh);required=max(gap(old['net'],n),local)+.025003
    if dd<required:bad.append({'kind':'owned_q_hard','uuid':u,'net':n,'actual_gap_mm':dd,'planner_required_mm':required})
   for u,n,sh in holes:
    if L.norm(n)==L.norm(old['net']):continue
    if body.distance(sh)<.280003:bad.append({'kind':'foreign_real_hole','uuid':u,'net':n,'guarded_edge_mm':body.distance(sh)-.005,'required_mm':.275})
   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
    for rr in rules:
     if'In2.Cu'not in rr['layers']or(not ex and not rr.get('no_tracks'))or(ex and L.norm(old['net'])in exempt.get(rr['name'],set())):continue
     if any(body.distance(sh)<.025003 for sh in L.poly(rr['outline'])):bad.append({'kind':'frozen_rule','name':rr.get('name',rr.get('uuid'))})
   row={'left':left,'right':right,'axis':[a,bb],'width_mm':1.25,'new_In2_length_mm':line.length,'original_F_middle_delete_axis':[[116.2,202.35],[120.1,202.35]],'only_added_In2_anchor_overlap_mm':line.length-3.9,'full_new_actual_discrete_q_hole_rule_deficits':bad,'full_new_In2_hard_geometry_PASS':not bad};proposals.append(row)
   if not bad:
    fn=O/'first-legal-fullwidth-In2-provisional-body.wkb';fn.write_bytes(body.wkb);row['full1p25_actual_provisional_body_WKB_sha256']=sha(fn);put(O/'first-legal-fullwidth-In2-existing-ground-port-proposal.json',row);break
  if proposals and proposals[-1]['full_new_In2_hard_geometry_PASS']:break
 put(O/'fullwidth-In2-existing-return-pair-combination-census.json',proposals);legal=any(r['full_new_In2_hard_geometry_PASS']for r in proposals);put(O/'receipt.json',{'verdict':'EXISTING_ACTUAL_RETURN_PORT_FULLWIDTH_CM79_DIAGNOSTIC_NOMINATION_PENDING_ALL_GATES'if legal else'NO_STRAIGHT_FULLWIDTH_CM79_EXISTING_RETURN_PORT_NOMINATION_IN_DECLARED_PAIRS','exact_failed_diagnostic_model_sha256':sha(mp),'exact_R313_power_nomination_receipt_sha256':sha(prior/'receipt.json'),'exact_R313_power_nomination_file_sha256':sha(prior/'widened-original-anchor-finite-pair-census.json'),'actual_source_LG_port_count':len(ports),'ordinary_existing_port_pair_counts':{k:len(v)for k,v in matched.items()},'fullwidth_pair_combination_count':len(proposals),'only_new_power_ports_diameter_drill_mm':[.5,.2],'new_ground_holes':0,'original_full1p25_F_pre_post_anchor_Cu_preserved':True,'D4_POWER_permission_or_aperture_radius_expansion':False,'fresh_all49_source_direct_contacts_strict_oldref_newfullbody_actualnative_all6_current_plating_bottleneck_drop_thermal_fault':'OPEN','inherited_CORE_fullbody_FIELD_IO3_and_reference_FAIL_flags_retained':True,'model_source_rules_board_native_changes':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R314_COMPLETE',sha(O/'receipt.json'),legal,flush=True)
if __name__=='__main__':main()
