"""Directly bind exact R504/R506 source arrays to the SAME_PLANE proposal."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'audit_Q0_SENSE_actual_same_plane_finite_paths_r482.py'
code=base.read_text()
replacements={
 'Q0-SENSE-actual-same-plane-finite-paths-r482':'Q0-R504-SENSE-same-plane-finite-paths-r510',
 'Q0-R478-exact-pose-current-contacts-reference-r480':'Q0-R504-explicit-final-current-r506',
 'fa9629bb0b6bc93b39b0148e9e4236c351aaabd0edba06823f9423c86b3e6279':'8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a',
 'Q0-exact-R476-ground-contact-pose-r478/model.pkl':'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl',
 'aec47d8600135e340be9e38ca18891e2903e7c283ee0b7095673d383ce079ebd':'f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a',
 'finite=local.buffer(-.105,quad_segs=128)':'finite=local.difference(own).buffer(-.105,quad_segs=128)',
 'R480_incremental_receipt_sha256':'R506_incremental_receipt_sha256',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
marker="audit=json.loads(ar.read_bytes());"
assert code.count(marker)==1
code=code.replace(marker,marker+"assert audit['actual_final_owned_roles_and_filled_model_sha256']=='f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a';")
derived=H/'Q0-R504-SENSE-same-plane-finite-paths-r510-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
