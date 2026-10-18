from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import hardware_route_ordinary_wip_r05 as issued
import hardware_bind_ordinary_route_manifest_r03 as binder
from hardware_scope_anchored_reference_pieces import qualify
out=ROOT/'reports/motherboard-ordinary-routing-20261001/actual-source26-root62-r01'
out.mkdir()
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'
full=base.parent/'actual-board-bound-reference-review.json'
mapping=ROOT/'reports/motherboard-domains-20261001/source26-r62-r01/domain-map.json'
proof=qualify(full,mapping,base,['/LOGIC_GND'],['In1.Cu','In4.Cu'])
issued.engine.write(out/'piece-eligibility.json',proof)
review=issued.engine.read(ROOT/issued.SOURCE);names=sorted(review['nets']);issued.engine.write(out/'selected.json',names)
manifest=binder.bind(base,out/'piece-eligibility.json',out/'manifest.json',names)
print(json.dumps(dict(selected_nets=len(manifest['nets']),eligible_pieces=len(proof['eligible_filled_components']),failed_pieces_retained=len(proof['complete_unanchored_components']),whole_return_net_qualification=False,whole_board_reference_qualification=False)))
