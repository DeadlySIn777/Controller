"""Adopt a bounded, already native-qualified routing improvement; not release."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
root=Path.cwd()
p=root/'reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06'
board=p/'motherboard-two-same-side-bypass-candidate.kicad_pcb'
old=root/'reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/adoption.json'
validation=root/'reports/pre-hardware-validation-20261001/full-two-cap-r05/report.json'
audit=root/'reports/motherboard-pcb-integration-20261001/two-cap-full-drill-SMD-audit-r01/receipt.json'
source=root/'hardware/motherboard/design.json';netlist=root/'hardware/motherboard/netlist.xml'
assert not(p/'adoption.json').exists()
assert sha(board)=='769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5'
assert sha(source)=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
assert sha(netlist)=='9f2c3c7b1e1b8f8cf108d0460dd0f709033f6ebdbf7f7a1b596abf1190eec633'
read=lambda f:json.loads(f.read_text())
freeze=read(p/'freeze-receipt.json');assert freeze['passed']and freeze['board_sha256']==sha(board)
assert freeze['baseline_sha256']==read(old)['board_sha256']
evidence={str(f):sha(f)for f in(board,source,netlist,old,p/'freeze-receipt.json',validation,audit,Path(__file__))}
for name,wanted in freeze['evidence_sha256'].items():
    f=p/name;assert sha(f)==wanted,(name,'Frozen native proof changed');evidence[str(f)]=wanted
for row in freeze['six_refilled_and_freshly_reloaded_actual_cut_negatives']:
    f=p/row['review'];assert sha(f)==row['sha256'];evidence[str(f)]=sha(f)
inv=read(p/'independent-connectivity/review.json')
assert inv['source_net_checks_pass']and inv['complete_source_population_pass']and not inv['orphan_copper_items']and not inv['errors']
assert inv['uncapped_unconnected_ratsnest_edges']==inv['independent_physical_cluster_missing_joins']==3524
assert inv['board_sha256']==sha(board)
proof=read(p/'combined108-proof.json');assert proof['passed']and proof['retained_local_loops_checked']==108
assert len(proof['actual_receiving_return_anchor_reviews'])==221
v=read(validation);assert v['mode']=='full'and v['source_hashes_unchanged']and not v['source_changes']
assert v['started_from']['board_sha256']==sha(board)and v['started_from']['source_design_sha256']==sha(source)
stages={s['name']:s for s in v['stages']}
assert not any(s['status']=='FAIL'for s in v['stages'])
for name in ['host_suite','native_test_replay','native_source_validation','native_ERC','native_DRC','source_physical_connectivity','input_integrity']:
    assert stages[name]['status']=='PASS',name
assert stages['complete_PCB_routing']['status']=='BLOCKED'
drc=read(p/'drc.json');assert not drc['violations']and not drc['ignored_checks']
d=read(audit);assert d['board_sha256']==sha(board)and d['source_board_unchanged']and d['foreign_net_intersections']==0
assert d['intersection_count']==279 and d['unique_intersecting_vias']==275
b=pcbnew.LoadBoard(str(board));assert len(b.GetFootprints())==2688 and len(b.GetTracks())==11641
assert all(sha(Path(name))==value for name,value in evidence.items())
r=dict(passed=True,adopted=True,working_revision='ROOT102',scope='Two existing capacitor poses and six actual local conductors adopted after full fresh disconnected regression on this exact board. Inherited unresolved routing/electrical/assembly work remains explicit.',
    board=str(board),board_sha256=sha(board),exact_source_design_sha256=sha(source),exact_source_netlist_sha256=sha(netlist),baseline_adoption=str(old),baseline_board_sha256=read(old)['board_sha256'],evidence_sha256=evidence,
    physical_footprints=len(b.GetFootprints()),track_via_count=len(b.GetTracks()),zone_count=len(b.Zones()),missing_joins=3524,
    fully_joined_multiple_pad_nets=inv['fully_joined_multiple_pad_nets'],incomplete_multiple_pad_nets=inv['incomplete_multiple_pad_nets'],native_errors=0,native_warnings=0,ignored_checks=[],orphan_copper_count=0,
    retained_bypass_loops=108,receiving_return_endpoints=221,actual_Source_anchored_reference_resources=188,all5903_ROOT101_Source_groups_preserved=True,relative_rail_geometry_preserved=True,
    changed_poses=freeze['exact_changed_poses'],exact_added_copper_UUIDs=freeze['exact_added_copper_UUIDs'],full_validation_report=str(validation),full_validation_status=v['status'],
    preexisting_SMD_drill_intersections=d['intersection_count'],preexisting_intersecting_drilled_vias=d['unique_intersecting_vias'],SMD_assembly_qualification_complete=False,
    remaining_engineering=['3524 required joins remain unrouted','Health U20/U26 controls/receiving loops still being repaired in separate unadopted candidates',
        'Source27 slow-input/reset/supervisor correction is staged and not adopted/routed','275 inherited drilled vias intersect279 same-net paste SMD lands; each needs layout correction or exact qualified filled/capped fabrication and assembly process. Tenting is not a disposition.',
        'Full rail ampacity/drop/fault/thermal and all local return paths remain unqualified','Stateful CNC3/complete twelve-joint HAL machine integration and vendor fit/timing remain unfinished',
        'Full20ms inhibit, partial-power, reset and missing-module chain still needs exact circuit and physical qualification','Full footprint/mating/mechanical/stackup/cost review and fabrication release remain unfinished'],
    global_power_or_reference_qualification=False,physical_qualification=False,manufacturing_ready=False)
write(p/'adoption.json',r)
write(p/'baseline-disposition.json',dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=[],ignored_checks=[],remaining_required_joins=3524))
print(json.dumps({k:r[k]for k in ['adopted','working_revision','missing_joins','retained_bypass_loops','manufacturing_ready']}),flush=True)
