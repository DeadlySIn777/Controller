"""Freeze persisted native and adversarial evidence for both strict wrappers."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
import pcbnew
import hardware_route_selected_additive_r03 as selected
import hardware_check_return_corridors_r02 as strict
import hardware_route_owned_bypass_loops_r02 as hf

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,data):Path(p).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 out=a.out.resolve()
 if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('Fresh immutable report required')
 out.mkdir(parents=True);frozen={};cases=[]
 def freeze(p):frozen[str(Path(p).resolve())]=sha(p)
 for p in [Path(__file__),Path(selected.__file__),Path(strict.__file__),Path(hf.__file__),
   ROOT/'tools/hardware_route_owned_bypass_loops.py',ROOT/'tools/hardware_route_selected_additive_r02.py',
   ROOT/'tools/hardware_check_return_corridors.py',ROOT/'tools/hardware_validate_ordinary_router_fixture_r03.py',
   ROOT/'tests/test_owned_bypass_annuli.py',ROOT/'tests/test_motherboard_return_corridors_r02.py']:
  freeze(p)
 selected.checked_dependencies();hf.checked_dependencies()
 prior=ROOT/'reports/motherboard-return-corridor-20261001/native-r01';freeze(prior/'receipt.json')
 rows={'/DATA':{'return_net':'/LOGIC_GND','reference_layers':{'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},
  'reference_corridor_margin_mm':.10,'allow_vias':True,'via_diameter_mm':.60,'via_drill_mm':.30,'return_stitch_distance_mm':1.}}
 for case in read(prior/'receipt.json')['native_cases']:
  folder=prior/case['kind'];path=folder/'native.kicad_pcb';freeze(path)
  if sha(path)!=case['board_sha256']:raise ValueError('Frozen native fixture changed')
  b=pcbnew.LoadBoard(str(path));b.BuildConnectivity()
  ids={t.m_Uuid.AsString()for t in b.GetTracks()if t.GetNetname()=='/DATA'}
  accepted=True;reason=None;proof=None
  try:proof=strict.return_corridor_check(b,ids,rows)
  except ValueError as error:accepted=False;reason=str(error)
  if accepted!=case['expected_acceptance']:raise ValueError('Native fixture expectation changed '+case['kind'])
  cases.append({'case':'ordinary_'+case['kind'],'accepted':accepted,'expected_acceptance':case['expected_acceptance'],
   'board_sha256':sha(path),'native_DRC_regular':case['actual_native_drc_regular'],
   'ignored_checks':case['actual_native_ignored'],'proof':proof,'rejection':reason})
 actual=ROOT/'reports/motherboard-ordinary-routing-20261001/actual-router-fixture-r03-annulus-r01/receipt.json'
 freeze(actual);actual_receipt=read(actual)
 if not actual_receipt['passed']or not actual_receipt['actual_flashed_and_native_connected_reference_annuli_required']:
  raise ValueError('Actual interchange fixture not qualified with stronger checker')
 hf_cases=ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-strict-final-proof-r04';freeze(hf_cases/'review.json')
 if not read(hf_cases/'review.json')['passed']:raise ValueError('Actual strict HF fixtures not passed')
 # Remove one actual filled reference resource and persist that native state.
 # It cannot be accepted merely because the drill spans a defined zone layer.
 # This intentionally invalid fixture must not be automatically refilled;
 # doing so would repair the fault instead of testing the absent resource.
 fault=out/'missing_hf_reference_annulus';fault.mkdir()
 origin=hf_cases/'top/owned-bypass-loop-candidate.kicad_pcb';freeze(origin)
 b=pcbnew.LoadBoard(str(origin));b.BuildConnectivity();receipt=read(hf_cases/'top/receipt.json')
 manifest=read(ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-fixture-r08/top/owners.json')
 qualified=hf.actual_receiving_return_anchors(b,receipt,manifest)
 near={p['uuid']for row in qualified for p in row['physical_reference_anchors']}
 for zone in b.Zones():
  if zone.IsOnLayer(pcbnew.In4_Cu):zone.UnFill()
 path=fault/'native.kicad_pcb';pcbnew.SaveBoard(str(path),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(origin.with_suffix(ext),path.with_suffix(ext))
 run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--format','json','-o',str(fault/'drc.json'),str(path)],capture_output=True,text=True)
 (fault/'command.log').write_text(run.stdout+run.stderr,encoding='utf8')
 if run.returncode:raise ValueError('Native missing-annulus fixture did not execute')
 b=pcbnew.LoadBoard(str(path));b.BuildConnectivity();flags=[]
 for v in b.GetTracks():
  if v.m_Uuid.AsString()in near:
   flags.append({'uuid':v.m_Uuid.AsString(),'spans_In4':v.IsOnLayer(pcbnew.In4_Cu),
    'actually_flashed_In4':v.FlashLayer(pcbnew.In4_Cu),
    'native_connected_In4':b.GetConnectivity().IsConnectedOnLayer(v,pcbnew.In4_Cu)})
 if not flags or any(v['native_connected_In4']for v in flags):raise ValueError('Native missing-annulus fault was not actually induced')
 rejection=None
 try:hf.actual_receiving_return_anchors(b,receipt,manifest)
 except ValueError as error:rejection=str(error)
 if not rejection:raise ValueError('Actual missing HF reference annulus was accepted')
 drc=read(fault/'drc.json')
 if drc.get('ignored_checks'):raise ValueError('Ignored checks in actual negative fixture')
 cases.append({'case':'HF_missing_actual_reference_annulus','accepted':False,'expected_acceptance':False,
  'board_sha256':sha(path),'actual_native_flags':flags,'native_DRC_regular':len(drc['violations']),
  'ignored_checks':drc.get('ignored_checks',[]),'rejection':rejection})
 # Use the stricter wrapper in the real native additive test implementation.
 selected.install();sys.path.insert(0,str(ROOT/'tests'))
 import unittest
 suite=unittest.TestSuite()
 for name in ['test_motherboard_return_corridors_r02','test_owned_bypass_annuli','test_selected_additive_routing_r02_native']:
  suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
 with(out/'native-tests.log').open('w',encoding='utf8')as log:
  result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
 if not result.wasSuccessful()or result.skipped:raise ValueError('Strict native wrapper regression failed or skipped')
 if any(sha(p)!=digest for p,digest in frozen.items()):raise ValueError('Frozen wrapper inputs changed')
 write(out/'review.json',{'passed':True,'source_electrical_architecture_modified':False,
  'frozen_inputs':frozen,'ordinary_persisted_native_cases':cases[:8],
  'HF_persisted_cases':read(hf_cases/'review.json')['native_cases'],
  'additional_actual_missing_annulus_case':cases[8],
  'actual_DSN_SES_native_additive_interchange_receipt':str(actual),'actual_DSN_SES_receipt_sha256':sha(actual),
  'actual_DSN_SES_ordinary_missing_joins':actual_receipt['uncapped_missing_joins'],
  'native_regression_tests':result.testsRun,'native_tests_passed':True,'native_tests_skipped':0,
  'ordinary_wrapper_dependencies':selected.checked_dependencies(),'HF_wrapper_dependencies':hf.checked_dependencies(),
  'current_controller_ordinary_routing_executed':False,'manufacturing_ready':False,
  'awaiting_frozen_actual_controller_reference_plane_receipt':True})
 print(json.dumps({'passed':True,'native_tests':result.testsRun,'persisted_cases':len(cases)+6,
  'actual_interchange_native_DRC':actual_receipt['native_drc'],'manufacturing_ready':False}))

if __name__=='__main__':main()
