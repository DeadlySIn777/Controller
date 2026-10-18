"""One native board load per process; persisted, asserted mutation fixtures."""
import sys,json,copy
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
from hardware_check_return_corridors import circle
from hardware_map_motherboard_domains import write,sha
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
base=Path(sys.argv[2]);b=pcbnew.LoadBoard(str(base));b.BuildConnectivity()
if not isinstance(b,pcbnew.BOARD):raise ValueError('Fresh process must load an actual BOARD')
decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
signal='9e3b3c61-a4fa-4f6d-a8e3-3105c611f45c';via='2b560de3-f84e-4d9e-a5e9-2e7289869ab7';ground='f51de4d1-376b-4ba9-bd45-2472d0d7d531'
items={t.m_Uuid.AsString():t for t in b.GetTracks()}
if sys.argv[1]=='positive':
 rows=json.loads(Path(sys.argv[3]).read_text())['rows'];check=ExactEndpointUnionCheck(b,{r['net']:decl for r in rows})
 proofs=[check.segment(items[r['actual_copper_UUIDs'][0]],decl)for r in rows]
 if len(proofs)!=82:raise ValueError('Exact82 obligations changed')
 write(Path(sys.argv[4]),dict(passed=True,board_sha256=sha(base),exact82_actual_control_segment_proofs=proofs));print('All82 actual controls passed');sys.exit()
name=sys.argv[3];dest=Path(sys.argv[4]);evidence={}
if name=='cut_actual_Source_Ground_stitch':
 b.Remove(items[ground]);assert ground not in {t.m_Uuid.AsString()for t in b.GetTracks()};evidence['actual_removed_uuid']=ground
elif name=='wrong_signal_via_net':
 t=items[via];old=t.GetNetname();t.SetIsFree(True);t.SetNetCode(next(t.GetNetCode()for t in b.GetTracks()if t.GetNetname()=='/motherboard_power_entry/MOTION_5V_RAW'));assert t.GetNetname()!=old;evidence.update(before=old,after=t.GetNetname())
elif name=='wrong_actual_endpoint_position':
 t=items[via];old=tuple(t.GetPosition());t.SetIsFree(True);t.SetPosition(t.GetPosition()+pcbnew.VECTOR2I(pcbnew.FromMM(.01),0));assert tuple(t.GetPosition())!=old;evidence.update(before_nm=old,after_nm=tuple(t.GetPosition()))
elif name=='wrong_declared_actual_via_geometry':
 decl['via_diameter_mm']=.6;assert pcbnew.ToMM(items[via].GetWidth(pcbnew.F_Cu))==.5;evidence.update(actual_diameter_mm=.5,declared_diameter_mm=.6)
elif name in('real_foreign_reference_hole_outside_endpoint_antipad','actual_adjacent_reference_plane_absent'):
 hole=circle((pcbnew.FromMM(273.2),pcbnew.FromMM(179.6)),pcbnew.FromMM(.08));before=after=0;changed=[]
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()!='/LOGIC_GND'or not z.HasFilledPolysForLayer(pcbnew.In1_Cu):continue
  p=pcbnew.SHAPE_POLY_SET();p.Append(z.GetFilledPolysList(pcbnew.In1_Cu));a=exact_twice_area(p);before+=a
  if name=='actual_adjacent_reference_plane_absent':p.RemoveAllContours()
  else:p.BooleanSubtract(hole)
  a2=exact_twice_area(p);after+=a2
  if a2!=a:changed.append(z.m_Uuid.AsString())
  z.SetFilledPolysList(pcbnew.In1_Cu,p)
 assert before>after and changed;evidence.update(before_twice_area_nm2=before,after_twice_area_nm2=after,changed_actual_zone_UUIDs=changed)
else:raise ValueError('Undeclared native negative')
b.BuildConnectivity();pcbnew.SaveBoard(str(dest),b);write(dest.with_suffix('.declaration.json'),decl);write(dest.with_suffix('.mutation.json'),dict(passed=True,name=name,evidence=evidence,board_sha256=sha(dest),one_native_load=True));print(json.dumps(evidence))
