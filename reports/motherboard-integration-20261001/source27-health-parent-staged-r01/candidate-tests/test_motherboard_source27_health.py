"""Independent exact parent-only health loading/pin/domain/ledger mutations."""
import copy, importlib.util, json, os
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

ROOT=Path.cwd()
CHECKER=Path(os.environ.get('CONTROLLER_SOURCE27_CHECKER',ROOT/'tools/hardware_check_source27_parts.py'))
spec=importlib.util.spec_from_file_location('health27_checks',CHECKER)
check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
STAGE=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01/candidate/motherboard'

def fixture():
    m=json.loads((STAGE/'design.json').read_text());a=json.loads((STAGE/'assembly-map.json').read_text())
    n={(p.get('ref'),p.get('pin')):net.get('name')for net in ET.parse(STAGE/'netlist.xml').findall('.//nets/net')for p in net.findall('node')}
    return m,a,n

def errors(m,a,n):return check.check_source27(m['components'],n,m,a)

def test_actual_three_part_native_health_source_pass():
    m,a,n=fixture();assert not errors(m,a,n)
    assert len(m['components'])==2688 and len(a['retained_native_pin_nets'])==1229
    assert a['reviewed_health_source_delta']['physical_qualified']is False

@pytest.mark.parametrize('ref',check.REFS)
@pytest.mark.parametrize('field,value',[
    ('mpn','FAKE'),('footprint','Package_TO_SOT_SMD:SOT-23-6'),
    ('inherited_mpn','UNREVIEWED'),('component_substitution','UNKNOWN'),
])
def test_unreviewed_identity_or_land_rejected(ref,field,value):
    m,a,n=fixture();m['components'][ref][field]=value;assert errors(m,a,n)

@pytest.mark.parametrize('ref',check.REFS)
def test_altered_native_input_rejected(ref):
    m,a,n=fixture();n[ref,'1']='/UNREVIEWED_HEALTH';assert errors(m,a,n)

@pytest.mark.parametrize('ref',check.REFS)
def test_altered_model_input_rejected(ref):
    m,a,n=fixture();m['components'][ref]['pins']['1']='WRONG_RAIL';assert errors(m,a,n)

@pytest.mark.parametrize('field',[
    'frozen_primary_receipt','frozen_primary_receipt_sha256','frozen_primary_review_sha256',
    'parent_only_override','immutable_child04_and_original_MC_baselines_retained',
    'native_pin_nets_unchanged','manufacturer_lands_unchanged','part_count_unchanged',
])
def test_false_parent_scope_or_primary_receipt_rejected(field):
    m,a,n=fixture();a['reviewed_health_source_delta'][field]='FAKE';assert errors(m,a,n)

def test_old_47k_loading_recipe_rejected():
    m,a,n=fixture();m['components']['R2106']['resistance_ohm']=47000;assert errors(m,a,n)

def test_field_receiver_cannot_borrow_logic_return():
    m,a,n=fixture();n['U11025','2']='/LOGIC_GND';assert errors(m,a,n)

def test_non_schmitt_input_type_rejected():
    m,a,n=fixture();m['components']['U11019']['kind']='LVC2G04';assert errors(m,a,n)

def test_physically_qualified_claim_rejected():
    m,a,n=fixture();m['health_source_correction']['physical_qualification']=True;assert errors(m,a,n)

def test_incomplete_exact_part_ledger_rejected():
    m,a,n=fixture();m['health_source_correction']['exact_three_part_ledger'].pop();assert errors(m,a,n)

def test_live_historical_no_health_override_is_readable():
    d=ROOT/'hardware/motherboard';m=json.loads((d/'design.json').read_text());a=json.loads((d/'assembly-map.json').read_text())
    n={(p.get('ref'),p.get('pin')):net.get('name')for net in ET.parse(d/'netlist.xml').findall('.//nets/net')for p in net.findall('node')}
    assert not errors(m,a,n)
