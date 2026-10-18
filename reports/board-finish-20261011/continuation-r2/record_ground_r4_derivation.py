"""Freeze the regional source-equivalent constructor before execution."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'repair_protected_field_returns_r4.py';compile(p.read_text(),str(p),'exec');out=H/'protected-field-return-r4-derivation.json';assert not out.exists()
inputs=[H/'repair_protected_field_returns_r3.py',H/'protected-field-return-restoration-r3-stop.json',H/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl',H/'sbc-power/core-pocket-outward-round-guards-r69/receipt.json',H/'sbc-power/core-pocket-independent-analytic-r71/receipt.json',H/'coupled-recovery/c10036-peer-reference-mask-r26.wkb',H/'coupled-recovery/c10036-reference-bridge-r24.wkb',H/'sbc-power/guarded_declared_settings_projection_r58.py',H/'field-power/fast_contacts.py']
assert all(i.exists() for i in inputs)
out.write_text(json.dumps({'inputs':{str(i.resolve()):sha(i) for i in inputs},'final_script_sha256':sha(p),'initial_R4_snapshot_at_R3_stop_preserved_in_stop_receipt':True,'source_input_changed_from_R59_to_independently_corrected_R69_before_first_run':True,'source_projection':'Same GP58 function, original-source-zone selection/allchangedCu/allforeignownedcutters; exact source-zone filled polygons and alltarget/priorroot source membership compared with wholeboard after eachbank','regional_windows_mm':[5,15,35,75,800],'foreign_track_cap_and_via_circles':'Outwardanalyticfullradii, not inflated inscribed Cu basepolygons','C10036_exact_full_reference_and_bridge_reserved_for_foreign_In4_returns':True,'finite_route_failure_is_not_no_path_proof':True,'old_Cu_or_native_outline_mutation':False,'all_other_net_contact_current_native_flashes_refill_DRC':'OPEN'},indent=1)+'\n')
print(json.dumps({'script':str(p),'sha256':sha(p),'baseline':'R69_CORRECTED'}))
