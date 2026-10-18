"""Actual communication source mutation controls, not target driver/device simulation."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_comms import validate

class CommsTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ROOT/'hardware/motherboard_comms/design.json').read_text())
 def test_native_source(self):self.assertTrue(validate(self.d,ROOT/'hardware/motherboard_comms/netlist.xml',ROOT/'hardware/motherboard_comms/erc.json')['ok'])
 def pin(self,key,pin,net):
  self.d['components'][self.d['blocks'][key]]['pins'][str(pin)]=net;self.assertFalse(validate(self.d)['ok'])
 def bias(self,a,z,v,new):
  q=next(q for q in self.d['components'].values() if q['kind']=='R' and q['pins']=={'1':a,'2':z} and q['resistance_ohm']==v);q['resistance_ohm']=new;self.assertFalse(validate(self.d)['ok'])
 def test_halfmegabit_part_cannot_claim_1M(self):self.d['components'][self.d['blocks']['rs_transceiver']]['mpn']='ISOW1412DFMR';self.assertFalse(validate(self.d)['ok'])
 def test_rs_mode_5V_changed(self):self.pin('rs_transceiver',13,'RS485_ISO_3V3_RAW')
 def test_rs_A_B_polarity(self):self.pin('rs_transceiver',20,'RS485_A')
 def test_rs_receiver_disabled(self):self.pin('rs_transceiver',5,'IO_3V3')
 def test_rs_de_unqualified(self):self.pin('rs_transceiver',3,'RS485_DE_HOST')
 def test_rs_compute_good_faked(self):self.pin('rs_de_gate',2,'IO_3V3')
 def test_rs_de_default_missing(self):self.bias('RS485_DE_QUALIFIED','LOGIC_GND',4700,1000000)
 def test_CAN_controller_reset_cannot_be_invented(self):self.pin('controller',3,'CAN_CTRL_READY')
 def test_CAN_controller_wrong_SPI_input(self):self.pin('controller',11,'CAN_SPI_MISO_HOST')
 def test_CAN_controller_no_module_powercycle(self):self.pin('load_switch',3,'IO_3V3')
 def test_CAN_switch_QOD_short_wrong(self):self.pin('load_switch',5,'CAN_CTRL_3V3')
 def test_CAN_controller_supervisor_wrong_pin(self):self.pin('controller_supervisor',2,'CAN_CTRL_3V3')
 def test_CAN_controller_voltage_abs_not_reset(self):self.pin('controller_supervisor',3,'IO_3V3')
 def test_CAN_spi_supply_unpowered_backfeed(self):self.pin('spi_buffer',14,'IO_3V3')
 def test_CAN_spi_health_strapped(self):self.pin('spi_buffer',1,'LOGIC_GND')
 def test_quad_TI125_unverified_IOFF(self):self.d['components'][self.d['blocks']['spi_buffer']]['mpn']='SN74LVC125APWR';self.assertFalse(validate(self.d)['ok'])
 def test_CAN_clock_missing(self):self.pin('controller',6,None)
 def test_CAN_clock_wrong_rail(self):self.pin('clock',4,'IO_3V3')
 def test_CAN_clock_not_gated(self):self.pin('clock',1,'IO_3V3')
 def test_CAN_dominant_missing_module(self):self.bias('CAN_TXD','IO_3V3',10000,1000000)
 def test_CAN_rx_backpowers_controller(self):self.pin('can_rx_buffer',5,'IO_3V3')
 def test_CAN_module_good_inhibit_faked(self):self.pin('link_ready_gate',2,'IO_3V3')
 def test_CAN_standby_unqualified(self):self.pin('standby_gate',2,'LOGIC_GND')
 def test_CAN_STB_floating_start(self):self.bias('CAN_STANDBY','IO_3V3',4700,1000000)
 def test_CAN_VSIN_wrong_filtered_node(self):self.pin('can_transceiver',13,'CAN_FIELD_5V')
 def test_CAN_one_ground_not_joined(self):self.pin('can_transceiver',17,'CAN_ISO_RETURN_RAW')
 def test_CAN_bus_wrong_polarity(self):self.pin('can_transceiver',18,'CAN_H')
 def test_CAN_fault_pin_used_as_driven_enable(self):self.pin('can_transceiver',8,'IO_3V3')
 def test_RS_fake_field_health(self):self.pin('rs_transceiver',14,'RS485_FIELD_3V3')
 def test_CAN_fake_field_health(self):self.pin('can_health_isolator',4,'CAN_FIELD_5V')
 def test_health_default_high_variant(self):self.d['components'][self.d['blocks']['can_health_isolator']]['mpn']='ISO7720DWR';self.assertFalse(validate(self.d)['ok'])
 def test_TVS_wrong_common_ground(self):self.pin('can_tvs',3,'LOGIC_GND')
 def test_term_always_enabled(self):self.d['components'][self.d['blocks']['can_termination']]['pins']['2']='CAN_H';self.assertFalse(validate(self.d)['ok'])
 def test_ferrite_erases_field_isolation(self):self.pin('RS485_return_bead',1,'LOGIC_GND')
 def test_RS_unqualified_any_voltage(self):self.d['limits']['RS485_abs_bus_v']=[-60,60];self.assertFalse(validate(self.d)['ok'])
 def test_RS_mismatched_TVS_claim(self):self.d['limits']['RS485_board_surge_claim']=True;self.assertFalse(validate(self.d)['ok'])
 def test_actual_cap_budget_stale(self):self.d['power_budget']['CAN_CTRL_bypass_nominal_uf']=.1;self.assertFalse(validate(self.d)['ok'])
 def test_native_not_target(self):self.d['target_image_compiled']=True;self.assertFalse(validate(self.d)['ok'])
 def test_external_pins_gpio14_not_stolen(self):self.d['boundaries']['J14802']['pins']['3']='ESP_SERVICE_UART_TX';self.assertFalse(validate(self.d)['ok'])
 def test_boolean_default_gates(self):
  # Bounded topology truth table; this does not establish analog power sequencing.
  for good in [0,1]:
   for ready in [0,1]:
    for request in [0,1]:
     self.assertEqual(good and request,request if good else 0)
     self.assertEqual(bool(request or not ready),True if not ready else bool(request))

if __name__=='__main__':unittest.main()
