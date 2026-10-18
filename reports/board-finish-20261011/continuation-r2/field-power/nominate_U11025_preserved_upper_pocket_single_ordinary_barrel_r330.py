"""Pin one site exposed by the concrete, fully connected loop changes."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'nominate_U11025_coupled_open_pocket_ordinary_barrel_r322.py').read_text(encoding='utf-8')
s=s.replace("R=H/'U11025-exact-health-loop-ground-escape-r320'","R=H/'U11025-health-shutdown-monitor-aperture-preserved-r328'")
s=s.replace('U11025-coupled-open-pocket-ordinary-barrel-r322','U11025-preserved-upper-pocket-single-barrel-r330')
s=s.replace('controller-U11025-r322-ordinary-','controller-U11025-r330-ordinary-')
s=s.replace("for x in [310.2,310.15,310.25,310.1,310.3,310.0]:","for x in [309.8]:")
s=s.replace("for y in [152.3,152.4,152.5,152.6,152.7,152.8,152.9,153.0]:","for y in [151.9]:")
exec(compile(s,str(H/'nominate_U11025_coupled_open_pocket_ordinary_barrel_r322.py'),'exec'))
