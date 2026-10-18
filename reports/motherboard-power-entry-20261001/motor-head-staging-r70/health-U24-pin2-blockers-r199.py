import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,segment_distance
from hardware_route_power_groups_native import hits
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r196/literal-retired-input.kicad_pcb');g=FastGeometry(b);pt=(346.85,173.635);n='/motherboard_power_entry/CORE_HEALTH_B_LED_K';gap=.26
for p in b.GetPads():
 if not p.IsOnLayer(pcbnew.F_Cu)or p.GetNetname()==n:continue
 q=p.GetEffectivePolygon(pcbnew.F_Cu)
 if any(hits(pt,pt,[mm(q.Outline(k).CPoint(i))for i in range(q.Outline(k).PointCount())],gap)for k in range(q.OutlineCount())):print('PAD',p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))
for t in b.GetTracks():
 if not t.IsOnLayer(pcbnew.F_Cu)or t.GetNetname()==n:continue
 w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())
 if segment_distance(pt,pt,mm(t.GetStart()),mm(t.GetEnd()))<gap+w/2-1e-6:print('CU',t.m_Uuid.AsString(),t.GetNetname(),mm(t.GetStart()),mm(t.GetEnd()),w)
print('SOURCE_POINT_CLEAR_F',g.clear([pt]*2,n,pcbnew.F_Cu,.2),'B',g.clear([pt]*2,n,pcbnew.B_Cu,.2))
