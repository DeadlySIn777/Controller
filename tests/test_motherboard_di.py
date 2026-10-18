"""Meaningful mutations of the new 24-general-DI source and native evidence."""
from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/motherboard_di"
spec = importlib.util.spec_from_file_location("motherboard_di_validation", ROOT / "tools/hardware_validate_motherboard_di.py")
HW = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HW)


class MotherboardInputTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((OUT / "design.json").read_text(encoding="utf-8"))

    def reject(self, fragment):
        result = HW.validate(self.d)
        self.assertFalse(result["ok"],result)
        self.assertTrue(any(fragment in msg for msg in result["errors"]),result)

    def test_native_source_model_and_exact_footprint_match(self):
        result = HW.validate(self.d,OUT/"netlist.xml",OUT/"erc.json",OUT/"CNC_MB_DI.pretty/ISO1212_DBQ16_TI.kicad_mod")
        self.assertTrue(result["ok"],result)
        self.assertFalse(result["manufacturing_ready"])
        self.assertFalse(result["physical_qualification"])

    def test_general_inputs_cannot_be_replaced_by_alarm_or_probe_channels(self):
        for key in ("general_count","motor_alarm_count","probe_count"):
            original = copy.deepcopy(self.d)
            self.d[key] = 1
            with self.subTest(key=key):
                self.reject("capacity/independence")
            self.d = original

    def test_last_pair_and_channel_count_are_real(self):
        self.d["components"].pop("U8012")
        self.reject("component set")

    def test_duplicate_general_channel_id_is_rejected(self):
        self.d["channels"][23]["id"] = "DI22"
        self.reject("IDs")

    def test_logic_outputs_cannot_consume_motor_alarm_name(self):
        self.d["channels"][0]["logic_net"] = "ALM0_FPGA"
        self.reject("channel/logic assignment")

    def test_output_feed_is_not_a_direct_fpga_pin_allocation(self):
        self.d["acquisition"]["output_nets"][0] = "DI0_FPGA"
        self.reject("acquisition")

    def test_field_return_never_joins_logic_ground(self):
        self.d["components"]["U8001"]["pins"]["14"] = "LOGIC_GND"
        self.reject("physical pin/net")

    def test_last_device_sense_current_pins_cannot_swap(self):
        pins = self.d["components"]["U8012"]["pins"]
        pins["10"],pins["11"] = pins["11"],pins["10"]
        self.reject("physical pin/net")

    def test_both_logic_ground_pins_required(self):
        self.d["components"]["U8003"]["pins"]["8"] = None
        self.reject("physical pin/net")

    def test_nc_pins_cannot_be_grounded(self):
        for pin in ("6","7"):
            original = copy.deepcopy(self.d)
            self.d["components"]["U8006"]["pins"][pin] = "LOGIC_GND"
            with self.subTest(pin=pin):
                self.reject("physical pin/net")
            self.d = original

    def test_substrate_islands_cannot_be_grounded_or_joined(self):
        for net in ("FIELD_B_0V","LOGIC_GND","DI0_SUB_ISLAND"):
            original = copy.deepcopy(self.d)
            self.d["components"]["U8001"]["pins"]["12"] = net
            with self.subTest(net=net):
                self.reject("separate single-pin floating island")
            self.d = original

    def test_enable_must_be_tied_to_logic_supply(self):
        for net in (None,"FIELD_B_24V"):
            self.d["components"]["U8001"]["pins"]["3"] = net
            with self.subTest(net=net):
                self.reject("physical pin/net")

    def test_weak_bias_does_not_guarantee_unpowered_low(self):
        self.d["output_default"]["brownout_or_unpowered"] = "guaranteed low"
        self.reject("brownout")

    def test_fixed_sinking_frontend_does_not_claim_auto_npn(self):
        self.d["interface"]["NPN_or_auto_mode_implemented"] = True
        self.reject("input voltage/mode")

    def test_sensor_supply_limit_is_point_two_shared_group_not_point_five(self):
        self.d["sensor_supplies"]["per_group_continuous_a"] = .5
        self.reject("0.20A shared-group")

    def test_boundary_does_not_claim_fitted_sensor_limiter(self):
        self.d["sensor_supplies"]["implemented"] = True
        self.reject("unimplemented sensor supply")

    def test_supply_contacts_nine_ten_share_one_group(self):
        self.d["boundaries"]["J8001"]["pins"]["10"] = "SENS24_G0_INDEPENDENT"
        self.reject("boundary mapping")

    def test_return_contacts_do_not_become_positive_supply(self):
        self.d["boundaries"]["J8003"]["pins"]["12"] = "SENS24_G2"
        self.reject("boundary mapping")

    def test_unselected_boundary_cannot_enter_pcb_or_bom(self):
        self.d["boundaries"]["J8002"]["fitted"] = True
        self.reject("boundary became fitted connector")

    def test_terminal_channel_mapping_cannot_shift(self):
        self.d["channels"][16]["terminal"]["position"] = 2
        self.reject("terminal mapping")

    def test_marketing_typical_current_does_not_replace_maximum(self):
        self.d["source_spec"]["current_above_falling_to_30v_a"][1] = .00247
        self.reject("TI source specification")

    def test_filter_cannot_move_before_threshold_resistor(self):
        self.d["components"]["C8001"]["pins"]["1"] = "DI0_FIELD"
        self.reject("field filter")

    def test_larger_filter_needs_new_timing_review(self):
        self.d["components"]["C8024"]["capacitance_f"] = 330e-9
        self.reject("field filter")

    def test_threshold_melf_cannot_be_replaced_by_plain_0603(self):
        self.d["components"]["R8001"]["mpn"] = "CRCW06031001FKEA"
        self.reject("resistor MPN")

    def test_source_footprint_rejects_generic_nxp_land_geometry(self):
        text = (OUT/"CNC_MB_DI.pretty/ISO1212_DBQ16_TI.kicad_mod").read_text(encoding="utf-8")
        self.assertTrue(HW.footprint_check(text))
        self.assertFalse(HW.footprint_check(text.replace("-2.7 ","-2.625 ").replace("2.7 ","2.625 ").replace("1.6 0.41","1.65 0.4")))
        self.assertFalse(HW.footprint_check(text.replace('(pad "6"','(pad "7"',1)))
        self.assertFalse(HW.footprint_check(text+'(pad "17" smd circle (at 0 0) (size 1 1) (layers "F.Cu"))'))

    def test_native_netlist_pin_mutation_not_hidden_by_unchanged_model(self):
        tree = ET.parse(OUT/"netlist.xml")
        target = next(n for n in tree.findall("nets/net") if n.get("name").removeprefix("/")=="LOGIC_GND")
        for net in tree.findall("nets/net"):
            found = next((n for n in net.findall("node") if n.get("ref")=="U8001" and n.get("pin")=="13"),None)
            if found is not None:
                net.remove(found)
                target.append(found)
                break
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"mutated.xml"
            tree.write(path)
            result = HW.validate(self.d,netlist=path)
        self.assertFalse(result["ok"])
        self.assertIn("U8001 native pins mismatch",result["errors"])

    def test_erc_only_retains_exact_twenty_four_substrate_warnings(self):
        original = json.loads((OUT/"erc.json").read_text(encoding="utf-8"))
        for mode in ("extra","error","wrong_uuid","deleted","suppressed"):
            report = copy.deepcopy(original)
            violations = report["sheets"][0]["violations"]
            if mode=="extra": violations.append(copy.deepcopy(violations[0]))
            if mode=="error": violations[0]["severity"]="error"
            if mode=="wrong_uuid": violations[0]["items"][0]["uuid"]="not-substrate"
            if mode=="deleted": violations.pop()
            if mode=="suppressed": report["ignored_checks"].append({"key":"isolated_pin_label"})
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as td:
                path = Path(td)/"erc.json"
                path.write_text(json.dumps(report),encoding="utf-8")
                self.assertFalse(HW.validate(self.d,erc=path)["ok"])

    def test_screens_are_not_certification_or_complete_latency(self):
        result = HW.validate(self.d)
        self.assertTrue(result["ok"],result)
        c = result["calculations"]
        self.assertAlmostEqual(c["all_24_active_field_current_screen_a"],1/15)
        self.assertAlmostEqual(c["all_24_field_power_at_30v_screen_w"],2)
        self.assertLess(c["logic_static_current_screen_a"],.024)
        self.assertLess(c["rising_threshold_conservative_screen_max_v"],15)
        self.assertGreater(c["falling_threshold_intrinsic_screen_min_v"],5)
        self.assertFalse(self.d["analysis"]["filter_corner_result_is_end_to_end_delay"])
        self.assertIn("not complete input propagation", " ".join(c["limitations"]))


if __name__ == "__main__":
    unittest.main()
