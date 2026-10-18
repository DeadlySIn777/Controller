"""Explicit new-loop In2/In3 reference declarations; original checker unchanged."""
from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-five-bypass-current-manifest-r618.py')
s=p.read_text().replace('Source27-closer-bypass-native-proof-r596/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb','Source27-power-repair-native-proof-r616/motherboard-Source27-private-power-repair-candidate.kicad_pcb').replace('Source27-five-bypass-current-manifest-r618','Source27-five-bypass-current-manifest-r622')
s=s.replace("{'F.Cu':'In1.Cu','B.Cu':'In4.Cu'}","{'F.Cu':'In1.Cu','B.Cu':'In4.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu'}")
assert 'In2.Cu' in s
exec(compile(s,str(Path(__file__)), 'exec'))
