from pathlib import Path
import sys, json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_search_native_local_path import find_local_pad_path
e=o.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-four-reference-closures-r71/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r71-r01/domain-map.json')
MAN=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root71-local-clipped-r02/manifest.json')
OUT=Path('reports/motherboard-ordinary-routing-20261001/finite-local-search-native-r01')
OUT.mkdir(exist_ok=False)
board=pcbnew.LoadBoard(str(BASE));board.BuildConnectivity();o.MAPPING=e.read(MAP)
check=o.LiteralPieces(board,e.read(MAN)['nets']);fill=check.reference('/LOGIC_GND',pcbnew.In1_Cu)
g=w.Geometry(board);pads={(f.GetReference(),p.GetNumber()):p for f in board.GetFootprints()for p in f.Pads()}
a,b=pads['U1001','A3'],pads['TP22001','1']
healthy=find_local_pad_path(board,a,b,geometry=g,eligible_reference_fill=fill,clearance_mm=.15)
if not healthy['passed'] or healthy['path_length_mm']>8:raise ValueError('Actual full motherboard SOURCE-pair positive failed')
empty=find_local_pad_path(board,a,b,geometry=g,eligible_reference_fill=pcbnew.SHAPE_POLY_SET(),clearance_mm=.15)
if empty['passed']:raise ValueError('Actual missing adjacent reference negative failed')
wrong=False
try:find_local_pad_path(board,a,pads['U1001','A4'],geometry=g,eligible_reference_fill=fill)
except ValueError:wrong=True
if not wrong:raise ValueError('Actual foreign SOURCE endpoint negative failed')
e.write(OUT/'review.json',dict(passed=True,board_sha256=e.sha(BASE),map_sha256=e.sha(MAP),helper_sha256=e.sha('tools/hardware_search_native_local_path.py'),actual_full_motherboard_positive=healthy,actual_missing_reference_negative=empty,actual_wrong_SOURCE_net_negative_rejected=wrong,complete_failed_reference_piece_ledger=check.full_native_report['unanchored_components'],no_copper_added=True,whole_board_reference_qualification=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,path_mm=healthy['path_length_mm'],explored=healthy['explored_states'],negative_controls=2)),flush=True)
