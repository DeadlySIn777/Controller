"""Exported encoder power connectivity plus meaningful fault mutations, no devices."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_encoder_power import validate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/encoder_power"


class EncoderPowerTests(unittest.TestCase):
    def setUp(self):
        self.tree = ET.parse(OUT / "netlist.xml")
        self.design = json.loads((OUT / "input-electrical-design.json").read_text(encoding="utf-8"))
        self.envelope = json.loads((OUT / "design-envelope.json").read_text(encoding="utf-8"))

    def net(self, name):
        return self.tree.find(f".//nets/net[@name='/{name}']")

    def check(self):
        return validate(self.tree, self.design, self.envelope)

    def move(self, source, destination, ref, pin):
        node = self.net(source).find(f"node[@ref='{ref}'][@pin='{pin}']")
        self.net(source).remove(node)
        self.net(destination).append(node)

    def test_actual_export_matches_frozen_ledger_and_two_independent_branches(self):
        self.assertEqual([], self.check())

    def test_limiter_bypass_or_port_merge_is_rejected(self):
        for destination in ("CORE_5V", "ENC0_5V_LIMITED"):
            with self.subTest(destination=destination):
                self.setUp()
                self.move("ENC1_5V_LIMITED", destination, "JOUT1", "3")
                self.assertTrue(self.check())

    def test_dbv_input_output_swap_is_rejected(self):
        a = self.net("CORE_5V").find("node[@ref='U1']")
        b = self.net("ENC0_5V_LIMITED").find("node[@ref='U1']")
        a.attrib["pin"], b.attrib["pin"] = b.attrib["pin"], a.attrib["pin"]
        self.assertTrue(self.check())

    def test_plain_auto_recover_or_different_package_is_rejected(self):
        for replacement in ("TPS2553DBVR", "TPS2553DRVR-1"):
            with self.subTest(mpn=replacement):
                self.setUp()
                self.tree.find(".//comp[@ref='U1']/fields/field[@name='MPN']").text = replacement
                self.assertTrue(self.check())

    def test_missing_or_wrong_ilim_resistor_is_rejected(self):
        for replacement in ("10k 1% 100ppm", "110k 5% 100ppm"):
            with self.subTest(value=replacement):
                self.setUp()
                self.tree.find(".//comp[@ref='R1']/value").text = replacement
                self.assertTrue(self.check())
        self.setUp()
        self.move("LOGIC_GND", "CORE_5V", "R1", "2")
        self.assertTrue(self.check())

    def test_enable_cannot_float_or_default_on(self):
        self.net("ENC0_POWER_EN").remove(self.net("ENC0_POWER_EN").find("node[@ref='R2']"))
        self.assertTrue(self.check())
        self.setUp()
        self.move("LOGIC_GND", "IO_3V3", "R2", "2")
        self.assertTrue(self.check())

    def test_fault_cannot_be_pulled_to_five_volts_or_swapped_between_ports(self):
        self.move("IO_3V3", "CORE_5V", "R3", "1")
        self.assertTrue(self.check())
        self.setUp()
        self.move("ENC0_POWER_FAULT_N", "ENC1_POWER_FAULT_N", "JCTRL1", "2")
        self.assertTrue(self.check())

    def test_missing_bypass_ground_or_dnp_is_rejected(self):
        for net, ref, pin in (("CORE_5V", "C1", "1"), ("LOGIC_GND", "U2", "2"), ("LOGIC_GND", "JOUT1", "4")):
            with self.subTest(ref=ref):
                self.setUp()
                self.net(net).remove(self.net(net).find(f"node[@ref='{ref}'][@pin='{pin}']"))
                self.assertTrue(self.check())
        self.setUp()
        ET.SubElement(self.tree.find(".//comp[@ref='C1']"), "property", name="dnp")
        self.assertTrue(self.check())

    def test_open_drain_fault_pin_definition_is_required(self):
        self.tree.find(".//libpart[@part='TPS2553DBVR-1']/pins/pin[@num='4']").attrib["type"] = "output"
        self.assertTrue(self.check())

    def test_normal_budget_cannot_disguise_simultaneous_fault_current(self):
        self.envelope["budget"]["simultaneous_limited_fault_a_both"] = 0.4
        self.assertTrue(self.check())
        self.setUp()
        next(p for p in self.design["power_loads"] if p["id"] == "encoder_supply")["budget_a"] = 0.2
        self.assertTrue(self.check())

    def test_thermal_retry_reverse_flow_and_missing_inhibit_cannot_be_hidden(self):
        for key, replacement in (("thermal_auto_retry_possible", False), ("reverse_current_before_turnoff_possible", False),
                                 ("external_fault_inhibit_implemented", True), ("fault_is_power_good", True),
                                 ("active_output_discharge", True)):
            with self.subTest(key=key):
                envelope = copy.deepcopy(self.envelope)
                envelope["behavior"][key] = replacement
                self.assertTrue(validate(self.tree, self.design, envelope))

    def test_finite_current_and_unqualified_partial_power_thermal_envelopes(self):
        for section, key, replacement in (("calculated_threshold_a", "max", float('nan')),
                                          ("budget", "fault_a_both_with_switch_reservation", float('inf')),
                                          ("logic_io_v", "partial_power_qualified", True),
                                          ("thermal", "qualified", True),
                                          ("rilim", "tolerance", 0)):
            with self.subTest(key=key):
                envelope = copy.deepcopy(self.envelope)
                envelope[section][key] = replacement
                self.assertTrue(validate(self.tree, self.design, envelope))


if __name__ == "__main__":
    unittest.main()
