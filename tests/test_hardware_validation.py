"""Fault injection into an electrical proposal; no hardware qualification implied."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools"/(name+".py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
build=load("hardware_build_design").build
validator=load("hardware_validate")


class ElectricalLedgerTests(unittest.TestCase):
    def setUp(self):self.design=build()
    def errors(self):return validator.validate(self.design)["errors"]
    def test_consistent_proposal_is_never_release_ready(self):
        result=validator.validate(self.design)
        self.assertTrue(result["consistency_pass"],result["errors"])
        self.assertFalse(result["manufacturing_ready"])
        self.assertGreater(len(result["release_blockers"]),20)
    def test_two_logical_signals_cannot_share_one_driver(self):
        self.design["channels"][1]["device_channel"]=1
        self.assertTrue(any("IC channel collision" in x for x in self.errors()))
    def test_duplicate_bga_ball_is_rejected_even_when_rest_unassigned(self):
        for c in self.design["channels"][:2]:c["fpga_package_pin"]="A1";c["bank"]="example_bank"
        self.assertTrue(any("package pin collision" in x for x in self.errors()))
    def test_accidental24v_on_logic_supply_rejected(self):
        rail=next(r for r in self.design["rails"] if r["id"]=="CORE_5V")
        rail.update(min_v=23,nominal_v=24,max_v=25)
        self.assertTrue(any("device operating limits" in x for x in self.errors()))
    def test_missing_decoupling_cannot_pass_as_complete_parts_ledger(self):
        self.design["components"]=[p for p in self.design["components"] if p["id"]!="tx_decoupling"]
        self.assertTrue(any("required part missing" in x for x in self.errors()))
    def test_missing_driver_detected_without_crashing_validator(self):
        self.design["components"]=[p for p in self.design["components"] if p["id"]!="tx"]
        self.assertTrue(any("required part missing" in x for x in self.errors()))
    def test_secondary_isolator_power_must_also_be_checked(self):
        rail=next(r for r in self.design["rails"] if r["id"]=="FIELD_5V")
        rail.update(min_v=23,nominal_v=24,max_v=25)
        self.assertIn("supply outside device operating limits: iso_cmd",self.errors())
    def test_isolator_port_removal_cannot_silence_supply_check(self):
        next(p for p in self.design["components"] if p["id"]=="iso_analog").pop("supply_ports")
        self.assertIn("isolator not fitted across both rails: analog_commands",self.errors())
        for pid in ("iso_cmd","iso_fault"):next(p for p in self.design["components"] if p["id"]==pid).pop("supply_ports")
        errors=self.errors()
        self.assertIn("isolator not fitted across both rails: output_commands",errors)
        self.assertIn("isolator not fitted across both rails: field_faults",errors)
    def test_isolator_mpn_must_name_a_fitted_part(self):
        self.design["logic_links"][3]["isolator_mpn"]="ISO9999"
        self.assertIn("isolator not fitted across both rails: field_faults",self.errors())
    def test_fpga_io_bank_port_removal_rejected(self):
        next(p for p in self.design["components"] if p["id"]=="fpga").pop("supply_ports")
        self.assertIn("FPGA declares no supply port on the reserved I/O bank rail",self.errors())
    def test_isolation_ground_alias_rejected(self):
        self.design["domains"][1]["ground"]="LOGIC_GND"
        self.assertIn("isolation domains alias a ground",self.errors())
    def test_direct_wire_across_isolation_domain_rejected(self):
        self.design["logic_links"][2]["bridge"]="wire"
        self.assertTrue(any("unisolated domain" in x for x in self.errors()))
    def test_enable_cannot_default_on(self):
        next(c for c in self.design["channels"] if c["kind"]=="drive_enable")["default"]="on"
        self.assertTrue(any("default not off" in x for x in self.errors()))
    def test_rtl_watchdog_is_derived_from_endpoint_parameter(self):
        perm=self.design["permission"]
        self.assertEqual(perm["rtl_watchdog_cycles"],250000)
        self.assertEqual(perm["rtl_watchdog_ms"],5.0)
        self.assertEqual(perm["external_watchdog_study_ms"],20)
        self.assertNotIn("deadline_ms",perm)
    def test_rtl_watchdog_ms_cannot_drift_from_cycles(self):
        self.design["permission"]["rtl_watchdog_ms"]=20
        self.assertTrue(any("disagrees with WATCHDOG_CYCLES" in x for x in self.errors()))
    def test_rtl_watchdog_cycles_cannot_drift_from_rtl(self):
        self.design["permission"]["rtl_watchdog_cycles"]=1000000
        self.design["permission"]["rtl_watchdog_ms"]=20.0
        self.assertTrue(any("differs from RTL WATCHDOG_CYCLES" in x for x in self.errors()))
    def test_ambiguous_deadline_field_rejected(self):
        self.design["permission"]["deadline_ms"]=20
        self.assertTrue(any("deadline_ms is ambiguous" in x for x in self.errors()))
    def test_esp_cannot_be_added_to_permission_path(self):
        self.design["permission"]["esp_in_required_path"]=True
        self.assertTrue(any("ESP improperly" in x for x in self.errors()))
    def test_excess_load_detected_by_channel_bank_and_rail(self):
        for c in self.design["channels"]:
            if c["component"]=="DO0":c["load_target_a"]=2
        errors=self.errors()
        self.assertTrue(any("channel target" in x for x in errors))
        self.assertTrue(any("bank over" in x for x in errors))
        self.assertTrue(any("rail understates" in x for x in errors))
    def test_physical_connector_contact_collision_rejected(self):
        self.design["terminals"][1]=deepcopy(self.design["terminals"][0])
        self.assertTrue(any("terminal collision" in x for x in self.errors()))
    def test_renamed_terminal_net_cannot_hide_lost_step_pair(self):
        self.design["terminals"][0]["net"]="BOGUS_P";self.design["terminals"][1]["net"]="BOGUS_N"
        errors=self.errors()
        self.assertTrue(any("missing or duplicated for channel STEP0" in x for x in errors),errors)
    def test_orphan_signal_terminal_rejected(self):
        self.design["terminals"][0]["net"]="STEP9_P"
        self.assertTrue(any("no ledger channel: STEP9_P" in x for x in self.errors()))
    def test_terminal_domain_must_match_channel_domain(self):
        self.design["terminals"][0]["domain"]="FIELD"
        self.assertTrue(any("terminal domain differs" in x for x in self.errors()))
    def test_logic_high_voltage_and_noise_margin_checked(self):
        link=self.design["logic_links"][0]
        link["source_voh_min"]=1.8;link["source_max_v"]=6
        self.assertTrue(any("noise margin" in x for x in self.errors()))
        self.assertTrue(any("input overvoltage" in x for x in self.errors()))
    def test_input_conversion_power_reservation_checked(self):
        next(x for x in self.design["power_loads"] if x["id"]=="logic_converter_input")["budget_a"]=0.5
        self.assertTrue(any("conversion" in x for x in self.errors()))
    def test_sub_rail_conversion_reservations_checked(self):
        for load_id,entry in (("fpga_core","core1v2_input"),("esp_peak","esp3v3_input"),("fpga_io_rx_isolators","io3v3_input")):
            with self.subTest(load_id):
                d=deepcopy(self.design)
                next(x for x in d["power_loads"] if x["id"]==load_id)["budget_a"]=1.0
                self.assertTrue(any(entry in x and "conversion" in x for x in validator.validate(d)["errors"]))
    def test_actual_kicad_export_matches_pin_contract(self):
        self.assertEqual([],validator.check_tx_netlist(ROOT/"hardware/tx_bank/netlist.xml"))


if __name__=="__main__":unittest.main()
