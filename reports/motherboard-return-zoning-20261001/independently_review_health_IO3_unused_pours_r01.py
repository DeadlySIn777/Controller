"""Independent literal unused-pour review: exact eight native corner contours, no area exemption."""
from pathlib import Path
import sys,json,re
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-ordinary-routing-20261001')]
import pcbnew as p
import check_io3_backbone_preservation_r07 as g
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_zone_motherboard_returns import split_polygons
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
R=Path('reports/motherboard-return-zoning-20261001')
O=R/'health-IO3-baseline-cleanup-independent-r01';assert not O.exists();O.mkdir()
D=R/'health-IO3-baseline-cleanup-r02';P=D/'proposal.json';pr=json.loads(P.read_text())
B=Path(pr['input_board']);C=D/'motherboard-health-unused-IO3-candidate.kicad_pcb'
F=R/'health-IO3-baseline-cleanup-review-r02/outside-region-failure.json'
V=R/'health-IO3-baseline-cleanup-review-r03/receipt.json';rv=json.loads(F.read_text());verified=json.loads(V.read_text())
assert verified['passed'] and sha(C)=='1719e13d17336716b59078007447706f692abb9d0a6a9efb9bc9a23454b7e365'
assert sha(B)=='3990f4918ff9b3c672e28eaeb098806093ac9b6dae2f2fe84dfefd972ea5731b'
assert sha(g.__file__)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
inputs={str(q):sha(q)for q in(B,C,P,F,V,D/'native.json',Path(__file__),Path(g.__file__),g.SOURCE,g.FEEDS)}
assert not json.loads((D/'native.json').read_text())['violations']
b=p.LoadBoard(str(B));c=p.LoadBoard(str(C));b.BuildConnectivity();c.BuildConnectivity()
assert {t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}=={t.m_Uuid.AsString():identity(t)for t in c.GetTracks()}
assert {q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()}=={q.m_Uuid.AsString():pad_identity(q)for q in c.GetPads()}
bz=definitions(B);cz=definitions(C);new={r['UUID']for r in pr['regions']};assert set(cz)==set(bz)|new and all(cz[u]==row for u,row in bz.items())
zones={z.m_Uuid.AsString():z for z in c.Zones()};physical=p.SHAPE_POLY_SET();allow=p.SHAPE_POLY_SET();envs=[]
for r in pr['regions']:
 z=zones[r['UUID']];cut=g.box(*r['bounds_mm']);physical.BooleanAdd(cut);allow.BooleanAdd(cut)
 assert z.GetIsRuleArea() and list(z.GetLayerSet().Seq())==[p.In2_Cu]
 assert z.GetDoNotAllowZoneFills() and not any([z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowPads(),z.GetDoNotAllowFootprints()])
 assert g.symmetric_equal(z.Outline(),cut) and r['IO3_metal_contacts']==[]
 assert r['actual_filled_hits'] and all(h['net']=='/IO_3V3'and h['minimum_width_mm']==.25 for h in r['actual_filled_hits'])
 x0,y0,x1,y1=r['bounds_mm'];envs.append(g.box(x0-.125,y0-.125,x1+.125,y1+.125))
assert len(rv['all_literal_outside_removals'])==8
literal=[]
for row in rv['all_literal_outside_removals']:
 assert 'poly.AddHole' not in row['native_polygon']
 points=[tuple(map(int,q))for q in re.findall(r'VECTOR2I\(\s*(-?\d+),\s*(-?\d+)\)',row['native_polygon'])]
 contour=p.SHAPE_POLY_SET();contour.NewOutline()
 for x,y in points:contour.Append(x,y)
 assert exact_twice_area(contour)==row['exact_twice_area_nm2']
 owners=[i for i,e in enumerate(envs)if not g.subtract(contour,e).OutlineCount()]
 assert len(owners)==1 and not g.intersection(contour,physical).OutlineCount()
 allow.BooleanAdd(contour);literal.append(dict(row,physical_rule_index=owners[0],independent_exact_contour=True))
allow.Simplify();physical.Simplify()
for q in b.GetPads():
 if q.GetNetname()=='/IO_3V3':assert not any(q.IsOnLayer(layer)and allow.Collide(q.GetEffectiveShape(layer))for layer in[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]),(q.GetParentFootprint().GetReference(),q.GetNumber())
for t in b.GetTracks():
 if t.GetNetname()=='/IO_3V3'and t.IsOnLayer(p.In2_Cu):assert not allow.Collide(t.GetEffectiveShape(p.In2_Cu)),t.m_Uuid.AsString()
def owners(old,now,label):
 pieces=list(split_polygons(now));rows=[]
 for i,part in enumerate(split_polygons(old)):
  hits=[j for j,q in enumerate(pieces)if g.intersection(part,q).OutlineCount()]
  assert len(hits)==1,(label,i,hits);rows.append(dict(before_component=i,after_component=hits[0]))
 assert rows
 return rows
def literal_cleanup(old,now):
 full=owners(old,now,'actual full IO3');bc=g.duplicate(old);ac=g.duplicate(now)
 for core in(bc,ac):core.Deflate(p.FromMM(.502),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.001))
 backbone=owners(bc,ac,'actual502umcores')
 precision=g.duplicate(now);precision.Inflate(p.FromMM(.001),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 outside=g.subtract(g.subtract(old,precision),allow)
 if outside.OutlineCount():write(O/'literal-outside-failure.json',dict(native_polygon=outside.Format(False)));raise ValueError('Physical removal beyond exact declared rules/eight literal native-width corner contours')
 assert not g.intersection(now,physical).OutlineCount()
 return dict(passed=True,actual_unbuffered_components=full,actual502um_core_components=backbone,exact_eight_corner_contours=literal,exact_physical_rules=pr['regions'],native_boundary_comparison_um=1.,no_area_exemption=True,no_global_route_guard_change=True)
original=g.backbone
try:g.backbone=literal_cleanup;proof=g.review(b,c)
finally:g.backbone=original
nets={q.GetNetname()for q in b.GetPads()if q.GetNumber()};bc=native_pad_clusters(b,nets);cc=native_pad_clusters(c,nets);assert clusters_survive(bc,cc)
write(O/'all-Source-clusters.json',dict(passed=True,before=bc,after=cc));write(O/'literal-cleanup-power-proof.json',proof)
assert all(sha(Path(f))==h for f,h in inputs.items())
write(O/'receipt.json',dict(passed=True,input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),board=str(C),board_sha256=sha(C),only_three_In2_pour_rule_areas_added=True,all_old_Cu_lands_pads_Source_clusters_zones_preserved=True,actual_Source44_receiving22_CORE_backbone_pass=True,exact_eight_native_width_corner_contours_checked=True,maximum_native_minimum_width_corner_region_mm=.125,global_guard_unchanged=True,full_current_capacity_IR_drop_thermal_qualified=False,combined_current_circuit_and_power_reproof_required=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(C))),flush=True)
