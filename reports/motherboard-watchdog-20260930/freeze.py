"""Freeze this source/RTL review without changing any hardware sources."""
from pathlib import Path
import hashlib,io,json,shutil,sys,unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 out=HERE/'receipt-r01.json'
 if out.exists():raise SystemExit('Immutable watchdog receipt already exists')
 native=json.loads((HERE/'native-r03/review.json').read_text())
 rtl=json.loads((HERE/'rtl-r04/receipt.json').read_text())
 if not native['passed'] or not rtl['passed']:raise SystemExit('Evidence did not pass')
 for r,h in rtl['source_sha256'].items():
  if digest(ROOT/r)!=h:raise SystemExit('RTL source changed: '+r)
 for r,h in native['source_files'].items():
  if digest(Path(r))!=h:raise SystemExit('Native review input changed: '+r)
 for name in ('tps3851-timing-native.png','tps274-timing-native.png'):
  shutil.copy2(ROOT/'tmp'/name,HERE/'sources'/name)
 sys.path.insert(0,str(ROOT/'tools'))
 suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_motherboard_watchdogs.py')
 stream=io.StringIO();res=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 (HERE/'host-tests-r01.log').write_text(stream.getvalue(),encoding='utf-8')
 if not res.wasSuccessful():raise SystemExit('Focused watchdog host tests failed')
 mapping={'schema_version':1,'native_source_snapshot':'reports/motherboard-integration-20260930/r19-2663-status-identity-staged-source',**native['bringup_pin_map']}
 (HERE/'pin-map-r01.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
 primary=[ROOT/r for r in [
  'research/is1-watchdogs/tps3851-revb.pdf','research/is1-watchdogs/sn74lvc2g17.pdf',
  'research/is1-watchdogs/sn74lvc1g34.pdf','research/is1-watchdogs/cl10c332jb8nnnc.html',
  'research/machine-permission/sn74lvc2g74.pdf','research/machine-permission/sn74lvc2g08.pdf',
  'research/machine-permission/sn74lvc1g11.pdf','research/mc-motor-buffers/am26c31.pdf',
  'reports/motherboard-motors-20260930/sources/tlp3640a.pdf',
  'reports/motherboard-motors-20260930/sources/tlp4176a.pdf',
  'reports/motherboard-motors-20260930/sources/ltc6994-primary-web-review.json',
  'reports/motherboard-do-20260930/sources/iso7760.pdf',
  'reports/motherboard-do-20260930/sources/tps274c65.pdf']]
 sources=[ROOT/'tools/hardware_validate_motherboard_watchdogs.py',ROOT/'tools/hardware_check_motherboard_watchdog_rtl.py',ROOT/'tests/test_motherboard_watchdogs.py']
 sources+=list((ROOT/'gateware/motherboard_bringup').glob('*'))
 files=primary+sources+[HERE/'native-r03/review.json',HERE/'rtl-r04/receipt.json',HERE/'rtl-r04/mapped-stat.json',HERE/'README.md'] if (HERE/'README.md').exists() else primary+sources+[HERE/'native-r03/review.json',HERE/'rtl-r04/receipt.json',HERE/'rtl-r04/mapped-stat.json']
 files += [HERE/'REVIEW.md',HERE/'freeze.py',HERE/'host-tests-r01.log',HERE/'pin-map-r01.json']+list((HERE/'sources').glob('*'))
 cells=json.loads((HERE/'rtl-r04/mapped-stat.json').read_text())['design']['num_cells_by_type']
 receipt={'schema_version':1,'status':'source_and_diagnostic_RTL_review_frozen_physical_gates_open',
  'native_source_assertions':native['native_source_assertions'],'focused_host_tests':res.testsRun,
  'current_RTL_checks':rtl['checks'],'M_completed_1us_pulses':rtl['motion_pulses'],'O_completed_1us_pulses':rtl['output_pulses'],
  'historical_checks':{'six_axis_two_encoder_default':252,'ABI2_discovery':27,'permission':49},
  'strict_lint_passed':True,'verilog_2005_elaboration_passed':True,'real_Yosys_efinix_family_mapping':cells,
  'byte_preserved_historical_source_hashes_verified':True,
  'changed_hardware_sources':[],'changed_PCB_or_retained_copper':False,
  'target_MCU_firmware_compiled':False,'production_CNC3':False,'twelve_axis_runtime':False,
  'vendor_package_fit':False,'vendor_routed_timing':False,'physical_20ms_proof':False,
  'board_ERC_DRC_rerun_by_this_task':False,'manufacturing_ready':False,
  'conditional_20ms':native['conditional_20ms'],
  'remaining_engineering_and_physical_gates':[
   'Manufacturer/measurement qualification of TPS3851 maximum output-assertion delay, enable setup and startup',
   'Board CWD parasitic/leakage allowance and actual loaded logic/series-contact gate RC',
   'NO opening/NC closing over required internal ambient, actual LED currents and loads',
   'Complete DO/PWM/AO terminal withdrawal and every cold/partial-power ramp',
   'Target acquisition MCU firmware, epoch provisioning, watchdog self-test and actual four-link qualification',
   'Production pin constraints, package fit/place-and-route, current protocol/authority implementation and twelve-axis runtime'],
  'input_and_artifact_sha256':{rel(p):digest(p) for p in sorted(set(files))}}
 out.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'receipt':rel(out),'passed':True,'source_native_assertions':native['native_source_assertions'],'host_tests':res.testsRun,'RTL_checks':rtl['checks'],'hashed_files':len(receipt['input_and_artifact_sha256'])}))
if __name__=='__main__':main()
