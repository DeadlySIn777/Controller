import sys,json,math,time
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,segment_distance
from hardware_route_local_signals import GeometryIndex
from hardware_route_power_groups_native import hits
class InnerGeometry(FastGeometry):
 def __init__(self,b):
  super().__init__(b);self.actual_inner_pad=[]
  for p in b.GetPads():
   if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:continue
   self.actual_inner_pad.append(p)
  for l in[pcbnew.In3_Cu]:
   self.tracks[l]=GeometryIndex()
   for t in b.GetTracks():
    if t.IsOnLayer(l):
     a,c=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM((t.GetWidth(l) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth()));self.tracks[l].add((t.GetNetname(),a,c,w),(min(a[0],c[0])-w/2,min(a[1],c[1])-w/2,max(a[0],c[0])+w/2,max(a[1],c[1])+w/2))
 def clear(self,ps,n,l,w):
  if l in[pcbnew.F_Cu,pcbnew.B_Cu]:return super().clear(ps,n,l,w)
  gap=w/2+.16
  for s,e in zip(ps,ps[1:]):
   if any(not(.8+w/2<=p[0]<=459.2-w/2 and .8+w/2<=p[1]<=339.2-w/2)for p in[s,e]):return False
   if any(hits(s,e,poly,w/2)for ref,poly in self.barrier_index.candidates(s,e,w/2)):return False
   for p in self.actual_inner_pad:
    if p.GetNetname()==n:continue
    if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(s[0]),pcbnew.FromMM(s[1]))):return False
    z=mm(p.GetPosition());padw=max(mm(p.GetSize()))/2
    if segment_distance(s,e,z,z)<gap+padw-1e-6:return False
   for net,a,c,width in self.tracks[l].candidates(s,e,gap):
    if net!=n and segment_distance(s,e,a,c)<gap+width/2-1e-6:return False
  return True
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r326/debug.kicad_pcb');g=InnerGeometry(b);n='/motherboard_power_entry/MOTOR_FEED_CLEAR_SOURCE_B';s=(271.075,150);e=(353.15,178.385)
print('VIA',[(pt,all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]))for pt in[s,e]],flush=True)
for l in[pcbnew.In3_Cu]:
 t=time.time();pp=g.grid(s,e,n,l,.2,step=.5,padding=25,max_nodes=140000);print(b.GetLayerName(l),round(time.time()-t,1),pp,flush=True)
