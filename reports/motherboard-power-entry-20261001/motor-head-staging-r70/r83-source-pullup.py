import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()));import pcbnew
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity();f={f.GetReference():f for f in b.GetFootprints()}
for r,pn in [('R11043','1'),('R11071','1'),('C11055','1')]:
 p=next(p for p in f[r].Pads()if p.GetNumber()==pn);rows=[v for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T];print(r,pn,'SOURCE_COUNT',len(rows),'members',[(v.GetParentFootprint().GetReference(),v.GetNumber())for v in rows][:15])
