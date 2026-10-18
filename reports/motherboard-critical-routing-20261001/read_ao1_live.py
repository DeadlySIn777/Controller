import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_additive as c
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r04/motherboard-AO1-DAC-return-candidate.kicad_pcb')
r=json.loads(c.SOURCE_REVIEW.read_text())
for name,row in r['nets'].items():
 if 'AO1_DAC_' in name:
  pads=[]
  for p in b.GetPads():
   if p.GetNetname()==name:pads.append(dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),xy=list(pcbnew.ToMM(p.GetPosition())),size=list(pcbnew.ToMM(p.GetSize()))))
  print(json.dumps(dict(net=name,pads=pads)))
