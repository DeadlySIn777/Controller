"""Freeze matching interim geometry and constructor checkpoint without claiming completion."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'protected-field-return-restoration-r4';out=Path(sys.argv[1]).resolve()
assert out.is_relative_to(H) and not out.exists()
c=src/'checkpoint.json';p=src/'proposed-zones.pkl'
cb=c.read_bytes();pb=p.read_bytes();rows=json.loads(cb)['rows'];zones=pickle.loads(pb)
assert cb==c.read_bytes() and pb==p.read_bytes(),'Writer changed during snapshot; retry fresh output'
accepted=[r for r in rows if r['repair']]
assert {r['repair']['shape_uuid']for r in accepted}=={z['uuid']for z in zones}
assert len(zones)==len(accepted)
out.mkdir();(out/'checkpoint.json').write_bytes(cb);(out/'proposed-zones.pkl').write_bytes(pb)
proof=src/'bank-proofs.json';proofhash=None
if proof.exists():
 b=proof.read_bytes();assert b==proof.read_bytes();(out/'bank-proofs.json').write_bytes(b);proofhash=sha(b)
r={'verdict':'FROZEN_INTERIM_SOURCE_ONLY_CONSTRUCTION_NOT_FINAL_ACCEPTANCE','accepted_shapes':len(zones),'checkpoint_sha256':sha(cb),'proposed_zones_sha256':sha(pb),'bank_proofs_sha256':proofhash,'parent_model_sha256':'48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff','script_sha256':sha((H/'repair_protected_field_returns_r4.py').read_bytes()),'all_other_net_contacts_current_native_refill_DRC':'OPEN','rows':[{'net':r['net'],'shape_uuid':r['repair']['shape_uuid'],'layer':r['repair']['layer'],'length_mm':r['repair']['length_mm'],'minimum_core_width_mm':r['repair']['minimum_core_width_mm'],'target_named_pad_count':len(r['target_pad_UUIDs'])}for r in accepted],'adopted':False}
(out/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print(json.dumps(r))
