"""Actual pin/default negative controls and abstract circuit latch sequences."""
import copy,itertools,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_process import validate
OUT=ROOT/'hardware/motherboard_process'

def trace_circuit(d,events):
 """Ideal truth-table traversal of drawn gates; no timing/HDL/physical claim."""
 parts=d['components'];latches=[x for x in parts.values() if x['kind']=='DFF'];gates=[x for x in parts.values() if x['kind'] in ['AND1','AND4']];s={'IO_3V3':1,'LOGIC_GND':0};s.update({x['pins']['5']:0 for x in latches});old={};out=[]
 def settle():
  for _ in range(12):
   for x in gates:
    pins=x['pins'];triples=[('1','2','4')] if x['kind']=='AND1' else [('1','2','3'),('4','5','6'),('9','10','8'),('12','13','11')]
    for a,b,y in triples:s[pins[y]]=int(bool(s.get(pins[a],0) and s.get(pins[b],0)))
   for x in latches:
    if not s.get(x['pins']['6'],0):s[x['pins']['5']]=0
 for e in events:
  s.update(e);settle()
  for x in latches:
   pins=x['pins'];clk=s.get(pins['1'],0)
   if s.get(pins['6'],0) and clk and not old.get(pins['1'],0):s[pins['5']]=s.get(pins['2'],0)
  old={x['pins']['1']:s.get(x['pins']['1'],0) for x in latches};settle();out.append(copy.deepcopy(s))
 return out

class ProcessSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=json.loads((OUT/'design.json').read_text())
 def changed(self,fn):
  d=copy.deepcopy(self.base);fn(d);self.assertFalse(validate(d)['ok'])
 def test_exact_native_source(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json')['ok'])
 def test_LVC2T45_direction_cannot_swap(self):self.changed(lambda d:d['components'][d['PWM_channels'][0]['driver_ref']]['pins'].__setitem__('5','LOGIC_GND'))
 def test_LVC2T45_B1_B2_not_mirrored(self):self.changed(lambda d:d['components'][d['PWM_channels'][0]['driver_ref']]['pins'].__setitem__('7','PWM1_DRIVER'))
 def test_external_driver_output_not_FPGA3V3(self):self.changed(lambda d:d['components'][d['PWM_channels'][0]['driver_ref']]['pins'].__setitem__('8','IO_3V3'))
 def test_sourcing20mA_not_claimed80(self):self.changed(lambda d:d['PWM_channels'][0].__setitem__('continuous_source_sink_a',.08))
 def test_ideal5V_at20mA_claim_rejected(self):self.changed(lambda d:d['PWM_channels'][0].__setitem__('loaded_VOH_min_screen_v',5))
 def test_clamp_MOS_actual_G_S_D(self):self.changed(lambda d:d['components'][d['PWM_channels'][0]['clamp_ref']]['pins'].__setitem__('1','LOGIC_GND'))
 def test_high_threshold100VMOS_not_low_voltage_clamp(self):self.changed(lambda d:d['components'][d['PWM_channels'][0]['clamp_ref']].__setitem__('mpn','CSD19538Q3AT'))
 def test_poweroff_clamp_not_only_software(self):self.changed(lambda d:d['PWM_channels'][0].__setitem__('noIO3_clamp_ON',False))
 def test_gate_sink_pushpull_not_open_drain(self):self.changed(lambda d:d['components'][d['clamp_gate_ref']].__setitem__('mpn','SN74LVC1G04DBVR'))
 def test_gate_bias_cannot_pull_off_in_missingIO3(self):self.changed(lambda d:next(x for x in d['components'].values() if x['kind']=='R' and x['pins']['1']=='PWM_CLAMP_GATE')['pins'].__setitem__('2','LOGIC_GND'))
 def test_live_receiver_backfeed_not_motion_rail(self):self.changed(lambda d:d['components'][d['PWM_channels'][0]['rail_clamp_ref']]['pins'].__setitem__('2','MOTION_5V_RAW'))
 def test_idealdiode_CE_cannot_ground_disable_RCB(self):self.changed(lambda d:d['components'][d['reverse_feed_ref']]['pins'].__setitem__('3','LOGIC_GND'))
 def test_idealdiode_input_output_not_reversed(self):self.changed(lambda d:d['components'][d['reverse_feed_ref']]['pins'].__setitem__('1','PWM_5V_INTERNAL'))
 def test_PROCESS_permission_loss_clears_latch(self):self.changed(lambda d:d['components'][d['process_clear_ref']]['pins'].__setitem__('2','IO_3V3'))
 def test_separate_process_latch_observation_real(self):self.changed(lambda d:d['components'][d['process_latch_ref']]['pins'].__setitem__('5','ACC_OUT_EN_LATCH'))
 def test_relay_supply_ON_not_tiedHIGH(self):self.changed(lambda d:d['components'][d['relay_supply_ref']]['pins'].__setitem__('3','IO_3V3'))
 def test_relay_LED_gate_independent_OFF(self):self.changed(lambda d:d['components'][d['process_channels'][0]['sink_ref']]['pins'].__setitem__('2','PEN0_CMD'))
 def test_relay_contacts_never_grounded(self):self.changed(lambda d:d['components'][d['process_channels'][0]['relay_ref']]['pins'].__setitem__('4','LOGIC_GND'))
 def test_NO_process_not_250VAC_rating(self):self.changed(lambda d:d['process_channels'][0].__setitem__('contact_v_max',250))
 def test_LED_IFT_screen_not_typical(self):self.changed(lambda d:d['process_channels'][0].__setitem__('LED_min_screen_a',.001))
 def test_bidirectionalcontact_TVS_preserved(self):self.changed(lambda d:d['components'][d['process_channels'][0]['tvs_ref']].__setitem__('bidirectional',False))
 def test_conditional50mA_limit_not_exact_max(self):self.changed(lambda d:d['aux_supply'].__setitem__('not_a_guaranteed_50mA_maximum',False))
 def test_unbounded1pct_aux_resistor_rejected(self):self.changed(lambda d:d['components'][d['aux_supply']['ilim_ref']].__setitem__('tolerance',.01))
 def test_latchoff_aux_cannot_autoretry(self):self.changed(lambda d:d['aux_supply'].__setitem__('latchoff',False))
 def test_currentlimit_short_cannot_groundCL(self):self.changed(lambda d:d['components'][d['aux_supply']['limiter_ref']]['pins'].__setitem__('4','LOGIC_GND'))
 def test_500mA_USB_switch_not_50mA_aux(self):self.changed(lambda d:d['components'][d['aux_supply']['limiter_ref']].__setitem__('mpn','TPS2051BDBVR'))
 def test_no_fitted_boundary_connector(self):self.changed(lambda d:d['boundaries']['J14403'].__setitem__('physical',True))
 def test_no_physical_measurement_from_ERC(self):self.changed(lambda d:d.__setitem__('physical_qualification',True))
 def test_nativeXML_pin_drift_rejected(self):
  tree=ET.parse(OUT/'netlist.xml');net=next(n for n in tree.findall('nets/net') if n.attrib['name'].removeprefix('/')=='PWM0');net.attrib['name']='BROKEN_PWM0'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.xml';tree.write(p,encoding='utf-8');self.assertFalse(validate(self.base,p)['ok'])
 def test_ignoredERC_not_accepted(self):
  e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['pin_to_pin']
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])
 def test_permissions_alone_do_not_arm(self):
  s=trace_circuit(self.base,[{'OUT_PERMIT_ACC':1,'PROC_PERMIT':1,'ACC_CONTROLLER_RESET_N':1,'ACC_CARD_EN':1,'PWM0_FPGA':1,'PEN0_CMD':1}])[-1];self.assertEqual((s['PWM0_GATED'],s['PEN0_LED_REQUEST']),(0,0))
 def test_process_permission_return_needs_new_edge(self):
  s=trace_circuit(self.base,[{'OUT_PERMIT_ACC':1,'PROC_PERMIT':1,'ACC_CONTROLLER_RESET_N':1,'ACC_CARD_EN':1,'PWM0_FPGA':1,'PEN0_CMD':1,'ACC_IO_ENABLE_STROBE':0},{'ACC_IO_ENABLE_STROBE':1},{'PROC_PERMIT':0},{'PROC_PERMIT':1},{'ACC_IO_ENABLE_STROBE':0},{'ACC_IO_ENABLE_STROBE':1}]);self.assertEqual([x['PEN0_LED_REQUEST'] for x in s],[0,1,0,0,0,1]);self.assertEqual(s[2]['PWM0_GATED'],1)
 def test_output_permission_return_needs_new_edge(self):
  s=trace_circuit(self.base,[{'OUT_PERMIT_ACC':1,'PROC_PERMIT':1,'ACC_CONTROLLER_RESET_N':1,'ACC_CARD_EN':1,'PWM1_FPGA':1,'PEN1_CMD':1,'ACC_IO_ENABLE_STROBE':0},{'ACC_IO_ENABLE_STROBE':1},{'OUT_PERMIT_ACC':0},{'OUT_PERMIT_ACC':1},{'ACC_IO_ENABLE_STROBE':0},{'ACC_IO_ENABLE_STROBE':1}]);self.assertEqual([x['PWM1_GATED'] for x in s],[0,1,0,0,0,1]);self.assertEqual([x['PEN1_LED_REQUEST'] for x in s],[0,1,0,0,0,1])
 def test_missing_controller_reset_inhibits_even_strobe(self):
  for out,proc,cmd in itertools.product([0,1],repeat=3):
   s=trace_circuit(self.base,[{'OUT_PERMIT_ACC':out,'PROC_PERMIT':proc,'ACC_CONTROLLER_RESET_N':0,'ACC_CARD_EN':1,'PWM0_FPGA':cmd,'PEN0_CMD':cmd},{'ACC_IO_ENABLE_STROBE':1}])[-1];self.assertEqual((s['PWM0_GATED'],s['PEN0_LED_REQUEST']),(0,0))

if __name__=='__main__':unittest.main()
