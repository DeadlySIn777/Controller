"""Meaningful negative controls on actual pins/defaults and interface ownership."""
import copy,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_io_control import validate
OUT=ROOT/'hardware/motherboard_io_control'

class IOL1SourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=json.loads((OUT/'design.json').read_text());cls.di=json.loads((ROOT/'hardware/motherboard_di/design.json').read_text());cls.do=json.loads((ROOT/'hardware/motherboard_do/design.json').read_text())
 def changed(self,fn):
  d=copy.deepcopy(self.base);fn(d);r=validate(d,di=self.di,do=self.do);self.assertFalse(r['ok'],r)
 def test_exact_native_source_and_frontends(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json',self.di,self.do)['ok'])
 def test_twenty_fourth_DI_is_acquired(self):self.changed(lambda d:d['components'][d['nodes'][0]['mcu_ref']]['pins'].__setitem__('33',None))
 def test_DI_cannot_be_aliased_to_motor_alarm(self):self.changed(lambda d:d['components'][d['nodes'][0]['mcu_ref']]['pins'].__setitem__('1','ALM0_FPGA'))
 def test_GPIO_name_doesnot_replace_exact_package_pin(self):self.changed(lambda d:d['nodes'][0]['pin_port_names'].__setitem__('33','PA9'))
 def test_hostSPI_cannot_use_wrong_AF_gpio(self):self.changed(lambda d:d['components'][d['nodes'][1]['mcu_ref']]['pins'].__setitem__('11','DOA_SCLK_HOST'))
 def test_driverSPI_return_direction_is_real(self):self.changed(lambda d:d['components'][d['nodes'][1]['mcu_ref']]['pins'].__setitem__('30','DOA_SDI_HOST'))
 def test_different_package_pin_pitch_rejected(self):self.changed(lambda d:d['components'][d['nodes'][1]['mcu_ref']].__setitem__('footprint','Package_QFP:LQFP-32_7x7mm_P0.5mm'))
 def test_per_node_reset_cannot_be_shortened_into_one(self):self.changed(lambda d:d['components'][d['nodes'][2]['supervisor_ref']]['pins'].__setitem__('1','DOA_NRST_N'))
 def test_supervisor_CT_ground_not_open20ms(self):self.changed(lambda d:d['components'][d['nodes'][0]['supervisor_ref']]['pins'].__setitem__('4','LOGIC_GND'))
 def test_supervisor_RESET_and_SENSE_cannot_swap(self):self.changed(lambda d:d['components'][d['nodes'][0]['supervisor_ref']]['pins'].__setitem__('5','DIC_NRST_N'))
 def test_unsupported_nominal_LSI_watchdog_screen_rejected(self):self.changed(lambda d:d['iwdg_candidate'].__setitem__('LSI_min_hz',32000))
 def test_512ms_reset_reload_not_active_configuration(self):self.changed(lambda d:d['iwdg_candidate'].__setitem__('RLR',4095))
 def test_iwdg_software_start_not_guaranteed_hardware_start(self):self.changed(lambda d:d['option_requirements'].__setitem__('IWDG_SW',1))
 def test_NRST_input_only_hides_internal_watchdog_reset(self):self.changed(lambda d:d['option_requirements'].__setitem__('NRST_MODE',1))
 def test_independent_watchdog_not_application_timer(self):self.changed(lambda d:d['iwdg_candidate'].__setitem__('application_refresh_only_full_accept',False))
 def test_debug_freeze_not_shipping_watchdog(self):self.changed(lambda d:d['iwdg_candidate'].__setitem__('no_debug_freeze_in_shipping',False))
 def test_unprovisioned_option_bytes_not_claimed_verified(self):self.changed(lambda d:d['nodes'][0].__setitem__('programmed_option_bytes_verified',True))
 def test_TI_buffer_without_IOFF_cannot_return(self):self.changed(lambda d:d['components'][d['nodes'][0]['link_buffer_ref']].__setitem__('mpn','SN74LVC125APWR'))
 def test_IOFF_not_typical_leakage(self):self.changed(lambda d:d['link_poweroff_review'].__setitem__('IOFF_VCC0_VI_or_VO5_5_max_a',.1e-6))
 def test_partial_power_spec_not_brownout_measurement(self):self.changed(lambda d:d['link_poweroff_review'].__setitem__('powered_brownout_qualified',True))
 def test_nativeERC_not_target_firmware(self):self.changed(lambda d:d.__setitem__('target_compilation_passed',True))
 def test_missing_sensor_monitor_is_not_healthy(self):self.changed(lambda d:d['nodes'][0]['health_inputs']['DI_SENSOR_G0_FAULT'].__setitem__('active_fault',0))
 def test_missing_field_monitor_cannot_be_marked_implemented(self):self.changed(lambda d:d['nodes'][1]['health_inputs']['DOA_FIELD_POWER_GOOD'].__setitem__('parent_monitor_implemented',True))
 def test_missing_field_good_bias_cannot_be_pulledUP(self):
  self.changed(lambda d:next(p for p in d['components'].values() if p['kind']=='R' and p['pins']=={'1':'DOA_FIELD_POWER_GOOD','2':'LOGIC_GND'})['pins'].__setitem__('2','IO_3V3'))
 def test_real_latch_observation_not_constanthealthy(self):self.changed(lambda d:d['components'][d['nodes'][1]['mcu_ref']]['pins'].__setitem__('9','IO_3V3'))
 def test_reset_buffer_can_never_swap_input_output(self):self.changed(lambda d:d['components'][d['nodes'][1]['reset_buffer_ref']]['pins'].__setitem__('2','DOA_CONTROLLER_RESET_N'))
 def test_reset_pushpull_not_direct_NRST_divider(self):self.changed(lambda d:d['components'][d['nodes'][1]['reset_buffer_ref']]['pins'].__setitem__('4','DOA_NRST_N'))
 def test_resolved_duplicate_biases_not_reintroduced(self):
  def edit(d):
   d['components']['R13025']={'kind':'R','mpn':'CRCW060310K0FKEA','value':'10000R1%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':'DOA_CARD_EN','2':'LOGIC_GND'},'resistance_ohm':10000}
  self.changed(edit)
 def test_frontend_owned_pulldown_cannot_disappear(self):
  do=copy.deepcopy(self.do);do['components']['R10004']['pins']['2']='IO_3V3';self.assertFalse(validate(self.base,do=do)['ok'])
 def test_slot_strap_wrong_bank_cannot_be_accepted(self):self.changed(lambda d:d['nodes'][2].__setitem__('slot',1))
 def test_port0_class_doesnot_become_output_class(self):self.changed(lambda d:d['nodes'][0].__setitem__('class',0x21))
 def test_obsolete_bulk_MPN_not_reintroduced(self):self.changed(lambda d:next(p for p in d['components'].values() if p['kind']=='C' and p['capacitance_f']==4700e-9).__setitem__('mpn','GRM21BR71A475KA73L'))
 def test_wrong_bulk_voltage_not_accepted(self):self.changed(lambda d:next(p for p in d['components'].values() if p['kind']=='C' and p['capacitance_f']==4700e-9).__setitem__('voltage_rating_v',2.5))
 def test_external_VREF_cannot_enable_internal_buffer(self):self.changed(lambda d:d['option_requirements'].__setitem__('DIC_VREFBUF_disabled_with_external_VREF',False))
 def test_factory_pad_not_purchased_connector(self):self.changed(lambda d:d['nodes'][0]['factory_pads'].pop())
 def test_unselected_boundary_cannot_be_physical_card(self):self.changed(lambda d:d['boundaries']['J13001'].__setitem__('physical',True))
 def test_nativeXML_pin_drift_independently_detected(self):
  tree=ET.parse(OUT/'netlist.xml');net=next(n for n in tree.findall('nets/net') if n.attrib['name'].removeprefix('/')=='DIC_IOL1_CS_MCU');net.attrib['name']='DIC_IOL1_BAD_CS_MCU'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'wrong.xml';tree.write(p,encoding='utf-8');self.assertFalse(validate(self.base,p,di=self.di,do=self.do)['ok'])
 def test_ERC_ignored_checks_rejected(self):
  e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['pin_to_pin']
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'wrong.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])

if __name__=='__main__':unittest.main()
