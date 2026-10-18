"""Freeze the literal full donor delta; no PCB edits or global readiness claim."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_map_motherboard_domains import sha,write
from hardware_build_assembly import parse,dump,children
from hardware_merge_bounded_pcb_delta import objects,reference,zone_definition,without_generated_fills
before=Path('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb')
donor=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r138-logic-reference-collars-r06/motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb')
motor=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r141/bounded-scope.json')
collar=donor.parent/'bounded-scope.json'
proof=Path('reports/motherboard-return-zoning-20261001/motor-exact-antipad-union-native-controls-r04/review.json')
oldreceipt=donor.parent/'receipt.json'
out=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-consolidated-reference-donor-r07')
if out.exists():raise ValueError('Immutable output already exists')
out.mkdir();frozen={str(p):sha(p)for p in(before,donor,motor,collar,proof,oldreceipt,Path(__file__))}
review=json.loads(proof.read_text());prior=json.loads(oldreceipt.read_text());m=json.loads(motor.read_text());c=json.loads(collar.read_text())
if not review['passed']or len(review['exact82_actual_control_segment_proofs'])!=82 or len(review['actual_native_negative_controls'])!=6 or review['board_sha256']!=sha(donor):raise ValueError('Exact82 plus6 physical proof is not bound to donor')
trees=[parse(without_generated_fills(p.read_text()))for p in(before,donor)]
fps=[{reference(f):f for f in children(t,'footprint')}for t in trees]
if set(fps[0])!=set(fps[1]):raise ValueError('Full population changed')
changedrefs=sorted(r for r in fps[0]if dump(fps[0][r])!=dump(fps[1][r]))
if changedrefs!=sorted(m['reviewed_footprint_references']):raise ValueError('Exact23 physical pose scope differs')
cu=[{**objects(t,'segment'),**objects(t,'via'),**objects(t,'arc')}for t in trees]
added=sorted(set(cu[1])-set(cu[0]));retired=sorted(set(cu[0])-set(cu[1]));modified=sorted(u for u in cu[0].keys()&cu[1].keys()if dump(cu[0][u])!=dump(cu[1][u]))
if set(added+retired+modified)!=set(m['reviewed_copper_delta_UUIDs'])or len(added)!=331 or len(retired)!=70 or modified:raise ValueError('Exact source-preserving Cu delta differs')
zones=[objects(t,'zone')for t in trees];newzones=sorted(set(zones[1])-set(zones[0]))
if set(zones[0])-set(zones[1])or any(zone_definition(z)!=zone_definition(zones[1][u])for u,z in zones[0].items())or newzones!=sorted(c['reviewed_added_zone_UUIDs']):raise ValueError('Existing zones changed or exact nine new collars differ')
scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=changedrefs,reviewed_copper_delta_UUIDs=sorted(added+retired),reviewed_added_zone_UUIDs=newzones,reviewed_scope_reason='Literal full Bank A transaction:23 reviewed original component poses,331 exact new/70 retired private copper objects,9 clipped LOGIC In1/In4 control-reference zones.82 actual signal segments and5 real source-backed transfer witnesses pass the exact equivalent endpoint-antipad algebra with6 persisted physical negatives.8 actual unused native slivers remain a separately required bounded DFM cut on the current merged outlines.LED rows are low-current POWER only; source27 electrical substitutions/startup/all-temperature/current qualifications remain separate.')
write(out/'bounded-scope.json',scope);write(out/'literal-delta-ledger.json',dict(exact_footprint_pose_references=changedrefs,exact_added_Cu_UUIDs=added,exact_retired_Cu_UUIDs=retired,exact_modified_Cu_UUIDs=modified,exact_added_zone_UUIDs=newzones,existing_zone_definitions_preserved=True))
receipt=dict(passed=True,scope='Native physical donor/82 control reference proofs only; required combined current-board and8 literal DFM cuts remain open',input_sha256=frozen,before_board=str(before),before_board_sha256=sha(before),donor_board=str(donor),board_sha256=sha(donor),native_errors=prior['native_errors'],native_warning_count=5,ignored_checks=[],native_uncapped_joins=3613,independent_SOURCE_missing_joins=3613,orphan_copper=[],all_prior_Source_clusters_pads_Cu_poses_oldzones_preserved_except_exact_bounded23pose_331add_70retire=True,actual_control_segments_passed=82,actual_source_ground_transfers=5,persisted_native_negative_controls_passed=6,existing_checker_frozen_bytes_unchanged=True,exact_equivalent_endpoint_union_checker=str(Path(__file__).with_name('check_exact_endpoint_antipad_union_r01.py')),checker_sha256=sha(Path(__file__).with_name('check_exact_endpoint_antipad_union_r01.py')),control_review=str(proof),control_review_sha256=sha(proof),remaining_unused_literal_native_slivers=8,global_reference_resource_passed=False,combined_current_board_proof_required=True,source27_adopted=False,manufacturing_ready=False)
if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen consolidation input changed')
write(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
