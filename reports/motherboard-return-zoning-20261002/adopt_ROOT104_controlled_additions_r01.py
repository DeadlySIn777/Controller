"""Adopt only the exact bounded routed increment after a fresh complete regression run."""
from pathlib import Path
import json,hashlib
root=Path.cwd()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
d=root/'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01'
board=d/'motherboard-bounded-merged-candidate.kicad_pcb'
full=root/'reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/report.json'
drill=root/'reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json'
f=read(full);local=read(d/'local-positive-freeze-r01.json');inv=read(d/'independent-inventory-r01/review.json')
assert sha(board)==local['board_sha256']==f['started_from']['board_sha256']=='70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc'
assert f['mode']=='full' and f['source_hashes_unchanged'] and not f['source_changes'] and not f['status_counts'].get('FAIL',0)
stages={x['name']:x for x in f['stages']}
required=['host_suite','native_test_replay','native_source_validation','native_ERC','native_DRC','source_physical_connectivity','actual_cnc3_SPI_edge_plant','seeded_actual_SPI_faults','bounded_IOL1_diagnostic_acquisition','bounded_IS2_CAP3_profile','bounded_CNC3_stateful_replay']
assert all(stages[n]['status']=='PASS'for n in required),[(n,stages.get(n,{}).get('status'))for n in required]
assert local['passed'] and inv['source_net_checks_pass'] and inv['complete_source_population_pass']
assert inv['uncapped_unconnected_ratsnest_edges']==inv['independent_physical_cluster_missing_joins']==3508 and not inv['orphan_copper_items']
for p,h in local['input_sha256'].items():assert sha(root/Path(p))==h,p
assert read(d/'persisted-all48-cut-r01/receipt.json')['passed']
dr=read(drill);assert dr['board_sha256']==sha(board) and dr['intersection_count']==277 and dr['unique_intersecting_vias']==274 and dr['foreign_net_intersections']==0
assert f['started_from']['source_design_sha256']==sha(root/'hardware/motherboard/design.json')
files=[board,full,drill,Path(__file__),root/'hardware/motherboard/design.json',root/'hardware/motherboard/netlist.xml',d/'local-positive-freeze-r01.json',d/'persisted-all48-cut-r01/receipt.json']+[root/Path(p)for p in local['input_sha256']]
inputs={str(p):sha(p)for p in files}
record=dict(adopted=True,working_revision='ROOT104',electrical_source='Source26',board=str(board),board_sha256=sha(board),
 physical_footprints=inv['footprints'],track_via_count=inv['track_via_items'],zone_and_rulearea_count=1544,missing_joins=3508,
 fully_joined_multi_pad_nets=inv['fully_joined_multiple_pad_nets'],incomplete_multi_pad_nets=inv['incomplete_multiple_pad_nets'],orphan_copper_items=0,
 native_regular_DRC_errors=0,native_regular_DRC_warnings=0,ignored_checks=[],native_ERC_errors=0,native_ERC_unsuppressed_warnings=70,
 added_copper_items=48,prior_copper_pads_poses_zone_definitions_preserved=True,owned_bypass_loops=120,receiving_returns=245,Source_anchored_filled_resources=188,
 full_validation_report=str(full),full_validation_status_counts=f['status_counts'],full_validation_source_file_count=f['original_source_file_count'],
 input_sha256=inputs,preexisting_SMD_drill_intersections=277,preexisting_intersecting_drilled_vias=274,
 Freerouting_copper_adopted=False,Source27_adopted=False,manufacturing_ready=False,
 remaining_blockers=['3508 required physical joins; complete routing/power/returns remain unfinished.','Source27 reset/health corrections staged and not yet physically reconciled/adopted; full 20ms hardware inhibit remains unqualified.','277 same-net paste-land/drill overlaps involving274 vias require correction or exact qualified filled/capped process.','Complete CNC3/HAL/provider commissioning, FPGA resource fit/timing, machine profiles and analog-chain qualification remain open.','Complete mechanical/stackup/assembly verification, cost quotations, manufacturing exports and physical prototype testing remain open.'])
assert not(d/'adoption.json').exists()
(d/'adoption.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in record.items()if k not in ('input_sha256','remaining_blockers')}))
