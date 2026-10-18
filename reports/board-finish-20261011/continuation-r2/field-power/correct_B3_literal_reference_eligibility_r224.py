"""Use exact existing REF domain eligibility; preserve the overbroad R222 diagnostic."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'correct_B3_exact_current_reference_mask_r222.py').read_text(encoding='utf-8')
s=s.replace('B3-exact-current-LOGIC-reference-correction-r222','B3-literal-eligible-LOGIC-reference-correction-r224')
s=s.replace("if t['layer']!='F.Cu' or t['uuid'] not in original:continue","if t['layer']!='F.Cu' or t['uuid'] not in original or C.norm(t['net'])=='/LOGIC_GND' or h['domains_normalized'].get(C.norm(t['net']))!=h['domains_normalized']['/LOGIC_GND']:continue")
exec(compile(s,str(H/'correct_B3_exact_current_reference_mask_r222.py'),'exec'))
