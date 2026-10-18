"""Freeze exact final local positives, without promoting pending physical-cut or bench evidence."""
from pathlib import Path
import hashlib,json

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=Path('reports/motherboard-return-zoning-20261001')
D=R/'ROOT102-health-current110-composed-r31'
B=D/'motherboard-bounded-merged-candidate.kicad_pcb'
expected='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
assert sha(B)==expected
files={
 'merger':D/'receipt.json',
 'binding':D/'final-binding-r02/binding.json',
 'source_clusters':D/'final-binding-r02/all-ROOT102-prior-native-Source-clusters.json',
 'loops':D/'final-current110-strict-proof-r01.json',
 'controls':D/'final-actual-controls-r01.json',
 'resources':D/'final-literal-resources-r01.json',
 'registration':D/'final-registration-r01.json',
 'relative_power':D/'final-global-IO3-r07.json',
 'inventory':D/'final-independent-inventory-r01/review.json',
 'map':D/'final-source26-map-r01/domain-map.json',
 'current110':D/'final-binding-r02/current110-bypass-manifest.json',
 'prior108':R/'ROOT101-two-same-side-bypass-restored-r06/current108-bypass-manifest.json',
 'delta':R/'ROOT101-health-complete-delta-r30/literal-delta.json',
 'scope':R/'ROOT101-health-complete-delta-r30/bounded-scope.json',
 'drc':D/'drc.json',
}
reports={k:json.loads(p.read_text())for k,p in files.items()}
for k in('binding','source_clusters','loops','controls','resources','registration','relative_power'):
 assert reports[k]['passed']and reports[k]['board_sha256']==expected,k
assert reports['merger']['board_sha256']==expected and reports['merger']['native_DRC_regular']==0 and not reports['merger']['ignored_checks']
assert not reports['drc']['violations']and not reports['drc']['ignored_checks']
i=reports['inventory'];assert i['board_sha256']==expected and i['source_net_checks_pass']and not i['errors']and not i['orphan_copper_items']
assert i['uncapped_unconnected_ratsnest_edges']==i['independent_physical_cluster_missing_joins']==3521
assert reports['loops']['retained_local_loops_checked']==110 and len(reports['loops']['actual_receiving_return_anchor_reviews'])==225
assert reports['resources']['filled_component_count']==188 and not reports['resources']['unanchored_components']
assert len(reports['controls']['rows'])==34 and reports['registration']['new_or_modified_vias_checked']==21
prior={g['ref']:g for g in reports['prior108']['owned_loops']if g['retained']}
current={g['ref']:g for g in reports['current110']['owned_loops']if g['retained']}
assert len(prior)==108 and len(current)==110 and not set(prior)-set(current)
added=sorted(set(current)-set(prior));changed=sorted(k for k in prior if prior[k]!=current[k])
assert added==['C11079','C11081']and changed==['C11078','C11080']
inputs={str(p):sha(p)for p in[B,*files.values(),Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
out=D/'local-positive-freeze-r01.json';assert not out.exists()
result=dict(passed=True,scope='Exact local physical/electrical positive checks only. Parent full bench and final independent persisted health cuts remain separately required before adoption.',board=str(B),board_sha256=expected,input_sha256=inputs,
 Source26_unchanged=True,ROOT102_two_cap_improvement_exactly_preserved=True,
 loops=dict(previous108=108,unchanged106=106,rebound_C11078_C11080=changed,new_C11079_C11081=added,current110=110,receiving_returns225=225),
 native_DRC_errors=0,native_DRC_warnings=0,ignored_checks=[],required_joins_remaining=3521,independent_required_joins=3521,orphan_Cu=0,
 physical_Source_anchored_reference_resources=188,synthetic_or_exempt_resources=0,actual_control_objects34=34,new_or_modified_registration_vias21=21,nominal_drill_registration_clearance_mm=.15,
 original_r07_unchanged=True,relative_power_topology_only=True,proof_paths={k:str(p)for k,p in files.items()},
 persisted_new_health_cut_controls_pending=True,parent_complete_bench_pending=True,live_pointers_or_CAD_published=False,
 loaded_current_thermal_all_temperature_timing_qualified=False,upstream_MC_RAILS_OK_5V_producer_path_qualified=False,whole_board_assembly_registration_qualified=False,manufacturing_ready=False)
out.write_text(json.dumps(result,indent=2))
assert all(sha(Path(p))==h for p,h in inputs.items())
print(json.dumps(dict(passed=True,board_sha256=expected,local_scope_only=True,loops=110,returns=225)),flush=True)
