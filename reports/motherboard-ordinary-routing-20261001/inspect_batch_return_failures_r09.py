from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
from hardware_check_return_corridors import circle,corridor_polygon
e=o.engine;p=Path(__file__).parent/'actual-source26-root83-In2-batch-r09'
b=pcbnew.LoadBoard(str(p/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'));b.BuildConnectivity();o.MAPPING=e.read(p/'fresh-domain-map/domain-map.json')
man=e.read(p/'manifest.json');checker=o.LiteralPieces(b,man['nets']);cu={t.m_Uuid.AsString():t for t in b.GetTracks()};groups=e.read(p/'proposed-groups.json')['groups'];rows=[]
for g in groups:
 failures=[]
 for uid in g['signal_UUIDs']:
  t=cu[uid]
  try:checker.via(t,man['nets'][g['net']])if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,man['nets'][g['net']])
  except Exception as ex:
   failures.append(dict(uuid=uid,kind='via'if t.Type()==pcbnew.PCB_VIA_T else'segment',layer=b.GetLayerName(t.GetLayer()),start_mm=[x/1e6 for x in tuple(t.GetStart())],end_mm=[x/1e6 for x in tuple(t.GetEnd())],reason=str(ex)))
 rows.append(dict(net=g['net'],pair=g['source_pair'],failures=failures,passed=not failures))
e.write(p/'individual-return-inspection.json',dict(board_sha256=e.sha(p/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'),groups=rows,diagnostic_only=True))
print(json.dumps(rows,indent=2))
