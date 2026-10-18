import sys
sys.path.insert(0,'tools')
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm
from hardware_route_power_groups_native import hits
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-supply-cells-r19/C11058-supply-debug.kicad_pcb');g=Geometry(b);n='/motherboard_motors/MOTOR_5V_A';v=(343.8,184.125)
print('via',g.clear([v,v],n,pcbnew.F_Cu,.5),g.clear([v,v],n,pcbnew.B_Cu,.5))
print('F',g.clear([(344.475,185.5),(344.475,184.125),v],n,pcbnew.F_Cu,.3))
print('B',g.clear([(338.5,184.975),(343.8,184.975),v],n,pcbnew.B_Cu,.4))
print('pads',[(net,polys)for net,polys,top,bot,npth in g.pads.candidates(v,v,.3)if any(hits(v,v,p,.3)for p in polys)])
