from pathlib import Path
import hashlib,json
D=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-actual-r01')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
binding=read(D/'literal-delta-binding.json');board=Path(binding['board']);before=Path(binding['before_board'])
assert sha(board)==binding['board_sha256']and sha(before)==binding['before_board_sha256']
old=read(D/'all101-retained-current-proof.json');new=read(D/'three-current-bypass-proof.json')
assert old['passed']and new['passed']and old['board_sha256']==new['board_sha256']==sha(board)
assert old['frozen_dependencies']==new['frozen_dependencies']
assert old['retained_local_loops_checked']==101 and new['retained_local_loops_checked']==3
assert len(old['actual_receiving_return_anchor_reviews'])==207 and len(new['actual_receiving_return_anchor_reviews'])==6
controls=read(D/'all82-retained-control-proof.json');assert controls['passed']
resources=read(D/'full-reference-resource-review.json');assert resources['passed']and not resources['unanchored_components']
assert resources['filled_component_count']==188 and not resources['derived_nonphysical_computation_artifacts']
power=read(D/'actual-IO3-relative-power-proof.json');assert power['passed']and power['board_sha256']==sha(board)
inventory=read(D/'independent-connectivity/review.json')
assert inventory['source_net_checks_pass']and not inventory['orphan_copper_items']
assert inventory['uncapped_unconnected_ratsnest_edges']==inventory['independent_physical_cluster_missing_joins']==3533
native=read(D/'routed-1.json');assert not native['violations']and not native['ignored_checks']
checks=[]
for ref in ['C19033','C13017','C15004']:
    for case in ['VCC_branch','cap_return_branch','nearby_Source_Ground_barrel']:
        p=D/f'actual-cut-{ref}-{case}.fresh-native-review-r02.json'
        r=read(p)
        assert r['passed']and r['persisted_mutation_verified']
        assert r['board_sha256']==sha(D/f'actual-cut-{ref}-{case}.kicad_pcb')
        checks.append({'path':str(p),'sha256':sha(p),'ref':ref,'case':case,'rejection':r['rejection']})
names=['receipt.json','bounded-scope.json','literal-delta-binding.json','combined-current104-bypass-manifest.json',
       'all101-retained-current-proof.json','three-current-bypass-proof.json','all82-retained-control-proof.json',
       'full-reference-resource-review.json','actual-IO3-relative-power-proof.json','independent-connectivity/review.json','routed-1.json']
r=dict(passed=True,before_board=str(before),before_board_sha256=sha(before),board=str(board),board_sha256=sha(board),
  exact_added_Cu_UUIDs=binding['added_copper_UUIDs'],added_Cu_count=18,
  actual_new_stationary_receivers=['C19033 / U19022','C13017 / U13009','C15004 / U15001'],
  prior_101_current_groups_retained=True,new_strict_groups=3,composed_current_strict_groups=104,
  prior_actual_return_endpoints=207,new_actual_return_endpoints=6,composed_actual_return_endpoints=213,
  exact_common_native_board_and_frozen_checker_dependencies=True,
  actual_old_82_BankA_controls_preserved=True,
  native_errors=0,native_warnings=0,ignored_checks=0,
  native_missing_joins=3533,independent_missing_joins=3533,orphan_Cu_count=0,
  complete_source_population=2688,actual_anchored_reference_resources=188,unanchored=0,synthetic=0,
  actual_nine_physical_supply_return_Source_stitch_cuts_rejected_after_fresh_reload=checks,
  frozen_IO3_full_core_narrow_Source44_feed22_guard_passed=True,CORE1V2_exact_native_fill_preserved=True,
  all_old_Source_clusters_Cu_pads_lands_poses_zones_and_source_preserved=True,
  source27_adopted=False,health4_full_reference_qualified=False,
  new_power_feed_capacity_load_thermal_timing_or_measured_inductance_qualified=False,
  manufacturing_ready=False,evidence={n:{'path':str(D/n),'sha256':sha(D/n)}for n in names})
(D/'freeze-receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(passed=True,board_sha256=sha(board),receipt_sha256=sha(D/'freeze-receipt.json'),new_loops=3,current_loops=104,current_return_endpoints=213)))
