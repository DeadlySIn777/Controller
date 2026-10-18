"""Adopt the exact locally proved health layout after its full disconnected run."""
from pathlib import Path
import json, hashlib, sys
import pcbnew
root=Path.cwd();sys.path.insert(0,str(root/'tools'))
from hardware_populate_motherboard_pcb import write
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
p=root/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31'
board=p/'motherboard-bounded-merged-candidate.kicad_pcb'
old=root/'reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06/adoption.json'
validation=root/'reports/pre-hardware-validation-20261001/full-health-stateful-plant-r07/report.json'
audit=root/'reports/motherboard-pcb-integration-20261001/health-r31-full-drill-SMD-audit-r01/receipt.json'
source=root/'hardware/motherboard/design.json';netlist=root/'hardware/motherboard/netlist.xml'
assert not(p/'adoption.json').exists()
assert sha(board)=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
assert sha(source)=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
assert sha(netlist)=='9f2c3c7b1e1b8f8cf108d0460dd0f709033f6ebdbf7f7a1b596abf1190eec633'
freeze=read(p/'final-scoped-freeze-r01.json')
assert freeze['passed'] and freeze['board_sha256']==sha(board)
evidence={str(f):sha(f)for f in(board,source,netlist,old,p/'final-scoped-freeze-r01.json',validation,audit,Path(__file__))}
for name,wanted in freeze['input_sha256'].items():
    f=root/Path(name);assert sha(f)==wanted,(name,'Frozen proof changed');evidence[str(f)]=wanted
peer=read(root/'reports/motherboard-power-entry-20261001/ROOT102-facing-health-peer-freeze-r482/receipt.json')
assert peer['passed'] and len(peer['persisted_native_refilled_fresh_reload_functional_cuts'])==8
inv=read(p/'final-independent-inventory-r01/review.json')
assert inv['source_net_checks_pass'] and inv['complete_source_population_pass'] and not inv['orphan_copper_items'] and not inv['errors']
assert inv['uncapped_unconnected_ratsnest_edges']==inv['independent_physical_cluster_missing_joins']==3521
assert inv['board_sha256']==sha(board)
proof=read(p/'final-current110-strict-proof-r01.json')
assert proof['passed'] and proof['retained_local_loops_checked']==110
assert len(proof['actual_receiving_return_anchor_reviews'])==225
clusters=read(p/'final-binding-r02/all-ROOT102-prior-native-Source-clusters.json')
assert clusters['passed'] and clusters['all_prior_native_Source_pad_clusters_survive'] and len(clusters['before'])==5899
v=read(validation);assert v['mode']=='full' and v['source_hashes_unchanged'] and not v['source_changes']
assert v['started_from']['board_sha256']==sha(board) and v['started_from']['source_design_sha256']==sha(source)
stages={s['name']:s for s in v['stages']}
assert not any(s['status']=='FAIL'for s in v['stages'])
for name in ['host_suite','native_test_replay','native_source_validation','native_ERC','native_DRC','source_physical_connectivity','input_integrity']:
    assert stages[name]['status']=='PASS',name
assert v['status_counts']=={'PASS':22,'BLOCKED':9,'NOT_RUN':1}
assert stages['complete_PCB_routing']['status']=='BLOCKED'
drc=read(p/'drc.json');assert not drc['violations'] and not drc['ignored_checks']
d=read(audit);assert d['board_sha256']==sha(board) and d['source_board_unchanged'] and d['foreign_net_intersections']==0
assert d['intersection_count']==277 and d['unique_intersecting_vias']==274
b=pcbnew.LoadBoard(str(board));assert len(b.GetFootprints())==2688 and len(b.GetTracks())==11759
merger=read(p/'receipt.json')
assert len(merger['exact_changed_footprints'])==6 and len(merger['exact_copper_delta'])==435
assert all(sha(Path(name))==value for name,value in evidence.items())
r=dict(passed=True,adopted=True,working_revision='ROOT103',scope='Exact health receiving/control correction after complete fresh disconnected regression. Full routing, source27 circuit corrections and loaded electrical qualification remain unfinished.',
 board=str(board),board_sha256=sha(board),exact_source_design_sha256=sha(source),exact_source_netlist_sha256=sha(netlist),baseline_adoption=str(old),baseline_board_sha256=read(old)['board_sha256'],evidence_sha256=evidence,
 physical_footprints=len(b.GetFootprints()),track_via_count=len(b.GetTracks()),zone_count=len(b.Zones()),missing_joins=3521,
 fully_joined_multiple_pad_nets=inv['fully_joined_multiple_pad_nets'],incomplete_multiple_pad_nets=inv['incomplete_multiple_pad_nets'],native_errors=0,native_warnings=0,ignored_checks=[],orphan_copper_count=0,
 retained_bypass_loops=110,receiving_return_endpoints=225,actual_Source_anchored_reference_resources=188,all5899_ROOT102_Source_groups_preserved=True,relative_rail_geometry_preserved=True,
 changed_poses=merger['exact_changed_footprints'],exact_copper_delta=merger['exact_copper_delta'],full_validation_report=str(validation),full_validation_status=v['status'],full_validation_status_counts=v['status_counts'],
 preexisting_SMD_drill_intersections=277,preexisting_intersecting_drilled_vias=274,SMD_assembly_qualification_complete=False,
 remaining_engineering=['3521 required joins remain unrouted, including remote MC_RAILS_OK_5V producer',
 'Source27 slow-input/reset/supervisor corrections are staged and not yet adopted or fully routed',
 '274 drilled vias intersect277 same-net paste SMD lands; correct layout or qualify exact filled/capped fabrication and assembly. Audit excludes tangency and registration margin; tenting does not close it.',
 'Full rail ampacity/drop/fault/thermal and all local returns remain unqualified',
 'Actual CNC3 C driver cannot discover this RTL: CAP3 READ_PAGE remains unimplemented; complete HAL/IOL1/providers and vendor fit/timing remain unfinished',
 'Complete20ms inhibit, partial-power, reset and missing-module chain requires circuit and physical qualification',
 'Full footprint/mating/mechanical/stackup/cost review and fabrication release remain unfinished'],
 global_power_or_reference_qualification=False,physical_qualification=False,manufacturing_ready=False)
write(p/'adoption.json',r)
write(p/'baseline-disposition.json',dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=[],ignored_checks=[],remaining_required_joins=3521))
print(json.dumps({k:r[k]for k in ['adopted','working_revision','missing_joins','track_via_count','zone_count','retained_bypass_loops','manufacturing_ready']}))
