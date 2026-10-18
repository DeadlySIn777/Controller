"""Adopt one exact reset-buffer receiving-rail bypass; no old endpoint changes."""
import datetime,hashlib,json,shutil,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'));import hardware_validate_motherboard as validator
STAGE=REPORT/'r23-2688-reset-bypass-staged';LIVE=ROOT/'hardware/motherboard'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
model=read(STAGE/'design.json');mapping=read(STAGE/'assembly-map.json');old=read(LIVE/'design.json')
assert set(model['components'])-set(old['components'])=={'C18001'} and set(old['components'])<=set(model['components'])
before=validator.nodes(ET.parse(LIVE/'netlist.xml'));after=validator.nodes(ET.parse(STAGE/'netlist.xml'))
assert all(after.get(k)==v for k,v in before.items())
assert set(after)-set(before)=={('C18001','1'),('C18001','2')}
assert after['C18001','1']=='/IO_3V3' and after['C18001','2']=='/LOGIC_GND'
assert not validator.validate(ET.parse(STAGE/'netlist.xml'),model,mapping,check_hashes=True)
erc=read(REPORT/'r23-native-erc.json');v=[v for s in erc['sheets'] for v in s['violations']]
assert not erc['ignored_checks'] and not any(x['severity']=='error' for x in v) and len(v)==70
tests=(REPORT/'r23-focused-tests.txt').read_text();assert 'Ran 59 tests' in tests and tests.rstrip().endswith('OK')
archive=REPORT/'before-r23-2687';assert not archive.exists();shutil.copytree(LIVE,archive)
for f in STAGE.iterdir():
    if f.is_file():shutil.copyfile(f,LIVE/f.name)
    elif f.is_dir():shutil.copytree(f,LIVE/f.name,dirs_exist_ok=True)
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_parts=2688,
    purchased_fitted_parts=2642,bare_geometry=44,DNP=2,exact_added_references=['C18001'],
    all_existing_native_pin_nets_preserved=True,native_ERC_errors=0,native_ERC_warnings=70,
    ignored_checks=0,independent_validation_pass=True,focused_tests_passed=59,
    source=str(STAGE.relative_to(ROOT)),archive=str(archive.relative_to(ROOT)),
    hashes={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()},
    manufacturing_ready=False,physical_qualification=False,
    scope='One100nF receivingIO3/LOGICGND bypass on actual U2006.VCC5/GND3. All prior electrical endpoints remain exact. PCB and physical qualification are separate.')
(REPORT/'r23-2688-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('physical_parts','native_ERC_errors','native_ERC_warnings','focused_tests_passed')}))
