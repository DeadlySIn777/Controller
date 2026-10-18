from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_scope_anchored_reference_pieces as pieces
from hardware_check_return_corridors import covered
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-critical7-r79/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r79-r01/domain-map.json')
OUT=Path('reports/motherboard-critical-routing-20261001/source26-root79-FPGA-endpoint-reference-r01');OUT.mkdir(exist_ok=False,parents=True)
name='/fpga_core/FPGA_FLASH_CCK_SOURCE';row=e.read('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')['nets'][name]
b=pcbnew.LoadBoard(str(BASE));check=pieces.SourceAnchoredPiecesCheck(b,{name:row},e.read(MAP));records=[]
for side,ref in((pcbnew.F_Cu,pcbnew.In1_Cu),(pcbnew.B_Cu,pcbnew.In4_Cu)):
 fill=check.reference('/LOGIC_GND',ref)
 for point in((95.6,46.8),(95.2,47.2),(94.4,47.2),(93.6,47.2),(110.175,27),(108.575,33.2),(108.575,34)):
  center=tuple(pcbnew.FromMM(v)for v in point);poly=e.corridor_polygon(center,center,pcbnew.FromMM(.575))
  raw=pcbnew.SHAPE_POLY_SET()
  for zone in b.Zones():
   if zone.GetNetname()=='/LOGIC_GND'and zone.HasFilledPolysForLayer(ref):raw.BooleanAdd(zone.GetFilledPolysList(ref))
  raw.Simplify()
  records.append(dict(side=b.GetLayerName(side),reference=b.GetLayerName(ref),point_mm=point,actual_raw_native_fill_center=raw.Contains(pcbnew.VECTOR2I(*center)),actual_SOURCE_eligible_fill_center=fill.Contains(pcbnew.VECTOR2I(*center)),actual_raw_full_40_margin_screen=covered(poly,raw),actual_SOURCE_eligible_full_40_margin_screen=covered(poly,fill)))
e.write(OUT/'review.json',dict(board_sha256=e.sha(BASE),map_sha256=e.sha(MAP),records=records,all_full_native_failed_resources=check.full_native_report['unanchored_components'],no_board_or_source_mutation=True,manufacturing_ready=False));print(json.dumps(records),flush=True)
