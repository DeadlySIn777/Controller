import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_local_signals import GeometryIndex
from hardware_route_logic_return import mm,segment_distance
from hardware_route_power_groups_native import hits
from hardware_collect_native_reference_fills import collect_native_reference_fills
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-head-feed-r74/rejected-debug.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()};p={(r,v.GetNumber()):v for r,f in fs.items()for v in f.Pads()};g=FastGeometry(b)
print('collect actual In1 reference',flush=True);fill=collect_native_reference_fills(b,{'/LOGIC_GND'},{pcbnew.In1_Cu})['/LOGIC_GND',pcbnew.In1_Cu];print('fill collected',fill.OutlineCount(),flush=True)
idx=GeometryIndex()
for t in b.GetTracks():
 if t.IsOnLayer(pcbnew.In2_Cu):
  via=isinstance(t,pcbnew.PCB_VIA);w=pcbnew.ToMM(t.GetWidth(pcbnew.In2_Cu)if via else t.GetWidth());s,e=mm(t.GetStart()),mm(t.GetEnd());idx.add((t.GetNetname(),s,e,w),(min(s[0],e[0])-w/2,min(s[1],e[1])-w/2,max(s[0],e[0])+w/2,max(s[1],e[1])+w/2))
class Inner:
 grid=FastGeometry.grid
 def clear(self,pts,n,l,w):
  for s,e in zip(pts,pts[1:]):
   if any(hits(s,e,poly,w/2)for ref,poly in g.barrier_index.candidates(s,e,w/2)):return False
   for net,a,c,ww in idx.candidates(s,e,w/2+.16):
    if net!=n and segment_distance(s,e,a,c)<w/2+ww/2+.16:return False
   dx,dy=e[0]-s[0],e[1]-s[1];d=math.hypot(dx,dy);nx,ny=(-dy/d,dx/d)if d else(0,1)
   # Search screen only; exact native Boolean corridor is required after fill.
   for j in range(max(2,math.ceil(d/.3)+1)):
    t=j/(max(2,math.ceil(d/.3)+1)-1);x,y=s[0]+dx*t,s[1]+dy*t
    for k in[-.2,0,.2]:
     if not fill.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x+nx*k),pcbnew.FromMM(y+ny*k))):return False
  return True
ig=Inner()
for r,sv,ev in [('U11010',(345.5,203.25),(270.85,180.8)),('U11011',(354.6929,195.9571),(270.85,187.8))]:
 n=p[r,'5'].GetNetname();print('TRY INNER',r,'ends',ig.clear([sv,sv],n,pcbnew.In2_Cu,.2),ig.clear([ev,ev],n,pcbnew.In2_Cu,.2),flush=True);pp=ig.grid(sv,ev,n,pcbnew.In2_Cu,.2,step=.5,padding=50,max_nodes=70000);print('RESULT',r,pp,flush=True)
 if pp:Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/'+r+'-In2-path.json').write_text(json.dumps(pp))
