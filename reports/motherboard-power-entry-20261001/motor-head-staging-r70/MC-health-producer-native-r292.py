import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');n='/mc_local_power/MC_RAILS_OK_5V'
for p in b.GetPads():
 if p.GetNetname()==n:print(p.GetParentFootprint().GetReference(),p.GetNumber(),mm(p.GetPosition()),flush=True)
