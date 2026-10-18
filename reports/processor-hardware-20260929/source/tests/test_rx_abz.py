"""Mutation checks for actual receiver connectivity and termination assumptions."""
import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.hardware_validate_rx_abz import validate

ROOT = Path(__file__).resolve().parents[1]


class EncoderReceiverTests(unittest.TestCase):
    def setUp(self):
        self.tree = ET.parse(ROOT / "hardware/rx_abz/netlist.xml")
        self.design = json.loads((ROOT / "hardware/electrical-design.json").read_text(encoding="utf-8"))
        self.mapping = json.loads((ROOT / "hardware/rx_abz/channel-map.json").read_text(encoding="utf-8"))

    def net(self,name):
        return self.tree.find(f".//nets/net[@name='/{name}']")

    def check(self):
        return validate(self.tree,self.design,self.mapping)

    def test_actual_export_matches_both_encoder_ports_and_ledger(self):
        self.assertEqual([],self.check())

    def test_differential_polarity_swap_is_rejected(self):
        first = self.net("ENC1_A_P").find("node[@ref='U1']")
        second = self.net("ENC1_A_N").find("node[@ref='U1']")
        first.attrib["pin"],second.attrib["pin"] = second.attrib["pin"],first.attrib["pin"]
        self.assertTrue(self.check())

    def test_cross_chip_encoder_output_swap_is_rejected(self):
        a = self.net("ENC1_A_FPGA").find("node[@ref='JLOGIC1']")
        b = self.net("ENC1_B_FPGA").find("node[@ref='JLOGIC1']")
        a.attrib["pin"],b.attrib["pin"] = b.attrib["pin"],a.attrib["pin"]
        self.assertTrue(self.check())

    def test_enable_and_unused_inputs_cannot_float(self):
        for pin in (4,12,10,14):
            with self.subTest(pin=pin):
                tree = copy.deepcopy(self.tree)
                net = tree.find(".//nets/net[@name='/IO_3V3']")
                net.remove(net.find(f"node[@ref='U2'][@pin='{pin}']"))
                self.assertTrue(validate(tree,self.design,self.mapping))

    def test_unused_outputs_require_explicit_no_connect(self):
        node = self.tree.find(".//nets/net/node[@ref='U2'][@pin='11']")
        node.attrib["pintype"] = "tri_state"
        self.assertTrue(self.check())

    def test_termination_cannot_be_shorted_underpowered_or_silently_dnp(self):
        for replacement in ("0R","120R 1% 0.125W / FIT"):
            with self.subTest(value=replacement):
                tree = copy.deepcopy(self.tree)
                tree.find(".//components/comp[@ref='R1']/value").text = replacement
                self.assertTrue(validate(tree,self.design,self.mapping))
        ET.SubElement(self.tree.find(".//components/comp[@ref='R1']"),"property",name="dnp")
        self.assertTrue(self.check())

    def test_protected_encoder_supplies_and_references_stay_separate(self):
        node = self.net("ENC1_5V_LIMITED").find("node[@ref='JPWR1']")
        self.net("ENC1_5V_LIMITED").remove(node)
        self.net("ENC0_5V_LIMITED").append(node)
        self.assertTrue(self.check())

    def test_missing_supply_bypass_is_rejected(self):
        self.net("IO_3V3").remove(self.net("IO_3V3").find("node[@ref='C3']"))
        self.assertTrue(self.check())

    def test_common_mode_cannot_become_a_fourteen_volt_differential_rating(self):
        self.mapping["termination"]["maximum_applied_differential_v"] = 14
        self.assertTrue(self.check())

    def test_thermal_claim_or_arithmetic_change_is_rejected(self):
        for key,value in (("physical_thermal_qualified",True),("initial_local_ambient_max_c",85),
                          ("calculated_worst_case_w_per_channel",0.1),
                          ("calculated_worst_case_w_per_channel",float('nan')),
                          ("calculated_worst_case_w_all_six",float('inf'))):
            with self.subTest(key=key):
                mapping = copy.deepcopy(self.mapping)
                mapping["termination"][key] = value
                self.assertTrue(validate(self.tree,self.design,mapping))


if __name__ == "__main__":
    unittest.main()
