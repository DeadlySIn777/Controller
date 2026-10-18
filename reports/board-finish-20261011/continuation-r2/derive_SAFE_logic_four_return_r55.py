"""Restore the actual lost35f6 logic branch with existing flashed barrel ports."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'repair_logic_two_reference_safe_r42.py';dst=H/'repair_SAFE_logic_four_return_r55.py';assert not dst.exists();t=src.read_text()
old="assert sha(mp)==r['model_sha256']=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a' and r['verdict']=='PASS_SAFE_FIVE_LOGIC_AND_EXPLICIT_FAG_MARGIN_HOST_SOURCE_REFERENCE_CONTACT_NATIVE_CURRENT_OPEN'"
assert old in t;t=t.replace(old,"assert sha(mp)==r['model_sha256']=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b' and sha(mr)=='fbc477ec36118a413cd6dd38786848eebfdc2d83482b680324e8b8d2a3354de6'")
t=t.replace('logic-two-reference-safe-return-restoration-r42','SAFE-logic-four-return-restoration-r55').replace('controller-logic-two-reference-safe-return-r42','controller-SAFE-logic-four-return-r55')
old="OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes())";assert old in t
t=t.replace(old,"OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes());import restore_SAFE_generated_precision_states_r168 as PS;assert sha(PS.__file__)=='88e352a26ee60e62f2d50d7d7c8bb2ed9cdbd1b4786a6818c6c8354676b90e54';precision_replay=PS.restore_bound_generated_precision_states(binding,zones);write(OUT/'exact-parent-generated-precision-state-replay.json',precision_replay)")
t=t.replace("{'82b11372','849811b6'}","{'35f6d361'}")
old="permitted={'82b11372-0000-0000-0000-000000000000','849811b6-0000-0000-0000-000000000000'};prefixes={'35f6d361'}";assert old in t;t=t.replace(old,"prefixes={'35f6d361'}")
old="foreign_net='/motherboard_do/FIELD_B_0V';foreign_root=root(F.graph(current,foreign_net),'J11005');foreign_return={l:unary_union([q['shape']for q in foreign_root if q['layer']==l])for l in LAYERS}"
assert old in t;t=t.replace(old,"foreign_roots=[root(F.graph(current,n),r)for n,r in [('/motherboard_do/FIELD_B_0V','J11005'),('/motherboard_motors/FIELD_GND','J11003')]];foreign_return={l:unary_union([q['shape']for rs in foreign_roots for q in rs if q['layer']==l])for l in LAYERS}")
t=t.replace("'Logic unchanged-source union reuse return R18'","'SAFE lost-four unchanged-original-barrel source return R55'")
compile(t,str(dst),'exec');dst.write_text(t)
(H/'SAFE-logic-four-r55-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'exact_frozen_FAILED_parent':'d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b','target':'exact4pads in existing35f6d361 branch; current native existing flashed ports only','all_Cu_holes_sourceposes_nativeoutlines_preserved':True,'both_FAG_FBG_actual_source_returns_all4inner_layers_hard':True,'no_field_or_CORE_or_protected_power_carve':True,'adopted':False,'board_written':False},indent=1)+'\n')
print(dst)
