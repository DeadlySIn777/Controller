"""Prepare matching immutable interim LG shape/checkpoint snapshots."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'freeze_regional_return_checkpoint_r1.py';o=H/'freeze_logic_return_checkpoint_r18.py';assert not o.exists()
s=p.read_text();changes={"src=H/'protected-field-return-restoration-r4'":"src=H/'logic-source-union-reuse-return-restoration-r18'","48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff":"24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8","repair_protected_field_returns_r4.py":"repair_logic_source_union_reuse_returns_r18.py"}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
compile(s,str(o),'exec');o.write_text(s)
(H/'logic-checkpoint-freezer-r18-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'only_current_LG_constructor_and_exactR11_parent_bound':'PRESERVED_MATCHED_IMMUTABLE_CHECKPOINT_GEOMETRY_GATES','snapshot_does_not_claim_final_allnet_native_current_acceptance':True,'native_jobs':0,'board_written':False},indent=1)+'\n')
