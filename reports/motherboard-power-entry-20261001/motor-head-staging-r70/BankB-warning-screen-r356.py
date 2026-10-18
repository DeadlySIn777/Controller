import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
D=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r350');b=pcbnew.LoadBoard(str(D/'motor-bank-B-receiving-candidate.kicad_pcb'));b.BuildConnectivity();ts={t.m_Uuid.AsString():t for t in b.GetTracks()};old=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/motherboard-health-U19-facing-cell-candidate.kicad_pcb');os={t.m_Uuid.AsString()for t in old.GetTracks()}
for v in json.loads((D/'drc.json').read_text())['violations']:
 for row in v['items']:
  t=ts[row['uuid']];cc=b.GetConnectivity().GetConnectedItems(t)
  print(v['type'],'OLD'if row['uuid']in os else'NEW',identity(t),'PADS',[(q.GetParentFootprint().GetReference(),q.GetNumber())for q in cc if q.Type()==pcbnew.PCB_PAD_T][:20],flush=True)
  if v['type']=='via_dangling':print('LOCAL',[(q.m_Uuid.AsString(),identity(q))for q in b.GetTracks()if q.GetNetname()==t.GetNetname()and (q.GetStart()==t.GetPosition()or q.GetEnd()==t.GetPosition())],flush=True)
