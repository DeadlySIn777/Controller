import pcbnew,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import mm,xy
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motion-raw-delivery-r45/motion-raw-delivery-candidate.kicad_pcb');zs=[z for z in b.Zones()if z.GetZoneName()=='MOTION_RAW_actual_motor_input_distribution_0'];z=zs[0];p=z.GetFilledPolysList(pcbnew.In3_Cu);print('outlines',p.OutlineCount());print('right occupied per y')
for y in[169,171,175,179,180,181,182,183,184,185,186,187]:
 xs=[x/10 for x in range(2490,3470)if p.Contains(xy((x/10,y)))];print(y,min(xs)if xs else None,max(xs)if xs else None)

