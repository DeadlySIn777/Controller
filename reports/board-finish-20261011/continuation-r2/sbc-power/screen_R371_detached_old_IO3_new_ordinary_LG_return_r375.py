"""One ordinary new LG return near the old IO3 port; no POWER D4 credit."""
import json,pickle,hashlib,sys,time,math,traceback
from pathlib import Path
from shapely.geometry import Point,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
O=H/'sbc-power/CM79-R371-detached-old-IO3-one-new-ordinary-actual-source-LG-return-screen-r375'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
LG='/LOGIC_GND';IO='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups[LG],'J11001','2');refs={ly:unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly])for ly in ('In1.Cu','In4.Cu')};port=next(v for v in h['vias']if v['uuid']=='3945a1ae-f8cb-441a-ad9d-21bde31e0e9f');assert [port['x'],port['y']]==[84.15,24.7];region=Point(port['x'],port['y']).buffer(2);rec,trees=F.build(c);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;originalNative=set(A.C.inventory((H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb').read_bytes())[3]);holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);vxy=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vxy);courts=[(f['ref'],s)for f in h['footprints']for ps in f['courtyard'].values()for s in L.poly(ps)];ct=STRtree([s for ref,s in courts]);reserve,exempt=A.reservations();masks={ly:[]for ly in refs}
 for layer,rlayer in [('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]:
  for rr in rec[layer]:
   if rr['kind']=='fill'or L.norm(rr['net'])==LG or dom.get(L.norm(rr['net']))!=dom.get(LG)or not rr['shape'].intersects(region):continue
   sh=rr['shape'].intersection(refs[rlayer])
   if not sh.is_empty:masks[rlayer].append({'uuid':rr['uuid'],'kind':rr['kind'],'shape':sh})
 for ly in refs:
  for rr in lg:
   if rr['kind']=='via'and rr['layer']==ly and rr['shape'].intersects(region):
    sh=rr['shape'].intersection(refs[ly])
    if not sh.is_empty:masks[ly].append({'uuid':rr['uuid'],'kind':'old_actual_source_LG_annulus','shape':sh})
 mt={ly:STRtree([rr['shape']for rr in masks[ly]])for ly in refs};rows=[];eligible=[]
 for radius in (.925,.95,.975):
  for angle in range(0,360,5):
   ar=math.radians(angle);xy=[round(port['x']+radius*math.cos(ar),6),round(port['y']+radius*math.sin(ar),6)];p=Point(xy);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={ly:ann.intersection(refs[ly]).area for ly in refs};bad=[];normalNativeIO=[]
   if not all(a>.025 for a in areas.values()):continue
   for ly in K.LAYERS:
    for j in trees[ly].query(p.buffer(1.25),predicate='intersects'):
     rr=rec[ly][int(j)]
     if L.norm(rr['net'])==LG:continue
     local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;req=max(local,gap(LG,rr['net']))+.025;dist=p.distance(rr['shape'])-.25
     if rr['kind']=='fill'and L.norm(rr['net'])==IO and rr['uuid']in originalNative and dist<req:
      normalNativeIO.append({'UUID':rr['uuid'],'layer':ly,'explicit_normal_new_via_antipad_radius_mm':.25+req,'original_outline_profile_UUID_exact':True});continue
     if dist<req:bad.append({'UUID':rr['uuid'],'net':rr['net'],'kind':rr['kind'],'layer':ly,'actual_gap_mm':dist,'planner_required_mm':req})
    for z in q:
     if z['layer']!=ly or L.norm(z['net'])==LG:continue
     req=max(float(z['clearance_mm']),gap(LG,z['net']))+.025;dist=p.distance(z['shape'])-.25
     if dist<req:bad.append({'UUID':z['uuid'],'net':z['net'],'kind':'owned_physical_role_hard','layer':ly,'actual_gap_mm':dist,'planner_required_mm':req})
   for j in ht.query(p.buffer(.385),predicate='intersects'):
    uid,n,sh=holes[int(j)];dist=p.distance(sh)-.1
    if dist<.28:bad.append({'UUID':uid,'kind':'every_real_hole_to_new_drill','actual_gap_mm':dist,'planner_required_mm':.28})
   for j in vt.query(p.buffer(.825),predicate='intersects'):
    dist=p.distance(vxy[int(j)])
    if dist<.815:bad.append({'UUID':h['vias'][int(j)]['uuid'],'kind':'ordinary_via_pitch','distance_mm':dist})
   for j in ct.query(p.buffer(.25),predicate='intersects'):bad.append({'ref':courts[int(j)][0],'kind':'actual_component_courtyard_no_POWER_D4'})
   for rules,ex in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
    for rr in rules:
     if not ex and not rr.get('no_vias'):continue
     if ex and LG in exempt.get(rr['name'],set()):continue
     if any(p.distance(sh)<.275 for sh in L.poly(rr['outline'])):bad.append({'kind':'native_or_frozen_reserved_via_rule','name':rr.get('name',rr.get('uuid'))})
   hole=p.buffer(.1,quad_segs=128)
   for ly in refs:
    for j in mt[ly].query(hole,predicate='intersects'):
     rr=masks[ly][int(j)];hit=hole.intersection(rr['shape'])
     if not hit.is_empty:bad.append({'UUID':rr['uuid'],'kind':'actual_old_supported_body_or_ground_source_annulus_drill_hit','layer':ly,'native_kind':rr['kind'],'hit_type':hit.geom_type,'hit_mm2':hit.area})
   row={'new_LG_xy':xy,'size_drill_mm':[.5,.2],'paired_old_IO3_UUID':port['uuid'],'ordinary_pair_distance_mm':p.distance(Point(port['x'],port['y'])),'actual_In1_In4_J1_source_annulus_overlap_mm2':areas,'explicit_normal_native_IO3_fill_hole_operations':normalNativeIO,'deficits':bad,'local_source_geometry_and_old_reference_drill_mask_PASS':not bad};rows.append(row)
   if not bad:eligible.append(row)
 put(O/'all-two-plane-source-eligible-return-site-native-guard-ledger.json',rows);put(O/'only-eligible-new-ordinary-return-sites.json',eligible);put(O/'receipt.json',{'verdict':'READ_ONLY_NEW_ORDINARY_LG_RETURN_LOCAL_GEOMETRY_SOURCE_MASK_SCREEN','current_R371_model_sha256':sha(D/'model.pkl'),'actual_both_source_plane_candidate_count':len(rows),'eligible_count':len(eligible),'declared_radii_mm':[.925,.95,.975],'declared_angle_step_degrees':5,'original_own_masks_source_body_support_and_all_foreign_owned_roles_hard':True,'normal_original_native_IO3_fill_hole_projections_if_selected':'EXPLICIT; no outline/settings or foreign-owned carve','fresh_IO3_all3689_source_direct_oldref_native_and_fullsigned_loop':'OPEN','model_source_native_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R375',sha(O/'receipt.json'),len(rows),len(eligible),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
