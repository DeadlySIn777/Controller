"""Adopt the four exact frozen MCU clock-counter taps after native checks."""
import datetime,hashlib,json,shutil,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_validate_motherboard as validator
REPORT=Path(__file__).resolve().parent
STAGE=REPORT/'r21-2667-clock-taps-staged'
LIVE=ROOT/'hardware/motherboard'
def read(p):return json.loads(p.read_text())
def native(p):
    return {(n.attrib['ref'],n.attrib['pin']):net.attrib['name']
        for net in ET.parse(p).findall('.//nets/net') for n in net.findall('node')}
model=read(STAGE/'design.json');mapping=read(STAGE/'assembly-map.json')
old=read(LIVE/'design.json');before=native(LIVE/'netlist.xml');after=native(STAGE/'netlist.xml')
added={'R13057','R13058','R13059','R14533'}
pins={('U13001','44'),('U13004','29'),('U13008','29'),('U14501','44')}
assert set(model['components'])-set(old['components'])==added
assert set(old['components'])<=set(model['components'])
assert {k for k in before if before[k]!=after.get(k)}==pins
assert all(before[k].startswith('unconnected-') for k in pins)
assert set(after)-set(before)=={(r,p) for r in added for p in ('1','2')}
assert all(model['components'][r]['mpn']=='CRCW06030000Z0EA' for r in added)
errors=validator.validate(ET.parse(STAGE/'netlist.xml'),model,mapping,check_hashes=True)
assert not errors,errors
erc=read(REPORT/'r21-native-erc.json');v=[v for s in erc['sheets'] for v in s['violations']]
assert not erc['ignored_checks'] and not any(x['severity']=='error' for x in v)
tests=(REPORT/'r21-focused-tests.txt').read_text()
assert 'Ran 52 tests' in tests and tests.rstrip().endswith('OK')
clock=read(ROOT/'reports/motherboard-iol1-firmware-20260930/clock-taps-r01/receipt.json')
for entry in clock['hashes']:
    p=ROOT/entry['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],p
archive=REPORT/'before-r21-2663';assert not archive.exists()
shutil.copytree(LIVE,archive)
for f in STAGE.iterdir():
    if f.is_file():shutil.copyfile(f,LIVE/f.name)
    elif f.is_dir():shutil.copytree(f,LIVE/f.name,dirs_exist_ok=True)
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_parts=len(model['components']),
    exact_added_references=sorted(added),exact_changed_existing_pins=sorted(r+'.'+p for r,p in pins),
    all_other_existing_native_pin_nets_preserved=True,native_ERC_errors=0,native_ERC_warnings=len(v),ignored_checks=0,
    independent_validation_pass=True,focused_tests_passed=52,source=str(STAGE.relative_to(ROOT)),archive=str(archive.relative_to(ROOT)),
    hashes={p.relative_to(LIVE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in LIVE.rglob('*') if p.is_file()},
    manufacturing_ready=False,scope='Exact counter wiring/source adoption. Target firmware, full PCB and physical clock-edge capture remain separately qualified.')
(REPORT/'r21-2667-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('physical_parts','native_ERC_errors','native_ERC_warnings','focused_tests_passed')}))
