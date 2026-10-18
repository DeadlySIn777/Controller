"""Freeze literal two-group replacement contract; no native or readiness claim."""
import copy,hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'sbc-power'))
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/IO3-minimal-validated-integration-packet-r188'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ds(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 oldp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';newp=H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183/model.pkl'
 assert sha(oldp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 assert sha(newp)=='6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5'
 g,h,b,z,c=pickle.loads(newp.read_bytes());og,oh,ob,oz,oc=pickle.loads(oldp.read_bytes());assert g==og and h==oh
 PS.restore_bound_generated_precision_states(b,z);PS.restore_bound_generated_precision_states(ob,oz)
 om={(q['net'],q['layer']):q for q in oz};rows=[];replacements=[];untouched=[]
 for q in z:
  before=om[q['net'],q['layer']]
  if q['net']!='/IO_3V3' or q['layer'] not in ('In2.Cu','In3.Cu'):
   assert before['uuid']==q['uuid'] and before['shape'].wkb==q['shape'].wkb and before['zone_outline_shape'].wkb==q['zone_outline_shape'].wkb
   untouched.append({'UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_SHA256':ds(q['shape']),'outline_SHA256':ds(q['zone_outline_shape'])});continue
  replacements.append(copy.deepcopy(q));r={'operation':'REPLACE_ONE_OWNED_HOST_CANONICAL_GROUP','raw_net':q['net'],'layer':q['layer'],'old_UUID':before['uuid'],'new_UUID':q['uuid'],'constituent_UUIDs':q['constituent_proposal_UUIDs'],'roles':{}}
  for role in ('shape','zone_outline_shape'):
   a,s=before[role],q[role]
   af=O/(before['uuid']+'.'+role+'.old.wkb');nf=O/(q['uuid']+'.'+role+'.new.wkb');af.write_bytes(a.wkb);nf.write_bytes(s.wkb)
   r['roles'][role]={'old_file':str(af.resolve()),'old_sha256':sha(af),'new_file':str(nf.resolve()),'new_sha256':sha(nf),'removed_mm2':a.difference(s).area,'added_mm2':s.difference(a).area}
  rows.append(r)
 assert len(rows)==2 and len(untouched)==34
 qf=O/'exact-owned-IO3-two-group-replacements.pkl';qf.write_bytes(pickle.dumps(replacements,protocol=5))
 proofs=[]
 for dirname,verdict in [('IO3-exact-primitive-independent-true-geometry-r184','PASS_STRICT_TRUE_GEOMETRY_SCOPE'),('IO3-exact-primitive-original198b-DC936-contact-audit-r185',None),('IO3-exact-primitive-all76-incremental-audit-r186','PASS_INCREMENTAL_ALL76_OLD_CONTACT_SOURCE_STRICT_REFERENCE')]:
  f=H/'sbc-power'/dirname/'receipt.json';r=json.loads(f.read_bytes());assert r.get('model_sha256')==sha(newp)
  if verdict:assert r['verdict']==verdict
  proofs.append({'file':str(f.resolve()),'sha256':sha(f),'verdict':r['verdict']})
 r={'verdict':'PASS_EXACT_INCREMENTAL_GEOMETRY_ALL76_CONTACT_SOURCE_OLD_REFERENCE_SCOPE_ONLY','parent_model_file':str(oldp.resolve()),'parent_model_sha256':sha(oldp),'frozen_full_model_file':str(newp.resolve()),'frozen_full_model_sha256':sha(newp),'only_two_owned_host_group_replacements':rows,'replacement_objects_file':str(qf.resolve()),'replacement_objects_sha256':sha(qf),'all34_unchanged_group_WKB_rows':untouched,'independent_proofs':proofs,'source_original_IO3_connected_named_pads':593,'remaining_original_isolated_IO3_named_pads':23,'remaining_CORE1V2_named_pads':3,'old_IO3_pad_free_branch_split':'OPEN','eight_new_feed_current_drop_thermal_and_actual_return':'OPEN','root_R55_four_ground_pad_repair_not_included':True,'root_CORE1V2_reference_shadow_or_source_repair_not_included':True,'field_U10017_R183_and_REG6_not_included':True,'whole_earlier_scope_substitution_forbidden':True,'no_original_discrete_source_or_native_zone_definition_changes':True,'no_area_waiver':True,'host_all_supply_rooted':False,'board_written':False,'native_jobs':0,'manufacturing_ready':False,'script_sha256':sha(__file__)}
 (O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R188_COMPLETE',sha(O/'receipt.json'),sha(qf),flush=True)
if __name__=='__main__':main()
