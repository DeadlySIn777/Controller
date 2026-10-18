import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
for r,pn in [('C11046','2'),('R11076','2'),('R11080','2'),('C11087','1'),('U11031','2'),('U11033','2'),('R11076','1'),('R11080','1'),('R11048','2')]:
 p=next(p for p in fs[r].Pads()if p.GetNumber()==pn);joined=[v for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T];print(r,pn,mm(p.GetPosition()),'pads',len(joined),flush=True)
 if r.startswith('R'):
  for t in b.GetTracks():
   if t.GetNetname()==p.GetNetname()and any(p.HitTest(v)for v in[t.GetStart(),t.GetEnd()]):print(identity(t),flush=True)
