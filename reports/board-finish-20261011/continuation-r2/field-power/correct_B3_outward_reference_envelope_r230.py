"""Reserve the entire circumscribed buffer envelope, without changing the required gap."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'correct_B3_exact_current_reference_mask_r222.py').read_text(encoding='utf-8')
s=s.replace('B3-exact-current-LOGIC-reference-correction-r222','B3-outward-reference-envelope-correction-r230')
s=s.replace("if t['layer']!='F.Cu' or t['uuid'] not in original:continue","if t['layer']!='F.Cu' or t['uuid'] not in original or C.norm(t['net'])=='/LOGIC_GND' or h['domains_normalized'].get(C.norm(t['net']))!=h['domains_normalized']['/LOGIC_GND']:continue")
s=s.replace('mask,.625+.00002','mask,.625+.0001').replace("'extra_construction_reserve_mm':.00002","'extra_construction_reserve_mm':.0001")
s=s.replace("receipt={'verdict'", "proof=P.bounded_buffer(q['shape'],.625).intersection(mask);assert proof.area<1e-12,('direct outward reference intrusion',proof.area);receipt={'direct_guarded_buffer_reference_intrusion_mm2':proof.area,'maximum_circumscribed_guard_radial_overshoot_mm':(.625+.000002)/__import__('math').cos(__import__('math').pi/256)-.625,'verdict'")
exec(compile(s,str(H/'correct_B3_exact_current_reference_mask_r222.py'),'exec'))
