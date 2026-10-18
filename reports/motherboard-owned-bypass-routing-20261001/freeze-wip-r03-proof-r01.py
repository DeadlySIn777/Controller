"""Freeze exact native WIP routing guards and their real warning fixture."""
import hashlib,json,subprocess
from pathlib import Path
base=Path('reports/motherboard-owned-bypass-routing-20261001')
out=base/'wip-r03-final-proof-r02'
if out.exists():raise ValueError('Fresh immutable proof required')
out.mkdir()
paths=[Path(p)for p in [
 'tools/hardware_route_owned_bypass_loops_wip_r03.py',
 'tools/hardware_route_owned_bypass_loops_r02.py',
 'tools/hardware_route_owned_bypass_loops.py',
 'tools/hardware_check_return_corridors_r04.py',
 'tools/hardware_check_return_corridors_r03.py',
 'tools/hardware_check_return_corridors_r02.py',
 'tools/hardware_check_return_corridors.py',
 'tools/hardware_collect_native_reference_fills.py',
 'tools/hardware_anchor_owned_cmos_returns.py',
 'tools/hardware_route_selected_additive.py',
 'tools/hardware_route_local_signals.py',
 'tools/hardware_populate_motherboard_pcb.py',
 'tests/test_owned_bypass_wip_native.py',
 'tests/test_owned_bypass_annuli.py',
 'tests/test_reviewed_zone_outlines_native.py',
 'tests/test_native_generated_fill_interchange.py']]
paths+=list((base/'wip-r03-native-warning-fixture-r03').glob('*.json'))
paths+=list((base/'wip-r03-native-warning-fixture-r03').glob('*.kicad_pcb'))
paths+=list((base/'wip-r03-warning-fixture-preparation-r03').glob('*.json'))
paths+=list((base/'wip-r03-warning-fixture-preparation-r03').glob('*.kicad_pcb'))
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):digest(p)for p in paths}
command=['C:/Program Files/KiCad/10.0/bin/python.exe','-m','unittest',
 'tests/test_owned_bypass_wip_native.py','tests/test_owned_bypass_annuli.py',
 'tests/test_reviewed_zone_outlines_native.py','tests/test_native_generated_fill_interchange.py']
run=subprocess.run(command,capture_output=True,text=True)
(out/'native-tests.log').write_text(run.stdout+run.stderr)
if run.returncode or 'Ran 26 tests'not in run.stderr or not run.stderr.rstrip().endswith('OK'):raise ValueError('Actual native26 regression checks failed/skipped')
if before!={str(p):digest(p)for p in paths}:raise ValueError('Proof input changed during native checks')
fixture=json.loads((base/'wip-r03-native-warning-fixture-r03/receipt.json').read_text())
if fixture['native_DRC_regular']!=1 or fixture['complete_board_DRC_pass']or fixture['manufacturing_ready']or fixture['new_route_DRC_defects']:raise ValueError('Actual retained native warning was hidden or misrepresented')
tool=Path('tools/hardware_route_owned_bypass_loops_wip_r03.py')
actual={h for p,h in fixture['input_sha256'].items()if Path(p).resolve()==tool.resolve()}
if actual!={digest(tool)}:raise ValueError('Actual warning fixture used another routing tool')
r=dict(passed=True,input_sha256=before,tool_sha256=digest(tool),native_regression_tests=26,
 tests_passed=True,no_skipped_native_tests=True,actual_persisted_native_warning_fixture_pass=True,
 exact_warning_guard_keeps_full_native_JSON=True,new_warnings_errors_ignored_checks_and_source_fragmentation_rejected=True,
 all_native_reference_annuli_and_return_guards_preserved=True,
 no_complete_controller_routing_claim=True,manufacturing_ready=False)
(out/'review.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items()if k!='input_sha256'}))
