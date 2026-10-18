"""Adopt exact two RTHR endpoints plus non-electrical FPGA text/metadata."""
import copy,datetime,hashlib,json,shutil,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import hardware_validate_motherboard as validator
from hardware_apply_motherboard_fpga_allocation import parse,children,value
STAGE=REPORT/'r24-2688-probe-topology-staged';LIVE=ROOT/'hardware/motherboard'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
before_model=read(LIVE/'design.json');after_model=read(STAGE/'design.json')
assert set(before_model['components'])==set(after_model['components'])
expected=[dict(ref='R14069',pin='2',old='/motherboard_operator/PRB0_IN_SENSE',new='/motherboard_operator/PRB0_SENSE'),
          dict(ref='R14072',pin='2',old='/motherboard_operator/PRB1_IN_SENSE',new='/motherboard_operator/PRB1_SENSE')]
before=validator.nodes(ET.parse(LIVE/'netlist.xml'));after=validator.nodes(ET.parse(STAGE/'netlist.xml'))
assert set(before)==set(after)
actual=[dict(ref=r,pin=p,old=old,new=after[r,p]) for (r,p),old in before.items() if old!=after[r,p]]
assert sorted(actual,key=lambda x:x['ref'])==expected,actual
normalized=copy.deepcopy(after_model['components'])
for row in expected:
    normalized[row['ref']]['pins'][row['pin']]=before_model['components'][row['ref']]['pins'][row['pin']]
assert normalized==before_model['components']
assert sha(STAGE/'bom.csv')==sha(LIVE/'bom.csv')
old_core=parse((LIVE/'fpga_core.kicad_sch').read_text())
new_core=parse((STAGE/'fpga_core.kicad_sch').read_text())
electrical=lambda c:[n for n in c if not isinstance(n,list) or n[0]!='text']
assert electrical(old_core)==electrical(new_core)
texts=[value(t[1]) for t in children(new_core,'text')]
assert sum(t.startswith('HISTORICAL TRANSACTION') for t in texts)==4
assert sum(t.startswith('CURRENT IS2 FPGA ALLOCATION:135 assigned /48 free') for t in texts)==1
old_meta=read(LIVE/'fpga-allocation-parent.json');new_meta=read(STAGE/'fpga-allocation-parent.json')
for field in ['exact_pin_rename_ledger','home_deallocation_pin_rename_ledger',
              'reserved_health_pin_rename_ledger','obsolete_machine_status_pin_rename_ledger']:
    assert old_meta[field]==new_meta[field],field
assert (new_meta['assigned_user_pins'],new_meta['free_user_gpio'],new_meta['promoted_nc_pin_count'])==(135,48,66)
mapping=read(STAGE/'assembly-map.json')
assert not validator.validate(ET.parse(STAGE/'netlist.xml'),after_model,mapping,check_hashes=True)
erc=read(REPORT/'r24-native-erc.json');violations=[v for s in erc['sheets'] for v in s['violations']]
assert not erc['ignored_checks'] and len(violations)==70 and all(v['severity']=='warning' for v in violations)
tests=(REPORT/'r24-focused-tests.txt').read_text()
assert 'Ran 61 tests' in tests and tests.rstrip().endswith('OK')
annotations=(REPORT/'r24-fpga-annotation-tests.txt').read_text()
assert 'Ran 4 tests' in annotations and annotations.rstrip().endswith('OK')
all_fpga=(REPORT/'r24-fpga-allocation-tests.txt').read_text()
assert all_fpga.rstrip().endswith('OK')
contract=read(ROOT/'reports/motherboard-fpga-source-20260930/actual-source23-pcb25c-contract-r01/fpga-electrical-contract.json')
assert all(after['U1001',r['ball']]==r['native_net'] for r in contract['resources'])
archive=REPORT/'before-r24-2688';assert not archive.exists();shutil.copytree(LIVE,archive)
for f in STAGE.iterdir():
    if f.is_file():shutil.copyfile(f,LIVE/f.name)
    elif f.is_dir():shutil.copytree(f,LIVE/f.name,dirs_exist_ok=True)
assert not validator.validate(ET.parse(LIVE/'netlist.xml'),read(LIVE/'design.json'),read(LIVE/'assembly-map.json'),check_hashes=True)
receipt=dict(date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_parts=2688,
    purchased_fitted_parts=2642,bare_geometry=44,DNP=2,
    exact_native_pin_changes=expected,all_other_native_pin_nets_preserved=True,
    all_other_component_fields_values_MPNs_and_footprint_lands_preserved=True,BOM_bytes_unchanged=True,
    FPGA_all_electrical_items_and256_ball_nets_unchanged=True,
    FPGA_current_assigned=135,FPGA_current_free=48,FPGA_historical66_promotion_ledger_preserved=True,
    FPGA_four_old_annotations_marked_historical=True,FPGA_current_metadata_alias_reconciled=True,
    native_ERC_errors=0,native_ERC_warnings=70,ignored_checks=0,
    independent_validation_pass=True,focused_integration_tests_passed=61,FPGA_annotation_tests_passed=4,
    FPGA_allocation_regression_log='r24-fpga-allocation-tests.txt',
    source=str(STAGE.relative_to(ROOT)),archive=str(archive.relative_to(ROOT)),
    operator_child_receipt='reports/motherboard-probe-safety-20261001/operator-two-pad-source-r01/receipt.json',
    derived198_receipt='reports/motherboard-probe-safety-20261001/derived198-r24-receipt.json',
    primary_topology_receipt='reports/motherboard-probe-safety-20261001/source-topology-r01/review.json',
    source_hashes={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()},
    manufacturing_ready=False,physical_qualification=False,PCB_two_pin_reconciliation_required=True,
    scope='Correct actual external-probe RTHR feed to SENSE before RSENSE. Parent-source native checks only; PCB reconciliation/routing and physical thresholds/EMC remain separate.')
(REPORT/'r24-2688-adoption.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['physical_parts','native_ERC_errors','native_ERC_warnings','focused_integration_tests_passed','FPGA_current_assigned','FPGA_current_free']}))
