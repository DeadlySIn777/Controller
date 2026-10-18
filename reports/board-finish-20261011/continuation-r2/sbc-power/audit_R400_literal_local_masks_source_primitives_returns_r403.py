"""Constructive scoped old-reference preservation, preserving raw global gates as OPEN."""
import sys,json,pickle,hashlib,time,traceback,collections
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
N=H/'sbc-power/CM79-R397-exact-five-tracks-three-ordinary-vias-R7035-real-pose-r398'
P=H/'sbc-power/CM79-R398-native-R7035-real-pose-three-via-mask-readonly-r399'
B=H/'sbc-power/CM79-R398-actual-native-pad-local-aperture-fresh-source-r400'
O=H/'sbc-power/CM79-R400-literal-local-mask-source-primitive-two-plane-return-audit-r403'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());gg,hh,bb,qq,cc=pickle.loads((B/'model.pkl').read_bytes());assert g==gg and b==bb;pack=pickle.loads((N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl').read_bytes());own={p['uuid']for p in pack['R7035_source_scope']['pads']};sourceRows=json.loads((B/'fresh-all-changed-source-oldgroups-and-pad-layer-keys.json').read_text());otherIdentity=json.loads((B/'other-source-bank-new-hole-disjoint-full-physics-identity.json').read_text());newBodyRows=json.loads((B/'all-five-new-body-and-two-native-full-SMD-source-reference-proof.json').read_text());fresh=pickle.loads((B/'fresh-actual-drilled-all-source-groups.pkl').read_bytes());before=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());oldRoot=K.root(before['/LOGIC_GND'],'J11001','2');newRoot=K.root(fresh['/LOGIC_GND'],'J11001','2');projection=json.loads((B/'explicit-local-original-native-plane-hole-pad-track-impact.json').read_text());tracks={t['uuid']:t for t in pack['tracks']};vias={v['uuid']:v for v in pack['vias']};pads={p['uuid']:p for p in cc['pads']if p['uuid']in own};cuts=[]
 for rr in projection:
  if L.norm(rr['raw_net'])!='/LOGIC_GND':continue
  for op in rr['exact_declared_new_physical_Cu_and_hole_operations']:
   uid=op['new_UUID'];kind=op['kind']
   if kind=='via':candidate=[Z.bounded_disk(vias[uid],op['physical_native_radius_mm'])]
   elif kind=='track':t=tracks[uid];candidate=[Z.bounded_buffer(LineString([t['a'],t['b']]),op['physical_native_radius_mm'])]
   else:candidate=[Z.bounded_buffer(sh,op['native_local_clearance_mm'])for sh in L.poly(pads[uid]['native_outside_layers'].get(rr['layer'],[]))]
   sh=next(x for x in candidate if hashlib.sha256(x.wkb).hexdigest()==op['cutter']['WKB_sha256']);cuts.append({'zone_UUID':rr['zone_UUID'],'layer':rr['layer'],'new_UUID':uid,'shape':sh})
 # Physical hole_context also removes every new drill from every current fill.
 for v in pack['vias']:
  for ly in K.LAYERS:cuts.append({'zone_UUID':'EVERY_ACTUAL_PHYSICAL_FILL','layer':ly,'new_UUID':v['uuid'],'shape':Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)})
 afterSourceHash={(r['uuid'],r['layer'],r['shape'].wkb)for r in newRoot if r['kind']=='fill'};unchanged=[];missing=[];changed=[]
 for r in oldRoot:
  if r['kind']!='fill':continue
  intersects=[op for op in cuts if op['layer']==r['layer']and(op['zone_UUID']in(r['uuid'],'EVERY_ACTUAL_PHYSICAL_FILL'))and op['shape'].intersects(r['shape'])]
  row={'UUID':r['uuid'],'layer':r['layer'],'old_actual_source_primitive':ds(r['shape'])}
  if not intersects:
   row['WKB_identical_source_rooted_after_counterpart']=(r['uuid'],r['layer'],r['shape'].wkb)in afterSourceHash;unchanged.append(row)
   if not row['WKB_identical_source_rooted_after_counterpart']:missing.append(row)
  else:row['only_declared_local_remove_only_cut_UUIDs']=sorted({op['new_UUID']for op in intersects});changed.append(row)
 put(O/'all-unchanged-original-actual-J1-source-fill-primitive-exact-counterparts.json',unchanged);put(O/'unchanged-source-primitive-missing-counterparts-FAIL.json',missing);put(O/'only-original-source-primitives-intersecting-declared-local-holes-newCu.json',changed);print('R403_PRIMITIVES',len(unchanged),len(missing),len(changed),flush=True)
 oldAllHashes={(r['uuid'],r['layer'],r['shape'].wkb)for xs in before['/LOGIC_GND']for r in xs if r['kind']=='fill'};oldSourceBy=collections.defaultdict(list)
 for r in oldRoot:
  if r['kind']=='fill':oldSourceBy[r['uuid'],r['layer']].append(r['shape'])
 oldSourceTree={key:STRtree(ss)for key,ss in oldSourceBy.items()};rootIndex=next(i for i,xs in enumerate(fresh['/LOGIC_GND'])if any(r['kind']=='pad'and r.get('ref')=='J11001'and str(r.get('pin'))=='2'for r in xs));detached=[];nonRootUnchanged=0;newNonRootChecks=0
 for i,xs in enumerate(fresh['/LOGIC_GND']):
  if i==rootIndex:continue
  for r in xs:
   if r['kind']!='fill':continue
   key=(r['uuid'],r['layer'])
   if(r['uuid'],r['layer'],r['shape'].wkb)in oldAllHashes:nonRootUnchanged+=1;continue
   if key not in oldSourceTree:continue
   newNonRootChecks+=1
   for j in oldSourceTree[key].query(r['shape'],predicate='intersects'):
    hit=r['shape'].intersection(oldSourceBy[key][int(j)])
    if not hit.is_empty:detached.append({'UUID':r['uuid'],'layer':r['layer'],'after_non_J1_group':i,'raw_nonempty_old_source_primitive_contact':ds(hit)})
 put(O/'changed-surviving-original-source-fill-detachment-FAIL.json',detached);print('R403_SOURCE_FILL_MEMBERSHIP',nonRootUnchanged,newNonRootChecks,len(detached),flush=True)
 rec,trees=F.build(c);beforeCtx=K.hole_context(c);hits=[];checks=[];seen=set();sourceFills={ly:[r['shape']for r in oldRoot if r['kind']=='fill'and r['layer']==ly]for ly in('In1.Cu','In4.Cu')};sourceTrees={ly:STRtree(ss)for ly,ss in sourceFills.items()}
 for op in cuts:
  rlayer=op['layer']
  if rlayer not in sourceFills:continue
  cut=op['shape'];localRef=unary_union([sourceFills[rlayer][int(j)]for j in sourceTrees[rlayer].query(cut,predicate='intersects')]).intersection(cut)
  if localRef.is_empty:continue
  layers=('F.Cu','In2.Cu')if rlayer=='In1.Cu'else('B.Cu','In3.Cu')
  for layer in layers:
   candidates=[rec[layer][int(j)]for j in trees[layer].query(cut,predicate='intersects')]
   candidates += [{'uuid':z['uuid'],'net':z['net'],'kind':'owned_physical_role','shape':z['shape']}for z in q if z['layer']==layer and z['shape'].intersects(cut)]
   for r in candidates:
    if r['kind']=='fill'or r['uuid']in own or h['domains_normalized'].get(L.norm(r['net']))!=h['domains_normalized'].get('/LOGIC_GND'):continue
    key=(op['zone_UUID'],op['new_UUID'],layer,r['kind'],r['uuid'])
    if key in seen:continue
    seen.add(key);body=r['shape'].difference(unary_union([beforeCtx[0][int(j)]for j in beforeCtx[1].query(r['shape'],predicate='intersects')]));hit=body.intersection(localRef);row={'old_UUID':r['uuid'],'old_kind':r['kind'],'old_layer':layer,'declared_cut_UUID':op['new_UUID'],'source_reference_plane':rlayer,'exact_literal_before_supported_body_mask_hit':ds(hit)};checks.append(row)
    if not hit.is_empty:hits.append(row)
  for r in oldRoot:
   if r['kind']!='via'or r['layer']!=rlayer or not r['shape'].intersects(cut):continue
   hit=r['shape'].intersection(localRef);row={'old_UUID':r['uuid'],'old_kind':'SOURCE_LG_NATIVE_ANNULUS','old_layer':rlayer,'declared_cut_UUID':op['new_UUID'],'exact_literal_before_supported_body_mask_hit':ds(hit)};checks.append(row)
   if not hit.is_empty:hits.append(row)
 put(O/'literal-all-declared-cuts-before-supported-Cu-role-source-annulus-mask-checks.json',checks);put(O/'literal-local-old-reference-mask-hits-FAIL.json',hits);print('R403_LOCAL_MASKS',len(checks),len(hits),flush=True)
 refs={ly:unary_union([r['shape']for r in newRoot if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')};ports=[]
 for v in pack['vias']:
  if L.norm(v['net'])!='/LOGIC_GND':continue
  ov={ly:unary_union([r['shape']for r in newRoot if r['kind']=='via'and r['uuid']==v['uuid']and r['layer']==ly]).intersection(refs[ly]).area for ly in refs};ports.append({'UUID':v['uuid'],'xy_mm':[v['x'],v['y']],'fresh_actual_J1_source_annulus_plane_overlap_mm2':ov,'both_positive':all(x>0 for x in ov.values())})
 put(O/'both-new-ordinary-LG-returns-fresh-actual-J1-source-annuli.json',ports);bodyFail=sum(not x.get('exact_inner_guard_reference_gap',x.get('whole_actual_J1_In1_reference_gap'))['EMPTY']for x in newBodyRows);keysLost=sum(len(x['all_old_source_keys_lost'])for x in sourceRows.values());groupsLost=sum(len(x['old_group_relationship_losses'])for x in sourceRows.values());put(O/'receipt.json',{'verdict':'CONSTRUCTIVE_SCOPED_OLD_SOURCE_REFERENCE_MASK_AND_ORDINARY_RETURN_AUDIT_FULL_NATIVE_OPEN','R400_diagnostic_model_sha256':sha(B/'model.pkl'),'R398_packet_sha256':sha(N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl'),'R399_actual_native_API_sha256':sha(P/'actual-native-API.json'),'source_key_loss_count':keysLost,'old_group_relationship_loss_count':groupsLost,'other_source_exact_newhole_disjoint_bank_count':len(otherIdentity),'new_five_body_and_two_native_OUTSIDE_SMD_ref_FAIL_count':bodyFail,'unchanged_actual_J1_source_fill_primitive_count':len(unchanged),'unchanged_primitive_WKB_counterpart_loss_count':len(missing),'only_locally_changed_source_primitive_count':len(changed),'surviving_changed_old_source_fill_detachment_FAIL_count':len(detached),'literal_before_supported_Cu_role_SOURCE_annulus_vs_every_local_cut_check_count':len(checks),'literal_local_old_reference_mask_hit_FAIL_count':len(hits),'new_LG_actual_two_source_plane_annulus_FAIL_count':sum(not p['both_positive']for p in ports),'constructive_source_primitive_membership_plus_literal_local_mask_oldref_PASS':not missing and not detached and not hits,'raw_global_perbody_original_ref_predicate':'R401 unfinished retained; OPEN for matched full combined native allnet audit; no area/radius/predicate waiver','one_combined_full_native_candidate_refill_allmasks_finite_terminal_loop_signed_current_capacity_SI_thermal':'OPEN','inherited_CORE14_CORE93_and_other_FAILs':'RETAINED','adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R403',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
