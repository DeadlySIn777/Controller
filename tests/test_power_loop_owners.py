"""Independent real owning-pin checks; no native PCB/routing shortcut claims."""
import copy,json
from pathlib import Path
import pytest
from tools.hardware_power_loop_manifest import build,qualified_cap_pins,BLOCKS
ROOT=Path(__file__).resolve().parents[1]
def cap(ref):return next(x for x in build()['capacitors']if x['ref']==ref)
def test_inventory_every_cap_and_actual_power_parts():
    m=build();assert m['capacitor_count']==204 and len(m['full_power_entry_inventory'])==221
    assert not m['layout_qualified']and not m['pcb_modified']
def test_ltc_bypass_never_tied_en_configuration_or_threshold_pins():
    c=cap('C19019');assert {(x['ref'],x['pin'])for x in c['actual_owner_endpoints']['1']}=={('U19008','1')}
    assert {x['pin']for x in c['actual_owner_endpoints']['2']}=={'3','17'}
def test_max_ground_never_ovlo_control():
    c=cap('C19014');assert {x['pin']for x in c['actual_owner_endpoints']['2']}=={'9','11'}
def test_dff_bypass_never_logic_high_D_or_PRE():
    c=cap('C11083');assert {x['pin']for x in c['actual_owner_endpoints']['1']}=={'8'}
def test_iso7720_bypass_excludes_unused_input_and_nc_ties():
    c=cap('C19025');assert {x['pin']for x in c['actual_owner_endpoints']['2']}=={'1'}
def test_lmr_vcc_cap_never_tied_rt_pin():
    c=cap('C11053');assert {x['pin']for x in c['actual_owner_endpoints']['1']}=={'7'}
def test_B_LDO_input_owns_real_post_preregulator_IN_not_24V_or_EN():
    c=cap('C19053');assert c['owner_ref']=='U11018'
    assert {(x['ref'],x['pin'])for x in c['actual_owner_endpoints']['1']if x['ref']=='U11018'}=={('U11018','8')}
    assert c['capacitor_pins']['1']=='FIELD_B_5V_PRE'
    assert cap('C11076')['owner_ref']=='U11006'
@pytest.mark.parametrize('pin',['1','2'])
def test_wrong_cap_supply_or_return_rejected(pin):
    models={n:json.loads((ROOT/'hardware'/n/'design.json').read_text())for n in BLOCKS}
    models['motherboard_safety_sensor']['components']['C19014']['pins'][pin]='LOGIC_GND'
    with pytest.raises(AssertionError):build(models)
def test_unreviewed_part_owning_cap_rejected():
    models={n:json.loads((ROOT/'hardware'/n/'design.json').read_text())for n in BLOCKS}
    models['motherboard_safety_sensor']['components']['U19006']['mpn']='UNKNOWN'
    with pytest.raises(ValueError):build(models)
def test_missing_cap_not_silently_excluded():
    models={n:json.loads((ROOT/'hardware'/n/'design.json').read_text())for n in BLOCKS}
    del models['motherboard_safety_sensor']['components']['C19014']
    with pytest.raises(AssertionError):build(models)
def test_manifest_numeric_targets_are_never_manufacturer_limits():
    assert all(c['numeric_target_is_manufacturer_limit']is False and c['effective_capacitance_qualified']is False for c in build()['capacitors'])
