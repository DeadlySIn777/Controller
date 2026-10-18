"""Derive bounded ordinary fanout with explicit new-plane-only antipad nominees."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_field_ground_bare_dogbones_r17.py';target=H/'nominate_field_ground_owned_antipads_r23.py';text=source.read_text()
def change(a,b):
 global text
 assert text.count(a)==1,(a,text.count(a));text=text.replace("controller-ground-bare-r17","controller-ground-bare-r23")
assert not target.exists();compile(text,str(target),'exec');target.write_text(text)
receipt={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'rule_and_native_clearance_unchanged':True,'new_only_owned_antipads_are_nominations_until_full_source_contact_reference_current_native_gates':True,'own_outward_field_side_courtyard_corridor_is_explicit_planning_mask_change_only':True,'native_jobs':0,'board_written':False}
(H/'field-bare-owned-antipads-r23-derivation.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps(receipt))
