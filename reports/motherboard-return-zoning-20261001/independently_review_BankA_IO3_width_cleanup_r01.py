"""Independent physical review of the literal Bank A unloaded IO3 pour cut.

No source, PCB, guard or root receipt is modified. The separate circuit checks
still govern adoption of a future combined board. Exact integer-native geometry
defines the bounded disposition; no copper is ignored because it is small.
"""
import hashlib,json,sys
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-ordinary-routing-20261001')]
import pcbnew
import check_io3_backbone_preservation_r07 as guard
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
from hardware_stitch_owned_return_planes import definitions
from hardware_route_logic_return import identity,pad_identity
from hardware_zone_motherboard_returns import split_polygons
from hardware_map_motherboard_domains import write

BASE=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb')
CAND=Path('reports/motherboard-pcb-integration-20261001/IO3-BankA-unused-pour-cleanup-baseline-r95a/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb')
ROOT_REVIEW=Path('reports/motherboard-pcb-integration-20261001/IO3-BankA-native-width-cleanup-review-r95e')
OUT=Path('reports/motherboard-return-zoning-20261001/BankA-IO3-width-cleanup-independent-r01')
if OUT.exists():raise ValueError('A fresh immutable independent receipt is required')
OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
INPUTS=[BASE,CAND,ROOT_REVIEW/'receipt.json',ROOT_REVIEW/'cleanup-specific-power-proof.json',ROOT_REVIEW/'literal-native-width-effect-scope.json',Path(guard.__file__),Path(__file__),guard.SOURCE,guard.FEEDS,Path('reports/motherboard-pcb-integration-20261001/kicad-10.0.4-zone-filler-reference.cpp')]
frozen={str(p):sha(p)for p in INPUTS}
assert sha(BASE)=='0a9e4975b2d9cd90f7853884d626427fb089809c45ae5ed749472c68235e2d13'
assert sha(CAND)=='fda233cbe5e176b4b134b01756a0463ccfa1fdf07663806b669608cdc1269146'
assert sha(guard.__file__)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
root=read(ROOT_REVIEW/'receipt.json');assert root['passed']and root['board_sha256']==sha(CAND)
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(CAND))
before.BuildConnectivity();after.BuildConnectivity()

old_cu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()}
assert old_cu=={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
bz=definitions(BASE);az=definitions(CAND);new=set(az)-set(bz)
assert new=={'4976d405-5f87-4adb-b61d-c03f4b0d2df0'} and all(az[u]==v for u,v in bz.items())
area=next(z for z in after.Zones()if z.m_Uuid.AsString()in new)
assert area.GetIsRuleArea()and list(area.GetLayerSet().Seq())==[pcbnew.In2_Cu]
assert area.GetDoNotAllowZoneFills()and not any([area.GetDoNotAllowTracks(),area.GetDoNotAllowVias(),area.GetDoNotAllowPads(),area.GetDoNotAllowFootprints()])
rect=[272.85,176.9,275.75,182.35]
assert guard.symmetric_equal(area.Outline(),guard.box(*rect))
corner_boxes=[[275.225,176.775,275.35,176.9],[275.225,182.35,275.35,182.475]]
allowed=guard.box(*rect)
for box in corner_boxes:allowed.BooleanAdd(guard.box(*box))

bf=guard.collect_native_reference_fills(before,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu])
af=guard.collect_native_reference_fills(after,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu])
old=bf['/IO_3V3',pcbnew.In2_Cu];now=af['/IO_3V3',pcbnew.In2_Cu]
assert guard.symmetric_equal(bf['/CORE_1V2',pcbnew.In3_Cu],af['/CORE_1V2',pcbnew.In3_Cu])
removed=guard.subtract(old,now);added=guard.subtract(now,old)
precision=guard.duplicate(now);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
outside=guard.subtract(guard.subtract(old,precision),allowed)
assert outside.OutlineCount()==0,'A literal old supply feature retreats outside the authorized rectangle/two native-width corners'
assert exact_twice_area(guard.intersection(now,guard.box(*rect)))==0

hit=[]
for z in before.Zones():
 if z.GetIsRuleArea()or not z.IsOnLayer(pcbnew.In2_Cu):continue
 intersect=guard.intersection(z.GetFilledPolysList(pcbnew.In2_Cu),allowed)
 if exact_twice_area(intersect)>0:
  hit.append(dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),minimum_thickness_mm=pcbnew.ToMM(z.GetMinThickness()),exact_twice_area_nm2=exact_twice_area(intersect)))
assert len(hit)==1 and hit[0]['uuid']=='2c0250f6-3aa3-408e-93e5-f0cae2f8dc22'and hit[0]['net']=='/IO_3V3'and hit[0]['minimum_thickness_mm']==.25
for y in(176.9,182.35):
 assert old.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(275.35)-1,pcbnew.FromMM(y)))
 assert not old.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(275.35)+1,pcbnew.FromMM(y)))

nearest=[];physical_hits=[]
for p in before.GetPads():
 if not p.GetNumber()or p.GetNetname()!='/IO_3V3':continue
 b=p.GetBoundingBox();xy=[pcbnew.ToMM(v)for v in(b.GetX(),b.GetY(),b.GetRight(),b.GetBottom())]
 nearest.append(dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),land_bbox_mm=xy,distance_center_mm=((pcbnew.ToMM(p.GetPosition().x)-274.3)**2+(pcbnew.ToMM(p.GetPosition().y)-179.625)**2)**.5))
 for layer in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu):
  if p.IsOnLayer(layer)and allowed.Collide(p.GetEffectiveShape(layer)):
   physical_hits.append(dict(kind='actual numbered IO3 pad',ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),layer=before.GetLayerName(layer)))
for t in before.GetTracks():
 if t.GetNetname()=='/IO_3V3'and t.IsOnLayer(pcbnew.In2_Cu)and allowed.Collide(t.GetEffectiveShape(pcbnew.In2_Cu)):
  physical_hits.append(dict(kind='actual IO3 In2 conductor/barrel',uuid=t.m_Uuid.AsString()))
assert not physical_hits,'The proposed unloaded pour cut actually reaches IO3 Source/receiving metal'

def ownership(a,b,label):
 current=list(split_polygons(b));rows=[]
 for i,p in enumerate(split_polygons(a)):
  owners=[j for j,q in enumerate(current)if guard.intersection(p,q).OutlineCount()]
  assert len(owners)==1,label+' loses/splits an old actual component'
  rows.append(dict(before_piece=i,after_piece=owners[0]))
 return rows
topology=ownership(old,now,'Full IO3')
ob=guard.duplicate(old);nb=guard.duplicate(now)
for p in(ob,nb):p.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
core=ownership(ob,nb,'502um eroded IO3 core')
opened=guard.duplicate(ob);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(old)
opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
narrow=guard.subtract(old,opened)
assert not guard.subtract(guard.subtract(narrow,precision),allowed).OutlineCount(),'An actual old thin feature outside the exact local physical disposition changed'

# Rerun the frozen rail-specific Source44/feed22/CORE checks. Only the one
# separately reviewed physical DFM disposition has a geometry-specific proof.
def checked_geometry(a,b):
 assert guard.symmetric_equal(a,old)and guard.symmetric_equal(b,now)
 return dict(passed=True,literal_geometry_proved_above=True,unbuffered_components=topology,actual502um_core_components=core,precisely_bounded_DFM_disposition_only=True,no_area_threshold=True,ampacity_qualified=False)
original=guard.backbone
try:
 guard.backbone=checked_geometry
 fresh=guard.review(before,after)
finally:guard.backbone=original
assert fresh['passed']and len(fresh['actual44_receiver_endpoints'])==44and len(fresh['actual22_receiving_annuli'])==22
write(OUT/'fresh-frozen-rail-Source44-feed22-proof.json',fresh)
write(OUT/'literal-physical-boundary.json',dict(rule_rectangle_mm=rect,two_actual_native_width_corner_envelopes_mm=corner_boxes,actual_half_minimum_width_mm=.125,actual_KiCad_postKnockout_prune_radius_mm=.124,only_copper_zone_intersection=hit,actual_removed_native_contours=removed.Format(False),actual_added_native_contours=added.Format(False),outside_scope_losses_beyond_original1um_precision=[],nearest_IO3_Source_lands=sorted(nearest,key=lambda r:r['distance_center_mm'])[:12],no_IO3_pad_or_barrel_or_trace_affected=not physical_hits,full_native_component_mapping=topology,actual502um_core_component_mapping=core))
for path,h in frozen.items():assert sha(path)==h,'Input drift'
write(OUT/'receipt.json',dict(passed=True,input_sha256=frozen,before_board=str(BASE),before_board_sha256=sha(BASE),board=str(CAND),board_sha256=sha(CAND),exact_pour_only_In2_DFM_rule_uuid=list(new)[0],no_old_copper_land_pad_pose_or_zone_definition_change=True,mechanical_boundary_is_known_literal_native_minimum_width_corner_not_generic_tolerance=True,IO3_Source_receiver_metal_not_intersected=True,CORE1V2_fill_exact=True,actual44_Source_endpoints_and22_receiving_annuli_passed=True,unbuffered_component_count=len(topology),actual502um_core_count=len(core),all_old_definite_thin_features_outside_literal_region_passed=True,relative_power_geometry_only=True,full_current_drop_thermal_or_fault_capacity_qualified=False,future_combined_board_retained_circuit_checks_required=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(CAND),receipt_sha256=sha(OUT/'receipt.json'),full_components=len(topology),core_components=len(core))))
