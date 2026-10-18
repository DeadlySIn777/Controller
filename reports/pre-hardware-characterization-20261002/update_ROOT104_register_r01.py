"""Carry every accepted characterization obligation forward with bounded new evidence."""
from pathlib import Path
import copy,json,hashlib
root=Path.cwd();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
old=root/'reports/pre-hardware-characterization-20261001/characterization-register-r04/requirements-and-coverage.json'
out=root/'reports/pre-hardware-characterization-20261002/characterization-register-r05';out.mkdir(parents=True,exist_ok=False)
d=read(old);prior=copy.deepcopy(d)
ad=root/'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/adoption.json';a=read(ad)
full=Path(a['full_validation_report']);f=read(full)
assert a['adopted'] and a['working_revision']=='ROOT104' and f['source_hashes_unchanged'] and not f['status_counts'].get('FAIL',0)
evidence={
 'seeded_actual_SPI_faults':full.parent/'seeded_actual_SPI_faults-evidence/receipt.json',
 'actual_SPI_reset_fault_plant':full.parent/'actual_cnc3_SPI_edge_plant-evidence/receipt.json',
 'read_only_IS2_CAP3_profile':full.parent/'bounded_IS2_CAP3_profile-evidence/report.json',
 'IOL1_diagnostic_acquisition':full.parent/'bounded_IOL1_diagnostic_acquisition-evidence/report.json',
 'actual_stateful_replay':full.parent/'bounded_CNC3_stateful_replay-evidence/report.json'}
for p in evidence.values():assert p.is_file(),str(p)
d.update(adopted_PCB_revision='ROOT104',actual_footprints=2688,required_remaining_joins=3508,current_board_sha256=a['board_sha256'],latest_disconnected_full_run=str(full.relative_to(root)),full_bench_counts=f['status_counts'],latest_source_hashes_unchanged=True,latest_bounded_stateful_replay=str(evidence['actual_stateful_replay'].relative_to(root)))
d['latest_bounded_evidence']={k:dict(path=p.relative_to(root).as_posix(),sha256=sha(p),complete_Hardware_HAL_machine_or_safety_qualification=False)for k,p in evidence.items()}
d['latest_bounded_evidence_scope']={'seeded_trials':2048,'seeded_fault_classes':8,'reset_fault_mechanics_scenarios':18,'IS2_CAP3_profile_complete':False,'IS2_actual_motion_authority':False,'IOL1_diagnostic_only':True,'full_machine_profiles_completed':0,'physical_hardware_measured':False,'note':'Actual C/RTL protocol and ideal-mechanics proofs. These are bounded subsets and do not close all22 requested faults,all9 full-machine profiles,complete HAL/IOL1 authority,vendor fit/timing,or the electrical20ms inhibit gate.'}
d['current_board_geometry_scope']={'native_regular_DRC_errors':0,'native_regular_DRC_warnings':0,'ignored_checks':[],'independent_missing_joins':3508,'native_missing_joins':3508,'orphan_copper':0,'owned_bypass_loops':120,'receiving_returns':245,'Source_anchored_filled_resources':188,'Source27_adopted':False,'Freerouting_copper_adopted':False}
d['input_sha256'].update({str(p.relative_to(root)):sha(p)for p in [old,ad,full,Path(__file__),*evidence.values()]})
for key in ['accepted_user_requirements','subsystems','virtual_plant','motion_scenarios','fault_injection','machine_profiles','toolchain_gates','measured_hardware_ratings']:
 assert d[key]==prior[key],key
assert not d['manufacturing_ready'] and not d['hardware_qualification_performed']
(out/'requirements-and-coverage.json').write_text(json.dumps(d,indent=2)+'\n')
(out/'receipt.json').write_text(json.dumps(dict(passed=True,prior_sha256=sha(old),register_sha256=sha(out/'requirements-and-coverage.json'),all_prior_requirements_preserved=True,hardware_ratings_changed=False,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,board='ROOT104',complete_machine_profiles=0,manufacturing_ready=False)))
