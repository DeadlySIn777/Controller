"""One fresh native process per real receiving-bypass physical cut."""
import sys,json
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import write,sha
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
base=Path('reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01/motherboard-C11087-ground-transfer-candidate.kicad_pcb');gen=json.loads((base.parent/'generation.json').read_text());name=sys.argv[1];dest=Path(sys.argv[2]);b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};pin=lambda r,n:next(p for p in fps[r].Pads()if p.GetNumber()==n)
if name=='cut_actual_VCC_receiving_branch':
 uid='04d15de0-5cea-4409-b460-c82bbac9b722';b.Remove(tracks[uid]);assert uid not in{t.m_Uuid.AsString()for t in b.GetTracks()};mut=dict(actual_removed_UUID=uid)
elif name=='cut_actual_nearby_SOURCE_Ground_barrel':
 uid=gen['new_ground_via_UUID'];b.Remove(tracks[uid]);assert uid not in{t.m_Uuid.AsString()for t in b.GetTracks()};mut=dict(actual_removed_UUID=uid)
elif name=='wrong_actual_Ground_barrel_net':
 t=tracks[gen['new_ground_via_UUID']];old=t.GetNetname();t.SetIsFree(True);t.SetNetCode(pin('C11087','1').GetNetCode());assert old!=t.GetNetname();mut=dict(UUID=t.m_Uuid.AsString(),before_net=old,actual_after_net=t.GetNetname())
else:raise ValueError('Undeclared physical case')
pcbnew.SaveBoard(str(dest),b);b.BuildConnectivity();cap=pin('C11087','1');vcc=pin('U11033','5');connected=vcc.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(cap)}
row=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);rejected=None
if name=='cut_actual_VCC_receiving_branch':
 if connected:raise ValueError('Actual VCC cut did not sever Source pair')
 rejected='Native SOURCE C11087.1 toU11033.5 pair is physically open'
else:
 check=NativeCollectedAnnulusCheck(b,{cap.GetNetname():row});power=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==gen['actual_existing_power_transfer_UUID'])
 try:check.via(power,row)
 except ValueError as error:rejected=str(error)
 if rejected is None:raise ValueError('Actual Source/Ground cut unexpectedly accepted')
write(dest.with_suffix('.review.json'),dict(passed=True,name=name,board_sha256=sha(dest),asserted_actual_mutation=mut,rejection=rejected,native_power_pair_connected=connected,no_radius_margin_Source_or_annulus_relaxation=True));print(json.dumps(dict(passed=True,name=name,rejection=rejected)))
