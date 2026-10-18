"""Adopt only the fully reconciled ROOT101 routing WIP, never a fab release."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
root=Path('reports/motherboard-pcb-integration-20261001')
p=root/'source26-BankA-health-U25-C19033-merged-trial-r101'
board=p/'motherboard-bounded-merged-candidate.kicad_pcb'
assert sha(board)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
assert not (p/'adoption.json').exists()
source=Path('hardware/motherboard/design.json');netlist=Path('hardware/motherboard/netlist.xml')
assert sha(source)=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
baseline_adoption=root/'source26-seven-path-larger-IO3-cleanup-trial-r87/adoption.json'
assert sha(baseline_adoption)=='7e9d995b9bfce00c906a705d82837ea1aa3450a7752f8bb1e7a4630024e26b3f'
assert sha(netlist)==json.loads(baseline_adoption.read_text())['exact_source_netlist_sha256']
frozen={str(x.resolve()):sha(x)for x in(board,source,netlist,Path(__file__),board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'))}
read=lambda x:json.loads(x.read_text())
def proof(path,current=False):
 d=read(path);assert d['passed'],str(path)
 if current:assert d['board_sha256']==sha(board)
 frozen[str(path.resolve())]=sha(path)
 # Each proof's own frozen source/dependency inputs must still be exact.
 for field in ('input_sha256','frozen_proof_sha256'):
  for k,h in d.get(field,{}).items():
   q=Path(k);assert q.exists() and sha(q)==h,(path,k,'Frozen input changed')
   frozen[str(q.resolve())]=h
 return d
names=['combined-bypass-proof.json','combined-ordinary-proof/review.json','combined-critical-proof/review.json','combined-AO1-verification/review.json','combined-C19042-proof.json','combined-C14804-proof.json','literal-reference-resources.json','retained-FPGA38-rule-proof.json','retained-MISO-and-seven-proof/review.json','current82-motor-reference-proof.json','current-four-pair-proof/review.json','current-retained-reference-bridges.json','current-retained-baseline-proof.json','current-full-delta-power-proof.json']
checks={name:proof(p/name,True)for name in names}
bypass=checks['combined-bypass-proof.json'];assert bypass['retained_local_loops_checked']==106 and len(bypass['actual_receiving_return_anchor_reviews'])==217
resource=checks['literal-reference-resources.json'];assert resource['filled_component_count']==188 and not resource['unanchored_components'] and not resource['derived_nonphysical_computation_artifacts']
assert resource['exact_source_pad_inventory_checked']==9515
assert len(checks['current82-motor-reference-proof.json']['exact82_actual_control_segment_proofs'])==82
assert checks['current-four-pair-proof/review.json']['actual_completed_pairs']==4
power=checks['current-full-delta-power-proof.json'];assert power['CORE1V2_exact_filled_geometry_preserved'] and power['old_exact_rail_copper_preserved']
assert len(power['actual44_receiver_endpoints'])==44 and len(power['actual22_receiving_annuli'])==22
bridges=checks['current-retained-reference-bridges.json'];assert len(bridges['actual_SOURCE_bridge_witnesses']['groups'])==54 and len(bridges['actual_AUX24_endpoints'])==15
chain=proof(root/'source26-root87-to101-transaction-chain-r02/receipt.json')
assert len(chain['steps'])==14 and chain['final_board_sha256']==sha(board)
external=[
 'reports/motherboard-return-zoning-20261001/motor-bank-A-consolidated-reference-donor-r07/receipt.json',
 'reports/motherboard-return-zoning-20261001/motor-exact-antipad-union-native-controls-r04/review.json',
 'reports/motherboard-pcb-integration-20261001/source26-BankA-health-duplicate-via-repair-r92/receipt.json',
 'reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01/receipt.json',
 'reports/motherboard-pcb-integration-20261001/IO3-BankA-complete-antipad-cleanup-review-r99c/receipt.json',
 'reports/motherboard-return-zoning-20261001/BankA-IO3-width-cleanup-independent-r02/receipt.json',
 'reports/motherboard-return-zoning-20261001/ROOT94-health-U25-field-collars-r03/closure-freeze-r02.json',
 'reports/motherboard-return-zoning-20261001/ROOT99b-C19033-existing-Source-stitch-r01/closure-freeze-r01.json',
 'reports/board-completion-20261001/source26-root101-combined-validation.json']
external_checks={name:proof(Path(name))for name in external}
reg=external_checks[external[-1]]
assert reg['host_passed']==1847 and reg['actual_KiCad_cases_passed']==235 and len(reg['remaining_skips'])==5
assert reg['all_scoped_source_hashes_unchanged'] and reg['scoped_source_files']==2813
assert reg['native_ERC']['errors']==0 and reg['native_ERC']['warnings']==70 and not reg['native_ERC']['ignored_checks']
for path in (p/'current-health20-proof/receipt.json',p/'current-RAW3-proof/receipt.json',p/'independent-connectivity/review.json',p/'drc.json',p/'native-check-command-results.json'):
 frozen[str(path.resolve())]=sha(path)
health=read(p/'current-health20-proof/receipt.json');assert health['source_board_sha256']==sha(board)
assert len(health['actual_endpoint_checks'])==20 and all(x['passed']for x in health['actual_endpoint_checks'])
assert len(health['four_local_bypass_negative_cuts'])==4 and all(x['actual_local_bypass_check_rejected']for x in health['four_local_bypass_negative_cuts'])
raw=read(p/'current-RAW3-proof/receipt.json');assert raw['board_sha256']==sha(board) and raw['source_EP_VIN_VBIAS_cap_native_continuity'] and raw['all_three_original_power_transitions_preserved']
assert raw['checks'][0]['all_native_identities_match'] and all(x['source_EP_and_converter_cap_connected']and x['native_min_hole_gap_mm']>=.2495 for x in raw['checks'][1:])
inv=read(p/'independent-connectivity/review.json');assert inv['board_sha256']==sha(board) and inv['source_net_checks_pass'] and inv['complete_source_population_pass']
assert inv['uncapped_unconnected_ratsnest_edges']==inv['independent_physical_cluster_missing_joins']==3528 and not inv['orphan_copper_items'] and not inv['errors']
drc=read(p/'drc.json');assert not drc['violations'] and not drc['ignored_checks']
command=read(p/'native-check-command-results.json');assert command['all_commands_completed'] and command['exact_inputs_unchanged']
b=pcbnew.LoadBoard(str(board));assert len(b.GetFootprints())==2688 and len(b.GetTracks())==11635
assert all(sha(Path(k))==h for k,h in frozen.items())
result=dict(passed=True,adopted=True,scope='Routing WIP only: complete literal ROOT87-to101 transaction chain, retained Source connectivity, current native physical return/circuit proofs and frozen-source regression reconciled. Not a completed PCB.',board_sha256=sha(board),exact_source_design_sha256=sha(source),exact_source_netlist_sha256=sha(netlist),evidence_sha256=frozen,physical_footprints=len(b.GetFootprints()),track_via_count=len(b.GetTracks()),zone_count=len(b.Zones()),missing_joins=3528,fully_joined_multiple_pad_nets=inv['fully_joined_multiple_pad_nets'],incomplete_multiple_pad_nets=inv['incomplete_multiple_pad_nets'],native_errors=0,native_warnings=0,ignored_checks=[],orphan_copper_count=0,retained_bypass_loops=106,receiving_return_endpoints=217,actual_Source_anchored_reference_resources=188,actual_motor_control_segments=82,actual_health_continuity_endpoints=20,actual_retained_bridge_groups=54,actual_new_ordinary_pairs=4,all_prior_5969_Source_pad_clusters_preserved=True,relative_rail_geometry_preserved=True,host_tests_passed=1847,native_tests_passed=235,environment_skips=5,ERC_errors=0,ERC_warnings=70,source27_known_electrical_corrections_still_required=True,remaining_engineering=['3528 required joins remain unrouted','U11020/U11026 receiving/control returns not yet qualified','Staged Source27 slow-input/reset/supervisor corrections not yet promoted or routed','Complete rail ampacity/load drop/thermal/fault distribution remains unqualified','Full FPGA pin/package/vendor fit/runtime binding remains unfinished','Full 20ms inhibit/default-safe/missing-module behavior needs remaining circuit qualification and physical measurement','Full footprint/mechanical/manufacturing/cost review and fabrication outputs remain unfinished'],global_power_or_reference_qualification=False,physical_qualification=False,manufacturing_ready=False)
write(p/'adoption.json',result)
write(p/'baseline-disposition.json',dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=[],ignored_checks=[],remaining_required_joins=3528))
print(json.dumps({k:result[k]for k in('adopted','missing_joins','retained_bypass_loops','receiving_return_endpoints','manufacturing_ready')}),flush=True)
