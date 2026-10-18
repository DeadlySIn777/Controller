import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import segment_distance,mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r114/debug.kicad_pcb');g=FastGeometry(b);s=(274.3,179.85);n='/motherboard_power_entry/MOTOR_FEED_PG_A';gap=.25+.16
for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
 print('LAYER',b.GetLayerName(l),g.clear([s,s],n,l,.5))
 for net,polys,top,bot,npth in g.pads.candidates(s,s,gap):
  if net==n and not npth:continue
  if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(s,s,p,gap)for p in polys):print(' PAD',net,polys)
 for net,a,c,width in g.tracks[l].candidates(s,s,gap):
  if net!=n and segment_distance(s,s,a,c)<gap+width/2-1e-6:print(' TRACK',net,a,c,width,segment_distance(s,s,a,c))

