"""Fault injection against the 22-channel input model, netlist and retained ERC cases."""
from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"hardware/digital_inputs"
SPEC=importlib.util.spec_from_file_location("digital_input_validation",ROOT/"tools/hardware_validate_digital_inputs.py")
HW=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(HW)


class DigitalInputTests(unittest.TestCase):
    def setUp(self):self.d=json.loads((OUT/"design.json").read_text(encoding="utf-8"))

    def reject(self,fragment):
        r=HW.validate(self.d)
        self.assertFalse(r["ok"],r)
        self.assertTrue(any(fragment in x for x in r["errors"]),r)

    def test_frozen_circuit_and_real_exports_match(self):
        r=HW.validate(self.d,OUT/"netlist.xml",OUT/"erc.json",OUT/"input-electrical-design.json")
        self.assertTrue(r["ok"],r)
        self.assertFalse(r["manufacturing_ready"])

    def test_no_silent_expansion(self):
        self.d["channel_count"]=24
        self.reject("baseline capacity")

    def test_port_voltage_cannot_be_silently_expanded(self):
        self.d["interface"]["operating_max_v"]=60
        self.reject("port voltage")

    def test_current_bound_cannot_use_marketing_typical_value(self):
        self.d["source_spec"]["current_above_falling_to_30v_a"][1]=.00247
        self.reject("source specification")

    def test_home_and_probe_assignments_cannot_swap(self):
        a,b=self.d["channels"][0],self.d["channels"][6]
        a["logic_net"],b["logic_net"]=b["logic_net"],a["logic_net"]
        self.reject("logic assignment")

    def test_duplicate_input_id(self):
        self.d["channels"][21]["id"]="DI20"
        self.reject("channel IDs")

    def test_ledger_common_terminal_must_remain_ground(self):
        self.d["components"]["JDI2"]["pins"]["7"]="FIELD_24V"
        self.reject("terminal pin")

    def test_no_invented_connector_number(self):
        self.d["channels"][3]["terminal"]["position"]=5
        self.reject("terminal mismatch")

    def test_cross_domain_return_is_rejected(self):
        self.d["components"]["U2"]["pins"]["14"]="LOGIC_GND"
        self.reject("exact pin/variant")

    def test_sense_and_current_input_pins_cannot_swap(self):
        p=self.d["components"]["U3"]["pins"]
        p["15"],p["16"]=p["16"],p["15"]
        self.reject("exact pin/variant")

    def test_both_logic_ground_pins_required(self):
        self.d["components"]["U11"]["pins"]["8"]=None
        self.reject("exact pin/variant")

    def test_substrate_islands_cannot_be_grounded_or_joined(self):
        original=copy.deepcopy(self.d)
        for net in ("FIELD_GND","LOGIC_GND","DI00_SUB_ISLAND"):
            self.d=copy.deepcopy(original);self.d["components"]["U1"]["pins"]["12"]=net
            with self.subTest(net=net):self.reject("substrate must be")

    def test_nc_pin_cannot_be_connected(self):
        self.d["components"]["U4"]["pins"]["6"]="LOGIC_GND"
        self.reject("exact pin/variant")

    def test_enable_cannot_float_or_take_field_voltage(self):
        for net in (None,"FIELD_24V"):
            self.d["components"]["U1"]["pins"]["3"]=net
            with self.subTest(net=net):self.reject("exact pin/variant")

    def test_threshold_resistor_bypass_is_detected(self):
        self.d["components"]["R1"]["pins"]["2"]="DI00_FIELD"
        self.reject("resistor connection")

    def test_filter_before_resistor_is_detected(self):
        self.d["components"]["C7"]["pins"]["1"]="DI06_FIELD"
        self.reject("filter connection")

    def test_filter_latency_change_requires_review(self):
        self.d["components"]["C7"]["capacitance_f"]=330e-9
        self.reject("filter parameters")

    def test_threshold_pulse_resistor_cannot_be_plain_0603(self):
        self.d["components"]["R1"]["mpn"]="CRCW06031001FKEA"
        self.reject("resistor connection/MPN")

    def test_support_ratings_and_values_checked(self):
        original=copy.deepcopy(self.d)
        for ref,key,value in [("C1","voltage_rating_v",25),("R1","power_screen_w",.1),("R101","resistance_ohm",200),("C101","capacitance_f",1e-9)]:
            with self.subTest(ref=ref,key=key):
                self.d=copy.deepcopy(original);self.d["components"][ref][key]=value
                self.assertFalse(HW.validate(self.d)["ok"])

    def test_bias_does_not_establish_unpowered_default(self):
        self.d["output_default"]["brownout_or_unpowered"]="guaranteed low"
        self.reject("unpowered default")

    def test_common_return_does_not_provide_channel_isolation(self):
        self.d["isolation"]["channel_to_channel_claim"]=True
        self.reject("channel isolation")

    def test_malformed_resistor_values_rejected(self):
        original=copy.deepcopy(self.d)
        for value in (True,-1,float("nan"),float("inf"),10**1000):
            self.d=copy.deepcopy(original);self.d["components"]["R1"]["resistance_ohm"]=value
            self.assertFalse(HW.validate(self.d)["ok"])

    def test_actual_netlist_mutation_not_hidden_by_model(self):
        tree=ET.parse(OUT/"netlist.xml")
        field=next(x for x in tree.findall("nets/net") if x.get("name").removeprefix("/")=="FIELD_GND")
        for net in tree.findall("nets/net"):
            found=next((x for x in net.findall("node") if x.get("ref")=="U1" and x.get("pin")=="13"),None)
            if found is not None:net.remove(found);field.append(found);break
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"bad.xml";tree.write(path);r=HW.validate(self.d,netlist=path)
        self.assertFalse(r["ok"]);self.assertIn("U1 exported pins mismatch",r["errors"])

    def test_erc_only_allows_exact_22_floating_island_warnings(self):
        original=json.loads((OUT/"erc.json").read_text(encoding="utf-8"))
        for mode in ("extra","error","wrong_pin","deleted","broad_suppression"):
            report=copy.deepcopy(original);v=report["sheets"][0]["violations"]
            if mode=="extra":v.append(copy.deepcopy(v[0]))
            if mode=="error":v[0]["severity"]="error"
            if mode=="wrong_pin":v[0]["items"][0]["uuid"]="bad"
            if mode=="deleted":v.pop()
            if mode=="broad_suppression":report["ignored_checks"].append({"key":"isolated_pin_label"})
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as td:
                path=Path(td)/"erc.json";path.write_text(json.dumps(report),encoding="utf-8")
                self.assertFalse(HW.validate(self.d,erc=path)["ok"])

    def test_frozen_ledger_tamper_is_rejected(self):
        self.d["ledger_sha256"]="0"*64
        self.assertFalse(HW.validate(self.d,ledger_path=OUT/"input-electrical-design.json")["ok"])

    def test_bounded_screens_are_not_timing_or_certification(self):
        r=HW.validate(self.d);c=r["calculations"]
        self.assertGreater(c["active_input_current_screen_a"][0],.002)
        self.assertLess(c["active_input_current_screen_a"][1],.0028)
        self.assertLess(c["rising_threshold_conservative_screen_max_v"],11.4)
        self.assertGreater(c["filter_rc_time_constant_screen_s"][0],9e-6)
        self.assertLess(c["filter_rc_time_constant_screen_s"][1],11e-6)
        self.assertGreater(c["all_22_field_power_at_30v_screen_w"],1.8)
        self.assertLess(c["logic_static_current_screen_a"],.022)
        self.assertFalse(self.d["analysis"]["filter_corner_result_is_end_to_end_delay"])
        self.assertIn("not propagation delay"," ".join(c["limitations"]))


if __name__=="__main__":unittest.main()
