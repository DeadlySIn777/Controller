import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r326/debug.kicad_pcb');g=FastGeometry(b);ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()}
s=mm(ps['R11078','2'].GetPosition());e=mm(ps['U11023','3'].GetPosition());n=ps['R11078','2'].GetNetname();print('ENDS',s,e,n,flush=True)
for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
 for tag,pt in[('s',s),('e',e)]:
  ok=[]
  for d in[1,2,4]:
   for i in range(16):
    x=(pt[0]+d*math.cos(i*math.pi/8),pt[1]+d*math.sin(i*math.pi/8))
    if g.clear([pt,x],n,l,.2):ok.append(x)
  print('ESC',b.GetLayerName(l),tag,ok,flush=True)
 for way in[(280,140),(280,160),(310,135),(365,150),(365,165),(360,175),(354,165),(354,180)]:
  one=next((x for x in paths(s,way)if g.clear(x,n,l,.2)),None);two=next((x for x in paths(way,e)if g.clear(x,n,l,.2)),None)
  if one and two:print('PATH',b.GetLayerName(l),one+two[1:],flush=True)
  elif two:print('LAST',b.GetLayerName(l),way,two,flush=True)
