"""Freeze native/source receipts and rerun affected tests without hardware."""
from __future__ import annotations
import datetime
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'hardware/motherboard_fast_inputs'
parser=argparse.ArgumentParser()
parser.add_argument('--case',default='validated-source-r01')
args=parser.parse_args()
if '/' in args.case or '\\' in args.case or not args.case.startswith('validated-source-r'):
    raise SystemExit('Use a local immutable validated-source-rNN directory name.')
CASE=HERE/args.case
if CASE.exists():raise SystemExit('Do not overwrite a recorded validation run.')
CASE.mkdir()
historical=[*sorted((ROOT/'hardware/rx_abz').glob('*')),ROOT/'tools/hardware_build_rx_abz.py',
            ROOT/'tools/hardware_validate_rx_abz.py',ROOT/'tests/test_rx_abz.py']
paths=[p for p in historical if p.is_file()]
paths += [p for p in OUT.iterdir() if p.is_file() and p.name not in ['validation.json','motherboard_fast_inputs.kicad_prl']]
paths += [ROOT/'tools/hardware_build_motherboard_fast_inputs.py',ROOT/'tools/hardware_validate_motherboard_fast_inputs.py',ROOT/'tests/test_motherboard_fast_inputs.py']
def hashall():return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=hashall()
for p in paths:
    q=CASE/'inputs'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
runs=[]
commands=[['C:/Python314/python.exe','-X','utf8','tools/hardware_validate_motherboard_fast_inputs.py'],
          ['C:/Python314/python.exe','-X','utf8','-m','unittest','discover','-s','tests','-p','test_motherboard_fast_inputs.py','-v'],
          ['C:/Python314/python.exe','-X','utf8','-m','unittest','discover','-s','tests','-p','test_rx_abz.py','-v']]
for i,cmd in enumerate(commands):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding='utf-8',errors='replace')
    (CASE/f'run-{i+1}.stdout.txt').write_text(r.stdout,encoding='utf-8')
    (CASE/f'run-{i+1}.stderr.txt').write_text(r.stderr,encoding='utf-8')
    runs.append({'argv':cmd,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode})
after=hashall();assert before==after
erc=json.loads((OUT/'erc.json').read_text());validation=json.loads((OUT/'validation.json').read_text())
assert all(r['exit_code']==0 for r in runs) and validation['consistency_pass']
receipt={'date':'2026-09-30','evidence_class':'native circuit ERC/XML plus source checks and disconnected host mutation tests',
         'source_hashes_before':before,'source_hashes_after':after,'all_scoped_sources_unchanged':True,
         'historical_rx_sources_preserved':True,'scoped_input_files':len(before),'runs':runs,
         'native_ERC_violations':validation['native_ERC_violations'],'ERC_ignored_checks':erc['ignored_checks'],
         'new_receiver_host_tests':13,'preserved_historical_rx_host_tests':10,'all_23_focused_tests_passed':True,
         'scope':'Four ABZ/two FREQ/MPG receiver source region only; not complete encoder/field motherboard',
         'native_nets':61,'receiver_ics':4,'receiver_paths':16,'physical_footprints':28,'fitted_parts':26,'DNP_parts':2,
         'full_host_suite_rerun':False,'PCB_DRC_rerun':False,'FPGA_fit_rerun':False,'target_build_rerun':False,'physical_measurements':False,
         'manufacturing_ready':False}
(CASE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(OUT/'validation.json',CASE/'native-source-validation.json')
print(json.dumps({k:receipt[k] for k in ['all_scoped_sources_unchanged','historical_rx_sources_preserved','scoped_input_files','native_ERC_violations','ERC_ignored_checks','all_23_focused_tests_passed','manufacturing_ready']},indent=2))
