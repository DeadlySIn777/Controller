"""Native mutation tests for discovered analog-PG/domain/default pitfalls."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_diagnostics import native,validate


class Diagnostics(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads((ROOT/'hardware/motherboard_diagnostics/design.json').read_text(encoding='utf-8'));cls.p=native(ROOT/'hardware/motherboard_diagnostics/netlist.xml')
 def reject(self,mutate):
  d,p=copy.deepcopy(self.d),copy.deepcopy(self.p);mutate(d,p);self.assertFalse(validate(d,p)['passed'])
 def test_actual_native_candidate(self):self.assertTrue(validate(self.d,self.p)['passed'])
 def test_wrong_TPS_package_pin_numbering(self):self.reject(lambda d,p:p['U22001']['pins'].update({'2':'DOA_FIELD_3V3','5':'FIELD_GND'}))
 def test_direct_FA_analog_node_into_CMOS(self):self.reject(lambda d,p:p['U22002']['pins'].update({'4':'FA_PGOOD'}))
 def test_FA_divider_rebiased(self):
  self.reject(lambda d,p:d['components']['R22001']['pins'].update({'1':'FA_PGOOD'}))
 def test_wrong_ISO_default_high_variant(self):self.reject(lambda d,p:p['U22003'].update({'mpn':'ISO7720DWR'}))
 def test_fieldA_B_returns_never_shared(self):self.reject(lambda d,p:p['U22003']['pins'].update({'1':'FIELD_GND','8':'FIELD_GND','5':'FIELD_GND'}))
 def test_DOA_receiver_cannot_borrow_B_rail(self):self.reject(lambda d,p:p['U22002']['pins'].update({'3':'DOB_FIELD_3V3'}))
 def test_logic_supply_cannot_be_field_supply(self):self.reject(lambda d,p:p['U22003']['pins'].update({'14':'DOB_FIELD_3V3'}))
 def test_FIELD_good_is_not_constant(self):self.reject(lambda d,p:p['U22003']['pins'].update({'4':'DOB_FIELD_3V3'}))
 def test_comparator_unused_input_defined(self):self.reject(lambda d,p:p['U22001']['pins'].update({'4':None}))
 def test_unused_ISO_input_defined(self):self.reject(lambda d,p:p['U22002']['pins'].update({'5':None}))
 def test_existing_MCU_input_not_wrong_bank(self):self.reject(lambda d,p:p['U22002']['pins'].update({'13':'DOB_FIELD_POWER_GOOD'}))
 def test_four_real_fault_testpads(self):self.reject(lambda d,p:p['TP22003']['pins'].update({'1':None}))
 def test_NPTH_has_no_fake_NC_copper_pad(self):self.reject(lambda d,p:p['H22001']['pins'].update({'1':None}))
 def test_NPTH_is_not_purchased_connector(self):self.reject(lambda d,p:d['components']['H22001'].update({'purchased':True}))
 def test_wrong_NPTH_diameter(self):self.reject(lambda d,p:d['components']['H22004'].update({'drill_mm':4.3}))
 def test_bypass_return_must_follow_local_domain(self):self.reject(lambda d,p:p['C22004']['pins'].update({'2':'LOGIC_GND'}))
 def test_missing_monitor_bypass(self):self.reject(lambda d,p:p.pop('C22001'))
 def test_false_inventory_count(self):self.reject(lambda d,p:d.update({'purchased_fitted_components':20}))


if __name__=='__main__':unittest.main()
