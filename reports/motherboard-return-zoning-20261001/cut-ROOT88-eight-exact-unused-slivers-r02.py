"""Bounded actual combined-outline DFM correction, never an area exemption."""
import sys,json,shutil,hashlib
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_zone_motherboard_returns import rectangle,split_polygons
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
base=Path('reports/motherboard-pcb-integration-20261001/source26-motor-bank-A-merged-native-r88/motherboard-bounded-merged-candidate.kicad_pcb')
mp=Path('reports/motherboard-domains-20261001/source26-bank-A-r88-independent-r01/domain-map.json')
manifest=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r141/actual-control-segment-manifest.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-ROOT88-eight-actual-DFM-slivers-r02')
if out.exists():raise ValueError('Fresh immutable output required')
out.mkdir();(out/'inputs').mkdir();frozen={str(p):sha(p)for p in(base,mp,manifest,Path(__file__),Path(__file__).with_name('check_exact_endpoint_antipad_union_r01.py'),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
for p in(base,mp,manifest,Path(__file__)):shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
rows=json.loads(manifest.read_text())['rows'];check=ExactEndpointUnionCheck(b,{r['net']:decl for r in rows});actual={t.m_Uuid.AsString():t for t in b.GetTracks()}
positive=[check.segment(actual[r['actual_copper_UUIDs'][0]],decl)for r in rows]
if len(positive)!=82:raise ValueError('Exact82 controls changed')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets)
write(out/'before-invariants.json',dict(Cu_identity_sha256=digest(oldcu),pad_identity_sha256=digest(oldpads),before_SOURCE_pad_clusters=before,actual82_control_proofs=positive,board_sha256=sha(base)))
targets={'8b732c21-51eb-4770-9ca0-6e82f46f9942':pcbnew.In1_Cu,'49d29d14-d119-4522-928d-87c5177e48d0':pcbnew.In4_Cu};zones={z.m_Uuid.AsString():z for z in b.Zones()};cuts={};proof=[]
for uid,layer in targets.items():
 z=zones[uid]
 if z.GetNetname()!='/LOGIC_GND'or not z.IsOnLayer(layer):raise ValueError('Exact reviewed native zone differs')
 hits=[]
 for index,piece in enumerate(split_polygons(z.GetFilledPolysList(layer))):
  # Identification of the eight frozen literal triangles, not an eligibility
  # threshold: all copper/source/reference proofs remain mandatory below.
  if exact_twice_area(piece)!=41160:continue
  box=piece.BBox();bounds_nm=[box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()];bounds=[pcbnew.ToMM(v)for v in bounds_nm]
  if not(250<bounds[0]<bounds[2]<283 and 176<bounds[1]<bounds[3]<236):raise ValueError('Reviewed eight-piece geometry identity differs')
  if piece.OutlineCount()!=1 or piece.COutline(0).PointCount()!=3 or piece.HoleCount(0):raise ValueError('Exact reviewed literal triangle topology differs')
  cut=rectangle(bounds,.01);pads=[p.m_Uuid.AsString()for p in b.GetPads()if p.IsOnLayer(layer)and cut.Collide(p.GetEffectiveShape(layer))];cu=[t.m_Uuid.AsString()for t in b.GetTracks()if t.IsOnLayer(layer)and cut.Collide(t.GetEffectiveShape(layer))]
  if pads or cu:raise ValueError('Unused sliver collar touches native Source pad or conductor')
  cuts.setdefault(uid,pcbnew.SHAPE_POLY_SET()).BooleanAdd(cut)
  hits.append(dict(zone_uuid=uid,net='/LOGIC_GND',layer=b.GetLayerName(layer),literal_piece=index,exact_twice_area_nm2=41160,exact_vertices_nm=[[piece.COutline(0).CPoint(i).x,piece.COutline(0).CPoint(i).y]for i in range(3)],bounds_nm=bounds_nm,bounds_mm=bounds,cut_bounds_mm=[bounds[0]-.01,bounds[1]-.01,bounds[2]+.01,bounds[3]+.01],actual_Source_pad_or_conductor_intersections=[]))
 if len(hits)!=4:raise ValueError('Each exact reviewed zone must have four frozen literal triangles')
 proof.extend(hits)
for uid,cut in cuts.items():
 z=zones[uid];p=pcbnew.SHAPE_POLY_SET();p.Append(z.Outline());p.BooleanSubtract(cut)
 if p.OutlineCount()!=1:raise ValueError('Bounded unused cut would split a real zone outline')
 z.Outline().RemoveAllContours();z.Outline().Append(p)
dest=out/'motherboard-eight-unused-slivers-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];rawzones=[objects(t,'zone')for t in trees];ledger=[]
for uid in cuts:
 old,new=[zone_definition(t[uid])for t in rawzones];ledger.append(dict(uuid=uid,before_definition_sha256=hashlib.sha256(old.encode()).hexdigest(),after_definition_sha256=hashlib.sha256(new.encode()).hexdigest(),electrical_outline_correction_reason='Remove only four exactly frozen unconnected native literal DFM triangles in this one own-net/layer zone via their explicitly reviewed10micrometre boundary collars; actual Source pads/conductors, all82 signal/annulus obligations, all inherited source clusters and current old101 loops must remain proven. No minimum-area deletion or checker exemption.'))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=[],reviewed_existing_zone_outline_deltas=ledger,reviewed_scope_reason='Exact eight physically unused literal native triangles removed from two actual ROOT88 zone outlines; all newer AO1/C19042/ADC/IO3 composition remains unchanged outside these explicit local outline cuts. No Cu/pose/pad/source changes. Complete native combined proofs required.'))
write(out/'generation.json',dict(input_sha256=frozen,exact_eight_literal_pieces=proof,board_sha256=sha(dest),before_board_sha256=sha(base),only_two_zone_outline_changes=True,no_area_exemption=True,native_refill_and_full_validation_pending=True))
if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen generation input changed')
print('Eight actual unused literal cuts emitted; native refill and full proofs required',flush=True)
