"""Native actual-board/cache identity and stale-fill controls for r02 wrapper."""
import json,hashlib,copy
from pathlib import Path
import pcbnew
from check_same_side_bypass_r02 import check_group,BoundSameSideCheck,board_geometry_digest
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
BASE=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/motherboard-literal38-neck-rule-candidate.kicad_pcb'
MP=ROOT/'reports/motherboard-domains-20261001/source26-r76-r01/domain-map.json'
OWNERS=ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
DEST=HERE/'same-side-native-cache-controls-r02.json';assert not DEST.exists()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[BASE,MP,OWNERS,HERE/'check_same_side_bypass_r02.py',HERE/'same-side-real-circuit-proof-r01.json',HERE/'same-side-native-controls-r02.json',Path(__file__)]
frozen={str(p):sha(p)for p in files}
row=next(v for v in read(OWNERS)['capacitors']if v['ref']=='C13013')
original=next(v for v in read(HERE/'same-side-real-circuit-proof-r01.json')['actual_circuit_checks']if v['ref']=='C13013')
g=original['group'];m=read(MP);b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity()
r=original['review'];declaration=dict(return_net=r['return_net'],reference_layers={'F.Cu':'In1.Cu'},allow_vias=False,reference_corridor_margin_mm=.10)
c=BoundSameSideCheck(b,{r['supply_net']:declaration},m)
good=check_group(b,g,row,m,c);assert good['passed']
results=[dict(mode='exact_current_board_map_fill',passed=True)]
def rejected(mode,board=b,mapping=m,checker=c):
 try:check_group(board,g,row,mapping,checker)
 except ValueError as e:results.append(dict(mode=mode,passed=True,rejection=str(e)));return
 raise AssertionError('Stale cache unexpectedly accepted: '+mode)
other=pcbnew.LoadBoard(str(BASE));rejected('different_board_same_geometry',board=other)
rejected('unbound_checker_class',checker=object())
wrong=copy.deepcopy(m);wrong['schema_version']+=1;rejected('changed_source_map',mapping=wrong)
z=next(z for z in b.Zones()if z.GetNetname()==r['return_net']and z.IsOnLayer(pcbnew.In1_Cu)and z.HasFilledPolysForLayer(pcbnew.In1_Cu)and z.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount()>0)
saved=pcbnew.SHAPE_POLY_SET();saved.Append(z.GetFilledPolysList(pcbnew.In1_Cu))
z.UnFill();assert board_geometry_digest(b)!=c._board_digest, 'Negative must actually alter a nonempty reference resource';rejected('refill_removed_after_cache')
z.SetFilledPolysList(pcbnew.In1_Cu,saved);z.SetIsFilled(True)
assert board_geometry_digest(b)==c._board_digest
t=next(t for t in b.GetTracks()if t.Type()==pcbnew.PCB_TRACE_T)
old=t.GetWidth();t.SetWidth(old+pcbnew.FromMM(.01));rejected('actual_conductor_geometry_changed');t.SetWidth(old)
assert board_geometry_digest(b)==c._board_digest
p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='C13013')
saved_pos=pcbnew.VECTOR2I(p.GetPosition());p.SetPosition(saved_pos+pcbnew.VECTOR2I(1,0));rejected('actual_pad_moved_one_nanometre');p.SetPosition(saved_pos)
assert board_geometry_digest(b)==c._board_digest
assert check_group(b,g,row,m,c)['passed']
assert frozen=={p:sha(Path(p))for p in frozen}
DEST.write_text(json.dumps(dict(passed=True,inputs=frozen,cases=results,restored_actual_native_board_passed=True,
                               previous_eight_geometry_controls_preserved_by_frozen_r01_dependency=True,
                               actual_disk_board_source_unchanged=True,new_router_authorized=False),indent=2)+'\n')
print(dict(passed=True,cases=len(results),restored_native_positive=True))
