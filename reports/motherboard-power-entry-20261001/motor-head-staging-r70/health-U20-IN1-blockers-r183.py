import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,segment_distance
from hardware_route_power_groups_native import hits
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r181/debug.kicad_pcb');g=FastGeometry(b);pt=(343.8625,174.35);n='/motherboard_power_entry/CORE_HEALTH_A_N';gap=.26
for p in b.GetPads():
 if not p.IsOnLayer(pcbnew.F_Cu)or p.GetNetname()==n:continue
 q=p.GetEffectivePolygon(pcbnew.F_Cu)
 if any(hits(pt,pt,[mm(q.Outline(k).CPoint(i))for i in range(q.Outline(k).PointCount())],gap)for k in range(q.OutlineCount())):print('PAD',p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))
for t in b.GetTracks():
 if not t.IsOnLayer(pcbnew.F_Cu)or t.GetNetname()==n:continue
 w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())
 if segment_distance(pt,pt,mm(t.GetStart()),mm(t.GetEnd()))<gap+w/2-1e-6:print('CU',t.m_Uuid.AsString(),t.GetNetname(),mm(t.GetStart()),mm(t.GetEnd()),w)
print('sourceclear',g.clear([(338.1625,174.35)]*2,n,pcbnew.F_Cu,.2),'endclear',g.clear([pt]*2,n,pcbnew.F_Cu,.2))
for r,p in g.barriers:
 if any(330<x<349 and 165<y<181 for x,y in p):print('BARRIER',r,p)
res=g.grid((338.1625,174.35),pt,n,pcbnew.F_Cu,.2,step=.1,padding=15,max_nodes=180000);print('LARGEPATH',res)
