"""Adopt exact source22 diagnostic/NPTH population and twenty functional NCs."""
import datetime,hashlib,json,shutil,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import hardware_validate_motherboard as validator
STAGE=REPORT/'r22b-2687-diagnostics-staged';LIVE=ROOT/'hardware/motherboard'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
model=read(STAGE/'design.json');mapping=read(STAGE/'assembly-map.json');old=read(LIVE/'design.json')
added={'U22001','U22002','U22003','R22001','R22002'}|{f'C2200{i}' for i in range(1,6)}|{
    f'TP2200{i}' for i in range(1,5)}|{f'H2200{i}' for i in range(1,7)}
assert set(model['components'])-set(old['components'])==added
assert set(old['components'])<=set(model['components']) and len(model['components'])==2687
before=validator.nodes(ET.parse(LIVE/'netlist.xml'));after=validator.nodes(ET.parse(STAGE/'netlist.xml'))
physical_before={k:v for k,v in before.items() if k[0] in old['components']}
physical_after={k:v for k,v in after.items() if k[0] in model['components']}
expected={(r['reference'],r['pin']):(r['old_native_net'],r['new_native_net'])
    for r in mapping['native_unused_functional_dispositions_allowed']}
assert len(expected)==20
assert {k for k in physical_before if physical_before[k]!=physical_after.get(k)}==set(expected)
assert all((physical_before[k],physical_after[k])==v for k,v in expected.items())
assert len(set(physical_after)-set(physical_before))==56
assert all(k[0] in added for k in set(physical_after)-set(physical_before))
errors=validator.validate(ET.parse(STAGE/'netlist.xml'),model,mapping,check_hashes=True);assert not errors,errors
erc=read(REPORT/'r22b-native-erc.json');vs=[v for s in erc['sheets'] for v in s['violations']]
assert not erc['ignored_checks'] and not any(v['severity']=='error' for v in vs)
assert len(vs)==70
assert 'Ran 57 tests' in (REPORT/'r22b-focused-tests.txt').read_text()
assert (REPORT/'r22b-focused-tests.txt').read_text().rstrip().endswith('OK')
frozen=read(ROOT/'reports/motherboard-diagnostics-20260930/r01/receipt.json')
for name,wanted in frozen['source_sha256'].items():
    assert sha(ROOT/'hardware/motherboard_diagnostics'/name)==wanted,name
fpga=read(STAGE/'fpga-allocation-parent.json')
assert (fpga['assigned_user_pins'],fpga['free_user_gpio'],fpga['promoted_nc_pin_count'])==(135,48,66)
archive=REPORT/'before-r22b-2667';assert not archive.exists();shutil.copytree(LIVE,archive)
for f in STAGE.iterdir():
    if f.is_file():shutil.copyfile(f,LIVE/f.name)
    elif f.is_dir():shutil.copytree(f,LIVE/f.name,dirs_exist_ok=True)
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_parts=2687,
    purchased_fitted_parts=2641,bare_geometry=44,DNP=2,exact_added_references=sorted(added),
    exact_changed_existing_fitted_pins=expected and ['.'.join(k) for k in sorted(expected)],
    exact_unused_functional_pin_dispositions=mapping['native_unused_functional_dispositions_allowed'],
    all_other_existing_fitted_native_pin_nets_preserved=True,native_ERC_errors=0,native_ERC_warnings=70,
    ignored_checks=0,independent_validation_pass=True,focused_tests_passed=57,
    source=str(STAGE.relative_to(ROOT)),archive=str(archive.relative_to(ROOT)),
    hashes={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()},
    manufacturing_ready=False,physical_qualification=False,
    scope='Real separate-return entryPG circuit, four diagnostic fault testpads, six unelectricalM3 mounts and exact unused functional NCs. PCB routing and physical qualification are separate.')
(REPORT/'r22b-2687-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('physical_parts','native_ERC_errors','native_ERC_warnings','focused_tests_passed')}))
