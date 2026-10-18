import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb')
for t in b.GetTracks():
 if t.GetNetname()in['/motherboard_power_entry/CORE_HEALTH_A_N','/motherboard_power_entry/CORE_HEALTH_B_N']:print(identity(t))
