"""Record bounded stateful/mechanical progress without advancing hardware ratings."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE/'characterization-register-r03';OUT.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=HERE/'characterization-register-r02'
r=read(prior/'requirements-and-coverage.json');d=read(prior/'provisional-datasheet.json')
paths={
 'full':ROOT/'reports/pre-hardware-validation-20261001/full-analog-plant-r06/report.json',
 'isolated_plant':ROOT/'reports/pre-hardware-validation-20261001/full-analog-plant-r06/isolated_edge_plant-evidence/receipt.json',
 'spi_plant':ROOT/'reports/controller-plant-20261001/actual-spi-edge-plant-r03/receipt.json',
 'stateful':ROOT/'reports/cnc3-stateful-implementation-20261001/serial-replay-full-r02/report.json',
 'handoff':ROOT/'reports/cnc3-stateful-implementation-20261001/serial-admission-handoff-r01/receipt.json',
 'analog_nominal_variants':HERE/'INA149-vendor-variant-compatibility-r01/receipt.json',
 'analog_four_TINA':HERE/'AI-chain-TINA-initialized-quick-r02/receipt.json',
 'analog_four_PSpice':HERE/'AI-chain-initialized-quick-r01/receipt.json',
 'analog_PSpice_extended':HERE/'INA149-bidirectional-nominal-r01/receipt.json',
}
v={k:read(p)for k,p in paths.items()}
assert v['full']['status_counts']=={'BLOCKED':9,'NOT_RUN':1,'PASS':20} and v['full']['source_hashes_unchanged']
assert v['isolated_plant']['status']=='PASS' and v['isolated_plant']['baseline_checks']==1114
assert v['spi_plant']['status']=='PASS' and len(v['spi_plant']['cases'])==9 and v['spi_plant']['source_unchanged']
assert v['stateful']['status']=='PASS' and v['stateful']['counts']=={'PASS':11,'FAIL':0,'BLOCKED':0,'NOT_RUN':0}
assert v['stateful']['inputs_unchanged'] and v['stateful']['protocol_rate_max']==0x01000000
assert not v['analog_four_TINA']['passed'] and not v['analog_four_PSpice']['passed'] and not v['analog_PSpice_extended']['passed']
inputs={str(p.relative_to(ROOT)):sha(p)for p in (*paths.values(),prior/'requirements-and-coverage.json',prior/'provisional-datasheet.json',Path(__file__))}
r['input_sha256'].update(inputs)
r.update(latest_disconnected_full_run=str(paths['full'].relative_to(ROOT)),full_bench_counts=v['full']['status_counts'],
         latest_source_hashes_unchanged=True,latest_bounded_stateful_replay=str(paths['stateful'].relative_to(ROOT)))
r['virtual_plant'].update(status='PARTIAL_ACTUAL_RTL_EDGE_INTEGRATION',isolated_checks=1114,compiled_negative_controls=12,
    actual_serial_RTL_scenarios=[c['scenario']for c in v['spi_plant']['cases']],
    actual_STEP_DIR_channels=12,actual_ABZ_channels=4,actual_LinuxCNC_HAL=False,
    actual_waveforms_from_position=True,ideal_external_power_permission_providers=True,
    electrical_safety_qualified=False,complete_nine_machine_suite=False,
    home_limit_probe_computed_but_not_connected_to_actual_event_RTL=True,
    inertia_torque_acceleration_and_spindle_frequency_not_implemented=True,
    evidence=str(paths['spi_plant'].relative_to(ROOT)))
updates={
 'STEP':'Twelve actual configured DDS channels pass asymmetric updates, zero rates, reversals and serial feedback reconciliation against emitted pins/ideal mechanics. Incoming global/timing rates are enforced in the staged stateful RTL. Real HAL, drive/load/timing/electrical corners remain open.',
 'ENCODER':'Four actual filtered ABZ cores count generated ideal position waveforms, including lost motor steps and unplug/supply-validity faults. Receiver/cable/metastability and complete acquisition/event/MPG/expansion providers remain open.',
 'SPI':'Actual motion/session/config/watchdog/rate admission and CRC/CS/reset rejection pass with frozen96/176-byte frames. Eleven fresh stateful stages pass; this bounded motion candidate has no backpressured request queue. Full CAP3/pages/IOL1/events/output authority, real HAL and physical SPI timing remain open.',
 'ANALOG':'96 passive filter and12 simultaneous buffer cases remain passed. Original TI TINA INA149 completes one nominal bidirectional path in two compatibility modes, but the actual four-channel corner experiment still fails numerically with both vendor releases; extended PSpice transient also aborts. ADC remains an approximate load. Full analog acquisition/corners/accuracy are unqualified.'}
for s in r['subsystems']:
    if s['id']in updates:
        s.update(status='PARTIAL',remaining_engineering=updates[s['id']],complete_subsystem_qualified=False)
        s['latest_component_evidence']=str(paths['stateful'if s['id']=='SPI'else'analog_four_TINA'if s['id']=='ANALOG'else'spi_plant'].relative_to(ROOT))
r['fault_injection']['bounded_evidence']={
    'actual_SPI_RTL_and_ideal_mechanics':str(paths['spi_plant'].relative_to(ROOT)),
    'actual_stateful_SPI_adversarial_and_mutation_suite':str(paths['stateful'].relative_to(ROOT)),
    'complete_22_fault_electrical_suite_passed':False,'randomized_thousands_or_overnight_run_performed':False}
r['toolchain_gates']['CNC3_HAL_and_actual_RTL']='BOUNDED_STATEFUL_MOTION_SPI_MECHANICS_PASS_COMPLETE_PROVIDERS_HAL_MACHINE_INCOMPLETE'
for row in d['ratings']:
    matching=next((s for s in r['subsystems']if s['name']==row['parameter']),None)
    if matching and 'reason'in row:row['reason']=matching['remaining_engineering']
d['ratings'] += [
    dict(parameter='Frozen CNC3 runtime rate guard',label='DESIGN LIMIT',MAX_RATE=0x01000000,assumed_core_Hz=50000000,
         protocol_steps_per_second=195312.5,per_channel_timing_check='abs(rate)*(STEP_high+STEP_low+1)<=2^32',
         requested_2MHz_target_qualified=False,hardware_qualified_value=None),
    dict(parameter='Actual stateful CNC3 serial/STEP/DIR/ABZ to ideal mechanics',label='SIMULATED LIMIT',
         scenarios=9,Cplusplus_assertions=sum(c['fixture_assertions']for c in v['spi_plant']['cases']),
         complete_HAL_machine_or_electrical_chain=False,hardware_qualified_value=None,
         scope=v['spi_plant']['scope']),
]
d.update(revision='Source26 / ROOT102 characterization-r03',evidence_sha256=r['input_sha256'])
d['notes'] += ['Full r06 has20passed stages,9blocked and1physical stage unrun; the later11-stage stateful replay and nine-scenario mechanics integration are additional separately bound evidence.',
              'Native electrical source/PCB remain Source26/ROOT102. No report-local reset/routing candidate is promoted here.',
              'Full analog convergence is not closed by a nominal alternate-vendor-model pass. All failed analyses remain retained.']
for name,data in [('requirements-and-coverage.json',r),('provisional-datasheet.json',d)]:
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
assert all(sha(ROOT/p)==h for p,h in inputs.items())
print(json.dumps({'status':'INCOMPLETE','subsystems':len(r['subsystems']),'machine_profiles':len(r['machine_profiles']),
                  'PCB':'ROOT102','manufacturing_ready':False}))
