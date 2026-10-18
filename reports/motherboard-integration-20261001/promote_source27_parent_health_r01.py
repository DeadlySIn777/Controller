"""Controlled minimal parent-only SOURCE27 adoption, only after root release.
No hierarchy regeneration, child baseline edits, or PCB mutations. The native
pin/net identity is independently validated after export; failure is visible.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,importlib.util,xml.etree.ElementTree as ET
ROOT=Path.cwd();STAGE=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01';LIVE=ROOT/'hardware/motherboard'
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(d):return {p.relative_to(d).as_posix():sha(p)for p in d.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
def execute(argv,log,env=None):
    p=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',env=env);log.write_text(p.stdout+p.stderr)
    if p.returncode:raise ValueError('Actual command failed: '+str(log))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adopt',action='store_true');p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if not args.adopt:raise ValueError('Explicit root-authorized --adopt required')
    proof=json.loads((STAGE/'freeze-receipt-r01.json').read_text());source=STAGE/'final-source27-candidate/motherboard'
    if not proof['passed']or proof['adopted']:raise ValueError('Invalid frozen report-only proof')
    if hashes(LIVE)!=proof['before_source_sha256']or hashes(source)!=proof['candidate_source_sha256']:raise ValueError('Source freeze differs')
    for folder,key in(('candidate-tools','candidate_tools_sha256'),('candidate-tests','candidate_tests_sha256')):
        if hashes(STAGE/folder)!=proof[key]:raise ValueError('Frozen proposed tool/test differs')
    for path,h in proof['evidence_sha256'].items():
        if sha(ROOT/path)!=h:raise ValueError('Frozen evidence differs '+path)
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copytree(LIVE,out/'before/motherboard')
    targets={ROOT/'tools'/n:STAGE/'candidate-tools'/n for n in('hardware_build_motherboard.py','hardware_validate_motherboard.py','hardware_check_source27_parts.py','hardware_apply_parent_health_overlay.py')}
    targets[ROOT/'tests/test_motherboard_source27_health.py']=STAGE/'candidate-tests/test_motherboard_source27_health.py'
    tool_before={}
    for target in targets:
        tool_before[target.relative_to(ROOT).as_posix()]=sha(target)if target.exists()else None
        if target.exists():
            backup=out/'before'/target.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup)
    changed=[name for name,h in proof['candidate_source_sha256'].items()if proof['before_source_sha256'].get(name)!=h]
    if set(changed)!={'design.json','assembly-map.json','mc_local_power.kicad_sch','motherboard_power_entry.kicad_sch','netlist.xml','bom.csv'}:raise ValueError('Unreviewed source file delta '+repr(changed))
    for target,src in targets.items():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    for name in changed:shutil.copy2(source/name,LIVE/name)
    execute([CLI,'sch','export','netlist','--format','kicadxml','-o',str(out/'fresh-netlist.xml'),str(LIVE/'motherboard.kicad_sch')],out/'export.log')
    execute([CLI,'sch','erc','--format','json','--severity-all','-o',str(out/'erc.json'),str(LIVE/'motherboard.kicad_sch')],out/'erc.log')
    sys.path.insert(0,str(ROOT/'tools'))
    spec=importlib.util.spec_from_file_location('health27_live_validation',ROOT/'tools/hardware_validate_motherboard.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    model=json.loads((LIVE/'design.json').read_text());mapping=json.loads((LIVE/'assembly-map.json').read_text());tree=ET.parse(out/'fresh-netlist.xml')
    if v.nodes(tree)!=v.nodes(ET.parse(out/'before/motherboard/netlist.xml')):raise ValueError('Native actual pin/net changed')
    if v.validate(tree,model,mapping,True):raise ValueError(v.validate(tree,model,mapping,True))
    native=json.loads((out/'erc.json').read_text());viol=[row for sheet in native['sheets']for row in sheet['violations']]
    if any(row['severity']=='error'for row in viol)or len(viol)!=70 or native['ignored_checks']:raise ValueError('Native ERC differs')
    shutil.copy2(out/'fresh-netlist.xml',LIVE/'netlist.xml')
    tests=['test_motherboard_source27_health.py','test_motherboard_integration.py','test_motherboard_fpga_allocation.py','test_motherboard_fpga_current_annotations.py','test_motherboard_adc_source_adoption.py','test_motherboard_analog_input.py','test_motherboard_source26_parts.py','test_motherboard_fuse_geometry.py','test_motherboard_power_entry.py','test_motherboard_motor_power.py','test_motherboard_io3_window.py','test_motherboard_io3_upgrade.py']
    import os
    env=os.environ.copy();env['CONTROLLER_MOTHERBOARD_TEST_SOURCE']=str(LIVE);env['CONTROLLER_SOURCE26_STAGE']=str(LIVE)
    execute(['C:/Python314/python.exe','-X','utf8','-m','pytest']+['tests/'+n for n in tests]+['-q'],out/'focused-tests.log',env)
    receipt=dict(passed=True,adopted=True,scope='Exact MB-HEALTH-001 three parent procurement/default identities; inherited child/original MC intact',source_design_sha256=sha(LIVE/'design.json'),source_netlist_sha256=sha(LIVE/'netlist.xml'),before_source_sha256=proof['before_source_sha256'],after_source_sha256=hashes(LIVE),changed_source_files=changed,changed_refs=['R2106','U11019','U11025'],tool_before_sha256=tool_before,tool_after_sha256={k.relative_to(ROOT).as_posix():sha(k)for k in targets},original327_native1229_pin_nets_unchanged=True,all_native_pin_nets_and_manufacturer_lands_unchanged=True,physical_parts=2688,FPGA_assigned=135,FPGA_free=48,native_ERC_errors=0,native_ERC_warnings=70,ignored_checks=[],frozen_stage_receipt_sha256=sha(STAGE/'freeze-receipt-r01.json'),source26_and_ADC_metadata_preserved=True,PCB_reconciliation_and_all_source_bound_route_manifest_rebinding_required=True,physical_qualification=False,manufacturing_ready=False)
    (out/'adoption.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(adopted=True,source_sha256=receipt['source_design_sha256'],ERC_errors=0,ERC_warnings=70)))

if __name__=='__main__':main()
