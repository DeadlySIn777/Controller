"""Independent read-only native local-metal screen of one explicit DFM cut.

This is not a topology/capacity waiver. The parent's actual full and eroded
Source/receiver proof still must pass before any outline mutation is adopted.
"""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import rectangle
from hardware_route_logic_return import mm,identity
base=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
cuts=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root83-In2-batch-r12/rejected-power-cut-location.json')
out=Path('reports/motherboard-return-zoning-20261001/IO3-three-tip-local-native-DFM-review-r01.json')
if out.exists():raise ValueError('Fresh immutable local native review required')
board=pcbnew.LoadBoard(str(base));layer=pcbnew.In2_Cu
cut=rectangle([91.095,211.11,91.18,211.30]);own='/IO_3V3'
actual_nets=sorted({p.GetNetname()for p in board.GetPads()if 'IO_3V3'in p.GetNetname()})
if actual_nets!=[own]:raise ValueError('Exact integrated IO3 rail name changed')
pad_hits=[];track_hits=[];nearest=[]
center=(91.1375,211.205)
for p in board.GetPads():
 if p.GetNetname()!=own or not p.GetNumber():continue
 fp=p.GetParentFootprint();nearest.append(dict(reference=fp.GetReference(),pin=p.GetNumber(),uuid=p.m_Uuid.AsString(),point_mm=mm(p.GetPosition()),distance_mm=math.dist(center,mm(p.GetPosition()))))
 # Project all actual Source/receiver pad metal onto the proposed positive
 # plane cut, even for an SMD pad on the opposite surface.
 layers=[l for l in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu)if p.IsOnLayer(l)]
 if any(cut.Collide(p.GetEffectiveShape(l))for l in layers):pad_hits.append(nearest[-1])
for t in board.GetTracks():
 if t.GetNetname()==own and t.IsOnLayer(layer)and cut.Collide(t.GetEffectiveShape(layer)):track_hits.append(identity(t))
write(out,dict(read_only=True,input_sha256={str(p):sha(p)for p in(base,cuts,Path(__file__))},exact_copper_pour_only_DFM_cut_bounds_mm=[91.095,211.11,91.18,211.30],return_layer='In2.Cu',literal_power_net=own,intersecting_actual_IO3_Source_receiver_pad_metal_all_sides=pad_hits,intersecting_actual_IO3_native_tracks_vias=track_hits,nearest_actual_numbered_IO3_pads=sorted(nearest,key=lambda r:r['distance_mm'])[:8],local_own_metal_clear=not pad_hits and not track_hits,full_native_topology_502um_core_all44_Source_22_receivers_annuli_and_reference_proof_still_required=True,blanket_area_or_precision_exemption=False,ampacity_qualified=False,manufacturing_ready=False))
print(json.dumps(dict(local_own_metal_clear=not pad_hits and not track_hits,pad_hits=len(pad_hits),track_hits=len(track_hits)),indent=2))
