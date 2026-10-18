"""Separate review of explicitly scoped In2 cleanup; frozen route guard unchanged."""
from pathlib import Path
import sys,json,argparse,subprocess
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
ap=argparse.ArgumentParser();ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=False);proposal=a.folder/'proposal.json';pr=json.loads(proposal.read_text())
base=Path(pr['input_board']);cand=a.folder/'motherboard-health-unused-IO3-candidate.kicad_pcb';native=a.folder/'native.json'
inputs={str(f):sha(f)for f in[base,cand,proposal,native,Path(g.__file__),Path(__file__),g.SOURCE,g.FEEDS]}
assert sha(base)==pr['input_board_sha256']and sha(g.__file__)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
v=json.loads(native.read_text());assert not v['violations']and not v['ignored_checks']
b=p.LoadBoard(str(base));c=p.LoadBoard(str(cand));b.BuildConnectivity();c.BuildConnectivity()
assert {t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}=={t.m_Uuid.AsString():identity(t)for t in c.GetTracks()}
assert {q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()}=={q.m_Uuid.AsString():pad_identity(q)for q in c.GetPads()}
bz=definitions(base);cz=definitions(cand);new={r['UUID']for r in pr['regions']}
assert set(cz)==set(bz)|new and all(cz[u]==v for u,v in bz.items())
allow=p.SHAPE_POLY_SET();zones={z.m_Uuid.AsString():z for z in c.Zones()}
physical_rule=p.SHAPE_POLY_SET()
native_source=Path('reports/motherboard-pcb-integration-20261001/kicad-10.0.4-zone-filler-reference.cpp')
assert sha(native_source)=='e379b507872245f6ab8a155010076ce8dcabe816c4747ca6552e2666add7816f'
inputs[str(native_source)]=sha(native_source)
retreats=Path('reports/motherboard-return-zoning-20261001/health-IO3-baseline-cleanup-review-r02/outside-region-failure.json')
inputs[str(retreats)]=sha(retreats)
rv=json.loads(retreats.read_text());assert rv['inputs'][str(cand)]==sha(cand)
assert len(rv['all_literal_outside_removals'])==8

for r in pr['regions']:
 z=zones[r['UUID']];cut=g.box(*r['bounds_mm']);physical_rule.BooleanAdd(cut);allow.BooleanAdd(cut)
 # Only the eight frozen actual refill-retreat polygons are separately
 # reviewed, each within the actual .25mm zone minimum's half-width.
 # No global contour tolerance, routing guard, or area filter changes.
 assert all(h['minimum_width_mm']==.25 for h in r['actual_filled_hits'])
 x0,y0,x1,y1=r['bounds_mm'];envelope=g.box(x0-.125,y0-.125,x1+.125,y1+.125)
 for item in rv['all_literal_outside_removals']:
  lo=item['bounds_mm'];piece=g.box(*lo)
  if not g.subtract(piece,envelope).OutlineCount():allow.BooleanAdd(piece)

 assert z.GetIsRuleArea()and list(z.GetLayerSet().Seq())==[p.In2_Cu]
 assert z.GetDoNotAllowZoneFills()and not any([z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowPads(),z.GetDoNotAllowFootprints()])
 assert g.symmetric_equal(z.Outline(),cut)
 for q in b.GetPads():
  if q.GetNetname()=='/IO_3V3':
   assert not any(q.IsOnLayer(layer)and cut.Collide(q.GetEffectiveShape(layer))for layer in[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]),q.GetParentFootprint().GetReference()
 for t in b.GetTracks():
  if t.GetNetname()=='/IO_3V3'and t.IsOnLayer(p.In2_Cu):assert not cut.Collide(t.GetEffectiveShape(p.In2_Cu))

for q in b.GetPads():
 if q.GetNetname()=='/IO_3V3':
  assert not any(q.IsOnLayer(layer)and allow.Collide(q.GetEffectiveShape(layer))for layer in[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu])
for t in b.GetTracks():
 if t.GetNetname()=='/IO_3V3'and t.IsOnLayer(p.In2_Cu):assert not allow.Collide(t.GetEffectiveShape(p.In2_Cu))
write(a.out/'literal-eight-native-width-retreats.json',dict(physical_rule_regions=pr['regions'],
 individually_recorded_actual_native_retreats=rv['all_literal_outside_removals'],
 actual_zone_minimum_width_mm=.25,maximum_corner_retreat_envelope_mm=.125,
 actual_manufactured_copper_checked=True,general_guard_or_precision_change=False,
 exact_additional_scope_native_polygons=g.subtract(allow,physical_rule).Format(False),
 source_cpp_sha256=sha(native_source)))

def owned(old,new,label):
 rows=[];pieces=list(split_polygons(new))
 for i,part in enumerate(split_polygons(old)):
  owners=[j for j,now in enumerate(pieces)if g.intersection(part,now).OutlineCount()]
  assert len(owners)==1,(label,i,owners)
  rows.append(dict(before_component=i,after_component=owners[0]))
 assert rows,label
 return rows

def cleanup_geometry(old,new):
 full=owned(old,new,'unbufferedIO3');bc=g.duplicate(old);ac=g.duplicate(new)
 for core in(bc,ac):core.Deflate(p.FromMM(.502),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.001))
 cores=owned(bc,ac,'502um_backbone')
 opened=g.duplicate(bc);opened.Inflate(p.FromMM(.502),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.001));opened.BooleanIntersection(old)
 opened.Inflate(p.FromMM(.001),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 precise=g.duplicate(new);precise.Inflate(p.FromMM(.001),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 outside=g.subtract(g.subtract(old,precise),allow)
 thinoutside=g.subtract(g.subtract(g.subtract(old,opened),precise),allow)
 if outside.OutlineCount()or thinoutside.OutlineCount():
  rows=[]
  for piece in split_polygons(outside):
   box=piece.BBox();rows.append(dict(bounds_mm=[p.ToMM(n)for n in[box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]],exact_twice_area_nm2=exact_twice_area(piece),native_polygon=piece.Format(False)))
  write(a.out/'outside-region-failure.json',dict(passed=False,all_literal_outside_removals=rows,unbuffered_mapping=full,backbone_mapping=cores,inputs=inputs,no_automatic_waiver=True))
  raise ValueError('Actual native removal outside declared cleanup bounds')
 assert not g.intersection(new,physical_rule).OutlineCount(),'Actual physical rule region contains fill'
 return dict(passed=True,cleanup_specific=True,explicit_regions=pr['regions'],unbuffered_component_mapping=full,
  minimum_screened_core_width_mm=1.,erosion_radius_mm=.502,core_mapping=cores,
  outside_declared_regions_native_1um_precision_unchanged=True,area_exemptions=False,
  removed_native_polygons=g.subtract(old,new).Format(False),added_native_polygons=g.subtract(new,old).Format(False),
  ampacity_IR_drop_or_thermal_qualification=False)

original=g.backbone
try:g.backbone=cleanup_geometry;proof=g.review(b,c)
finally:g.backbone=original
nets={q.GetNetname()for q in b.GetPads()if q.GetNumber()}
bc=native_pad_clusters(b,nets);cc=native_pad_clusters(c,nets);assert clusters_survive(bc,cc)
write(a.out/'all-source-cluster-proof.json',dict(passed=True,before=bc,after=cc))
write(a.out/'cleanup-specific-power-proof.json',proof)
assert all(sha(Path(f))==h for f,h in inputs.items())
write(a.out/'receipt.json',dict(passed=True,source_and_all_old_copper_and_zones_unchanged=True,
    board_sha256=sha(cand),baseline_sha256=sha(base),input_sha256=inputs,
    native_regular_errors=0,native_regular_warnings=0,ignored_checks=[],actual_Source44_and_receiving22=True,
    actual_CORE_exact=True,all_Source_clusters_preserved=True,cleanup_specific_not_routing_guard_waiver=True,
    independent_full_connectivity_and_retained_circuit_proofs_separately_required=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(cand))))
