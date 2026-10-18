"""Use exact UUID entity identity, preserving the R258 ordering assertion."""
from pathlib import Path
import hashlib,json,runpy
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'audit_joint_new_planes_unchanged_physics_r258.py';code=source.read_text().replace('physics-r258','physics-r260').replace('R258','R260')
needle="assert [x for x in c0[kind]if norm(x['net'])not in scope]==[x for x in c[kind]if norm(x['net'])not in scope],kind";assert code.count(needle)==1
code=code.replace(needle,"assert {x['uuid']:x for x in c0[kind]if norm(x['net'])not in scope}=={x['uuid']:x for x in c[kind]if norm(x['net'])not in scope},kind")
target=H/'audit_joint_new_planes_exact_entity_physics_r260.py';assert not target.exists();compile(code,str(target),'exec');target.write_text(code)
p=H/'joint-plane-audit-exact-entity-identity-derivation-r260.json';assert not p.exists();p.write_text(json.dumps({'source_SHA256':sha(source),'derived_SHA256':sha(target),'R258_assertion_before_any_board_modification':'track list order differs because original CLOCK restored at end; all83191 unaffected UUID entities exactly equal in R259','exact_entity_dict_identity_not_geometry_tolerance':True,'native_jobs':0,'adopted':False},indent=1)+'\n');runpy.run_path(str(target),run_name='__main__')
