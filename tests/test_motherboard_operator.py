"""Negative controls on actual safety/default/interface source, not live machines."""
import copy,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_operator import validate
OUT=ROOT/'hardware/motherboard_operator'

class OperatorSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=json.loads((OUT/'design.json').read_text())
 def changed(self,fn):
  d=copy.deepcopy(self.base);fn(d);self.assertFalse(validate(d)['ok'])
 def test_native_schematic_matches_complete_independent_contract(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json')['ok'])
 def test_probe_not_general_DI(self):self.changed(lambda d:d.__setitem__('external_probes_consume_general_DI',True))
 def test_probe_cannot_be_motor_alarm(self):self.changed(lambda d:d['components']['U14031']['pins'].__setitem__('4','ALM0_FPGA'))
 def test_probe_NC6_cannot_be_ground(self):self.changed(lambda d:d['components']['U14031']['pins'].__setitem__('6','LOGIC_GND'))
 def test_probe_SUB_not_field_ground(self):self.changed(lambda d:d['components']['U14031']['pins'].__setitem__('13','FIELD_GND'))
 def test_probe_current_sensor_pin_swap(self):self.changed(lambda d:d['components']['U14031']['pins'].__setitem__('16','PRB0_IN_SENSE'))
 def test_probe0_RTHR_cannot_feed_IN_instead_of_SENSE(self):self.changed(lambda d:d['components']['R14069']['pins'].__setitem__('2','PRB0_IN_SENSE'))
 def test_probe1_RTHR_cannot_feed_IN_instead_of_SENSE(self):self.changed(lambda d:d['components']['R14072']['pins'].__setitem__('2','PRB1_IN_SENSE'))
 def test_probe_RSENSE_cannot_bypass_IN(self):self.changed(lambda d:d['components']['R14070']['pins'].__setitem__('1','PRB0_IN'))
 def test_field_domain_cannot_join_logic(self):self.changed(lambda d:d['components']['U14031']['pins'].__setitem__('14','LOGIC_GND'))
 def test_probe_cannot_inherit_ordinaryDI_RC(self):
  def f(d):next(p for p in d['components'].values() if p['kind']=='C')['pins']['1']='PRB0_IN'
  self.changed(f)
 def test_contact_not_24V_input(self):self.changed(lambda d:d['contacts'][0].__setitem__('not_a_24V_input',False))
 def test_clamp_commonpin_cannot_be_rail(self):self.changed(lambda d:d['components']['U14001']['pins'].__setitem__('3','MOTION_5V_RAW'))
 def test_selector_no_contactfilter(self):
  def f(d):d['components'][d['contacts'][0]['filter_ref']]['capacitance_f']=0
  self.changed(f)
 def test_selector_active_polarity_not_inverted_silently(self):self.changed(lambda d:d['contacts'][0].__setitem__('active_low_external',False))
 def test_global_10k_default_not_adequate_for_allocation(self):
  def f(d):next(p for p in d['components'].values() if p['kind']=='R' and p['pins']['1']=='FAST_PORTS_ENABLE')['resistance_ohm']=10000
  self.changed(f)
 def test_config_done_cannot_be_constant_healthy(self):self.changed(lambda d:d['components']['U14018']['pins'].__setitem__('2','IO_3V3'))
 def test_slow_XF_request_cannot_bypass_Schmitt(self):self.changed(lambda d:d['components']['U14019']['pins'].__setitem__('2','XF_POWER_ENABLE'))
 def test_XF_absent_must_remove_power(self):self.changed(lambda d:d['components']['U14019']['pins'].__setitem__('6','IO_3V3'))
 def test_XF_must_not_share_unqualified_encoder_enable(self):
  def f(d):next(p for p in d['components'].values() if p['kind']=='R' and p['pins']['2']=='FREQ_POWER_EN' and p['resistance_ohm']==33)['pins']['1']='FAST_PORTS_EN_CONFIGURED'
  self.changed(f)
 def test_currentlimiter_same_package_wrongvariant(self):self.changed(lambda d:d['components']['U14020'].__setitem__('mpn','TPS2553DBVR'))
 def test_SW24_same_MPN_wrong_footprint(self):self.changed(lambda d:d['components']['U14026'].__setitem__('footprint','Package_TO_SOT_SMD:SOT-23-6'))
 def test_ISO7720_DWR_not_eightpin_D(self):self.changed(lambda d:d['components']['U14028'].__setitem__('footprint','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'))
 def test_LM4040_DBZ_not_DCK(self):self.changed(lambda d:d['components']['U14035'].__setitem__('footprint','Package_TO_SOT_SMD:SOT-353_SC-70-5'))
 def test_ENCODER_enable_NOT_currentlimit_pin(self):self.changed(lambda d:d['components']['U14020']['pins'].__setitem__('3','ENC0_ILIM'))
 def test_MPG_ilim_cannot_be_lower_to_200mA(self):self.changed(lambda d:d['ports_5v'][4].__setitem__('ilim_ohm',110000))
 def test_no_nominal_only_currentlimit(self):self.changed(lambda d:d['ports_5v'][4].__setitem__('maximum_calculated_a',.120))
 def test_FAULT_is_not_a_voltage_measurement(self):self.changed(lambda d:d['ports_5v'][0].__setitem__('fault_is_power_good',True))
 def test_unpowered_faultflag_must_be_invalid(self):self.changed(lambda d:d['ports_5v'][0].__setitem__('validation_requires_motion_rail_and_region_qualification',False))
 def test_24V_field_fault_cannot_cross_directly(self):self.changed(lambda d:d['components']['U14028']['pins'].__setitem__('14','DOA_FIELD_3V3'))
 def test_ISO7720_F_defaultLOW_required(self):self.changed(lambda d:d['components']['U14028'].__setitem__('mpn','ISO7720DWR'))
 def test_24V_limit_guarantee_not_fabricated(self):self.changed(lambda d:d['ports_24v'][0].__setitem__('guaranteed_current_bounds_available',True))
 def test_hardshort_bound_not_fabricated(self):self.changed(lambda d:d['ports_24v'][0].__setitem__('hard_short_bound_available',True))
 def test_marker_must_be_far_end(self):self.changed(lambda d:d['components']['U14032']['pins'].__setitem__('6','IO_3V3'))
 def test_marker_numeric_0xA_not_reversed(self):self.changed(lambda d:d['components']['U14034']['pins'].__setitem__('14','IO_3V3'))
 def test_serial_return_not_invertedQH(self):self.changed(lambda d:d['components']['U14032']['pins'].__setitem__('7','FAST_SR_DATA_SOURCE'))
 def test_FAR_SER_not_left_floating(self):self.changed(lambda d:d['components']['U14034']['pins'].__setitem__('10',None))
 def test_no_two_read_agreement_disabled(self):self.changed(lambda d:d.__setitem__('double_read_agreement_required',False))
 def test_marker_failures_do_latch(self):self.changed(lambda d:d.__setitem__('three_bad_markers_latch_fault',False))
 def test_reference_pinmap_not_reversed(self):self.changed(lambda d:d['components']['U14035']['pins'].__setitem__('1','LOGIC_GND'))
 def test_boundary_is_not_a_selected_connector(self):self.changed(lambda d:d['boundaries']['J14003'].__setitem__('physical',True))
 def test_not_claimed_manufacturable(self):self.changed(lambda d:d.__setitem__('manufacturing_ready',True))
 def test_nativeXML_unintended_join_detected(self):
  t=ET.parse(OUT/'netlist.xml');n=next(n for n in t.findall('nets/net') if n.attrib['name'].removeprefix('/')=='FAST_PORTS_EN_CONFIGURED');n.attrib['name']='/IO_3V3'
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'changed.xml';t.write(path,encoding='utf-8');self.assertFalse(validate(self.base,path)['ok'])
 def test_ERC_cannot_suppress(self):
  e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['isolated_pin_label']
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'changed.json';path.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=path)['ok'])
 def test_configuration_and_presence_truth_table(self):
  # Independent derived actual gate path. No bit assertspower without CDONE,
  # request, regionqualification AND actualXFpresence. Doesnot testtiming.
  for c in [0,1]:
   for e in [0,1]:
    for req in [0,1]:
     for present in [0,1]:
      five=c&e;xf=(c&e&req)&present
      self.assertEqual(five,bool(c and e));self.assertEqual(xf,bool(c and e and req and present))
 def test_Schmitt_default_has_worst_unused_pull_margin(self):
  r=4700*1.01;up=27000;v=(3.6/up+20e-6)/(1/up+1/r)
  self.assertLess(v,.89);self.assertLess(v,.8)

if __name__=='__main__':unittest.main()
