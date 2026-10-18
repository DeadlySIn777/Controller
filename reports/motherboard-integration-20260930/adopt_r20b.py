"""Adopt only the independently verified native electrical correction stage."""
import datetime,hashlib,json,shutil,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_validate_motherboard as validator
REPORT=Path(__file__).resolve().parent
STAGE=REPORT/'r20b-2663-electrical-corrections-staged'
LIVE=ROOT/'hardware/motherboard'
model=json.loads((STAGE/'design.json').read_text())
mapping=json.loads((STAGE/'assembly-map.json').read_text())
errors=validator.validate(ET.parse(STAGE/'netlist.xml'),model,mapping,check_hashes=True)
assert not errors,errors
erc=json.loads((REPORT/'r20b-native-erc.json').read_text())
violations=[v for s in erc['sheets'] for v in s['violations']]
assert not erc['ignored_checks'] and not any(v['severity']=='error' for v in violations)
tests=(REPORT/'r20b-focused-tests.txt').read_text()
assert 'Ran 50 tests' in tests and tests.rstrip().endswith('OK')
assert len(model['components'])==2663
archive=REPORT/'before-r20b-2663'
assert not archive.exists()
shutil.copytree(LIVE,archive)
for file in STAGE.iterdir():
    if file.is_file():shutil.copyfile(file,LIVE/file.name)
    elif file.is_dir():shutil.copytree(file,LIVE/file.name,dirs_exist_ok=True)
hashes={p.relative_to(LIVE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in LIVE.rglob('*') if p.is_file()}
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    physical_parts=2663,native_ERC_errors=0,native_ERC_warnings=len(violations),ignored_checks=0,
    independent_source_validation=True,focused_tests_run=50,focused_tests_passed=50,
    source=str(STAGE.relative_to(ROOT)),archive=str(archive.relative_to(ROOT)),hashes=hashes,
    corrections=['CORE-only7A design envelope/exact stronger coil/5mOhm/fourthbulk',
        'five wide-input analog supplies/exactAI5 LDO and window/monitorVDD',
        'nine explicit reserved FPGA NC balls plus real U2006.4/P4 rail readback'],
    source_qualification_receipts=[
        'reports/motherboard-power-entry-20260930/core7a-r04/receipt-r04b.json',
        'reports/motherboard-analog-wide-input-20260930/receipt-r02.json',
        'reports/motherboard-fpga-source-20260930/reserved-health-reconciliation-r01/receipt.json'],
    manufacturing_ready=False,scope='Actual integrated source; PCB reconciliation, fullrouting and qualification remain incomplete.')
(REPORT/'r20b-2663-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('physical_parts','native_ERC_errors','native_ERC_warnings','focused_tests_passed','manufacturing_ready')}))
