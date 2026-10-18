"""Electrical/source tamper controls for actual bounded single GPIO identity path."""
import json,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_identity_io import validate

class IdentityTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ROOT/'hardware/motherboard_identity_io/design.json').read_text())
 def badpin(self,key,pin,net):self.d['components'][self.d['blocks'][key]]['pins'][str(pin)]=net;self.assertFalse(validate(self.d)['ok'])
 def badres(self,key,value):self.d['components'][self.d['blocks'][key]]['resistance_ohm']=value;self.assertFalse(validate(self.d)['ok'])
 def test_native_source(self):self.assertTrue(validate(self.d,ROOT/'hardware/motherboard_identity_io/netlist.xml',ROOT/'hardware/motherboard_identity_io/erc.json',ROOT/'hardware/motherboard_identity_io/CNC_MB_Identity.pretty')['ok'])
 def test_nonA_contention_part(self):self.d['components'][self.d['blocks']['repeater']]['mpn']='TCA9517DGKR';self.assertFalse(validate(self.d)['ok'])
 def test_host_side5V_wrong(self):self.badpin('repeater',8,'FREQ_5V_LIMITED')
 def test_field_side_low_threshold_wrong(self):self.badpin('repeater',1,'IO_3V3')
 def test_host5V_unbuffered(self):self.badpin('repeater',6,'FREQ_MOD_ID_TO_FRONTEND')
 def test_field_series_bypassed(self):self.badpin('repeater',3,'FREQ_MOD_ID_TO_FRONTEND')
 def test_fake_constant_healthy_EN(self):self.badpin('repeater',5,'IO_3V3')
 def test_missing_unused_clock_A(self):self.badpin('repeater',2,None)
 def test_missing_unused_clock_B(self):self.badpin('repeater',7,None)
 def test_monitor_wrong_domain(self):self.badpin('window',5,'FREQ_5V_LIMITED')
 def test_monitor_OV_short(self):self.badpin('window',4,'FREQ_ID_FIELD_UV')
 def test_monitor_inverted_pins(self):self.badpin('window',3,'FREQ_ID_FIELD_OV')
 def test_monitor_only_ONE_output(self):self.badpin('window',6,None)
 def test_tvs_wrong_return(self):self.badpin('tvs',2,'FIELD_GND')
 def test_host_pulltoo_strong_VOL(self):self.badres('host_pullup',1000)
 def test_field_pulltoo_strong_low_drop(self):self.badres('field_pullup',470)
 def test_field_series_too_high(self):self.badres('field_series',1000)
 def test_monitor_stale_PG(self):self.badres('window_pullup',1000000)
 def test_extra_terminal(self):self.d['boundaries']['J21002']['pins']['3']='EXTRA_FIELD';self.assertFalse(validate(self.d)['ok'])
 def test_wrong_GPIO(self):self.d['boundaries']['J21002']['pins']['1']='ACC_SPI_MISO';self.assertFalse(validate(self.d)['ok'])
 def test_fake_terminal_footprint(self):self.d['boundaries']['J21002']['physical']=True;self.assertFalse(validate(self.d)['ok'])
 def test_numericIoff_invention(self):self.d['limits']['numeric_Ioff_guarantee_available']=True;self.assertFalse(validate(self.d)['ok'])
 def test_any24V_promise(self):self.d['limits']['arbitrary24V_miswire_claim']=True;self.assertFalse(validate(self.d)['ok'])
 def test_unknown_ID_low_logic(self):self.d['limits']['ordinary_ID_VIL_max_v']=.4;self.assertFalse(validate(self.d)['ok'])
 def test_serieshost_route_drift(self):self.d['limits']['host_trace_plus_return_resistance_max_ohm']=1000;self.assertFalse(validate(self.d)['ok'])
 def test_measured_delay_claim(self):self.d['threshold_screens']['rise_screens_are_not_loaded_latency_proof']=False;self.assertFalse(validate(self.d)['ok'])
 def test_overcap_cable(self):self.d['limits']['field_total_capacitance_candidate_pf']=5000;self.assertFalse(validate(self.d)['ok'])
 def test_missing_fieldcap(self):self.d['power_budget']['FREQ_5V_LIMITED_bypass_nominal_uf']=0;self.assertFalse(validate(self.d)['ok'])
 def test_fake_firmware(self):self.d['firmware_implemented']=True;self.assertFalse(validate(self.d)['ok'])
 def test_reset_restart_not_inhibit(self):self.d['defaults']['automatic_motion_rearm']=True;self.assertFalse(validate(self.d)['ok'])
 def test_land_geometry_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   src=ROOT/'hardware/motherboard_identity_io/CNC_MB_Identity.pretty/TCA9517A_DGK8_TI.kicad_mod';Path(t,'TCA9517A_DGK8_TI.kicad_mod').write_text(src.read_text().replace('(size 1.4 .45)','(size 1.35 .45)',1));self.assertFalse(validate(self.d,footprints=t)['ok'])

if __name__=='__main__':unittest.main()
