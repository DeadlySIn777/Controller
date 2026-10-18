import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.hardware_validate_esp_service import validate,analyze,gate97

ROOT=Path(__file__).resolve().parents[1]
class ESPServiceHardware(unittest.TestCase):
 def setUp(self):
  self.tree=ET.parse(ROOT/'hardware/esp_service/netlist.xml')
  self.d=json.loads((ROOT/'hardware/esp_service/design-envelope.json').read_text())
 def move(self,ref,pin,net):
  dest=next(n for n in self.tree.findall('.//nets/net') if n.attrib['name'].lstrip('/')==net)
  for n in self.tree.findall('.//nets/net'):
   for p in n.findall('node'):
    if (p.attrib['ref'],p.attrib['pin'])==(ref,str(pin)):n.remove(p);dest.append(p);return
  self.fail('missing pin')
 def reject(self):self.assertTrue(validate(self.tree,self.d))
 def test_actual_contract(self):
  self.assertEqual(validate(self.tree,self.d),[])
  a=analyze(self.d);self.assertTrue(a['fits_1a_local_regulator_assumed']);self.assertTrue(a['gate_100ua_voh_condition_met'])
  self.assertFalse(a['all_partial_power_states_proven']);self.assertFalse(a['manufacturing_ready'])
 def test_and_truth_table_requires_both_inputs(self):
  for seq in (False,True):
   for manual in (False,True):self.assertEqual(gate97(manual,False,seq),seq and manual)
 def test_vbus_inverter_truth_table(self):
  self.assertTrue(gate97(False,True,False));self.assertFalse(gate97(False,True,True))
 def test_usb_must_not_power_esp(self):self.move('JUSB1','A4','ESP_3V3');self.reject()
 def test_second_usb_orientation_must_join_same_data(self):self.move('JUSB1','B6','USB_DM_CONNECTOR');self.reject()
 def test_cc_pins_need_independent_rd(self):self.move('R18',1,'USB_CC1');self.reject()
 def test_reset_contact_must_not_short_sequencer(self):self.move('JRESET1',1,'ESP_CHIP_PU');self.reject()
 def test_reset_cannot_bypass_supervisor(self):self.move('U2',6,'ESP_3V3');self.reject()
 def test_unsafe_flash_voltage_strap_rejected(self):self.move('R2',2,'ESP_3V3');self.reject()
 def test_boot_mode_requires_gpio46_low(self):self.move('R3',2,'ESP_3V3');self.reject()
 def test_module_pad41_ground_required(self):self.move('U1',41,'ESP_3V3');self.reject()
 def test_usb_unused_port_must_not_short_main_path(self):self.move('U5',3,'USB_DP_CONNECTOR');self.reject()
 def test_usb_select_must_not_float_or_select_unused_port(self):self.move('U5',9,'ESP_3V3');self.reject()
 def test_tx_buffer_power_must_follow_external_adapter(self):self.move('U4',5,'ESP_3V3');self.reject()
 def test_incoming_buffer_power_must_follow_esp(self):self.move('U3',5,'SERVICE_VREF_3V3');self.reject()
 def test_esd_return_must_not_be_floating_shield(self):self.move('D1',3,'USB_SHIELD');self.reject()
 def test_part_variant_not_interchangeable(self):
  self.tree.find(".//components/comp[@ref='U1']/fields/field[@name='MPN']").text='ESP32-S3-WROOM-1-N8R8';self.reject()
 def test_previous_usb_switch_voltage_limit_part_rejected(self):
  self.tree.find(".//components/comp[@ref='U5']/fields/field[@name='MPN']").text='TS3USB31ERSER';self.reject()
 def test_no_silent_removal_of_boot_pull(self):
  ET.SubElement(self.tree.find(".//components/comp[@ref='R1']"),'property',{'name':'dnp'});self.reject()
 def test_reserved_pin_cannot_claim_field_voltage(self):
  self.d['module_pin_nets']['5']='FIELD_24V';self.reject()
 def test_charge_cap_increase_exposes_regulator_overload(self):
  base=analyze(self.d);self.d['bounds']['module_bulk_nominal_f']*=10;a=analyze(self.d)
  self.assertGreater(a['core5_extra_cap_charge_a_assumed'],base['core5_extra_cap_charge_a_assumed']);self.assertFalse(a['fits_1a_local_regulator_assumed'])
 def test_bad_bounds_rejected(self):
  for bad in (True,float('nan'),float('inf'),-1,'1A',10**10000):
   d=copy.deepcopy(self.d);d['bounds']['esp_total_running_reservation_a']=bad
   with self.subTest(value=type(bad).__name__),self.assertRaises(ValueError):analyze(d)
 def test_five_volt_uart_vref_rejected(self):
  self.d['bounds']['serial_vref_v']=[5,5.25]
  with self.assertRaises(ValueError):analyze(self.d)
 def test_results_cannot_override_physical_calculation(self):
  expected=analyze(self.d);self.d['results']={'manufacturing_ready':True};self.assertEqual(expected,analyze(self.d))

if __name__=='__main__':unittest.main()
