import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy,segment_distance
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_power_groups_native import hits
B=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-pose-screen-r274/literal-retired-U19-local-input.kicad_pcb');b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()};fs['U11019'].SetPosition(xy((343,175)));fs['U11019'].SetOrientationDegrees(180);fs['C11078'].SetPosition(xy((342.1625,174.225)));fs['C11078'].SetOrientationDegrees(90);g=FastGeometry(b)
for q,net in[((343,176.8),'/mc_local_power/CORE_5V'),((342.9125,173.45),'/LOGIC_GND'),((338.9125,173.45),'/LOGIC_GND'),((333.5875,186.05),'/motherboard_motors/FIELD_GND')]:
 for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
  fails=[];gap=.41
  for ref,p in g.barrier_index.candidates(q,q,.25):
   if hits(q,q,p,.25):fails.append(('BAR',ref,p))
  for n,polys,top,bot,npth in g.pads.candidates(q,q,gap):
   if n==net and not npth:continue
   if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(q,q,p,gap)for p in polys):fails.append(('PAD',n,polys))
  for n,s,e,w in g.tracks[l].candidates(q,q,gap):
   if n!=net and segment_distance(q,q,s,e)<gap+w/2-1e-6:fails.append(('CU',n,s,e,w))
  print(q,b.GetLayerName(l),fails,flush=True)
