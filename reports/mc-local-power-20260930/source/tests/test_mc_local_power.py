"""Disconnect-only MC power source/physical-net and hostile mutation checks."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_mc_local_power import validate,analytical_screen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/mc_local_power'


class MCLocalPowerTests(unittest.TestCase):
    def setUp(self):
        self.tree=ET.parse(OUT/'netlist.xml')
        self.model=json.loads((OUT/'design.json').read_text(encoding='utf-8'))
        self.fpga=json.loads((ROOT/'hardware/fpga_core/design.json').read_text(encoding='utf-8'))
        self.fps={p.stem:p.read_text(encoding='utf-8') for p in (OUT/'CNC_MC_Power.pretty').glob('*.kicad_mod')}
    def errors(self):return validate(self.tree,self.model,self.fpga,self.fps)
    def net(self,name):return self.tree.find(f".//nets/net[@name='/{name}']")
    def move(self,source,dest,ref,pin):
        a=self.net(source);n=a.find(f"node[@ref='{ref}'][@pin='{pin}']");a.remove(n);self.net(dest).append(n)
    def test_actual_native_export_and_static_corners_pass(self):self.assertEqual([],self.errors())
    def test_io_cannot_start_before_core_is_qualified(self):
        self.move('MC_SEQ_5V_OK','CORE_5V','U4','2');self.assertTrue(self.errors())
    def test_io_reset_cannot_bypass_core_qualification(self):
        self.move('IO_3V3_EN','CORE_5V','U5','2');self.assertTrue(self.errors())
    def test_pg_cannot_replace_independent_window_cascade(self):
        self.move('IO_3V3_EN','CORE_1V2_PG_OD','U2','5');self.assertTrue(self.errors())
    def test_core_enable_requires_both_declared_pulldowns(self):
        for ref in ('R2','R103'):
            with self.subTest(ref=ref):
                self.setUp();self.move('LOGIC_GND','CORE_5V',ref,'2');self.assertTrue(self.errors())
    def test_io_enable_requires_both_declared_pulldowns(self):
        for ref in ('R6','R105'):
            with self.subTest(ref=ref):
                self.setUp();self.move('LOGIC_GND','CORE_5V',ref,'2');self.assertTrue(self.errors())
    def test_5v_raw_qualifier_cannot_drive_destination_reset_directly(self):
        self.move('MC_RAILS_OK_5V','FPGA_CRESET_N','U6','2');self.assertTrue(self.errors())
    def test_reset_buffer_must_use_destination_supply(self):
        self.move('IO_3V3','CORE_5V','U6','5');self.assertTrue(self.errors())
    def test_buffer_physical_input_and_output_swap_detected(self):
        self.move('MC_RAILS_OK_5V','FPGA_CRESET_N','U6','2');self.move('FPGA_CRESET_N','MC_RAILS_OK_5V','U6','4');self.assertTrue(self.errors())
    def test_supervisor_reconfiguring_uv_into_ov_detected(self):
        self.move('MC_SEQ_REF2','LOGIC_GND','U4','6');self.assertTrue(self.errors())
    def test_rdis_cannot_become_margin_override(self):
        self.move('CORE_5V','LOGIC_GND','U4','1');self.assertTrue(self.errors())
    def test_delay_cannot_become_unconnected_or_grounded(self):
        self.move('CORE_5V','LOGIC_GND','U5','10');self.assertTrue(self.errors())
    def test_vset9_is_signal_not_ground_pad_on_io_regulator(self):
        self.move('IO_3V3_VSET','LOGIC_GND','U2','9');self.assertTrue(self.errors())
    def test_io_mode_cannot_return_to_old_1mhz_population(self):
        c=self.tree.find(".//comp[@ref='R5']");c.find('value').text='76.8k 1%';c.find("./fields/field[@name='MPN']").text='CRCW060376K8FKEA';self.assertTrue(self.errors())
    def test_supervisor_ic_pin_type_cannot_be_relabelled(self):
        self.tree.find(".//libpart[@part='LTC2962HUD']/pins/pin[@num='12']").set('type','output');self.assertTrue(self.errors())
    def test_precision_resistors_cannot_be_substituted_with_one_percent(self):
        self.tree.find(".//comp[@ref='R41']/value").text='1.10k 1%';self.assertTrue(self.errors())
    def test_external_fpga_cap_overload_is_detected(self):
        self.fpga['components']['C28']['capacitance_f']=100e-6;self.assertTrue(self.errors())
    def test_extra_cap_budget_cannot_hide_limit(self):
        self.model['rail_capacitor_limits']['IO_3V3']['additional_nominal_load_budget_uf']=50;self.assertTrue(self.errors())
    def test_loop_cap_ranges_account_actual_fpga_not_only_regulator(self):
        s=analytical_screen(self.fpga);r={r['rail']:r for r in s['rails']}
        self.assertAlmostEqual(8.6,r['CORE_1V2']['fpga_cap_nominal_uf'])
        self.assertAlmostEqual(35.51,r['IO_3V3']['fpga_cap_nominal_uf'])
        self.assertGreater(r['IO_3V3']['total_output_upper_uf'],50)
        self.assertLess(r['IO_3V3']['total_output_upper_uf'],100)
    def test_current_and_charging_do_not_claim_steady_only_startup(self):
        s=analytical_screen(self.fpga)
        self.assertGreater(s['steady_slot_input_a_model'],.45)
        self.assertLess(s['steady_slot_input_a_model'],.5)
        self.assertGreater(s['concurrent_startup_input_a_model'],.45)
        self.assertLess(s['concurrent_startup_input_a_model'],.8)
        self.assertTrue(s['cold_input_cap_current_not_included'])
        self.assertFalse(s['physical_or_arbitrary_partial_power'])
    def test_copper_pad_change_detected(self):
        self.fps['TPS62901_RPJ9']=self.fps['TPS62901_RPJ9'].replace('(size .65 .2)','(size .9 .2)').replace('(size 0.65 0.2)','(size 0.9 0.2)');self.assertTrue(self.errors())
    def test_ep17_cannot_be_given_signal_net(self):
        self.move('LOGIC_GND','IO_3V3','U5','17');self.assertTrue(self.errors())
    def test_source_manifest_cannot_diverge_from_export(self):
        self.model['components']['U4']['pins']['2']='CORE_5V';self.assertTrue(self.errors())
    def test_boundary_cannot_be_fake_fitted_connector(self):
        self.model['components']['B1']['physical']=True;self.assertTrue(self.errors())
    def test_manufacturing_ready_cannot_be_true(self):
        self.model['manufacturing_ready']=True;self.assertTrue(self.errors())
    def test_is1_part_deviation_cannot_be_hidden(self):
        self.model['component_deviation']['proposed']='TPS386000';self.assertTrue(self.errors())
    def test_actual_core_thresholds_keep_drift_margin(self):
        s=analytical_screen(self.fpga)
        self.assertTrue(all(r['static_acceptance_and_detection'] for r in s['aging_400ppm_sensitivity']))
        core=next(r for r in s['aging_400ppm_sensitivity'] if r['rail']=='CORE_1V2')
        self.assertGreater(min(core['static_margins_v']),.007)
    def test_historical_tight_ledger_cannot_replace_actual_core_limit_record(self):
        self.model['rail_limits_v']['CORE_1V2']=[1.17,1.23];self.assertTrue(self.errors())


if __name__=='__main__':unittest.main()
