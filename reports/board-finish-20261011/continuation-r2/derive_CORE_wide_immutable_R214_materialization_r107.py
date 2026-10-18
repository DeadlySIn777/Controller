"""Preserve original positive-head actual native fills; add only new primitive cuts."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'materialize_CORE_owned_In2_feed_incremental_r100.py';s=base.read_text();changes=[]
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
rep("CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert sha(packet/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd'", "CORE-wider-new-only-legal-envelope-proposal-r106';assert sha(packet/'receipt.json')=='74bb46a6fd31e60c8461f7f8c2ecf58cfc32a259abf3616466888f24400f4b39'")
rep("digest(core['shape'])=='4b5675bccc5a299d38f996843162681d4f227b6c194ae3d65194d4b00a823e74'", "digest(core['shape'])=='fc29d425b54f78f8fcfd04273ccb26698013a914cfa718e7ba7a110cafc5b853'")
rep("oldactual={q['uuid']:q for q in before['zones']};native=[]", "immutable_head=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(immutable_head)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';native_baseline=pickle.loads(immutable_head.read_bytes())[4];oldactual={q['uuid']:q for q in native_baseline['zones']};native=[]")
rep("'native_actual_fill_only_new_added_primitive_cuts':len(actualcuts)", "'native_actual_fill_only_new_added_primitive_cuts':len(actualcuts),'actual_native_fill_immutable_R214_baseline_sha256':sha(immutable_head),'only_owned_remove_only_masks_are_applied_NO_reclaimed_old_fill_credit':True,'failed_R100_R224_31tiny_SIGNAL_reference_losses_and_56mm2COREbodygap_UNCHANGED_EVIDENCE_NOT_WAIVED':True")
s=s.replace('CORE-In2-owned-notch-materialized-source-proposal-r100','CORE-wide-immutable-R214-materialized-source-proposal-r107').replace('R100_', 'R107_')
compile(s,'materialize_CORE_wide_immutable_R214_incremental_r107.py','exec');out=H/'materialize_CORE_wide_immutable_R214_incremental_r107.py';assert not out.exists();out.write_text(s)
(H/'CORE-wide-immutable-R214-r107-derivation.json').write_text(json.dumps({'base_script_sha256':sha(base),'new_script_sha256':sha(out),'changes':changes,'exact_frozen_R214_native_actual_fill_only_new_primitive_subtractions':True,'all_8_R83_own_remove_only_masks_remain_but_NO_native_reclaimed_credit':True,'no_actual_native_float_coordinates_rounding_or_any_reference_area_waiver':True,'wholebody_reference_current_all77_directcontacts_and_native_gates_open':True},indent=1)+'\n');print('R107_DERIVED',sha(out),flush=True)
