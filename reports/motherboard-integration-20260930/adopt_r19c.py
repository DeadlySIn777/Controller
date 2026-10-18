"""Adopt the corrected physical CAN IRQ source after native and host gates."""
import datetime, hashlib, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_validate_motherboard as validator
import xml.etree.ElementTree as ET
REPORT=Path(__file__).resolve().parent
STAGE=REPORT/'r19c-2663-local-substrate-staged'
LIVE=ROOT/'hardware/motherboard'
MODEL=json.loads((STAGE/'design.json').read_text())
MAP=json.loads((STAGE/'assembly-map.json').read_text())
errors=validator.validate(ET.parse(STAGE/'netlist.xml'),MODEL,MAP,check_hashes=True)
assert not errors, errors
erc=json.loads((REPORT/'r19c-native-erc.json').read_text())
violations=[v for s in erc['sheets'] for v in s['violations']]
assert not erc['ignored_checks'] and not any(v['severity']=='error' for v in violations)
assert len(MODEL['components'])==2663
tests=(REPORT/'r19c-focused-tests.txt').read_text()
assert 'Ran 47 tests' in tests and tests.rstrip().endswith('OK')
ARCHIVE=REPORT/'before-r19c-2359'
assert not ARCHIVE.exists()
shutil.copytree(LIVE,ARCHIVE)
for f in STAGE.iterdir():
    if f.is_file(): shutil.copyfile(f,LIVE/f.name)
    elif f.is_dir(): shutil.copytree(f,LIVE/f.name,dirs_exist_ok=True)
hashes={p.relative_to(LIVE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in LIVE.rglob('*') if p.is_file()}
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    physical_parts=2663,native_ERC_errors=0,native_ERC_warnings=len(violations),ignored_checks=0,
    independent_source_validation=True,focused_tests_run=47,focused_tests_passed=47,
    source=str(STAGE.relative_to(ROOT)),archive=str(ARCHIVE.relative_to(ROOT)),hashes=hashes,
    required_CAN_IRQ_path='U15040.2 -> U14805.11; U14806.4 remains on CAN_CTRL_INT_RAW',
    revokes_initial_r18='Initial CAN IRQ direct raw-output connection was not power-off qualified',
    manufacturing_ready=False,scope='Actual integrated circuit source; published copper is an earlier partial snapshot.')
(REPORT/'r19c-2663-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('physical_parts','native_ERC_errors','native_ERC_warnings','focused_tests_passed','manufacturing_ready')}))
