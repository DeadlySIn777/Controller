"""Fourth-node source/native tests and failure injection, no target claims."""
import copy,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_acc_control import validate
OUT=ROOT/'hardware/motherboard_acc_control'
class ACCControlTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=json.loads((OUT/'design.json').read_text());cls.process=json.loads((ROOT/'hardware/motherboard_process/design.json').read_text())
 def changed(self,fn):
  d=copy.deepcopy(self.base);fn(d);self.assertFalse(validate(d,process=self.process)['ok'])
 def test_native_exact_source_and_process(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json',self.process)['ok'])
 def test_K32_lacks_actual_selected_AI_SPI_GPIO(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']].__setitem__('mpn','STM32G031K8T6'))
 def test_QFN_EP_map_cannot_replace_LQFP(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']].__setitem__('footprint','Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm'))
 def test_SPI2_actual_output_pin(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']]['pins'].__setitem__('25','AI_SDI_HOST'))
 def test_AO0_CS_real_PB3_GPIO(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']]['pins'].__setitem__('42',None))
 def test_AO1_CS_real_PB4_GPIO(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']]['pins'].__setitem__('43','AO0_CS_N_HOST'))
 def test_AO_CS_defaults_deselected(self):
  self.changed(lambda d:next(q for q in d['components'].values() if q['kind']=='R' and q['pins']=={'1':'AO0_CS_N_HOST','2':'IO_3V3'})['pins'].__setitem__('2','LOGIC_GND'))
 def test_real_SPI2_not_inherited_I2C_DAC(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('interface','I2C'))
 def test_native_source_not_target_AO_firmware(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('target_firmware_implemented',True))
 def test_I2C_pin_AF6_not_SPI_AF(self):self.changed(lambda d:d['peripheral_mapping']['AO_I2C1'].__setitem__('PB8','SCL_AF1_open_drain'))
 def test_host_response_cannot_swap_AI_MISO(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']]['pins'].__setitem__('17','AI_SDO_HOST'))
 def test_process_latch_observation_not_constant(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']]['pins'].__setitem__('14','IO_3V3'))
 def test_current_PWM_fault_is_observed(self):self.changed(lambda d:d['components'][d['node']['mcu_ref']]['pins'].__setitem__('23',None))
 def test_real_slot3_not_slot1(self):self.changed(lambda d:d['node'].__setitem__('slot',1))
 def test_output_class_not_DI(self):self.changed(lambda d:d['node'].__setitem__('class',0x11))
 def test_logical_region_not_removable_customcard(self):self.changed(lambda d:d['logical_contract'].__setitem__('same_board_region_not_card',False))
 def test_no_automatic_rearm_after_returned_permission(self):self.changed(lambda d:d['logical_contract'].__setitem__('no_automatic_rearm',False))
 def test_invalid_frame_cannot_refresh_watchdog(self):self.changed(lambda d:d['logical_contract'].__setitem__('validate_before_outputs_and_watchdog',False))
 def test_watchdog_uses_min_LSI_not_nominal(self):self.changed(lambda d:d['iwdg_candidate'].__setitem__('LSI_min_hz',32000))
 def test_watchdog_512ms_reset_reload_not_finalsetting(self):self.changed(lambda d:d['iwdg_candidate'].__setitem__('RLR',4095))
 def test_software_start_not_hardware_watchdog(self):self.changed(lambda d:d['option_requirements'].__setitem__('IWDG_SW',1))
 def test_NRST_input_only_hides_internal_watchdog(self):self.changed(lambda d:d['option_requirements'].__setitem__('NRST_MODE',1))
 def test_missing_iso_monitor_not_healthy(self):self.changed(lambda d:d['node']['health_inputs']['AO0_POWER_GOOD_HOST'].__setitem__('active_good',0))
 def test_fault_monitor_not_claimed_implemented(self):self.changed(lambda d:d['node']['health_inputs']['AI_SENSOR_FAULT_HOST'].__setitem__('monitor_implemented',True))
 def test_real_analog_enable_request_defaults_OFF(self):
  self.changed(lambda d:next(p for p in d['components'].values() if p['kind']=='R' and p['pins']=={'1':'AO0_ENABLE_REQUEST','2':'LOGIC_GND'})['pins'].__setitem__('2','IO_3V3'))
 def test_no_invented_DAC_SPI_readback(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('selected_DAC','DAC80501ZDQFR'))
 def test_DAC_buffer_readback_not_measured_analogvoltage(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('readback_is_buffer_register_not_measured_VOUT',False))
 def test_synchronous_DAC_buffer_not_applied_readback(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('asynchronous_update_required',False))
 def test_nativeERC_not_target_firmware(self):self.changed(lambda d:d.__setitem__('target_compilation_passed',True))
 def test_fixedCT_not_grounded(self):self.changed(lambda d:d['components'][d['node']['supervisor_ref']]['pins'].__setitem__('4','LOGIC_GND'))
 def test_TI125_noIoff_not_returned(self):self.changed(lambda d:d['components'][d['node']['link_buffer_ref']].__setitem__('mpn','SN74LVC125APWR'))
 def test_reset_buffer_drives_separate_frontend(self):self.changed(lambda d:d['components'][d['node']['reset_buffer_ref']]['pins'].__setitem__('4','ACC_NRST_N'))
 def test_existing_offbias_not_removed(self):
  p=copy.deepcopy(self.process);p['components']['R14405']['pins']['2']='IO_3V3';self.assertFalse(validate(self.base,process=p)['ok'])
 def test_frontend_OFFbias_not_fitted_twice(self):
  def edit(d):
   q=copy.deepcopy(next(x for x in d['components'].values() if x['kind']=='R'));q['pins']={'1':'ACC_CARD_EN','2':'LOGIC_GND'};q['resistance_ohm']=10000;d['components']['R14599']=q
  self.changed(edit)
 def test_no_fitted_boundary_connector(self):self.changed(lambda d:d['boundaries']['J14501'].__setitem__('physical',True))
 def test_factory_pad_not_charged_as_part(self):self.changed(lambda d:d.__setitem__('purchased_fitted_parts',50))
 def test_nativeXML_drift_caught(self):
  t=ET.parse(OUT/'netlist.xml');n=next(n for n in t.findall('nets/net') if n.attrib['name'].removeprefix('/')=='PEN_OUT_EN_LATCH');n.attrib['name']='NOT_PEN_LATCH'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.xml';t.write(p);self.assertFalse(validate(self.base,netlist=p)['ok'])
 def test_ignoredERC_rejected(self):
  e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['pin_to_pin']
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])
if __name__=='__main__':unittest.main()
