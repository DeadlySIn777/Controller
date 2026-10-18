"""Read actual blocked Source pad and reference geometry before changing routing."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import mm
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb')
O=Path('reports/motherboard-ordinary-routing-20261001/ROOT101-permission-receiving-inspection-r48.json');assert not O.exists()
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
fills=collect_native_reference_fills(b,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu])
rows=[]
for ref,num in [('U14402','13'),('U14501','20'),('U17013','6'),('U13001','38')]:
 p=next(p for p in fps[ref].Pads()if p.GetNumber()==num);c=mm(p.GetPosition())
 near=[]
 for v in b.GetTracks():
  if v.Type()==pcbnew.PCB_VIA_T and math.dist(mm(v.GetPosition()),c)<3:
   near.append(dict(uuid=v.m_Uuid.AsString(),net=v.GetNetname(),mm=mm(v.GetPosition()),diameter=pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))))
 rows.append(dict(ref=ref,pin=num,net=p.GetNetname(),mm=c,land_mm=mm(p.GetSize()),surface=b.GetLayerName(fps[ref].GetLayer()),pad_center_own_reference={b.GetLayerName(l):covered(circle(tuple(p.GetPosition()),pcbnew.FromMM(.2)),fills['/LOGIC_GND',l])for l in (pcbnew.In1_Cu,pcbnew.In4_Cu)},nearby_barrels=near,nearby_pads=[dict(ref=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),net=q.GetNetname(),mm=mm(q.GetPosition()))for q in b.GetPads()if math.dist(mm(q.GetPosition()),c)<1.5]))
write(O,dict(board_sha256=sha(B),inspection_only=True,rows=rows))
for r in rows:print(json.dumps({k:v for k,v in r.items()if k!='nearby_pads'}))
