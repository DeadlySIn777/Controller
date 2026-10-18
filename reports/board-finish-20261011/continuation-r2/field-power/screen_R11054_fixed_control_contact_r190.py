"""Reuse the exact fixed-control-pad pose screen on remaining FIELD5 pull-up."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'screen_fixed_pin2_r14065_rotations_r174.py').read_text(encoding='utf-8')
s=s.replace('R14065','R11054').replace('r14065','r11054').replace('r174','r190').replace('R174','R190').replace('shutdown','control').replace('probe_shutdown','retained_control')
s=s.replace('B.Cu','F.Cu').replace("courtyard']['B']","courtyard']['F']").replace(".get('B',[])",".get('F',[])")
exec(compile(s,str(H/'screen_fixed_pin2_r14065_rotations_r174.py'),'exec'))
