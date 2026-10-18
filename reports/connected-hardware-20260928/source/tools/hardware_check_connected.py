"""Run the scoped connected-hardware checks and preserve their exact inputs.

This does not regenerate drawings, run PCB DRC or qualify physical hardware.
Existing evidence directories are never overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ('power_entry', 'core_converter', 'logic_power', 'field_power',
          'encoder_power', 'tx_six', 'rx_abz', 'sbc_power', 'power_sequence', 'digital_inputs')
TESTS = ('test_power_entry.py', 'test_power_entry_analysis.py', 'test_core_converter.py',
         'test_core_converter_analysis.py', 'test_logic_power.py', 'test_field_power.py',
         'test_encoder_power.py', 'test_tx_six.py', 'test_rx_abz.py', 'test_sbc_power.py',
         'test_power_sequence.py', 'test_digital_inputs.py', 'test_hardware_assembly.py')


def source_files():
    paths = {Path(__file__).resolve(), ROOT/'hardware/electrical-design.json'}
    for block in (*BLOCKS, 'controller_assembly'):
        folder = ROOT/'hardware'/block
        if not folder.is_dir():
            raise ValueError('Missing actual block: '+block)
        paths.update(p for p in folder.rglob('*') if p.is_file() and
                     not {'attempts', '__pycache__'} & set(p.parts) and
                     not p.name.endswith(('.lck', '.bak', '.kicad_prl')))
    for block in (*BLOCKS, 'assembly'):
        for kind in ('build', 'validate'):
            p = ROOT/'tools'/f'hardware_{kind}_{block}.py'
            if not p.is_file():raise ValueError('Missing tool: '+str(p))
            paths.add(p)
    paths.update(ROOT/'tests'/name for name in TESTS)
    paths.update(ROOT/'tools'/name for name in
                 ('hardware_build_tx_schematic.py','power_entry_analysis.py','core_converter_analysis.py','hardware_export_evidence.py'))
    for directory in ('power-entry','core-converter','sbc-power','power-sequence','digital-inputs','logic-power','field-power'):
        folder=ROOT/'research'/directory
        # Include manufacturer sources and the historical failure fixtures used
        # by the regression, not just summaries that refer outside the snapshot.
        paths.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for name in ('POWER_ENTRY_REVIEW','CORE_CONVERTER_REVIEW','FIELD_OUTPUT_PROTECTION_GAP'):
        p=ROOT/'research'/(name+'.md')
        if p.is_file():paths.add(p)
    for name in ('POWER_ENTRY','CORE_CONVERTER','LOGIC_POWER','FIELD_POWER','SBC_POWER',
                 'POWER_SEQUENCE','DIGITAL_INPUTS','CONNECTED_CONTROLLER'):
        p=ROOT/'reports'/(name+'.md')
        if p.is_file():paths.add(p)
    for p in paths:
        if not p.is_file():raise ValueError('Missing input: '+str(p))
    return sorted(paths)


def hashes(paths):
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir',required=True,
                        help='New output directory for immutable source snapshot, test log and review JSON')
    args=parser.parse_args()
    target=Path(args.evidence_dir).resolve()
    if target.exists():raise SystemExit('Refusing to overwrite existing evidence directory: '+str(target))
    paths=source_files()
    before=hashes(paths)
    target.mkdir(parents=True)
    copied={}
    for p in paths:
        name=p.relative_to(ROOT).as_posix()
        raw=p.read_bytes();dest=target/'source'/name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        copied[name]=hashlib.sha256(raw).hexdigest()
    export_run=subprocess.run([sys.executable,str(target/'source/tools/hardware_export_evidence.py'),
                               '--source-root',str(target/'source'),'--output-dir',str(target/'native-exports')],
                              cwd=target/'source',capture_output=True,text=True,timeout=180)
    (target/'native-export-log.txt').write_text(export_run.stdout+export_run.stderr,encoding='utf-8')
    export_receipt=target/'native-exports/summary.json'
    export_result=json.loads(export_receipt.read_text()) if export_receipt.exists() else {'checks_pass':False}
    # Execute only the copied sources, so concurrent workspace edits cannot enter
    # the test process. Each block checks its own exported circuit/contract;
    # assembly tests independently check the cross-sheet union and actual ERC.
    runner='''import json, sys, unittest
from pathlib import Path
suite=unittest.TestSuite()
loader=unittest.TestLoader()
counts={}
for name in json.loads(sys.argv[1]):
    cases=loader.discover(str(Path.cwd()/"tests"),pattern=name)
    counts[name]=cases.countTestCases()
    if counts[name]==0:raise RuntimeError("No tests discovered in "+name)
    suite.addTests(cases)
r=unittest.TextTestRunner(verbosity=2).run(suite)
Path(sys.argv[2]).write_text(json.dumps({"tests_run":r.testsRun,"failures":len(r.failures),
    "errors":len(r.errors),"skipped":len(r.skipped),"successful":r.wasSuccessful(),"module_counts":counts}))
raise SystemExit(0 if r.wasSuccessful() else 1)
'''
    start=time.monotonic()
    run=subprocess.run([sys.executable,'-c',runner,json.dumps(TESTS),str(target/'test-result.json')],
                       cwd=target/'source',capture_output=True,text=True,timeout=60)
    elapsed=time.monotonic()-start
    after=hashes(paths)
    copied_after={k:hashlib.sha256((target/'source'/k).read_bytes()).hexdigest() for k in copied}
    changed=sorted(k for k,v in before.items() if after[k]!=v or copied[k]!=v or copied_after[k]!=v)
    result=json.loads((target/'test-result.json').read_text()) if (target/'test-result.json').exists() else {
        'tests_run':0,'failures':0,'errors':1,'skipped':0,'successful':False}
    successful=(run.returncode==0 and result['successful'] and not changed and not result['skipped']
                and result['tests_run']>0 and export_run.returncode==0 and export_result.get('checks_pass') is True)
    review={'schema_version':1,'scope':'Connected hardware source/netlist/ERC and numerical checks only',
            'manufacturing_ready':False,'checks_pass':successful,'tests_run':result['tests_run'],
            'failures':result['failures'],'errors':result['errors'],'skipped':result['skipped'],
            'execution':'separate Python process inside copied source snapshot','process_exit_code':run.returncode,
            'fresh_native_exports_pass':export_run.returncode==0 and export_result.get('checks_pass') is True,
            'fresh_native_export_receipt':'native-exports/summary.json',
            'module_test_counts':result.get('module_counts',{}),
            'elapsed_s':elapsed,'test_modules':list(TESTS),'source_file_count':len(paths),
            'changed_during_snapshot_or_run':changed,'input_sha256':before,
            'not_proved':['complete controller circuit','PCB layout/DRC','device implementation and timing',
                          'regulator stability/transient response','physical safety/EMC/thermal qualification',
                          'complete manufactured price']}
    (target/'tests.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    (target/'source-inventory.json').write_text(json.dumps({'before':before,'copied':copied,'after':after,'copied_after':copied_after},indent=2)+'\n')
    (target/'review.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps({k:v for k,v in review.items() if k!='input_sha256'},indent=2))
    return 0 if successful else 1


if __name__=='__main__':raise SystemExit(main())
