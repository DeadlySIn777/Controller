from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_route_logic_return import mm
p=Path(__file__).parent;board=pcbnew.LoadBoard(str(p/'CORE-literal-antipad-join-cck-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'))
old=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb');oldids={t.m_Uuid.AsString()for t in old.GetTracks()};rows=[]
for xy in((94.4,46.4),(93.6,48.8)):
 neighbours=[]
 for t in board.GetTracks():
  if t.Type()!=pcbnew.PCB_VIA_T or t.m_Uuid.AsString()not in oldids:continue
  if math.dist(mm(t.GetPosition()),xy)<=1.3:neighbours.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),xy=mm(t.GetPosition()),physical_In3_Cu_shape=t.GetEffectiveShape(pcbnew.In3_Cu).Format(),diameter_In3_mm=pcbnew.ToMM(t.GetWidth(pcbnew.In3_Cu)),drill_mm=pcbnew.ToMM(t.GetDrill()),FlashLayer=t.FlashLayer(pcbnew.In3_Cu),distance_mm=math.dist(mm(t.GetPosition()),xy)))
 rows.append(dict(new_xy=xy,actual_retained_neighbours=neighbours))
(p/'CORE-collar-pair-antipads-review-r03/neighbours-r04.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
