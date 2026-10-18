"""Exact additive two-root-ground delta onto the accepted IO3 source repair."""
from pathlib import Path
import pickle,json,hashlib
H=Path(__file__).resolve().parent.parent
O=H/'sbc-power/IO3-notch-ROOT42-SAFE-unprojected-r165'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/IO3-bounded-owned-CORE-notch-reroute-r164/unprojected-model.pkl';assert sha(mp)=='cffdbb37883239d4a3a0feba88c702ad376650c3f6cf4bd2e73c8ea0d439599d';g,h,b,z,c=pickle.loads(mp.read_bytes())
 qf=H/'logic-two-reference-safe-return-restoration-r42/proposed-zones.pkl';rf=H/'logic-two-independent-full-r43/receipt.json'
 assert sha(qf)=='6dade25d3aced12036dcd56ef8bbec590f5bd721ec47bd83435cd3ad2186b114' and sha(rf)=='c0688d943d936947bb21ce60b7afc57574e5c4220db00ff7349b6b4821a0f0b3'
 qs=pickle.loads(qf.read_bytes());assert len(qs)==2 and all(q['net']=='/LOGIC_GND' and q['layer']=='In2.Cu' for q in qs);assert not {q['uuid'] for q in qs}&{q['uuid'] for q in z}
 rows=[{'UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_WKB_SHA256':hashlib.sha256(q['shape'].wkb).hexdigest(),'intended_WKB_SHA256':hashlib.sha256(q.get('zone_outline_shape',q['shape']).wkb).hexdigest()} for q in qs]
 b['SAFE_exact_accepted_ROOT42_two_ground_additions']={'source_zones_file':str(qf.resolve()),'source_zones_sha256':sha(qf),'independent_receipt_file':str(rf.resolve()),'independent_receipt_sha256':sha(rf),'only_exact2_NEW_zones_appended':True,'no_h_g_old_zone_discrete_or_source_replacement':True,'rows':rows,'fresh_joint_reference_contact_native_current_gates_required':True}
 b['host_all_supply_rooted']=False;b['SAFE_excludes_failed_REG6_DI6_DI15_and_unaccepted_C1024_nominee']=True
 model=O/'unprojected-model.pkl';model.write_bytes(pickle.dumps((g,h,b,z+qs,None),protocol=5))
 (O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_SAFE_IO3_ROOT42_DELTA_COMPOSED_FRESH_ALL_GATES_REQUIRED','model_sha256':sha(model),'parent_model_sha256':sha(mp),'owned_NEW_zone_count':len(z+qs),'ROOT42_rows':rows,'CORE_notch_qualification_current_A':7.882034293398381,'original_native_definitions_and_actual_discrete_unchanged_from_R164':True,'host_all_supply_rooted':False,'native_jobs':0,'board_written':False},indent=1)+'\n');print('SAFE_R165',sha(model),len(z+qs))
if __name__=='__main__':main()
