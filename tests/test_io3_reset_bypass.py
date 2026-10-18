import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_apply_io3_reset_bypass import apply_io3_reset_bypass,OUT,REPORT
from hardware_build_assembly import parse
from hardware_validate_io3_reset_bypass import validate,native_nodes
@pytest.fixture
def base():
 d=ROOT/'hardware/motherboard_io3_upgrade'
 return parse((d/'motherboard_io3_upgrade.kicad_sch').read_text()),json.loads((d/'design.json').read_text())
def test_pure_additive_preservation(base):
 before=copy.deepcopy(base);t,m,r=apply_io3_reset_bypass(*base)
 assert base==before
 assert validate(m,baseline=base[1])['passed']
 assert set(m['components'])-set(base[1]['components'])=={'C18001'}
 assert r['owner']==dict(ref='U2006',power_pin='5',return_pin='3')
@pytest.mark.parametrize('ref,pin,net',[('U2006','5','IO_3V3_REG_LOCAL'),('U2006','3','FIELD_GND'),('C2010','1','IO_3V3')])
def test_wrong_receiving_domain_rejected(base,ref,pin,net):
 base[1]['components'][ref]['pins'][pin]=net
 with pytest.raises(ValueError):apply_io3_reset_bypass(*base)
def test_duplicate_rejected(base):
 t,m,_=apply_io3_reset_bypass(*base)
 with pytest.raises(ValueError):apply_io3_reset_bypass(t,m)
def test_wrong_manufacturer_rejected(base):
 base[1]['components']['C2010']['mpn']='placeholder'
 with pytest.raises(ValueError):apply_io3_reset_bypass(*base)
def test_pre_damping_cap_cannot_masquerade_as_local_reset_bypass(base):
 _,m,_=apply_io3_reset_bypass(*base);m['components']['C18001']['pins']['1']='IO_3V3_REG_LOCAL'
 assert not validate(m,baseline=base[1])['passed']
def test_independent_native_and_no_ignored_ERC():
 m=json.loads((OUT/'design.json').read_text());n=native_nodes(OUT/'netlist.xml')
 assert validate(m,n)['passed'];assert n['C18001','1']==n['U2006','5'] and n['C18001','1']!=n['C2010','1']
 e=json.loads((REPORT/'erc.json').read_text());assert not e['ignored_checks'] and not [v for s in e['sheets']for v in s['violations']]
def test_unbounded_old_component_change_rejected(base):
 _,m,_=apply_io3_reset_bypass(*base);m['components']['U2001']['mpn']='different'
 assert not validate(m,baseline=base[1])['passed']
