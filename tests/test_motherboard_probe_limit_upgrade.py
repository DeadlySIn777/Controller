"""Current/enable/default/native mutation controls for two actual probe feeds."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_probe_limit_upgrade import validate,OUT
class ProbeLimits(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=json.loads((OUT/'design.json').read_text())
 def bad(self,fn):
  d=copy.deepcopy(self.d);fn(d);self.assertFalse(validate(d)['ok'])
 def test_exact_native_source(self):self.assertTrue(validate(self.d,netlist=OUT/'netlist.xml',erc=OUT/'erc.json')['ok'])
 def test_TPS49p9k_cannot_return(self):self.bad(lambda d:d['components']['U14026'].__setitem__('mpn','TPS26624DRCR'))
 def test_PIN5_enable_not_ground(self):self.bad(lambda d:d['components']['U14026']['pins'].__setitem__('5','FIELD_GND'))
 def test_FIELDreturn_not_logic(self):self.bad(lambda d:d['components']['U14027']['pins'].__setitem__('9','LOGIC_GND'))
 def test_UVfault_not_unobserved(self):self.bad(lambda d:d['components']['U14026']['pins'].__setitem__('7',None))
 def test_current_voltage_not_DVDT_pin(self):self.bad(lambda d:d['components']['U14026']['pins'].__setitem__('8','PRB0_DVDT'))
 def test_autoretry_not_latch(self):self.bad(lambda d:d['components']['R19403'].__setitem__('resistance_ohm',0))
 def test_cap150mA_not_159(self):self.bad(lambda d:d['ports_24v'][0].__setitem__('frozen_limit_max_a',.159))
 def test_normal100mA_not_lowered(self):self.bad(lambda d:d['ports_24v'][1].__setitem__('normal_load_a',.087))
 def test_unquoted_limit_not_guaranteed(self):self.bad(lambda d:d['ports_24v'][0].__setitem__('limit_accuracy_fraction',.02))
 def test_bleed_not_excludedfrom_rating(self):self.bad(lambda d:d['ports_24v'][0].__setitem__('current_bound_min_a',.100))
 def test_limit_passive_MPN_not_empty(self):self.bad(lambda d:d['components']['R14057'].__setitem__('mpn',''))
 def test_probe_exactland_not_TPS_EP(self):self.bad(lambda d:d['components']['U14027'].__setitem__('footprint','CNC_MB_Operator:TPS2662_DRC10_TI'))
 def test_unrelatedMPG_preserved(self):self.bad(lambda d:d['components']['R14001'].__setitem__('value','unreviewed'))
 def test_original24DI_scope_preserved(self):self.bad(lambda d:d.__setitem__('external_probes_consume_general_DI',True))
 def test_powerup_peak_not_staticguarantee(self):self.bad(lambda d:d['ports_24v'][0].__setitem__('transient_peak_qualified',True))
 def test_no_hidden_removal(self):self.bad(lambda d:d['components'].pop('C14047'))
 def test_no_extra_daughterboard(self):self.bad(lambda d:d['components'].__setitem__('J99999',copy.deepcopy(d['components']['R19401'])))
if __name__=='__main__':unittest.main()
