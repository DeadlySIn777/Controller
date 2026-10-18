"""R318 preserved: correct two new-track endpoint mutual spacing."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_U11025_exact_health_loop_ground_escape_r318.py').read_text(encoding='utf-8')
s=s.replace('U11025-exact-health-loop-ground-escape-r318','U11025-exact-health-loop-ground-escape-r320')
s=s.replace('controller-field-r318-','controller-field-r320-')
s=s.replace('151.72','151.70').replace('(310.2,152.0)','(310.2,152.08)')
exec(compile(s,str(H/'construct_U11025_exact_health_loop_ground_escape_r318.py'),'exec'))
