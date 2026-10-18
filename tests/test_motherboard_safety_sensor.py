"""Meaningful exact-pin/domain/default negative controls, disconnected only."""
import copy,itertools,json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_safety_sensor import validate
from hardware_apply_motherboard_safety_sensor import apply_safety_sensor_endpoints
from hardware_build_assembly import parse,dump
OUT=ROOT/'hardware/motherboard_safety_sensor'
class SafetySensor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=json.loads((OUT/'design.json').read_text())
 def bad(self,fn):
  d=copy.deepcopy(self.base);fn(d);self.assertFalse(validate(d)['ok'])
 def test_native_exact_source(self):self.assertTrue(validate(self.base,OUT/'netlist.xml',OUT/'erc.json')['ok'])
 def test_general_inputs_not_reused(self):self.bad(lambda d:d.__setitem__('general_DI_unchanged',False))
 def test_six_safety_receivers_not_four(self):self.bad(lambda d:d.__setitem__('XS1_dedicated_input_count',4))
 def test_ISO_receiver_polarity_ground(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='ISO1212')['pins'].__setitem__('9','LOGIC_GND'))
 def test_SUB_cannot_ground(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='ISO1212')['pins'].__setitem__('13','FIELD_B_0V'))
 def test_safety_input_always_enable(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='ISO1212')['pins'].__setitem__('3','LOGIC_GND'))
 def test_sensor_group_A_return_cannot_replaceB(self):self.bad(lambda d:d['components'][d['sensor_groups'][1]['limiter_ref']]['pins'].__setitem__('9','FIELD_GND'))
 def test_group_unprotected_main_supply(self):self.bad(lambda d:d['components'][d['sensor_groups'][0]['limiter_ref']]['pins'].__setitem__('1','FIELD_B_24V_INPUT'))
 def test_limit_resistor_not_interpolated_TPS(self):self.bad(lambda d:d['components'][d['sensor_groups'][0]['limiter_ref']].__setitem__('mpn','TPS26624DRCR'))
 def test_sensor_current_accuracy_not_typical(self):self.bad(lambda d:d['sensor_groups'][0].__setitem__('guaranteed_limit_accuracy_fraction',.01))
 def test_transient_peak_not_claimed_from_static(self):self.bad(lambda d:d['sensor_groups'][0].__setitem__('transient_short_overshoot_qualified',True))
 def test_SAFE_actual_supply_no_fixed_constant(self):self.bad(lambda d:d['components'][d['safe_limiter_ref']]['pins'].__setitem__('7','FIELD_B_24V_PROTECTED'))
 def test_SAFE_50mA_not_too_low_nominal_row(self):self.bad(lambda d:d['components'][d['safe_ilim_ref']].__setitem__('resistance_ohm',10000))
 def test_LED_current_not243R(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='R' and c['pins']['2']=='EXT_PERMIT_HEALTH_LED_A').__setitem__('resistance_ohm',243))
 def test_health_monitor_rail_not_metadata(self):self.bad(lambda d:d['components'][d['safe_monitor_ref']]['pins'].__setitem__('12','IO_3V3'))
 def test_RAW_EXT_cannot_skip_healthcontact(self):self.bad(lambda d:d['components'][d['safe_health_contacts'][0]]['pins'].__setitem__('4','EXT_PERMIT_RAW'))
 def test_PROCESS_contact_independent_motion(self):self.bad(lambda d:d['components'][d['safe_health_contacts'][1]]['pins'].__setitem__('4','EXT_PERMIT_3V3'))
 def test_NO_external_contact_floating(self):self.bad(lambda d:d['components'][d['permit_contact_ref']]['pins'].__setitem__('4','LOGIC_GND'))
 def test_external_selftest_request_required(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='AND_TTL')['pins'].__setitem__('1','CORE_5V'))
 def test_field_fault_transfer_not_constant_good(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='ISO7760F')['pins'].__setitem__('5','DOB_FIELD_3V3'))
 def test_ADC_channels_real_postlimiter(self):self.bad(lambda d:d['components'][d['adc_ref']]['pins'].__setitem__('4','IO_3V3'))
 def test_I2C_sideGND_not_short_domains(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='ISO1540')['pins'].__setitem__('5','LOGIC_GND'))
 def test_analog_switch_is_powerqualified(self):self.bad(lambda d:next(c for c in d['components'].values() if c['kind']=='MUX')['pins'].__setitem__('1','DOB_FIELD_3V3'))
 def test_B_preregulator_source_loop_preserved(self):self.bad(lambda d:d['components'][d['field_B_preregulator_clone_map']['L11003']]['pins'].__setitem__('2','FIELD_5V'))
 def test_B_LDO_wrong_enable_override(self):self.bad(lambda d:d['required_LDO_pin_changes']['U11018.5'].__setitem__('new','CORE_5V'))
 def test_DIC_existing_health_pin_not_reassigned(self):self.bad(lambda d:d['required_DIC_pin_changes'].__setitem__('U13001.40',d['required_DIC_pin_changes'].pop('U13001.42')))
 def test_manufacture_claim_refused(self):self.bad(lambda d:d.__setitem__('manufacturing_ready',True))
 def test_native_pin_mutation_refused(self):
  t=ET.parse(OUT/'netlist.xml');n=next(n for n in t.findall('nets/net') if n.get('name').lstrip('/')=='SAFE_24V');n.set('name','FAKE_SUPPLY')
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.xml';t.write(p);self.assertFalse(validate(self.base,p)['ok'])
 def test_native_ERC_suppression_refused(self):
  e=json.loads((OUT/'erc.json').read_text());e['ignored_checks']=['power_pin_not_driven']
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.json';p.write_text(json.dumps(e));self.assertFalse(validate(self.base,erc=p)['ok'])
 def test_safety_and_process_ideal_truth(self):
  # Drawn NO contacts perform two independent ANDs, no motion request authority.
  p=self.base['components'];q1=p[self.base['safe_health_contacts'][0]];q2=p[self.base['safe_health_contacts'][1]]
  for health,ext,proc in itertools.product([0,1],repeat=3):
   sig={'EXT_PERMIT_RAW':ext,'PROCESS_PERMIT_RAW':proc};result={q['pins']['4']:int(health and sig[q['pins']['3']]) for q in [q1,q2]}
   self.assertEqual(result,{'EXT_PERMIT_3V3':health&ext,'PROCESS_PERMIT_EXT_3V3':health&proc})
 def endpoint(self,scope):
  folder='motherboard_power_entry' if scope=='power_entry' else 'motherboard_io_control';m=json.loads((ROOT/'hardware'/folder/'design.json').read_text());t=parse((ROOT/'hardware'/folder/(folder+'.kicad_sch')).read_text());return t,m
 def test_power_override_exact_two_pins_only(self):
  t,m=self.endpoint('power_entry');old=copy.deepcopy(m);nt,nm,r=apply_safety_sensor_endpoints(t,m,'power_entry');self.assertEqual(m,old);a=copy.deepcopy(nm);a['components']['U11018']['pins']['5']=a['components']['U11018']['pins']['8']='FIELD_B_24V_PROTECTED';self.assertEqual(a,old);self.assertEqual(len(r['exact_endpoint_changes']),2)
 def test_DIC_override_exact_spares_only(self):
  t,m=self.endpoint('io_control');old=copy.deepcopy(m);nt,nm,r=apply_safety_sensor_endpoints(t,m,'io_control');self.assertEqual(m,old);a=copy.deepcopy(nm);a['components']['U13001']['pins']['42']=a['components']['U13001']['pins']['43']=None;self.assertEqual(a,old);self.assertEqual(len(r['exact_endpoint_changes']),2)
 def test_wrong_original_LDO_refuse(self):
  t,m=self.endpoint('power_entry');m['components']['U11018']['pins']['8']='FIELD_A_24V_PROTECTED'
  with self.assertRaises(ValueError):apply_safety_sensor_endpoints(t,m,'power_entry')
 def test_DIC_already_used_pin_refuse(self):
  t,m=self.endpoint('io_control');m['components']['U13001']['pins']['42']='HEALTH_EXISTING'
  with self.assertRaises(ValueError):apply_safety_sensor_endpoints(t,m,'io_control')
if __name__=='__main__':unittest.main()
