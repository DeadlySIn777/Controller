import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_zone_motherboard_returns import return_net
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r216/motor-health-U26-cell-candidate.kicad_pcb');m=json.loads(Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U26-Source-field-screen-r01/domain-map.json').read_text());ds={p['net']:p['domain']for p in m['pads']};rows=[]
for t in b.GetTracks():
 if t.Type()==pcbnew.PCB_VIA_T or t.GetLayer()!=pcbnew.F_Cu:continue
 bb=t.GetBoundingBox();v=[pcbnew.ToMM(n)for n in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())]
 if v[0]>333.5 or v[2]<330.4 or v[1]>188.6 or v[3]<186.5:continue
 ret=return_net(dict(net=t.GetNetname(),domain=ds.get(t.GetNetname())))
 if ret=='/LOGIC_GND':rows.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),start=[pcbnew.ToMM(n)for n in tuple(t.GetStart())],end=[pcbnew.ToMM(n)for n in tuple(t.GetEnd())],width=pcbnew.ToMM(t.GetWidth())))
print(json.dumps(rows,indent=2))
