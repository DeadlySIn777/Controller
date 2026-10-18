"""One actual KiCad board per process; reject electrically invalid transfers."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_validate_return_bridge_sources import review
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered
from hardware_route_selected_additive import corridor_polygon

folder=Path('reports/motherboard-return-zoning-20261001/source26-r62-C17014-field-return-reroute-r01')
receipt=json.load(open(folder/'receipt.json'))
board=folder/'motherboard-C17014-field-ground-rerouted-candidate.kicad_pcb'
source_map=folder/'inputs/domain-map.json'
case=sys.argv[1]
base=folder/'inputs/motherboard-source26-orphan-free-candidate.kicad_pcb'
path=base if case=='original-in1-obstruction' else board
b=pcbnew.LoadBoard(str(path))
items={t.m_Uuid.AsString():t for t in b.GetTracks()}
via_id=receipt['actual_ground_transfer_annuli'][0]['via_uuid']
if case=='missing-southern-transfer':b.Remove(items[via_id])
elif case=='wrong-domain-southern-transfer':items[via_id].SetNet(b.FindNet('/LOGIC_GND'))
elif case=='via-span-without-required-annulus':items[via_id].SetLayerPair(pcbnew.F_Cu,pcbnew.In1_Cu)
elif case not in('healthy','original-in1-obstruction'):raise ValueError(case)
b.BuildConnectivity()
accepted=False;reason=''
try:
 if case=='original-in1-obstruction':
  pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()}
  fills=collect_native_reference_fills(b,{'/LOGIC_GND'},[pcbnew.In1_Cu])
  shape=corridor_polygon(tuple(pads['C17014','1'].GetPosition()),tuple(pads['U17014','14'].GetPosition()),pcbnew.FromMM(.5))
  if not covered(shape,fills['/LOGIC_GND',pcbnew.In1_Cu]):raise ValueError('Actual original In1 FIELD_GND metal cuts the unchanged strict C17014 LOGIC reference corridor')
 else:
  mapping=json.load(open(source_map));actual={t.m_Uuid.AsString():t for t in b.GetTracks()}
  wanted=receipt['new_copper_UUIDs']+[receipt['changed_exact_ground_UUID']]
  review(b,[dict(net='/motherboard_motors/FIELD_GND',new_copper_UUIDs=wanted)],mapping['pads'])
  conn=b.GetConnectivity()
  for row in receipt['actual_ground_transfer_annuli']:
   v=actual.get(row['via_uuid'])
   if v is None:raise ValueError('Actual required same-net ground transfer barrel is missing')
   if v.GetNetname()!='/motherboard_motors/FIELD_GND':raise ValueError('Actual transfer barrel belongs to another return domain')
   for layer in(pcbnew.In1_Cu,pcbnew.In3_Cu):
    if not physical_reference_contact(v,layer,conn):raise ValueError('Actual flashed/native-connected ground transfer annulus absent on '+b.GetLayerName(layer))
 accepted=True
except (ValueError,KeyError) as exc:reason=str(exc)
expected=case=='healthy'
result=dict(case=case,input_board_sha256=sha(path),input_source_map_sha256=sha(source_map),actual_native_accepted=accepted,expected_acceptance=expected,passed=accepted==expected,rejection_reason=reason,mutated_board_saved=False,unchanged_reference_margin_mm=.4)
write(folder/('native-control-'+case+'.json'),result)
print(json.dumps(result,indent=2))
if accepted!=expected:raise SystemExit(1)
