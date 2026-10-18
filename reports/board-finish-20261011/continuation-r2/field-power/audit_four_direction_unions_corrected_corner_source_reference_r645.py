"""Fresh exact R643 physical/source/reference proof; preserve R633/R635 failures."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_four_minimal_owned_unions_actual_contacts_reference_r633.py').read_text(encoding='utf-8')
s=s.replace('R543-four-unions-bound-exact-line-owned-scopes-r631/model.pkl','two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/model.pkl').replace('four-minimal-owned-unions-actual-all-drill-source-contact-reference-r633','four-direction-unions-corrected-corners-actual-source-contact-reference-r645').replace('R633','R645')
s=s.replace('8dacfdb44f609ecbd3fcfb9280aac624eca7d03e3bf6d50ada3dbe3ac230887a','7141d6d37a909617aa339dadfc3b8a1b539904af1b06b2bf8f00ea2abeee69f9').replace('a52f6d19ea241092ad469de8e9ac2097cbbb136012fdd44f5a711f35e088c962','6598205d8e1b480bc6386fb16e94a291e6c65c11691952164423f59dc9f1e850')
s=s.replace('only-four-current-member-to-inward-union-and-local-current-record-operations.pkl','only-four-current-member-to-qualified-direction-union-operation-candidates.pkl').replace("rc['packet_SHA256']","rc['complete_four_cluster_packet_SHA256']").replace("('/motherboard_do/DOB_FIELD_3V3','U11018','8')","('/motherboard_do/DOB_FIELD_3V3','U11018','1')")
old="gain=after.difference(old);assert gain.is_empty;role.append({'UUID':uid,'role':r,'before_literal_union_SHA256':hs(old),'new_SHA256':hs(after),'literal_gained_Cu_EMPTY':True,'exact_removed_owned_Cu':ds(old.difference(after))})"
new="gain=after.difference(old);lost=old.difference(after);assert lost.is_empty if L.norm(new['net'])in('/LOGIC_GND','/motherboard_motors/FIELD_GND')else gain.is_empty;role.append({'UUID':uid,'role':r,'before_literal_union_SHA256':hs(old),'new_SHA256':hs(after),'explicit_declared_added_owned_Cu':ds(gain),'exact_removed_owned_Cu':ds(lost),'declared_positive_corner_R643_authority_NOT_a_negative_only_assertion':not gain.is_empty})"
assert old in s;s=s.replace(old,new)
s=s.replace("put(OUT/'exact-minimal-owned-role-original-identity-and-negative-only-proof.json',role)","put(OUT/'exact-direction-union-owned-role-original-identity-and-explicit-added-Cu-proof.json',role)")
anchor=' sources=[]\n';assert s.count(anchor)==1
s=s.replace(anchor," sources=[]\n checkpoint=OUT/'fresh-four-actual-graphs-checkpoint.pkl';checkpoint.write_bytes(pickle.dumps(now,protocol=5));put(OUT/'fresh-four-actual-graphs-checkpoint-receipt.json',{'model_SHA256':sha(M),'before_group_SHA256':sha(gf),'checkpoint_SHA256':sha(checkpoint),'remaining_reference_gates':'OPEN'})\n")
s=s.replace("'eight_old_native_overlap_ERRORS_not_yet_remeasured':True","'eight_old_native_overlap_ERRORS_not_yet_remeasured':True,'R631_R635_rejected_reference_failures_preserved':True,'declared_positive_corner_true_guard_nozone_R643_receipt_SHA256':sha(M.with_name('receipt.json'))")
exec(compile(s,str(Path(__file__)),'exec'))
