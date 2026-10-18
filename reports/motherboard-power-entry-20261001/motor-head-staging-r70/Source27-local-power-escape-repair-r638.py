"""Simultaneous paired-barrel preflight; preserve failed transient r636 evidence."""
from pathlib import Path
DERIVED_INPUT=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-local-power-escape-repair-r636.py')
s=DERIVED_INPUT.read_text().replace('Source27-local-power-escape-repair-r636','Source27-local-power-escape-repair-r638')
line=" assert all(not isinstance(t,pcbnew.PCB_VIA)or t==v or math.dist(mm(t.GetPosition()),point)>=.4495 for t in b.GetTracks()),('Actual hole separation',uid)\n"
assert line in s;s=s.replace(line,'')
s=s.replace('g=m.InnerGeometry(b)',"for uid,point in moves.items():\n assert all(not isinstance(t,pcbnew.PCB_VIA)or t.m_Uuid.AsString()==uid or math.dist(mm(t.GetPosition()),point)>=.4495 for t in b.GetTracks()),('Actual final simultaneous hole separation',uid)\ng=m.InnerGeometry(b)")
s=s.replace('};b0=pcbnew.LoadBoard', '};inputs[str(DERIVED_INPUT)]=sha(DERIVED_INPUT);b0=pcbnew.LoadBoard')
exec(compile(s,str(Path(__file__)),'exec'))
