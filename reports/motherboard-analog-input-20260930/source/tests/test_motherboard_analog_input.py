"""Source/default/pin/limit mutation controls; these do not simulate target hardware."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_analog_input import validate

class AnalogInputTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ROOT/'hardware/motherboard_analog_input/design.json').read_text())
 def test_native_source(self):self.assertTrue(validate(self.d,ROOT/'hardware/motherboard_analog_input/netlist.xml',ROOT/'hardware/motherboard_analog_input/erc.json')['ok'])
 def reject_pin(self,block,pin,net):
  self.d['components'][self.d['blocks'][block]]['pins'][str(pin)]=net;self.assertFalse(validate(self.d)['ok'])
 def test_incorrect_sar_suffix(self):self.d['components'][self.d['blocks']['adc']]['mpn']='ADS8684APWR';self.assertFalse(validate(self.d)['ok'])
 def test_adc_wrong_output_ball(self):self.reject_pin('adc',36,'AI_ADC_SDI')
 def test_adc_analogue_supply_wrong(self):self.reject_pin('adc',30,'IO_3V3')
 def test_adc_reset_strapped(self):self.reject_pin('adc',2,'AI_5V')
 def test_adc_gnd_swapped(self):self.reject_pin('adc',22,'AI3_N')
 def test_adc_range_pin_floating(self):self.reject_pin('adc',4,None)
 def test_sdo_ungated(self):self.reject_pin('return_buffer',1,'LOGIC_GND')
 def test_isolation_direction_wrong(self):self.reject_pin('spi_isolator',7,'AI_ADC_SDO')
 def test_reset_health_strapped(self):self.reject_pin('reset_gate',2,'AI_5V')
 def test_i2c_direction_wrong(self):self.reject_pin('i2c_isolator',6,'AI_I2C_SDA')
 def test_expander_wrong_address(self):self.reject_pin('mode_expander',1,'AI_5V')
 def test_expander_fault_faked(self):self.reject_pin('mode_expander',10,'AI_5V')
 def test_reference_dnc_is_not_enable(self):self.reject_pin('reference',1,'AI_5V')
 def test_limiter_wrong_ground(self):self.reject_pin('reference_limiter',2,'AI_AGND')
 def test_limiter_set_wrong_ground(self):
  q=next(q for q in self.d['components'].values() if q['kind']=='R' and q['pins'].get('1')=='AI_REF_SET');q['pins']['2']='AI_AGND';self.assertFalse(validate(self.d)['ok'])
 def test_feedback_before_limiter(self):
  q=next(q for q in self.d['components'].values() if q['kind']=='R' and q['pins']=={'1':'AI_REF_10V','2':'AI_REF_FB'});q['pins']['1']='AI_REF_DRIVE';self.assertFalse(validate(self.d)['ok'])
 def test_reference_minimumload_missing(self):
  q=next(q for q in self.d['components'].values() if q['kind']=='R' and q['pins']=={'1':'AI_REF_10V','2':'AI_AGND'});q['resistance_ohm']=1000000;self.assertFalse(validate(self.d)['ok'])
 def test_sensor_wrong_efuse_variant(self):self.d['components'][self.d['blocks']['sensor_efuse']]['mpn']='MAX17612AATB+T';self.assertFalse(validate(self.d)['ok'])
 def test_sensor_auto_retry(self):
  q=next(q for q in self.d['components'].values() if q['kind']=='R' and q['pins'].get('1')=='AI_SENSOR_CLMODE');q['resistance_ohm']=0;self.assertFalse(validate(self.d)['ok'])
 def test_sensor_reverse_status_faked(self):self.reject_pin('sensor_efuse',7,'AI_5V')
 def test_sensor_en_unpowered_weak_enable(self):self.reject_pin('sensor_efuse',5,None)
 def test_sensor_seti_ground_incorrect(self):self.reject_pin('sensor_efuse',9,'LOGIC_GND')
 def test_sensor_nominal100_not_guaranteed(self):
  q=next(q for q in self.d['components'].values() if q['kind']=='R' and q['pins'].get('1')=='AI_SENSOR_SETI');q['resistance_ohm']=3000;self.assertFalse(validate(self.d)['ok'])
 def test_sensor_current_units(self):self.d['power_budget']['sensor_static_limit_max_a']/=1000;self.assertFalse(validate(self.d)['ok'])
 def test_sensor_usable_100_claim(self):self.d['power_budget']['sensor_usable_a']=.1;self.assertFalse(validate(self.d)['ok'])
 def test_minimumload_wrong_820(self):self.d['components'][self.d['blocks']['dc24_bleed']]['resistance_ohm']=820;self.assertFalse(validate(self.d)['ok'])
 def test_minimumload_downstream(self):self.d['components'][self.d['blocks']['dc24_bleed']]['pins']['1']='AI_SENS_24V';self.assertFalse(validate(self.d)['ok'])
 def test_actual_terminal_telemetry_not_cache(self):self.reject_pin('diagnostic_adc',4,'AI_REF_2V5')
 def test_address_conflict(self):self.reject_pin('diagnostic_adc',1,'AI_AGND')
 def test_health_faked(self):self.reject_pin('health_isolator',4,'AI_5V')
 def test_host_fault_polarity(self):self.reject_pin('fault_inverter',4,'AI_SENSOR_HEALTH_HOST')
 def test_differential_not_single_ended(self):
  q=self.d['components'][self.d['channels'][0]['ina_ref']];q['pins']['2']='AI_AGND';self.assertFalse(validate(self.d)['ok'])
 def test_incorrect_ina_reference_equation(self):
  q=self.d['components'][self.d['channels'][1]['ina_ref']];q['pins']['1']='AI_AGND';self.assertFalse(validate(self.d)['ok'])
 def test_burden_tbu_drop_excluded(self):
  q=self.d['components'][self.d['channels'][2]['ina_ref']];q['pins']['3']='AI2_P';self.assertFalse(validate(self.d)['ok'])
 def test_burden_wrong_power_package(self):
  q=self.d['components'][self.d['channels'][0]['burden_resistors'][0]];q['footprint']='Resistor_SMD:R_0603_1608Metric';self.assertFalse(validate(self.d)['ok'])
 def test_burden_default_closed(self):
  q=self.d['components'][self.d['channels'][0]['relay_ref']];q['mpn']='TLP4176A(TP,F';self.assertFalse(validate(self.d)['ok'])
 def test_missing_burden_qualification(self):
  q=self.d['components'][self.d['channels'][3]['mode_gate_ref']];q['pins']['2']='AI_5V';self.assertFalse(validate(self.d)['ok'])
 def test_quad_buffer_channel_swapped(self):self.reject_pin('quad_buffer',12,'AI2_SCALED')
 def test_false_ready(self):self.d['manufacturing_ready']=True;self.assertFalse(validate(self.d)['ok'])

if __name__=='__main__':unittest.main()
