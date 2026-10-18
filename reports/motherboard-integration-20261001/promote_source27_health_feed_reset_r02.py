"""Root-authorized minimal SOURCE27 transaction; no hierarchy regeneration.
The report-only stage is not an adoption. Root must explicitly release this
transaction after the retained PCB/power proof closes.
"""
from pathlib import Path
import argparse,json,hashlib,shutil,subprocess,sys,importlib.util,xml.etree.ElementTree as ET,os
ROOT=Path.cwd();P=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';LIVE=ROOT/'hardware/motherboard';CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(folder):return{p.relative_to(folder).as_posix():sha(p)for p in folder.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
def execute(args,log,env=None):
 run=subprocess.run(args,capture_output=True,text=True,encoding='utf8',env=env);log.write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Actual command failed '+str(log))
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--adopt',action='store_true');parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
 if not args.adopt:raise ValueError('Explicit root release and --adopt required')
 frozen=json.loads((P/'freeze-receipt-r02.json').read_text());D=P/'candidate/motherboard'
 if not frozen['passed']or frozen['adopted']:raise ValueError('A report-only frozen reviewed candidate is required')
 if hashes(LIVE)!=frozen['before_source_sha256']or hashes(D)!=frozen['candidate_source_sha256']:raise ValueError('Exact source freeze changed')
 if hashes(P/'candidate-tools')!=frozen['candidate_tools_sha256']or hashes(P/'candidate-tests')!=frozen['candidate_tests_sha256']:raise ValueError('Frozen tool/test candidate changed')
 for file,h in frozen['evidence_sha256'].items():
  if sha(ROOT/file)!=h:raise ValueError('Frozen independent evidence changed '+file)
 changed={name for name,h in frozen['candidate_source_sha256'].items()if frozen['before_source_sha256'].get(name)!=h}
 expected={'design.json','assembly-map.json','mc_local_power.kicad_sch','motherboard_power_entry.kicad_sch','netlist.xml','bom.csv','fp-lib-table','sym-lib-table','CNC_MB_FeedReset.kicad_sym','CNC_MB_FeedReset.pretty/TI_DBV5.kicad_mod','CNC_MB_FeedReset.pretty/TI_DBV6.kicad_mod'}
 if changed!=expected:raise ValueError('Unreviewed native source file scope '+repr(changed))
 out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copytree(LIVE,out/'before/motherboard')
 tools={ROOT/'tools'/name:P/'candidate-tools'/name for name in frozen['candidate_tools_sha256']}
 tests={ROOT/'tests'/name:P/'candidate-tests'/name for name in frozen['candidate_tests_sha256']}
 original={}
 for target,source in {**tools,**tests}.items():
  original[target.relative_to(ROOT).as_posix()]=sha(target)if target.exists()else None
  if target.exists():backup=out/'before'/target.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup)
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 for name in sorted(changed):target=LIVE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/name,target)
 execute([CLI,'sch','export','netlist','--format','kicadxml','-o',str(out/'actual-native.xml'),str(LIVE/'motherboard.kicad_sch')],out/'export.log')
 execute([CLI,'sch','erc','--format','json','--severity-all','-o',str(out/'actual-native-erc.json'),str(LIVE/'motherboard.kicad_sch')],out/'erc.log')
 sys.path[:0]=[str(ROOT/'tools')]
 import hardware_validate_motherboard as v
 v.ROOT=ROOT;v.OUT=LIVE
 model=json.loads((LIVE/'design.json').read_text());mapping=json.loads((LIVE/'assembly-map.json').read_text());tree=ET.parse(out/'actual-native.xml');before=ET.parse(out/'before/motherboard/netlist.xml');a,b=v.nodes(tree),v.nodes(before)
 deltas={k:(n,a.get(k))for k,n in b.items()if n!=a.get(k)}
 expected_deltas={('U11032','6'):('/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_A'),('U11034','6'):('/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B')}
 if deltas!=expected_deltas:raise ValueError('Actual native existing endpoint delta differs')
 errors=v.validate(tree,model,mapping,True)
 if errors:raise ValueError(errors)
 erc=json.loads((out/'actual-native-erc.json').read_text());viol=[r for sheet in erc['sheets']for r in sheet['violations']]
 if erc['ignored_checks']or len(viol)!=70 or any(r['severity']=='error'for r in viol):raise ValueError('Actual native ERC differs')
 shutil.copy2(out/'actual-native.xml',LIVE/'netlist.xml')
 env=os.environ.copy();env['CONTROLLER_MOTHERBOARD_TEST_SOURCE']=str(LIVE);env['CONTROLLER_SOURCE26_STAGE']=str(LIVE)
 names=['test_motherboard_source27_health.py','test_motherboard_source27_feed_reset.py','test_motherboard_integration.py','test_motherboard_adc_source_adoption.py','test_motherboard_fpga_allocation.py','test_motherboard_fpga_current_annotations.py','test_motherboard_analog_input.py','test_motherboard_source26_parts.py','test_motherboard_fuse_geometry.py','test_motherboard_power_entry.py','test_motherboard_motor_power.py','test_motherboard_io3_window.py','test_motherboard_io3_upgrade.py','test_motor_feed_reset.py']
 execute(['C:/Python314/python.exe','-X','utf8','-m','pytest']+['tests/'+name for name in names]+['-q'],out/'focused-tests.log',env)
 receipt=dict(passed=True,adopted=True,source_design_sha256=sha(LIVE/'design.json'),source_netlist_sha256=sha(LIVE/'netlist.xml'),before_source_sha256=frozen['before_source_sha256'],after_source_sha256=hashes(LIVE),changed_source_files=sorted(changed),changed_existing_references=frozen['changed_existing_references'],new_references=frozen['new_references'],actual_existing_pin_changes=[dict(reference=k[0],pin=k[1],old=n[0],new=n[1])for k,n in deltas.items()],physical_parts=2698,purchased_fitted_parts=2652,bare_features=44,DNP_footprints=2,original_327_1229_pin_maps_and_FPGA_135_48_preserved=True,source26_ADC_and_fuse_qualification_retained=True,native_ERC_errors=0,native_ERC_warnings=70,no_ignored_checks=True,tool_test_before_sha256=original,tool_test_after_sha256={target.relative_to(ROOT).as_posix():sha(target)for target in {**tools,**tests}},immutable_stage_sha256=sha(P/'freeze-receipt-r02.json'),PCB_exact_pins_lands_parts_and_all_Source_bound_receipts_rebinding_required=True,physical_qualification=False,manufacturing_ready=False)
 (out/'adoption.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(adopted=True,source=receipt['source_design_sha256'],native_ERC_errors=0,native_ERC_warnings=70,parts=2698)))
if __name__=='__main__':main()
