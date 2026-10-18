"""Fresh native persisted U11025 supply/Source-stitch/reference-hole controls."""
import argparse,json,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import circle
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
ap=argparse.ArgumentParser();ap.add_argument('case',choices=['VCC_branch','actual_nearby_Source_Ground_barrel','actual_foreign_hole_in_reference_annulus']);ap.add_argument('--reload',action='store_true');a=ap.parse_args()
D=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U25-field-collars-r02');B=D/'motherboard-health-U25-field-reference-candidate.kicad_pcb'
dest=D/('physical-cut-'+a.case+'.kicad_pcb');meta=dest.with_suffix('.mutation.json')
if not a.reload and dest.exists():raise ValueError('Fresh persisted native control required')
b=pcbnew.LoadBoard(str(dest if a.reload else B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()}
cp=next(p for p in fps['C11080'].Pads()if p.GetNumber()=='1');op=next(p for p in fps['U11025'].Pads()if p.GetNumber()=='5')
field=next(p for p in fps['C11080'].Pads()if p.GetNumber()=='2').GetNetname()
pv=cu['0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3']
if a.reload:
 m=json.loads(meta.read_text());assert sha(dest)==m['board_sha256']
 if a.case=='VCC_branch':assert m['removed_uuid']not in cu
 elif a.case=='actual_nearby_Source_Ground_barrel':assert m['removed_uuid']not in cu
 else:
  before=m['before_in1_twice_area_nm2'];after=sum(exact_twice_area(z.GetFilledPolysList(pcbnew.In1_Cu))for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()==field and z.IsOnLayer(pcbnew.In1_Cu));assert after==m['after_in1_twice_area_nm2']and before>after
else:
 m=dict(case=a.case,before_board_sha256=sha(B))
 if a.case=='VCC_branch':
  uid='f05f32fd-1116-432e-afbe-c48a00ed63c0';b.Remove(cu[uid]);m['removed_uuid']=uid
 elif a.case=='actual_nearby_Source_Ground_barrel':
  t=next(t for t in cu.values()if t.Type()==pcbnew.PCB_VIA_T and tuple(t.GetPosition())==(pcbnew.FromMM(333.4375),pcbnew.FromMM(191.)))
  m['removed_uuid']=t.m_Uuid.AsString();b.Remove(t)
 else:
  hole=circle((pcbnew.FromMM(333.4375),pcbnew.FromMM(190.5)),pcbnew.FromMM(.08));before=after=0;changed=[]
  for z in b.Zones():
   if z.GetIsRuleArea()or z.GetNetname()!=field or not z.IsOnLayer(pcbnew.In1_Cu):continue
   p=pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(pcbnew.In1_Cu));old=exact_twice_area(p);before+=old;p.BooleanSubtract(hole);new=exact_twice_area(p);after+=new
   if old!=new:changed.append(z.m_Uuid.AsString())
   p.Fracture();z.SetFilledPolysList(pcbnew.In1_Cu,p);z.SetIsFilled(True)
  assert before>after and changed
  m.update(before_in1_twice_area_nm2=before,after_in1_twice_area_nm2=after,exact_hole_xy_mm=[333.4375,190.5],hole_radius_mm=.08,changed_zone_UUIDs=changed)
 b.BuildConnectivity()
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(suffix),dest.with_suffix(suffix))
 pcbnew.SaveBoard(str(dest),b);m['board_sha256']=sha(dest);write(meta,m)
co=b.GetConnectivity()
if a.case=='VCC_branch':
 assert op.m_Uuid.AsString()not in{x.m_Uuid.AsString()for x in co.GetConnectedItems(cp)},'Actual VCC pair stayed closed; not a meaningful supply cut'
 reason='Actual capacitor1/receiverVCC5 pair is open'
else:
 row=dict(return_net=field,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10)
 check=NativeCollectedAnnulusCheck(b,{cp.GetNetname():row});reason=None
 try:check.via(pv,row)
 except ValueError as e:reason=str(e)
 assert reason,'Actual cut incorrectly passes the unchanged Source/annulus/stitch guard'
out=dest.with_suffix('.fresh-native-review.json'if a.reload else'.review.json');assert not out.exists()
write(out,dict(passed=True,case=a.case,board_sha256=sha(dest),persisted_actual_mutation_verified=a.reload,rejection=reason,no_guard_radius_margin_geometry_or_Source_exception=True))
print(json.dumps(dict(passed=True,case=a.case,fresh_reload=a.reload,rejection=reason)))
