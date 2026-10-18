"""One exact SOURCE-backed Ground transfer for the moved U11033 bypass."""
import sys,json,math,shutil
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_owned_bypass_loops import Geometry
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import circle,covered
from hardware_route_logic_return import xy,mm,identity,pad_identity
base=Path('reports/motherboard-return-zoning-20261001/source26-ROOT88-eight-actual-DFM-slivers-r02/motherboard-eight-unused-slivers-candidate.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01')
if out.exists():raise ValueError('Fresh immutable output required')
out.mkdir();b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};pin=lambda ref,n:next(p for p in fps[ref].Pads()if p.GetNumber()==n);ground=pin('C11087','2');power=pin('C11087','1');vcc=pin('U11033','5');return_pin=pin('U11033','3')
if ground.GetNetname()!='/LOGIC_GND' or power.GetNetname()!=vcc.GetNetname()or return_pin.GetNetname()!=ground.GetNetname():raise ValueError('Exact actual C11087/U11033 Source pair differs')
g=Geometry(b);check=NativeCollectedAnnulusCheck(b,{});source_via=next(t for t in b.GetTracks()if t.m_Uuid.AsString()=='8bc78829-90a6-4e9c-a190-9bcaaa46fd1f');center=mm(source_via.GetPosition());s=mm(ground.GetPosition());trial=[];chosen=None
for x,y in [(252.3,194.3),(252.2,194.3),(252.3,194.0),(252.2,194.0),(252.4,194.0),(252.2,194.5),(252.3,194.6),(252.4,194.6),(252.95,195.1),(252.4,193.9),(252.3,193.9)]:
 if math.dist((x,y),center)>1.:continue
 via_ok=g.via((x,y),ground.GetNetname());fills={b.GetLayerName(l):covered(circle(tuple(xy((x,y))),pcbnew.FromMM(.24)),check.reference(ground.GetNetname(),l))for l in(pcbnew.In1_Cu,pcbnew.In4_Cu)}
 routes=[[s,(x,y)],[s,(x,s[1]),(x,y)],[s,(s[0],y),(x,y)]];legal=next((r for r in routes if g.clear(r,ground.GetNetname(),pcbnew.B_Cu,.25)),None)
 trial.append(dict(point_mm=[x,y],via_geometry_clear=via_ok,actual_adjacent_full_circle_coverage=fills,legal_own_Ground_branch=legal))
 if via_ok and all(fills.values())and legal:chosen=((x,y),legal);break
write(out/'search.json',dict(base_board_sha256=sha(base),actual_Source_power_pair=dict(cap='C11087.1',owner='U11033.5',net=power.GetNetname()),actual_Source_return_pair=dict(cap='C11087.2',owner='U11033.3',net=ground.GetNetname()),actual_power_transfer_UUID=source_via.m_Uuid.AsString(),actual_power_transfer_mm=center,trials=trial))
if chosen is None:raise ValueError('No exact legal Source Ground transfer found; no PCB emitted')
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};point,path=chosen;new=[]
for start,end in zip(path,path[1:]):
 if start==end:continue
 t=pcbnew.PCB_TRACK(b);t.SetStart(xy(start));t.SetEnd(xy(end));t.SetWidth(pcbnew.FromMM(.25));t.SetLayer(pcbnew.B_Cu);t.SetNetCode(ground.GetNetCode());b.Add(t);new.append(t.m_Uuid.AsString())
v=pcbnew.PCB_VIA(b);v.SetPosition(xy(point));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNetCode(ground.GetNetCode());v.SetIsFree(True);b.Add(v);new.append(v.m_Uuid.AsString())
dest=out/'motherboard-C11087-ground-transfer-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=new,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='One actual low-current C11087 Ground branch/through stitch for its moved U11033 receiver bypass,0.5/0.2mm free-standing via within1mm of the existing actual power transfer; all old Source pads/Cu/poses/zones preserved. Native refill/full Source/cut/annulus/100retained+1replacement proofs required.'))
write(out/'generation.json',dict(before_board=str(base),before_board_sha256=sha(base),board_sha256=sha(dest),new_Cu_UUIDs=new,new_ground_via_UUID=v.m_Uuid.AsString(),new_ground_via_mm=point,actual_existing_power_transfer_UUID=source_via.m_Uuid.AsString(),source_ground_stitch_distance_mm=math.dist(point,center),Ground_branch_points_mm=path,all_old_Cu_pads_poses_zones_preserved=True,native_refill_and_validation_pending=True));print(json.dumps(dict(selected=chosen,new_ground_uuid=v.m_Uuid.AsString(),new_Cu=new)))
