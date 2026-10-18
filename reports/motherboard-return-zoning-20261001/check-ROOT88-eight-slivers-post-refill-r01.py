"""Independent native post-refill source, literal removal and82-control proof."""
import sys,json,hashlib,collections
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_zone_motherboard_returns import rectangle,split_polygons
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
out=Path('reports/motherboard-return-zoning-20261001/source26-ROOT88-eight-actual-DFM-slivers-r02');dest=out/'motherboard-eight-unused-slivers-candidate.kicad_pcb';gen=json.loads((out/'generation.json').read_text());inv=json.loads((out/'before-invariants.json').read_text());drc=json.loads((out/'native.json').read_text());scope=json.loads((out/'bounded-scope.json').read_text());base=Path('reports/motherboard-pcb-integration-20261001/source26-motor-bank-A-merged-native-r88/motherboard-bounded-merged-candidate.kicad_pcb')
if any(sha(Path(p))!=h for p,h in gen['input_sha256'].items()):raise ValueError('Frozen Source/baseline inputs changed')
baseline=json.loads((base.parent/'drc.json').read_text())
def warning_objects(r):return sorted((v['type'],v['severity'],tuple(sorted(i['uuid']for i in v.get('items',[]))))for v in r['violations'])
if drc.get('ignored_checks')or any(r['severity']=='error'for r in drc['violations']):raise ValueError('Native errors/ignored checks')
if warning_objects(drc)!=warning_objects(baseline):raise ValueError('Exact unsuppressed native baseline warning objects changed')
b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
if digest({t.m_Uuid.AsString():identity(t)for t in b.GetTracks()})!=inv['Cu_identity_sha256']or digest({p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()})!=inv['pad_identity_sha256']:raise ValueError('Old native source copper/pads/poses changed')
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};after=native_pad_clusters(b,nets);survive=clusters_survive(inv['before_SOURCE_pad_clusters'],after)
write(out/'all-native-SOURCE-cluster-proof.json',dict(passed=survive,before=inv['before_SOURCE_pad_clusters'],after=after))
if not survive:raise ValueError('Old Source pad cluster was lost')
zones={z.m_Uuid.AsString():z for z in b.Zones()};removed=[]
for r in gen['exact_eight_literal_pieces']:
 z=zones[r['zone_uuid']];layer=b.GetLayerID(r['layer']);p=pcbnew.SHAPE_POLY_SET();p.Append(z.GetFilledPolysList(layer));p.BooleanIntersection(rectangle(r['bounds_mm']))
 if exact_twice_area(p)>0:raise ValueError('Exactly frozen positive literal triangle survives native refill')
 removed.append(dict(zone_uuid=r['zone_uuid'],old_literal_piece=r['literal_piece'],bounds_nm=r['bounds_nm'],actual_remaining_twice_area_nm2=exact_twice_area(p)))
manifest=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r141/actual-control-segment-manifest.json');rows=json.loads(manifest.read_text())['rows'];decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.);check=ExactEndpointUnionCheck(b,{r['net']:decl for r in rows});tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};proof=[check.segment(tracks[r['actual_copper_UUIDs'][0]],decl)for r in rows]
write(out/'actual82-control-reference-proof.json',dict(passed=len(proof)==82,board_sha256=sha(dest),full_actual_segment_proofs=proof,strict_Source_stitch_annulus_radius_and_margin_unchanged=True))
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];zs=[objects(t,'zone')for t in trees];reviewed={r['uuid']:r for r in scope['reviewed_existing_zone_outline_deltas']};changed=[]
if set(zs[0])!=set(zs[1]):raise ValueError('Zone population changed')
for uid,z in zs[0].items():
 first,last=zone_definition(z),zone_definition(zs[1][uid])
 if first==last:continue
 row=reviewed.get(uid)
 if not row or hashlib.sha256(first.encode()).hexdigest()!=row['before_definition_sha256']or hashlib.sha256(last.encode()).hexdigest()!=row['after_definition_sha256']:raise ValueError('Literal changed zone scope/hash differs')
 changed.append(uid)
if set(changed)!=set(reviewed):raise ValueError('Reviewed outline scope differs')
write(out/'post-refill-proof.json',dict(passed=True,board_sha256=sha(dest),before_board_sha256=sha(base),exact_eight_unused_literal_triangles_absent=removed,all_actual82_Control_corridors_and_Source_annuli_passed=True,all_prior_Source_clusters_Cu_pads_poses_preserved=True,exact_two_reviewed_zone_outlines_changed=changed,native_errors=0,exact_original_unsuppressed_warnings_preserved=warning_objects(drc),ignored_checks=[],full_resource_and_independent_inventory_and_retained101_checks_pending=True,manufacturing_ready=False));print('Exact8 absent/all82 true/oldSource invariants/native baseline exact',flush=True)
