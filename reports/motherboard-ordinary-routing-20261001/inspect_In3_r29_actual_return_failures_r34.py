"""Check failed native corridors with the independently controlled exact union algebra."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path('reports/motherboard-return-zoning-20261001').resolve())]
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
e=ordinary.engine
p=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-DI7-In3-extended-r29')
board=p/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
plan=e.read(p/'proposed-groups.json');manifest=e.read(p/'manifest.json')
ordinary.MAPPING=e.read('reports/motherboard-domains-20261001/source26-In3-r29-r01/domain-map.json')
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();check=ordinary.LiteralPieces(b,manifest['nets'])
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};results=[]
for group in plan['groups']:
 for uid in group['signal_UUIDs']:
  t=cu[uid];row=manifest['nets'][t.GetNetname()]
  if t.Type()==pcbnew.PCB_VIA_T:continue
  result=dict(uuid=uid,net=t.GetNetname(),source_pair=group['source_pair'])
  try:result['original']=check.segment(t,row)
  except Exception as ex:result['original_error']=str(ex)
  try:result['exact_union']=ExactEndpointUnionCheck.segment(check,t,row)
  except Exception as ex:result['exact_union_error']=str(ex)
  results.append(result)
e.write(p/'actual-corridor-algebra-diagnostic-r34.json',dict(board_sha256=e.sha(board),results=results,algebra_controls='reports/motherboard-return-zoning-20261001/motor-exact-antipad-union-native-controls-r04/review.json',guard_tolerances_changed=False,adopted=False))
print(json.dumps([r for r in results if 'original_error'in r or 'exact_union_error'in r],indent=2))
