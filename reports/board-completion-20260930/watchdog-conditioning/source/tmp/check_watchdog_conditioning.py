"""Freeze only owned candidate inputs and re-export/tests from copied sources."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.hardware_export_evidence import canonical_netlist, canonical_erc

DEST=ROOT/'reports/board-completion-20260930/watchdog-conditioning'
if DEST.exists():
    raise SystemExit('Refusing to overwrite immutable evidence folder')
BLOCK='hardware/is1_watchdogs/startup_conditioning_r0_2'
names=['tools/hardware_build_watchdog_conditioning.py', 'tools/hardware_validate_watchdog_conditioning.py',
       'tools/watchdog_conditioning_analysis.py', 'tools/hardware_build_tx_schematic.py',
       'tools/hardware_build_logic_power.py', 'tools/hardware_export_evidence.py',
       'tests/test_watchdog_conditioning.py', 'tests/test_watchdog_conditioning_analysis.py',
       'tmp/check_watchdog_conditioning.py']
for folder in (BLOCK,'research/is1-watchdogs'):
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.kicad_prl', '.pdf')]
names += ['research/fpga-core/'+n for n in ('sn74lvc1g08.pdf','sn74lvc1g08.txt',
                                           'trion20-ds-v6.0.pdf','trion20-ds-v6.0.txt')]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
before={n:sha(ROOT/n) for n in sorted(set(names))}
spec=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/docs/interface-spec/04-safety-power-timing.md')
spec_before=sha(spec)
prior=ROOT/'reports/is1-watchdogs-drawing-final-20260930/source/hardware/is1_watchdogs'
historical={p.relative_to(prior).as_posix():sha(p) for p in prior.rglob('*') if p.is_file()}
original_unchanged_before=all(sha(ROOT/'hardware/is1_watchdogs'/n)==h for n,h in historical.items())
for name in before:
    path=DEST/'source'/name
    path.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/name,path)
work=DEST/'native-workspace'/BLOCK
shutil.copytree(DEST/'source'/BLOCK,work)
cli='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
commands=[
    [cli,'sch','export','netlist','--format','kicadxml','--output',str(work/'netlist.xml'),str(work/'is1_watchdogs.kicad_sch')],
    [cli,'sch','erc','--format','json','--severity-all','--output',str(work/'erc.json'),str(work/'is1_watchdogs.kicad_sch')],
]
runs=[]
for command in commands:
    p=subprocess.run(command,cwd=work,capture_output=True,text=True,encoding='utf-8',timeout=60)
    runs.append(dict(argv=command,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
stored=DEST/'source'/BLOCK
matches={'netlist':canonical_netlist((stored/'netlist.xml').read_bytes())==canonical_netlist((work/'netlist.xml').read_bytes()),
         'erc':canonical_erc((stored/'erc.json').read_bytes())==canonical_erc((work/'erc.json').read_bytes())}
runner='''import json,pathlib,unittest
suite=unittest.defaultTestLoader.discover('tests',pattern='test_watchdog_conditioning*.py')
if suite.countTestCases()!=50: raise RuntimeError('Unexpected test discovery count')
r=unittest.TextTestRunner(verbosity=2).run(suite)
pathlib.Path('test-result.json').write_text(json.dumps(dict(tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful())))
raise SystemExit(0 if r.wasSuccessful() else 1)
'''
p=subprocess.run([sys.executable,'-X','utf8','-c',runner],cwd=DEST/'source',capture_output=True,text=True,encoding='utf-8',timeout=60)
(DEST/'tests.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
test=json.loads((DEST/'source/test-result.json').read_text())
analysis=subprocess.run([sys.executable,'-X','utf8','tools/watchdog_conditioning_analysis.py','--output',str(DEST/'conditioning-analysis.json')],
                        cwd=DEST/'source',capture_output=True,text=True,encoding='utf-8',timeout=15)
after={n:sha(ROOT/n) for n in before}
copied={n:sha(DEST/'source'/n) for n in before}
changed=[n for n in before if before[n]!=after[n] or before[n]!=copied[n]]
erc=json.loads((work/'erc.json').read_text())
violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
original_unchanged_after=all(sha(ROOT/'hardware/is1_watchdogs'/n)==h for n,h in historical.items())
okay=not changed and all(matches.values()) and not violations and all(r['returncode']==0 for r in runs) and p.returncode==0 and test['successful'] and not test['skipped'] and analysis.returncode==0 and spec_before==sha(spec) and original_unchanged_before and original_unchanged_after
review=dict(schema_version=1,captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks_pass=okay,
            scope='Separate 29-part proposed IS-2 watchdog conditioning circuit; original IS-1 preserved',
            interface_revision='IS-2-PROPOSED',interface_agreed=False,manufacturing_ready=False,
            assembly_integrated=False,startup_defaults_qualified=False,complete_permission_chain=False,
            physical_qualification=False,source_count=len(before),input_sha256=before,copied_sha256=copied,
            after_sha256=after,changed_during_run=changed,native_exports_match=matches,native_runs=runs,
            native_erc_violation_count=len(violations),tests=test,
            frozen_IS1_sha256_before=spec_before,frozen_IS1_sha256_after=sha(spec),
            historical_r01_unchanged_before=original_unchanged_before,historical_r01_unchanged_after=original_unchanged_after,
            historical_r01_sha256=historical,
            open_qualification=['IS-2 agreement','TPS3851 SET1/WDI maximum pin leakage','GPIO loaded drive strength',
                                'reset guard loaded fanout and power sequencing','analog input slew/glitch/duplicate WDI edges',
                                'full permission/arm/trip/self-test integration','nominal-only SET1 setup maximum',
                                'CWD leakage/parasitics and physical20ms','routed PCB and assembly'])
(DEST/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in review.items() if 'sha256' not in k and k!='native_runs'},indent=2))
raise SystemExit(0 if okay else 1)
