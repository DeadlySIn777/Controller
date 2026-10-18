"""Freeze r0.2 permission inputs, re-export privately and test their copies."""
import datetime,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.hardware_export_evidence import canonical_netlist,canonical_erc
DEST=ROOT/'reports/board-completion-20260930/mc-permission-r02'
if DEST.exists():raise SystemExit('Refusing to overwrite immutable evidence')
names=['tools/hardware_build_mc_permission.py','tools/hardware_validate_mc_permission.py','tests/test_mc_permission.py',
       'tools/hardware_build_assembly.py','tools/hardware_build_tx_schematic.py','tools/hardware_export_evidence.py',
       'tmp/check_mc_permission_r02.py']
names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'hardware/mc_permission').rglob('*')
          if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.kicad_prl','.pdf')]
names += [f'research/machine-permission/{n}{s}' for n in ('sn74lvc1g11','sn74lvc2g08','sn74lvc2g74','sn74lvc2g04','sn74lvc2g32')
          for s in ('.pdf','-permission-pin-source.txt')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={n:sha(ROOT/n) for n in sorted(set(names))}
spec=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/docs/interface-spec/04-safety-power-timing.md')
spec_hash=sha(spec)
for n in before:
    dst=DEST/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dst)
private=DEST/'native-workspace/hardware/mc_permission'
shutil.copytree(DEST/'source/hardware/mc_permission',private)
cli='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
commands=[[cli,'sch','export','netlist','--format','kicadxml','--output',str(private/'netlist.xml'),str(private/'mc_permission.kicad_sch')],
          [cli,'sch','erc','--format','json','--severity-all','--output',str(private/'erc.json'),str(private/'mc_permission.kicad_sch')]]
native=[]
for cmd in commands:
    p=subprocess.run(cmd,cwd=private,capture_output=True,text=True,encoding='utf-8',timeout=60)
    native.append(dict(argv=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
stored=DEST/'source/hardware/mc_permission'
matches={'netlist':canonical_netlist((private/'netlist.xml').read_bytes())==canonical_netlist((stored/'netlist.xml').read_bytes()),
         'erc':canonical_erc((private/'erc.json').read_bytes())==canonical_erc((stored/'erc.json').read_bytes())}
runner='''import pathlib,json,unittest
s=unittest.defaultTestLoader.discover('tests',pattern='test_mc_permission.py')
if s.countTestCases()!=19:raise RuntimeError('Unexpected test count')
r=unittest.TextTestRunner(verbosity=2).run(s)
pathlib.Path('test-result.json').write_text(json.dumps(dict(tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful())))
raise SystemExit(0 if r.wasSuccessful() else 1)
'''
p=subprocess.run([sys.executable,'-X','utf8','-c',runner],cwd=DEST/'source',capture_output=True,text=True,encoding='utf-8',timeout=60)
(DEST/'tests.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
test=json.loads((DEST/'source/test-result.json').read_text())
validator=subprocess.run([sys.executable,'-X','utf8','tools/hardware_validate_mc_permission.py','--output',str(DEST/'candidate-validation.json')],
                         cwd=DEST/'source',capture_output=True,text=True,encoding='utf-8',timeout=20)
valid=json.loads((DEST/'candidate-validation.json').read_text())
after={n:sha(ROOT/n) for n in before};copied={n:sha(DEST/'source'/n) for n in before}
changed=[n for n in before if before[n]!=after[n] or before[n]!=copied[n]]
violations=[v for sheet in json.loads((private/'erc.json').read_text())['sheets'] for v in sheet['violations']]
okay=not changed and spec_hash==sha(spec) and all(matches.values()) and not violations and all(n['returncode']==0 for n in native) and p.returncode==0 and test['successful'] and validator.returncode==0 and valid['passed']
receipt=dict(schema_version=1,captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks_pass=okay,
             scope='MC r0.2 permission/OPI and actual-SET1-qualified falling-edge sticky watchdog trip circuit',
             physical_parts=56,source_count=len(before),input_sha256=before,copied_sha256=copied,after_sha256=after,
             changed_during_run=changed,native_exports_match=matches,native_runs=native,native_erc_violation_count=len(violations),
             tests=test,host_ideal_digital_checks=valid['host_ideal_digital_checks'],
             frozen_IS1_sha256_before=spec_hash,frozen_IS1_sha256_after=sha(spec),
             manufacturing_ready=False,physical_measurement=False,interface_agreed=False,
             evidence_class='manufacturer primary-pin extraction + host ideal-digital source-net simulation + native netlist/ERC',
             open_gates=valid['open_gates'])
(DEST/'review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if 'sha256' not in k and k!='native_runs'},indent=2))
raise SystemExit(0 if okay else 1)
