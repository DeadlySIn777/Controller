"""Meaningful bounded-transform and independent IO3 circuit checks."""
import copy,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_apply_motherboard_io3_upgrade import (apply_io3_upgrade,OUT,REPORT,ENDS,LOCAL,RREF,TOPREF,exact_label,symbol_for)
from hardware_validate_motherboard_io3_upgrade import validate,native_nodes
from hardware_build_assembly import parse,child,children,value,ref_property,point

@pytest.fixture
def source():
    tree=parse((ROOT/'hardware/motion_card/mc_local_power.kicad_sch').read_text())
    full=json.loads((ROOT/'hardware/motion_card/design.json').read_text())
    refs={value(ref_property(s)[2]) for s in children(tree,'symbol')}
    return tree,{'components':{r:c for r,c in full['components'].items() if r in refs}}

def test_bounded_transform_does_not_mutate_source(source):
    tree,base=source;before=(copy.deepcopy(tree),copy.deepcopy(base))
    t,m,r=apply_io3_upgrade(tree,base)
    assert (tree,base)==before
    assert validate(m,baseline=base)['consistency_pass']
    assert set(m['components'])-set(base['components'])=={'R18001','R18002'}
    assert set(r['added_refs'])=={'R18001','R18002'}

def test_existing_hierarchy_port_moves_to_distributed_rail(source):
    t,m,_=apply_io3_upgrade(*source)
    ports=[p for p in children(t,'hierarchical_label') if value(p[1])=='IO_3V3']
    assert len(ports)==1
    assert exact_label(t,RREF,'2','IO_3V3') is ports[0]
    assert all(not [p for p in children(t,'hierarchical_label') if value(p[1])==LOCAL] for _ in [0])

def test_native_pin_inventory_matches_every_component():
    model=json.loads((OUT/'design.json').read_text())
    result=validate(model,native_nodes(OUT/'netlist.xml'))
    assert result['consistency_pass'],result['errors']

def test_native_erc_has_no_suppressed_checks():
    erc=json.loads((REPORT/'erc.json').read_text())
    assert not erc['ignored_checks']
    assert not [v for s in erc['sheets'] for v in s['violations']]

@pytest.mark.parametrize('ref,pin',ENDS)
def test_incorrect_local_split_is_rejected(source,ref,pin):
    tree,model=source;model['components'][ref]['pins'][pin]='WRONG'
    with pytest.raises(ValueError,match='Unexpected bounded endpoint'):apply_io3_upgrade(tree,model)

def test_changed_regulator_manufacturer_pin_map_is_rejected(source):
    tree,model=source
    u=symbol_for(tree,'U2002');lid=value(child(u,'lib_id')[1])
    definition=next(x for x in children(child(tree,'lib_symbols'),'symbol') if value(x[1])==lid)
    for sub in children(definition,'symbol'):
        for pin in children(sub,'pin'):
            if value(child(pin,'number')[1])=='3':child(pin,'name')[1]='"WRONG"'
    with pytest.raises(ValueError,match='function map'):apply_io3_upgrade(tree,model)

def test_double_upgrade_is_rejected(source):
    t,m,_=apply_io3_upgrade(*source)
    with pytest.raises(ValueError):apply_io3_upgrade(t,m)

@pytest.mark.parametrize('mutation',[
    lambda m:m['components'][RREF]['pins'].update({'1':'IO_3V3'}),
    lambda m:m['components'][RREF].update(resistance_ohm=0),
    lambda m:m['components'][TOPREF].update(resistance_ohm=115000),
    lambda m:m['components']['R2005']['pins'].update({'2':'LOGIC_GND'}),
    lambda m:m['components']['R2005'].update(mpn='CRCW060332K4FKEA'),
    lambda m:m['components']['R2008'].update(mpn='CRCW0603301KFKEA'),
    lambda m:m['components']['U2002'].update(mpn='TPS62901RPJR'),
])
def test_real_circuit_faults_are_rejected(source,mutation):
    t,m,_=apply_io3_upgrade(*source);mutation(m)
    assert not validate(m)['consistency_pass']

def test_unrelated_retained_change_is_rejected(source):
    t,base=source;t,m,_=apply_io3_upgrade(t,base)
    m['components']['U2001']['pins']['6']='WRONG'
    assert any('Unbounded retained mutation U2001' in e for e in validate(m,baseline=base)['errors'])

def test_independent_native_mismatch_is_rejected():
    m=json.loads((OUT/'design.json').read_text());nodes=native_nodes(OUT/'netlist.xml')
    nodes[('U2002','3')]='IO_3V3'
    assert not validate(m,nodes)['consistency_pass']

def test_exact_current_and_voltage_corner_limits(source):
    _,m,_=apply_io3_upgrade(*source);s=validate(m)['screening']
    assert s['rmin_ohm']>.010
    assert .0008<s['fb_error_max_v']<.00081
    assert .00278<s['available_distribution_noise_budget_v']<.00280
    assert .00361<s['upper_arming_margin_v']<.00362
    assert abs(s['nominal_local_v']-3.30588235294)<1e-10
    # This explicitly excludes a guarantee of arbitrary layout/transients.
    assert not validate(m)['physical_qualification']

def test_manufacturer_susumu_land_geometry():
    fp=parse((OUT/'CNC_MB_IO3.pretty/KRL2012_Susumu.kicad_mod').read_text())
    pads=children(fp,'pad')
    assert len(pads)==2
    assert [value(p[1]) for p in pads]==['1','2']
    assert [point(child(p,'at')) for p in pads]==[(-.65,0),(.65,0)]
    assert all(point(child(p,'size'))==(.7,2.2) for p in pads)
    assert all(p[3]=='rect' for p in pads)

def test_original_source_hashes_are_still_exact():
    import hashlib
    r=json.loads((REPORT/'receipt.json').read_text())
    for p,digest in r['source_sha256'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest
