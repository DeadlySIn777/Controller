"""Freeze independent regional-return audit with true full-cap clearance."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'audit_regional_ground_joint_r5.py';compile(p.read_text(),str(p),'exec')
out=H/'regional-ground-joint-r5-derivation.json';assert not out.exists()
inputs=[H/'audit_protected_ground_joint_model_r4.py',H/'repair_protected_field_returns_r4.py',H/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl',H/'sbc-power/core-pocket-outward-round-guards-r69/receipt.json',H/'sbc-power/core-pocket-independent-analytic-r71/receipt.json',H/'sbc-power/remaining-core-feeds-r48/model.pkl',H/'field-power/fast_contacts.py',H/'field-power/contact_layout.py',H/'field-power/audit_field_io3_crossings_r15e.py']
assert all(i.exists()for i in inputs)
r={'script_sha256':sha(p),'inputs':{str(i.resolve()):sha(i)for i in inputs},'analytic_clearance':'Zone distance to exact foreign track centerline minus full half-width; exact via center minus full radius; actual pad polygons. Full domain/local clearance plus 0.025 mm planning guard. No inscribed-cap or round-buffer credit.','retained_contact_baselines':['current corrected R69','pre-protected R48'],'invariant':'All parent original copper, source pads, original native zone definitions and owned plane shapes retained exactly; added shapes only match constructor frozen receipt.','actual_source_census':True,'native_original_source_all_baselines_reference_current_mesh_barrel_thermal':'SEPARATE_OPEN','native_jobs':0,'adopted':False}
out.write_text(json.dumps(r,indent=1)+'\n');print(json.dumps({'script_sha256':sha(p),'receipt':str(out)}))
