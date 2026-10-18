"""Source-proof negative tests; no analogue or target-hardware claims."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_watchdogs import DEFAULT,Permission,bringup_pin_map,conditional_withdrawal,read_native,timer_screen,validate

class WatchdogSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.native=read_native(DEFAULT/'netlist.xml');cls.model=json.loads((DEFAULT/'design.json').read_text())
 def valid(self,p=None,m=None):return validate(p or self.native,m or self.model)
 def test_native_actual_2663_source(self):
  r=self.valid();self.assertTrue(r['passed'],r['errors']);self.assertGreater(r['native_source_assertions'],4200)
 def test_extended_variant_rejected(self):
  p=copy.deepcopy(self.native);p['U3001']['mpn']='TPS3851G18EDRBT';self.assertFalse(self.valid(p)['passed'])
 def test_4p7nf_rejected(self):
  m=copy.deepcopy(self.model);m['components']['C3001']['capacitance_f']=4.7e-9;self.assertFalse(self.valid(m=m)['passed'])
 def test_missing_reset_guard_rejected(self):
  p=copy.deepcopy(self.native);p['U3006']['pins']['2']='IO_3V3';self.assertFalse(self.valid(p)['passed'])
 def test_wrong_WDO_RESET_connection_rejected(self):
  p=copy.deepcopy(self.native);p['U3001']['pins']['8']='IO_3V3';self.assertFalse(self.valid(p)['passed'])
 def test_independent_output_timer_cannot_be_motion_timer(self):
  p=copy.deepcopy(self.native);p['U3002']['pins']['6']=p['U3001']['pins']['6'];self.assertFalse(self.valid(p)['passed'])
 def test_signal_contact_bypass_rejected(self):
  p=copy.deepcopy(self.native);p['U6042']['pins']['7']='motherboard_motors/MOTOR_TX_GATE_A';self.assertFalse(self.valid(p)['passed'])
 def test_motor_final_gate_consumer_cannot_use_source(self):
  p=copy.deepcopy(self.native);p['U6001']['pins']['4']='motherboard_motors/MOTOR_TX_GATE_SOURCE_A';self.assertFalse(self.valid(p)['passed'])
 def test_every_individual_enable_has_hardware_NAND_inhibit(self):
  p=copy.deepcopy(self.native)
  r=next(r for r,c in p.items() if c['mpn']=='SN74LVC00APWR' and c['pins'].get('3')=='motherboard_motors/MOTOR0_SINK_OFF')
  p[r]['pins']['2']='IO_3V3';self.assertFalse(self.valid(p)['passed'])
 def test_ISO_default_high_variant_rejected(self):
  p=copy.deepcopy(self.native);p['U10003']['mpn']='ISO7762DBQR';self.assertFalse(self.valid(p)['passed'])
 def test_smart_switch_DO_EN_bypass_rejected(self):
  p=copy.deepcopy(self.native);p['U10004']['pins']['3']=p['U10004']['pins']['4'];self.assertFalse(self.valid(p)['passed'])
 def test_clockstall_not_restored_on_WDO_release(self):
  c=Permission(self.native);healthy={'FPGA_CRESET_N':1,'FPGA_USER_RESET_N':1,'mc_permission/DIC_OK_QUALIFIED':1,'mc_permission/EXT_PERMIT_3V3':1,'mc_permission/TAMPER_CLEAR_N':1,'WD_M_OK':1,'WD_O_OK':1,'FPGA_ENDPOINT_READY':1}
  c.drive(**healthy);c.drive(FPGA_MOTION_REQUEST=1);self.assertEqual(c.v['TX_PERMIT'],1)
  c.drive(WD_M_OK=0);c.drive(WD_M_OK=1);self.assertEqual(c.v['TX_PERMIT'],0)
 def test_timer_formula_uses_standard_suffix_and_one_internal_error(self):
  r=timer_screen();self.assertAlmostEqual(r['ideal_nominal_ms'],11.04);self.assertAlmostEqual(r['capacitor_and_IC_only_ms'][1],(3.23*3.3*1.05+.381)*1.095)
 def test_external_leakage_not_a_manufacturer_guarantee(self):
  r=timer_screen();self.assertFalse(r['external_assumptions_physically_verified']);self.assertGreater(r['declared_external_screen_ms'][1],13.02)
 def test_tps_nominal_delays_never_promoted_to_maximum(self):
  r=timer_screen();self.assertTrue(r['WDI_to_WDO_50ns_is_NOM_only']);self.assertTrue(r['SET1_enable_setup_150us_is_NOM_only']);self.assertFalse(r['maximum_20ms_all_condition_proven'])
 def test_nc_closure_not_three_ms_assertion(self):
  r=conditional_withdrawal();self.assertEqual(r['motor_NC_close_max_ms_at25C_IF5mA_RL200_VDD20'],1);self.assertEqual(r['motor_NC_open_ASSERTION_max_ms_at_same_testpoint'],3)
 def test_tps274_complete_turnoff_is_not_57us_max(self):
  r=conditional_withdrawal();self.assertTrue(r['TPS274_tOFF_EN_to10percent_57us_is_TYP_only']);self.assertEqual(r['TPS274_tDF_EN_to90percent_max_us_at24V_48ohm'],33)
 def test_conditional_budget_preserves_unknowns(self):
  r=conditional_withdrawal();self.assertLess(r['known_terms_motor_NC_conditional_ms'],20);self.assertFalse(r['whole_20ms_requirement_met']);self.assertTrue(all(v is None for v in r['critical_unknown_terms'].values()))
 def test_nonfinite_or_boolean_timing_inputs_refused(self):
  for v in [True,float('inf'),float('nan')]:
   with self.assertRaises(ValueError):timer_screen(cap_nf=v)
 def test_unphysical_leakage_refused(self):
  for v in [-1,347,400]:
   with self.assertRaises(ValueError):timer_screen(declared_board_leakage_na=v)
 def test_longer_cap_really_exhausts_20ms_budget(self):
  self.assertGreater(timer_screen(cap_nf=6.8)['declared_external_screen_ms'][1],20)
 def test_exact_independent_native_bringup_ball_map(self):
  r=bringup_pin_map(self.native);self.assertTrue(r['passed'],r['errors']);self.assertEqual(r['ports']['progress_m']['ball'],'E4');self.assertEqual(r['ports']['progress_o']['ball'],'L2')
 def test_swapped_watchdog_ball_assignment_rejected(self):
  p=copy.deepcopy(self.native);p['U1001']['pins']['L2']=p['U1001']['pins']['E4'];self.assertFalse(bringup_pin_map(p)['passed'])

if __name__=='__main__':unittest.main()
