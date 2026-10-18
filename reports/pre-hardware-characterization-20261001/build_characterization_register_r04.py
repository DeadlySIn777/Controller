"""Bind current adopted PCB and separately scoped simulation evidence, without ratings."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=HERE/'characterization-register-r04';OUT.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=HERE/'characterization-register-r03'
r=read(prior/'requirements-and-coverage.json');d=read(prior/'provisional-datasheet.json')
names={
 'adoption':'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/adoption.json',
 'full':'reports/pre-hardware-validation-20261001/full-health-stateful-plant-r07/report.json',
 'spi_plant':'reports/controller-plant-20261001/actual-spi-reset-fault-plant-r06/receipt.json',
 'C_driver':'reports/controller-plant-20261001/actual-C-driver-SPI-probe-r02/receipt.json',
 'IOL1':'reports/cnc3-iol1-acquisition-20261001/diagnostic-replay-full-r01/report.json',
 'audit':'reports/motherboard-pcb-integration-20261001/health-r31-full-drill-SMD-audit-r01/receipt.json',
 'analysis_initialization':'reports/pre-hardware-characterization-20261001/AI-chain-analysis-initialization-r03/receipt.json',
 'common_mode':'reports/pre-hardware-characterization-20261001/INA149-common-mode-exploration-r04/receipt.json'}
v={k:read(ROOT/p)for k,p in names.items()};a=v['adoption']
assert a['adopted'] and a['working_revision']=='ROOT103' and a['missing_joins']==3521
assert v['full']['status_counts']=={'PASS':22,'BLOCKED':9,'NOT_RUN':1} and v['full']['source_hashes_unchanged']
assert v['full']['started_from']['board_sha256']==a['board_sha256']
assert v['spi_plant']['status']=='PASS' and len(v['spi_plant']['cases'])==18 and v['spi_plant']['source_unchanged']
assert v['C_driver']['status']=='BLOCKED' and v['C_driver']['probe_passed']
assert v['IOL1']['status']=='PASS' and v['IOL1']['inputs_unchanged']
inputs={p:sha(ROOT/p)for p in names.values()}
inputs.update({str(p.relative_to(ROOT)):sha(p)for p in [Path(__file__),prior/'requirements-and-coverage.json',prior/'provisional-datasheet.json']})
r['input_sha256'].update(inputs)
r.update(adopted_PCB_revision='ROOT103',current_board_sha256=a['board_sha256'],required_remaining_joins=3521,
 latest_disconnected_full_run=names['full'],full_bench_counts=v['full']['status_counts'],latest_source_hashes_unchanged=True,
 current_assembly_findings=dict(intersections=277,unique_vias=274,foreign_net_intersections=0,lower_bound=True,
                              qualified=False,evidence=names['audit']))
r['virtual_plant'].update(actual_serial_RTL_scenarios=[c['scenario']for c in v['spi_plant']['cases']],
 evidence=names['spi_plant'],counter_reset_preserves_actual_mechanical_position=True,
 fresh_valid_UPDATE_after_fault_cannot_restart=True,actual_LinuxCNC_HAL=False,
 actual_original_C_driver_discovery='BLOCKED_REAL_CAP3_READ_PAGE_ABSENT',actual_C_driver_probe=names['C_driver'])
updates={
 'SPI':'18 actual serial-to-mechanics scenarios pass, including CRC/session/replay/CS/MOSI/short-frame/reset faults and fresh valid UPDATE restart refusal. Actual original C driver against freshly compiled RTL stops with BAD_CAPS because CAP3 READ_PAGE is absent. Four-stage actual cached C-target/IOL1 diagnostic acquisition replay passes; this grants no factory identity, ACTIVE/output authority or complete HAL.',
 'DIGITAL_INPUT':'Actual four-lane cached target C and SPI acquisition RTL pass age/freshness, CRC/header, reset, recovery, seven compiled mutations and cycle-exact optimization. Factory record, CONFIG/ACTIVE implementation, target GPIO/ADC/MMIO and physical thresholds remain unqualified.',
 'ANALOG':'96 passive filter and12 simultaneous buffer cases remain passed. Three analysis-initialization variants abort inside the original INA149 model. One of six single-channel nominal common-mode studies runs; five abort numerically. The prior nominal TINA pass does not establish full-chain operation. ADC is still an approximate load; original vendor models are preserved. No hardware fault or ratings inferred from convergence failure.',
 'WATCHDOG':'Fault simulations include reset during CS and exact mechanical-position retention across counter reset. Clock-stall inhibition requires the actual independent electrical watchdog/gating; it is not proved by an RTL-clock timer. Source27 reset/slow-input corrections remain staged, and the full20ms electrical chain remains unfinished.'}
for s in r['subsystems']:
 if s['id']in updates:s.update(status='PARTIAL',remaining_engineering=updates[s['id']],complete_subsystem_qualified=False)
r['fault_injection']['bounded_evidence'].update(actual_SPI_RTL_and_ideal_mechanics=names['spi_plant'],
 actual_C_driver_capability_failure=names['C_driver'],actual_diagnostic_IOL1=names['IOL1'])
r['toolchain_gates']['CNC3_HAL_and_actual_RTL']='ACTUAL_C_DRIVER_DISCOVERY_BLOCKED_CAP3_READ_PAGE_ABSENT; FULL_HAL_PROVIDERS_INCOMPLETE'
for row in d['ratings']:
 if row['parameter']=='Actual stateful CNC3 serial/STEP/DIR/ABZ to ideal mechanics':
  row.update(scenarios=18,Cplusplus_assertions=sum(c['fixture_assertions']for c in v['spi_plant']['cases']))
 matching=next((s for s in r['subsystems']if s['name']==row['parameter']),None)
 if matching and 'reason'in row:row['reason']=matching['remaining_engineering']
d.update(revision='Source26 / ROOT103 characterization-r04',evidence_sha256=r['input_sha256'])
d['notes'] += ['Current adopted ROOT103/CAD29 exact-board full r07:22PASS,9BLOCKED,1physicalNOT_RUN,0FAIL;1887host+235nativepass and3765scopedinputsunchanged.',
 'The18case serial fault/plant and4stage IOL1 diagnostic replays are additional separately hashed evidence after full r07; full r07 used9serialplant cases.',
 'Prior r03/ROOT102 notes remain historical. Current Source26/ROOT103 still has3521requiredjoins and277paste-land drill intersections across274vias. No manufacturing readiness or new hardware rating.']
for name,data in [('requirements-and-coverage.json',r),('provisional-datasheet.json',d)]:
 (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8',newline='\n')
assert all(sha(ROOT/p)==h for p,h in inputs.items())
print(json.dumps(dict(status='INCOMPLETE',PCB='ROOT103',subsystems=len(r['subsystems']),machine_profiles=len(r['machine_profiles']),manufacturing_ready=False)))
