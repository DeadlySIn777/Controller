"""Disconnected real LED endpoint/fault/default tamper controls."""
import copy,json,sys,unittest,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_status import validate
from hardware_build_assembly import parse
OUT=ROOT/'hardware/motherboard_status'
class StatusIndicators(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=json.loads((OUT/'design.json').read_text())
 def bad(self,fn):
  d=copy.deepcopy(self.base);fn(d);self.assertFalse(validate(d)['ok'])
 def test_native_exact(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json')['ok'])
 def test_counts(self):self.assertEqual(self.base['fitted_component_count'],289);self.assertEqual(self.base['fitted_pad_count'],853)
 def test_fault_graph_all512(self):self.assertEqual(validate(self.base)['hardware_truth_cases'],512)
 def test_not_manufacture(self):self.bad(lambda d:d.__setitem__('manufacturing_ready',True))
 def test_not_physical(self):self.bad(lambda d:d.__setitem__('physical_qualification',True))
 def test_not_firmware(self):self.bad(lambda d:d.__setitem__('target_firmware_implemented',True))
 def test_no_cached_freshness(self):self.bad(lambda d:d.__setitem__('software_status_freshness_qualified',True))
 def test_TLC_F_not_constantcurrent(self):self.bad(lambda d:d['components'][d['rgb_driver_refs'][0]].__setitem__('mpn','TLC59116IPWR'))
 def test_pin1_not_Rext(self):self.bad(lambda d:d['components'][d['rgb_driver_refs'][0]]['pins'].__setitem__('1','LOGIC_GND'))
 def test_driver_reset_not_software(self):self.bad(lambda d:d['components'][d['rgb_driver_refs'][0]]['pins'].__setitem__('25','ESP_RGB_ENABLE'))
 def test_5V_driver_not_direct3V3bus(self):self.bad(lambda d:d['components'][d['rgb_driver_refs'][0]]['pins'].__setitem__('26','AO_I2C_SCL'))
 def test_hardwareGOOD_no_constant(self):self.bad(lambda d:d['components'][d['hardware_gate_refs'][1]]['pins'].__setitem__('11','CORE_5V'))
 def test_unpowered_pd_required(self):self.bad(lambda d:next(z for z in d['components'].values() if z['pins']=={'1':'WD_M_OK','2':'LOGIC_GND'}).__setitem__('resistance_ohm',1000000))
 def test_fault_sink_wrong_polarity(self):self.bad(lambda d:d['components'][d['fault_sink_ref']].__setitem__('mpn','74LVC06APW,118'))
 def test_fault_bank_max32mA(self):self.bad(lambda d:d['components'][d['fault_sink_ref']]['pins'].__setitem__('4','STATUS_RED_BUS0'))
 def test_both_motor_banks(self):self.bad(lambda d:d['components'][d['hardware_gate_refs'][1]]['pins'].__setitem__('5','MOTOR_TX_GATE_A'))
 def test_both_watchdogs(self):self.bad(lambda d:d['components'][d['hardware_gate_refs'][0]]['pins'].__setitem__('5','WD_M_OK'))
 def test_reset_fanout_not_ignored(self):self.bad(lambda d:d['components'][d['rgb_driver_refs'][1]]['pins'].__setitem__('25','CORE_5V'))
 def test_WDT_independent(self):self.bad(lambda d:d['components'][d['fault_sink_ref']]['pins'].__setitem__('5','STATUS_HW_GOOD'))
 def test_WDT_current_limit(self):self.bad(lambda d:d['components'][d['watchdog_current_ref']].__setitem__('resistance_ohm',680))
 def test_fieldcached_not_terminal(self):self.bad(lambda d:d['components'][d['output_indicators'][0]['current_refs'][0]]['pins'].__setitem__('1','OUT0_FPGA'))
 def test_fieldB_not_logicground(self):self.bad(lambda d:d['components'][d['output_indicators'][8]['led_ref']]['pins'].__setitem__('1','LOGIC_GND'))
 def test_fieldB_not_A(self):self.bad(lambda d:d['components'][d['output_indicators'][8]['reverse_ref']]['pins'].__setitem__('1','FIELD_A_0V'))
 def test_all16_actualterminal(self):self.bad(lambda d:d['output_indicators'].pop())
 def test_voltage_not_currentclaim(self):self.bad(lambda d:d['output_indicators'][0].__setitem__('observes','load_current'))
 def test_reverse_clamp_polarity(self):self.bad(lambda d:d['components'][d['output_indicators'][0]['reverse_ref']]['pins'].update({'1':'OUT0_A','3':'FIELD_A_0V'}))
 def test_BAS16_NC_not_ground(self):self.bad(lambda d:d['components'][d['output_indicators'][0]['reverse_ref']]['pins'].__setitem__('2','FIELD_A_0V'))
 def test_RGB_wrong_colour_pin(self):self.bad(lambda d:d['components'][d['rgb_indicators'][0]['led_ref']]['pins'].__setitem__('1','RGB_SYSTEM_G_K'))
 def test_RGB_common_anode(self):self.bad(lambda d:d['components'][d['rgb_indicators'][0]['led_ref']]['pins'].__setitem__('4','LOGIC_GND'))
 def test_RGB_hardware_red_separate(self):self.bad(lambda d:d['components'][d['rgb_indicators'][0]['hardware_red_ref']]['pins'].__setitem__('2','RGB_DRIVER_0'))
 def test_RGB_bleed_not_current_starve(self):self.bad(lambda d:d['components'][d['rgb_indicators'][0]['channels'][0]['bleed_ref']].__setitem__('resistance_ohm',1000))
 def test_di_not_request(self):self.bad(lambda d:d['components'][d['receive_indicators'][0]['buffer_ref']]['pins'].__setitem__('1','DI0_CACHE'))
 def test_12dedicated_alarms(self):self.bad(lambda d:d['receive_indicators'].pop())
 def test_alarm_actual_receive(self):self.bad(lambda d:d['components'][d['receive_indicators'][24]['buffer_ref']]['pins'].__setitem__('1','DI0_LOGIC'))
 def test_sink_powered_high_leak_exact_part(self):self.bad(lambda d:d['components'][d['receive_indicators'][0]['sink_ref']].__setitem__('mpn','SN74LVC06APWR'))
 def test_TTL_buffer_restoredHIGH(self):self.bad(lambda d:d['components'][d['receive_indicators'][0]['buffer_ref']].__setitem__('mpn','SN74HC04PWR'))
 def test_receive_1k_current(self):self.bad(lambda d:d['components'][d['receive_indicators'][0]['current_ref']].__setitem__('resistance_ohm',680))
 def test_receive_nonstarving_10k_bleed(self):self.bad(lambda d:d['components'][d['receive_indicators'][0]['bleed_ref']].__setitem__('resistance_ohm',1000))
 def test_no_1MHz_TCA(self):self.bad(lambda d:d.__setitem__('max_status_i2c_clock_hz',1000000))
 def test_forbidden_I2C(self):self.bad(lambda d:d.__setitem__('i2c_addresses',[0x60,0x48]))
 def test_address_pin_bounded(self):self.bad(lambda d:d['components'][d['rgb_driver_refs'][1]]['pins'].__setitem__('3','CORE_5V'))
 def test_allcall_default_not_hidden(self):self.bad(lambda d:d.__setitem__('i2c_por_allcall_address',None))
 def test_missing_bypass(self):self.bad(lambda d:d['components'].pop(next(r for r,z in d['components'].items() if z['kind']=='C')))
 def test_all_footprints_parse(self):
  for p in (OUT/'CNC_MB_Status.pretty').glob('*.kicad_mod'):self.assertEqual(parse(p.read_text())[0],'footprint')
 def test_exact_geometry_fixture(self):
  r=json.loads((ROOT/'reports/motherboard-status-20260930/native-geometry/receipt.json').read_text());self.assertEqual(r['native_load_parts'],289);self.assertEqual(r['native_numbered_pads'],853);self.assertTrue(r['geometry_pass']);self.assertFalse(r['ignored_checks']);self.assertTrue(r['unrouted_geometry_fixture']);self.assertFalse(r['manufacturing_ready'])
 def test_native_pin_mutation_detected(self):
  with tempfile.TemporaryDirectory() as t:
   e=ET.parse(OUT/'netlist.xml');target=self.base['rgb_driver_refs'][0]
   for n in e.findall('./nets/net'):
    for node in list(n):
     if node.tag=='node' and node.get('ref')==target and node.get('pin')=='25':node.set('pin','26')
   p=Path(t)/'bad.xml';e.write(p);self.assertFalse(validate(self.base,p)['ok'])
 def test_native_ignoredERC_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['pin_to_pin'];p=Path(t)/'bad.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])
if __name__=='__main__':unittest.main()
