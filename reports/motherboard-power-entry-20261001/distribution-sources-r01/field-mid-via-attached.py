import pcbnew,sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import identity
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb');p=pcbnew.VECTOR2I(pcbnew.FromMM(349.85),pcbnew.FromMM(181.635));print(json.dumps([{'uuid':t.m_Uuid.AsString(),'identity':identity(t)}for t in b.GetTracks()if t.GetStart()==p or t.GetEnd()==p],indent=2))
