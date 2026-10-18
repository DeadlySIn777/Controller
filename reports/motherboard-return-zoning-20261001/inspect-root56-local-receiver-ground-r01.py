import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_logic_return import mm
p='reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb';b=pcbnew.LoadBoard(p);fps={f.GetReference():f for f in b.GetFootprints()};b.BuildConnectivity()
for ref,pin in [('U14623','9'),('U14014','7')]:
 f=fps[ref];p=next(p for p in f.Pads()if p.GetNumber()==pin);print(ref,'origin',mm(f.GetPosition()),'layer',f.GetLayerName(),'pin',mm(p.GetPosition()),p.GetNetname(),flush=True)
 for q in b.GetConnectivity().GetConnectedItems(p):
  if isinstance(q,pcbnew.PCB_VIA)and q.GetNetname()==p.GetNetname():print('via',q.m_Uuid.AsString(),mm(q.GetPosition()),[(b.GetLayerName(l),q.FlashLayer(l),b.GetConnectivity().IsConnectedOnLayer(q,l))for l in [pcbnew.In1_Cu,pcbnew.In4_Cu]],flush=True)
