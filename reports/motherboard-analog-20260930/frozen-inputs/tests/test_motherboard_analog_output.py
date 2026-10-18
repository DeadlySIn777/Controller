"""Electrical-source failure injection; this does not simulate silicon or motion."""
import copy,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_analog_output import validate
OUT=ROOT/'hardware/motherboard_analog_output'
class AnalogOutputSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=json.loads((OUT/'design.json').read_text())
 def changed(self,fn):
  d=copy.deepcopy(self.base);fn(d);self.assertFalse(validate(d)['ok'])
 def part(self,d,key,i=0):return d['components'][d['channels'][i][key]]
 def test_native_exact_source(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json')['ok'])
 def test_plain_AD5683R_part_lacks_SDO(self):self.changed(lambda d:self.part(d,'dac_ref').__setitem__('mpn','AD5683RBRMZ'))
 def test_old_DAC80501_no_SPI_SDO(self):self.changed(lambda d:self.part(d,'dac_ref').__setitem__('mpn','DAC80501ZDQFR'))
 def test_SDO_and_RESET_not_interchanged(self):self.changed(lambda d:self.part(d,'dac_ref')['pins'].__setitem__('3','AO0_DAC_RESET_N'))
 def test_actual_DAC_LDAC_cannot_float(self):self.changed(lambda d:self.part(d,'dac_ref')['pins'].__setitem__('4',None))
 def test_ref_cannot_be_supply_strap(self):self.changed(lambda d:self.part(d,'dac_ref')['pins'].__setitem__('9','AO0_5V'))
 def test_LDO_DNC2_must_not_ground(self):self.changed(lambda d:self.part(d,'regulator_ref')['pins'].__setitem__('2','AO0_COM'))
 def test_LDO_EP_is_local_return(self):self.changed(lambda d:self.part(d,'regulator_ref')['pins'].__setitem__('9','LOGIC_GND'))
 def test_LDO_other_DGN_EP_not_same(self):self.changed(lambda d:self.part(d,'regulator_ref').__setitem__('footprint','CNC_MB_Process:TPS1H000_DGN8_TI'))
 def test_DCDC_pin5_not_fakecommon(self):self.changed(lambda d:self.part(d,'power_module_ref')['pins'].__setitem__('5','AO0_COM'))
 def test_DCDC_inputreturn_not_field(self):self.changed(lambda d:self.part(d,'power_module_ref')['pins'].__setitem__('1','AO0_COM'))
 def test_islands_not_return_joined(self):self.changed(lambda d:self.part(d,'power_module_ref',1)['pins'].__setitem__('6','AO0_COM'))
 def test_IO3_enable_cannot_bypass_rearm(self):self.changed(lambda d:self.part(d,'host_enable_gate_ref')['pins'].__setitem__('2','IO_3V3'))
 def test_local_enable_requires_real_powergood(self):self.changed(lambda d:self.part(d,'local_enable_gate_ref')['pins'].__setitem__('2','AO0_5V'))
 def test_host_permissionloss_resets_DAC(self):self.changed(lambda d:self.part(d,'spi_isolator_ref')['pins'].__setitem__('6','IO_3V3'))
 def test_F_defaultLOW_required(self):self.changed(lambda d:self.part(d,'spi_isolator_ref').__setitem__('mpn','ISO7761DWR'))
 def test_SPI_isolator_fifth_forward_reset_pin(self):self.changed(lambda d:self.part(d,'spi_isolator_ref')['pins'].__setitem__('11','AO0_ENABLE_ISOLATED'))
 def test_pushpull_returns_not_permanently_merged(self):self.changed(lambda d:self.part(d,'spi_return_buffer_ref')['pins'].__setitem__('1','LOGIC_GND'))
 def test_NC_clamp_not_NO_part(self):self.changed(lambda d:self.part(d,'input_clamp_ref').__setitem__('mpn','TLP3640A(TPL,E'))
 def test_NC_package_different_from_NO(self):self.changed(lambda d:self.part(d,'input_clamp_ref').__setitem__('footprint','CNC_MB_AO:TLP3640A_SO4_11-3C1'))
 def test_NO_disconnect_not_NC_part(self):self.changed(lambda d:self.part(d,'output_disconnect_ref').__setitem__('mpn','TLP4176A(TP,F'))
 def test_zero_uses_inputclamp_not_short_DAC(self):self.changed(lambda d:self.part(d,'input_clamp_ref')['pins'].__setitem__('3','AO0_DAC_VOUT'))
 def test_gain4_actual_amp_pinmap(self):self.changed(lambda d:self.part(d,'amplifier_ref')['pins'].__setitem__('3','AO0_FEEDBACK'))
 def test_analog12V_not5V_headroom(self):self.changed(lambda d:self.part(d,'amplifier_ref')['pins'].__setitem__('5','AO0_5V'))
 def test_readback_observes_terminal_not_commandDAC(self):self.changed(lambda d:self.part(d,'readback_adc_ref')['pins'].__setitem__('4','AO0_DAC_VOUT'))
 def test_reference_actual_adcchannel(self):self.changed(lambda d:self.part(d,'readback_adc_ref')['pins'].__setitem__('7','AO0_5V'))
 def test_adc_addresses_not_both48(self):self.changed(lambda d:self.part(d,'readback_adc_ref',1)['pins'].__setitem__('1','AO1_COM'))
 def test_I2C_isolation_keeps_correct_returns(self):self.changed(lambda d:self.part(d,'i2c_isolator_ref')['pins'].__setitem__('5','LOGIC_GND'))
 def test_clampobserved_voltage_not_commandbit(self):self.changed(lambda d:self.part(d,'clamp_observer_ref')['pins'].__setitem__('2','AO0_RUN'))
 def test_missing_domain_not_healthy(self):self.changed(lambda d:self.part(d,'health_isolator_ref').__setitem__('mpn','ISO7720DWR'))
 def test_no_false_8MHz_readback_latencyproof(self):self.changed(lambda d:d['contract_correction']['wire_time_only'].__setitem__('spi_hz',8000000))
 def test_input_register_not_independent_DAC_latch(self):self.changed(lambda d:d['channels'][0].__setitem__('no_independent_internal_DAC_latch_readout',False))
 def test_readback_contact_voltage_not_contactproof(self):self.changed(lambda d:d['channels'][0].__setitem__('contact_drive_observation_not_contact_proof',False))
 def test_two_kohm_receiver_not_silent10k_reduction(self):self.changed(lambda d:d['electrical_limits'].__setitem__('receiver_min_ohm',10000))
 def test_no_native_source_manufacturingclaim(self):self.changed(lambda d:d.__setitem__('manufacturing_ready',True))
 def test_nativeXML_drift_rejected(self):
  t=ET.parse(OUT/'netlist.xml');net=next(n for n in t.findall('nets/net') if n.attrib['name'].removeprefix('/')=='AO0_DAC_SDO');net.attrib['name']='FAKE_DAC_CACHE'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.xml';t.write(p);self.assertFalse(validate(self.base,netlist=p)['ok'])
 def test_ignoredERC_not_accepted(self):
  e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['ground_pin_not_ground']
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])
 def test_other_ERC_error_not_accepted(self):
  e=json.loads((OUT/'erc.json').read_text());e['sheets'][0]['violations'][0]['severity']='error'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])
if __name__=='__main__':unittest.main()
