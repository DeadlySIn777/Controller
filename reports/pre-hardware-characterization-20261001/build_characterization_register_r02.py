"""Advance coverage only where exact frozen component evidence exists."""
from pathlib import Path
import json,hashlib,re
root=Path.cwd();base=root/'reports/pre-hardware-characterization-20261001'
out=base/'characterization-register-r02';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
prior=base/'characterization-register-r01';r=read(prior/'requirements-and-coverage.json');d=read(prior/'provisional-datasheet.json')
full=root/'reports/pre-hardware-validation-20261001/full-two-cap-r05'
ad=root/'reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06/adoption.json'
a=read(ad);assert a['adopted']and a['working_revision']=='ROOT102'
paths=dict(full=full/'report.json',dynamic=full/'isolated_stepgen12_dynamic-evidence/receipt.json',
    encoder=full/'isolated_encoder4_sweep-evidence/receipt.json',spi=full/'cnc3-structural-RTL-evidence/receipt.json',
    analog=base/'analog-simulation-summary-r01/receipt.json',adoption=ad,
    assembly=root/'reports/motherboard-pcb-integration-20261001/two-cap-full-drill-SMD-audit-r01/receipt.json')
v={k:read(p)for k,p in paths.items()}
assert v['full']['status']=='BLOCKED' and not v['full']['source_changes']
assert v['dynamic']['passed']and v['encoder']['passed']and v['spi']['status']=='PASS'
assert not v['spi']['stateful_CNC3_endpoint']and not v['spi']['full_twelve_joint_machine']
assert v['analog']['status']=='PARTIAL_PASS_WITH_EXPLICIT_FULL_CHAIN_MODEL_BLOCKER'
inputs={str(p.relative_to(root)):sha(p)for p in [*paths.values(),prior/'requirements-and-coverage.json',prior/'provisional-datasheet.json',Path(__file__)]}
r.update(input_sha256={**r['input_sha256'],**inputs},adopted_PCB_revision=102,required_remaining_joins=a['missing_joins'],
    current_board_sha256=a['board_sha256'],latest_disconnected_full_run=str(paths['full'].relative_to(root)),
    full_bench_counts=v['full']['status_counts'],latest_source_hashes_unchanged=True,
    current_assembly_findings=dict(positive_drill_land_overlaps=279,unique_drilled_vias=275,foreign_net_overlaps=0,
        exact_tangency_excluded_by_native_zero_clearance=True,lower_bound_only=True,qualified_process_disposition=False))
updates={
 'STEP':('PARTIAL','Actual twelve-generator steady and changing independent rate/reversal/stop fixtures pass. Complete stateful CNC3/HAL integration, configured runtime timing, drive/cable/load corners and vendor timing remain open.'),
 'ENCODER':('PARTIAL','Four unchanged actual encoder instances tested at ideal digital boundaries, with index-at-rest and illegal-transition checks. Receiver/cable/filter/metastability, duty-cycle extremes, full controller integration and vendor timing remain open.'),
 'SPI':('PARTIAL','Actual CNC3 dual-CS transport, structural validator, atomic queue and response packers pass real serial/CRC/timing cases and independent C codec comparisons. Stateful motion/safety endpoint, HAL, target timing and routed electrical chain remain open.'),
 'ANALOG':('PARTIAL','96 actual source-bound passive filter cases and12 simultaneous four-channel manufacturer OPA buffer model cases pass. INA149 full-chain model convergence failed; ADC manufacturer model is encrypted TINA. Upstream/reference/power boundaries remain ideal,ADC load approximated; full analog accuracy/fault/corner qualification open.'),
 'SIGNAL_INTEGRITY':('NOT_RUN','Board still has3524required joins; actual final stackup, extracted copper and selected receiver/cable models are not complete.'),
}
for s in r['subsystems']:
 if s['id']in updates:s['status'],s['remaining_engineering']=updates[s['id']]
 if s['id']in ['STEP','ENCODER','SPI','ANALOG']:
  key={'STEP':'dynamic','ENCODER':'encoder','SPI':'spi','ANALOG':'analog'}[s['id']]
  s['latest_component_evidence']=str(paths[key].relative_to(root));s['complete_subsystem_qualified']=False
r['evidence_types']=list(dict.fromkeys(r['evidence_types']+['SPICE_COMPONENT_SIMULATION']))
r['toolchain_gates'].update(CNC3_HAL_and_actual_RTL='STRUCTURAL_RTL_PASS_STATEFUL_HAL_MACHINE_INCOMPLETE',
    ngspice_and_validated_models='NGSPICE_AND_SELECTED_PASSIVE_BUFFER_MODELS_PASS_COMPLETE_CHAIN_BLOCKED')
for row in d['ratings']:
 match=next((s for s in r['subsystems']if s['name']==row['parameter']),None)
 if match and 'reason'in row:row['reason']=match['remaining_engineering']
e=v['encoder'];g=v['analog'];counts=[]
for run in v['dynamic']['runs']:
 log=Path(run['simulation']['log']);assert sha(log)==run['simulation']['log_sha256']
 text=log.read_text();m=re.search(r'checks=(\d+)',text);assert m
 counts.append(int(m[1]))
d['ratings']+=[
 dict(parameter='Four actual encoder components at ideal digital input boundaries',label='SIMULATED LIMIT',
    passed_quadrature_edges_per_second=e['ideal_pass_edge_rate_hz'],first_tested_failure_edges_per_second=e['first_tested_failing_edge_rate_hz'],
    exact_continuous_boundary_proved=False,receiver_cable_metastability_or_vendor_timing_modeled=False,hardware_qualified_value=None),
 dict(parameter='Twelve pulse generators with independent speed, reversal and stop changes',label='SIMULATED LIMIT',
    assumed_core_Hz=50000000,assumed_update_Hz=1000,independent_edge_count_checks=sum(counts),profiles=3,
    per_channel_rates='25to75percent of each explicit isolated timing ceiling',actual_CNC3_complete_machine=False,hardware_qualified_value=None),
 dict(parameter='Four native-bound passive47ohm/2.2nF filter sections',label='SIMULATED LIMIT',cases=96,
    simulated_frequency_range_Hz=g['passive_filter']['frequency_range_Hz'],scope=g['passive_filter']['scope'],hardware_qualified_value=None),
 dict(parameter='Four native-bound divider/OPA4197/filter model sections',label='SIMULATED LIMIT',cases=12,
    simulated_frequency_range_Hz=g['active_buffer']['simulated_frequency_range_Hz'],
    simulated_settling_to_own_final_range_s=g['active_buffer']['simulated_final_settling_range_s'],
    scope=g['active_buffer']['scope'],absolute_accuracy_or_ENOB_qualified=False,hardware_qualified_value=None),
 dict(parameter='CNC3 structural codec and dual-CS serial transport',label='SIMULATED LIMIT',
    static_independent_C_oracle_cases=v['spi']['static_oracle_cases'],family_mapping=v['spi']['family_synthesis'],
    stateful_endpoint=False,actual_HAL=False,vendor_fit_timing=False,hardware_qualified_value=None)]
d.update(revision='Source26 / ROOT102 characterization-r02',evidence_sha256=r['input_sha256'])
d['notes']+=['No complete analog-chain pass is claimed from passive or buffer models. Failed full-chain convergence remains preserved.',
 'Positive SMD drill intersection count is a lower bound: exact tangency and process registration clearance need additional disposition.',
 'Full r05 has17passing stages,9blocked stages and1unrun physical stage; there are no failed stages. A blocked full bench is not completed controller qualification.']
for n,x in [('requirements-and-coverage.json',r),('provisional-datasheet.json',d)]:
 (out/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8',newline='\n')
assert all(sha(root/p)==h for p,h in inputs.items())
print(json.dumps(dict(status='INCOMPLETE',PCB='ROOT102',subsystems=len(r['subsystems']),checks=sum(counts),hardware_qualified=False)))
