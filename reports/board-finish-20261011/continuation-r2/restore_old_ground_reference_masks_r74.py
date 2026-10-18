"""Remove-only owned-plane proposal for exact prior source-ground-covered copper."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import complete_geometry_r2 as G
import audit_aux_exact_raw as A
import restore_SAFE_generated_precision_states_r168 as PS
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def root(groups,ref,pin):return next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)for q in xs))
def main():
 out=H/'SAFE-old-source-ground-reference-power-scope-proposal-r74';assert not out.exists();out.mkdir()
 mp=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';assert sha(mp)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011'
 old,h,b,z,current=pickle.loads(mp.read_bytes());bg=H/'logic-two-independent-full-r43/groups.pkl';ng=H/'SAFE-logic-four-independent-full-r57/groups.pkl';groups=pickle.loads(bg.read_bytes());parentgroups={net:F.graph(current,net) for net in ['/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V','/IO_3V3','/CORE_1V2','/mc_local_power/CORE_5V']}
 extra_UIDs={'ec99314b-c244-5748-bb67-de032c66ee3c','93bd9369-a6ff-537a-8678-5c84db255e75'};basez=[q for q in z if q['uuid'] not in extra_UIDs];assert len(basez)==36;precision=PS.restore_bound_generated_precision_states(b,basez)
 for extra in [q for q in z if q['uuid'] in extra_UIDs]:
  for key in ('shape','zone_outline_shape'):
   if key not in extra:continue
   before=digest(extra[key]);extra[key]=set_precision(extra[key],1e-6,mode='pointwise');assert digest(extra[key])==before
   precision.append({'UUID':extra['uuid'],'role':key,'grid_mm':1e-6,'WKB_before_after_exact':before,'constructor_origin':'exact nm-quantized ROOT55 or ROOT73 new owned strip'})
 put(out/'bound-precision-operation-replay.json',precision)
 lostfile=H/'SAFE-logic-four-independent-full-r57/reference-checkpoint.json';assert sha(H/'SAFE-logic-four-independent-full-r57/receipt.json')=='203e598c36adb975374b393929fcb26e40a42315a3eb35eb80a46e967e5b6f52'
 lostrows=json.loads(lostfile.read_bytes());lostby={row['net']:{q['uuid']for q in row['retained_outer_reference_losses']}for row in lostrows};assert sum(map(len,lostby.values()))==303
 proposalfile=H/'sbc-power/CORE1V2-own-rail-shadow-classification-proposal-r191/receipt.json';assert sha(proposalfile)=='bd84507d3c6321e21abeb40c1dd0ee9c847a5f7ae97d799795e05d12131fba4a';proposal=json.loads(proposalfile.read_bytes());assert proposal['verdict']=='SOURCE_BACKED_SCOPED_POWER_VS_SIGNAL_CLASSIFICATION_PROPOSAL_ONLY'and not proposal['original_strict_checker_modified']and not proposal['physical_PDN_qualified']
 candidates=proposal['literal_same_raw_CORE1V2_B_power_candidate_rows'];power_UIDs={q['exact_track_UUID']for q in candidates};assert len(power_UIDs)==20 and power_UIDs<=lostby['/LOGIC_GND']
 bytrack={t['uuid']:t for t in h['tracks']};assert all(bytrack[uid]['net']=='/CORE_1V2'and bytrack[uid]['layer']=='B.Cu'for uid in power_UIDs)
 reviewfile=H/'sbc-power/remaining84-power-shadow-source-resolved-tap-review-r204/receipt.json';assert sha(reviewfile)=='0f0c7b723c2f010dd7af20e935eed7afd946cf61badef0819f6ad7f16fd43801';review=json.loads(reviewfile.read_bytes());assert review['source_sha256']==proposal['source_sha256']=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 remaining=review['literal84_rows'];other_UIDs={q['exact_track_UUID']for q in remaining};assert len(other_UIDs)==84 and not(power_UIDs & other_UIDs)and other_UIDs<=lostby['/LOGIC_GND']
 for row in remaining:
  assert row['classification']=='LITERAL_SOURCE_BACKED_DC_SUPPLY_DISTRIBUTION_CANDIDATE_REQUIRES_PDN_QUALIFICATION'and not row['row_exempted']
  assert bytrack[row['exact_track_UUID']]==row['actual_current_native_track'],'Only exact source-reviewed native track geometry may enter this proposal'
 power_UIDs |= other_UIDs;assert len(power_UIDs)==104
 lostby['/LOGIC_GND']-=power_UIDs;assert len(lostby['/LOGIC_GND'])==130 and sum(map(len,lostby.values()))==199
 put(out/'additional84-source-backed-PDN-proposal.json',{'source_review_sha256':sha(reviewfile),'exact104_literal_DC_distribution_track_UUIDs':sorted(power_UIDs),'all130_logic_signal_shadows_hard':True,'all56_FA_and13_FB_shadows_hard':True,'original_raw_reference_FAIL_unchanged':True,'PDN_current_decoupling_loop_ground_return_stability_transient_native':'OPEN','not_a_board_release_waiver':True})
 put(out/'own-power-candidate-proposal.json',{'proposal_sha256':sha(proposalfile),'exact104_source_reviewed_power_track_UUIDs':sorted(power_UIDs),'geometry_masks_omit_only_these_candidates':True,'strict_original_checker_still_FAIL_unchanged':True,'PDN_loop_decoupling_source_current_return_stability_transient_qualification':'OPEN','adoption_and_host_retention_flags':False})
 refdata=[]
 for ground,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  prior=root(groups[ground],ref,'2')
  for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
   oldref=unary_union([q['shape']for q in prior if q['kind']=='fill'and q['layer']==inner]);local=max(float(q['clearance_mm'])for q in h['zones']if C.norm(q['net'])==ground and inner in q['fills'])
   shadows=[]
   for t in h['tracks']:
    if t['uuid']not in lostby[ground]:continue
    if t['layer']!=outer or C.norm(t['net'])==ground or h['domains_normalized'].get(C.norm(t['net']))!=h['domains_normalized'][ground]:continue
    body=A.shape({'kind':'segment',**t});protected=body.intersection(oldref)
    if not protected.is_empty:shadows.append(protected)
   combined=unary_union(shadows);refdata.append({'ground':ground,'layer':inner,'source':ref+'.2','native_ground_max_local_mm':local,'shadow':combined,'old_source_body_shadow_WKB_sha256':digest(combined),'eligible_tracks':len(shadows)})
 result=[];ledger=[]
 for q in z:
  cuts=[]
  for row in refdata:
   if q['layer']!=row['layer'] or C.norm(q['net'])==row['ground']:continue
   guard=max(G.gap(h,q['net'],row['ground']),float(q.get('clearance_mm',.15)),row['native_ground_max_local_mm'])+.025+.000020
   if q['shape'].distance(row['shadow'])>guard:continue
   cut=N.bounded_buffer(row['shadow'],guard);cuts.append((row,guard,cut))
  if not cuts:result.append(q);continue
  cutter=unary_union([c for row,guard,c in cuts]);shape=q['shape'].difference(cutter);outline=q.get('zone_outline_shape',q['shape']).difference(cutter)
  if shape.equals(q['shape'])and outline.equals(q.get('zone_outline_shape',q['shape'])):result.append(q);continue
  assert shape.difference(q['shape']).is_empty and outline.difference(q.get('zone_outline_shape',q['shape'])).is_empty,'No positive-plane expansion permitted'
  n=copy.deepcopy(q);n['shape']=shape;n['zone_outline_shape']=outline;result.append(n)
  ledger.append({'UUID':q['uuid'],'net':q['net'],'layer':q['layer'],'before_WKB_sha256':digest(q['shape']),'after_WKB_sha256':digest(shape),'physical_removed_mm2':q['shape'].difference(shape).area,'physical_added_mm2':shape.difference(q['shape']).area,'outline_removed_mm2':q.get('zone_outline_shape',q['shape']).difference(outline).area,'outline_added_mm2':outline.difference(q.get('zone_outline_shape',q['shape'])).area,'empty':shape.is_empty,'source_shadow_cutters':[{'ground':row['ground'],'source':row['source'],'required_guard_mm':guard,'cut_WKB_sha256':digest(cut),'source_covered_old_body_shadow_WKB_sha256':row['old_source_body_shadow_WKB_sha256']}for row,guard,cut in cuts]})
  print('R74_NEW_PLANE_REMOVED',q['uuid'],q['net'],ledger[-1]['physical_removed_mm2'],flush=True)
 put(out/'remove-only-ledger.json',ledger);(out/'owned-new-zone-updates.pkl').write_bytes(pickle.dumps([q for q in result if any(r['UUID']==q['uuid']for r in ledger)],protocol=5));projected,retreat=N.projected(old,h,result);(out/'full-projection-ledger.json').write_text(json.dumps(retreat,indent=1)+'\n')
 sourcechecks=[];newgroups={}
 for net,ref,pin in [('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/IO_3V3','R18001','2'),('/CORE_1V2','L2001','2'),('/mc_local_power/CORE_5V','R11022','2')]:
  prior=root(parentgroups[net],ref,pin);after=F.graph(projected,net);newgroups[net]=after;nr=root(after,ref,pin);lost=F.discrete_keys(prior)-F.discrete_keys(nr);sourcechecks.append({'net':net,'source':ref+'.'+pin,'lost_prior_source_keys':[list(k)for k in sorted(lost)],'before_source_named_pads':len({q['uuid']for q in prior if q['kind']=='pad'and q['pin']}),'after_source_named_pads':len({q['uuid']for q in nr if q['kind']=='pad'and q['pin']})});put(out/'source-checkpoint.json',sourcechecks);print('R74_SOURCE',net,len(lost),sourcechecks[-1]['after_source_named_pads'],flush=True)
 source=next(v for v in h['vias']if v['uuid']=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92');assert set(source['flashed'])=={'F.Cu','In3.Cu','In4.Cu'}
 oldplane=next(q for q in z if q['uuid']=='69c62b44-c4ad-55f0-bf91-575b93a0b295');newplane=next(q for q in result if q['uuid']==oldplane['uuid']);ann=N.bounded_disk(source,.25).difference(N.bounded_disk(source,.1));annloss=oldplane['shape'].intersection(ann).difference(newplane['shape']).area
 model=out/'model.pkl';model.write_bytes(pickle.dumps((old,h,b,result,projected),protocol=5));(out/'source-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));ok=not any(q['lost_prior_source_keys']for q in sourcechecks)and annloss==0 and not any(q['empty']for q in ledger)
 put(out/'receipt.json',{'verdict':'REMOVE_ONLY_REFERENCE_REPAIR_SOURCE_PRESERVED_FULL_GATES_OPEN'if ok else'REMOVE_ONLY_REFERENCE_REPAIR_SOURCE_LOSS_REPAIR_REQUIRED','model_sha256':sha(model),'parent_model_sha256':sha(mp),'source_checks':sourcechecks,'existing_f6ad_exact_required_F_In3_extra_In4_metadata_preserved':True,'existing_f6ad_source_In4_annular_Cu_removed_mm2':annloss,'remove_only_ledger_sha256':sha(out/'remove-only-ledger.json'),'all_original_Cu_holes_footprints_native_outlines_unchanged':True,'metadata_precision_ledger_stale_after_new_remove_only_coordinates_requires_rebind':True,'full76_contact_reference_geometry_native_current_thermal':'OPEN','own_rail_classification_proposal_sha256':sha(proposalfile),'other84_power_source_review_sha256':sha(reviewfile),'literal_power_scope104_pending_PDN':True,'strict_original_reference_checker_preserved_FAIL':True,'PDN_replacement_obligations':proposal['mandatory_replacement_PDN_obligations'],'host_retained_relationships_pass':False,'board_written':False,'native_jobs':0,'adopted':False})
 print('R74_COMPLETE',ok,sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
