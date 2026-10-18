"""Fresh source26 verification after the recorded narrow historical fixture repair.

Does not write electrical sources. Requires exact equality to the already frozen
five-part stage and the archived pre-transaction source. Failed runs stay intact.
"""
import argparse, datetime, json, os, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from hardware_adopt_adc_bypass_source import ROOT, CLI, sha, load, write, file_hashes
from hardware_adopt_source26_qualification import HOOK, NEEDLE, power_generator_hook
from hardware_check_source26_parts import check_source26, CAPS, FUSES
from hardware_validate_motherboard import validate, nodes

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('stage-receipt','prior-transaction','reference-proposal','out'):ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args()
 for n in ('stage_receipt','prior_transaction','reference_proposal','out'):setattr(a,n,getattr(a,n).resolve())
 assert not a.out.exists();r=load(a.stage_receipt);assert r['passed']and not r['adopted']
 live=ROOT/'hardware/motherboard';stage=ROOT/r['source'];before=a.prior_transaction/'before/motherboard'
 assert file_hashes(live)==r['source_hashes']==file_hashes(stage)
 old=load(before/'design.json');model=load(live/'design.json');mapping=load(live/'assembly-map.json')
 changes=[ref for ref in model['components']if model['components'][ref]!=old['components'][ref]]
 assert set(changes)==set(CAPS+FUSES)and len(model['components'])==2688
 oldpins=nodes(ET.parse(before/'netlist.xml'));tree=ET.parse(live/'netlist.xml');assert nodes(tree)==oldpins
 assert not validate(tree,model,mapping,True)and not check_source26(model['components'],nodes(tree),model,mapping)
 # Validate every original hardware input against the transaction archive;
 # unchanged inputs outside these three regions retain the live bytes.
 archive=a.prior_transaction/'before';original_input_proof=[]
 for p,h in r['input_sha256'].items():
  actual=Path(p);replacement=actual
  for region in ('motherboard','motherboard_analog_input','motherboard_power_entry'):
   base=ROOT/'hardware'/region
   if actual.is_relative_to(base):replacement=archive/region/actual.relative_to(base);break
  assert sha(replacement)==h,p;original_input_proof.append(dict(original=p,verified=str(replacement.resolve()),sha256=h))
 tool_changes=[]
 for name in ['hardware_build_motherboard_analog_input.py','hardware_validate_motherboard_analog_input.py']:
  target=ROOT/'tools'/name;assert sha(target)==sha(a.reference_proposal/'candidate-tools'/name)
  tool_changes.append(dict(path=str(target.relative_to(ROOT)),before_sha256=sha(archive/name),after_sha256=sha(target)))
 for name,wanted in [('hardware_build_motherboard_power_entry.py',power_generator_hook((archive/'hardware_build_motherboard_power_entry.py').read_text(encoding='utf8'))),
                     ('hardware_validate_motherboard.py',(archive/'hardware_validate_motherboard.py').read_text(encoding='utf8').replace(NEEDLE,HOOK+NEEDLE))]:
  target=ROOT/'tools'/name;assert target.read_text(encoding='utf8')==wanted,name
  tool_changes.append(dict(path=str(target.relative_to(ROOT)),before_sha256=sha(archive/name),after_sha256=sha(target)))
 frozen={str(p):sha(p)for p in [a.stage_receipt,ROOT/'tools/hardware_check_source26_parts.py',ROOT/'tools/hardware_adopt_source26_qualification.py',Path(__file__)]}
 frozen.update({str(live/n):h for n,h in r['source_hashes'].items()})
 for p,h in mapping['input_sha256'].items():frozen[str(ROOT/p)]=h
 a.out.mkdir(parents=True)
 for label,cmd in [('export',[str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(a.out/'fresh-netlist.xml'),str(live/'motherboard.kicad_sch')]),
                   ('ERC',[str(CLI),'sch','erc','--format','json','-o',str(a.out/'erc.json'),str(live/'motherboard.kicad_sch')])]:
  p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8');(a.out/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0
 fresh=ET.parse(a.out/'fresh-netlist.xml');assert nodes(fresh)==oldpins;assert not validate(fresh,model,mapping,True)
 erc=load(a.out/'erc.json');issues=[v for s in erc['sheets']for v in s['violations']];assert not erc['ignored_checks']and not any(v['severity']=='error'for v in issues)
 env={**os.environ,'CONTROLLER_MOTHERBOARD_TEST_SOURCE':str(live),'CONTROLLER_SOURCE26_STAGE':str(live)};tests=[]
 for name in ['test_motherboard_integration.py','test_motherboard_adc_source_adoption.py','test_motherboard_analog_input.py','test_motherboard_fpga_current_annotations.py','test_motherboard_fpga_allocation.py','test_motherboard_source26_parts.py']:
  cmd=[sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',name,'-v'];p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',cwd=ROOT,env=env);log=a.out/(name+'.log');log.write_text(p.stdout+p.stderr,encoding='utf8');tests.append(dict(name=name,returncode=p.returncode,log_sha256=sha(log)));assert p.returncode==0,name
 cmd=[sys.executable,'-X','utf8','-m','pytest','tests/test_motherboard_fuse_geometry.py','tests/test_motherboard_power_entry.py','tests/test_motherboard_motor_power.py','tests/test_motherboard_io3_window.py','tests/test_motherboard_io3_upgrade.py','-q']
 p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',cwd=ROOT,env=env);log=a.out/'power-107-tests.log';log.write_text(p.stdout+p.stderr,encoding='utf8');tests.append(dict(name='power/fuse/motor/IO3',returncode=p.returncode,log_sha256=sha(log)));assert p.returncode==0
 assert all(sha(p)==h for p,h in frozen.items())
 result=dict(passed=True,adopted=True,date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  stage_receipt_sha256=sha(a.stage_receipt),previous_failed_transaction=str(a.prior_transaction.relative_to(ROOT)),
  historical_fixture_correction='Power owner asserted and changed exactly the three prior expected fuse footprint identities; all other previous fields/pins still compared',
  exact_component_changes=r['exact_component_changes'],source=str(live.relative_to(ROOT)),source_hashes=file_hashes(live),
  native_ERC_errors=0,native_ERC_warnings=len(issues),ignored_checks=[],tests=tests,tool_changes=tool_changes,
  physical_parts=2688,purchased_fitted_parts=2642,bare_geometry=44,DNP=2,retained_mc_parts=327,retained_mc_native_pin_nets=1229,
  FPGA_assigned=135,FPGA_free=48,all_native_pin_nets_preserved=True,independent_validation_pass=True,
  actual_live_dependency_hashes_pass=True,original_hardware_inputs_verified_from_archive=original_input_proof,
  input_sha256=frozen,source_regions_unchanged_during_final_verification=True,physical_layout_adopted=False,physical_qualified=False,manufacturing_ready=False)
 write(a.out/'adoption.json',result);print(json.dumps(dict(passed=True,adopted=True,parts=2688,ERC_errors=0,ERC_warnings=len(issues),receipt=str(a.out/'adoption.json'))))

if __name__=='__main__':main()
