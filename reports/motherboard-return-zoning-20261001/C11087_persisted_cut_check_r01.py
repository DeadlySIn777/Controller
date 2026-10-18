"""Reload one persisted native physical cut independently, without mutation."""
import sys,json
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
p=Path(sys.argv[1]);r=json.loads(p.with_suffix('.review.json').read_text());assert r['passed']and r['board_sha256']==sha(p);b=pcbnew.LoadBoard(str(p));b.BuildConnectivity();tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};pin=lambda ref,n:next(q for q in fps[ref].Pads()if q.GetNumber()==n);cap=pin('C11087','1');vcc=pin('U11033','5');connected=vcc.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(cap)}
mut=r['asserted_actual_mutation'];name=r['name']
if name=='cut_actual_VCC_receiving_branch':
 assert mut['actual_removed_UUID']not in tracks and not connected;reason='Fresh native reload proves exact C11087.1/U11033.5 SOURCE pair physically open'
else:
 if name=='cut_actual_nearby_SOURCE_Ground_barrel':assert mut['actual_removed_UUID']not in tracks
 elif name=='wrong_actual_Ground_barrel_net':assert tracks[mut['UUID']].GetNetname()==mut['actual_after_net']and tracks[mut['UUID']].GetIsFree()
 else:raise ValueError('Unreviewed case')
 row=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);check=NativeCollectedAnnulusCheck(b,{cap.GetNetname():row});reason=None
 try:check.via(tracks['8bc78829-90a6-4e9c-a190-9bcaaa46fd1f'],row)
 except ValueError as error:reason=str(error)
 assert reason is not None
write(p.with_suffix('.fresh-native-review.json'),dict(passed=True,case=name,board_sha256=sha(p),fresh_native_reload_rejected=True,reason=reason,persisted_mutation_verified=True,no_Source_stitch_or_annulus_waiver=True));print(json.dumps(dict(passed=True,case=name,reason=reason)))
