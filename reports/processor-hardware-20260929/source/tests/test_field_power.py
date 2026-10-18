"""Fault injection for the field-side buck review model and actual KiCad netlist."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("field_power_validation",ROOT/"tools/hardware_validate_field_power.py")
HW=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HW)
OUT=ROOT/"hardware/field_power"


class FieldPowerTests(unittest.TestCase):
    def setUp(self):
        self.design=json.loads((OUT/"design.json").read_text(encoding="utf-8"))

    def reject(self,text):
        result=HW.validate(self.design)
        self.assertFalse(result["ok"],result)
        self.assertTrue(any(text in e for e in result["errors"]),result)

    def test_reviewed_model_matches_actual_export_and_erc(self):
        r=HW.validate(self.design,OUT/"netlist.xml",OUT/"erc.json",OUT)
        self.assertTrue(r["ok"],r)
        self.assertFalse(r["manufacturing_ready"])
        self.assertGreater(len(r["warnings"]),3)

    def test_bootstrap_grounding_is_rejected(self):
        self.design["components"]["C6"]["pins"]["2"]="FIELD_GND"
        self.reject("C6 connection")

    def test_fixed_output_pin_cannot_become_feedback_divider(self):
        self.design["components"]["U1"]["pins"]["8"]="FIELD_FB"
        self.reject("U1 exact pin")

    def test_vin_enable_swapped_is_rejected(self):
        p=self.design["components"]["U1"]["pins"]
        p["3"],p["4"]=p["4"],p["3"]
        self.reject("U1 exact pin")

    def test_rt_grounding_is_not_same_frequency(self):
        self.design["components"]["U1"]["pins"]["1"]="FIELD_GND"
        self.reject("U1 exact pin")

    def test_logical_ground_crossing_is_rejected(self):
        self.design["components"]["C1"]["pins"]["2"]="LOGIC_GND"
        self.reject("unexpected rail or ground")

    def test_enable_cannot_bootstrap_from_own_output(self):
        self.design["components"]["R1"]["pins"]["1"]="FIELD_5V"
        self.reject("R1 connection")

    def test_additional_5v_pullup_path_is_rejected(self):
        self.design["components"]["R99"]=copy.deepcopy(self.design["components"]["R3"])
        self.design["components"]["R99"]["pins"]["2"]="F_PGOOD"
        self.reject("component set")

    def test_input_25v_capacitor_is_rejected(self):
        self.design["components"]["C2"]["voltage_v"]=25
        self.reject("C2 voltage rating")

    def test_bootstrap_cap_must_be_differentially_rated(self):
        self.design["components"]["C6"]["voltage_v"]=4
        self.reject("C6 voltage rating")

    def test_inductor_must_cover_current_limit_reference(self):
        self.design["components"]["L1"]["isat_10pct_25c_a"]=.9
        self.reject("saturation margin")

    def test_weak_enable_divider_loses_startup_margin(self):
        self.design["components"]["R1"]["resistance_ohm"]=1000000
        self.reject("startup threshold margin")

    def test_wrong_regulator_variant_is_rejected(self):
        self.design["components"]["U1"]["mpn"]="LMR36506R3RPER"
        self.reject("MPN differs")

    def test_negative_or_nonfinite_components_are_rejected(self):
        base=copy.deepcopy(self.design)
        for value in (-1,float("nan"),float("inf"),10**1000,True):
            with self.subTest(value=str(value)[:25]):
                self.design=copy.deepcopy(base)
                self.design["components"]["R1"]["resistance_ohm"]=value
                self.assertFalse(HW.validate(self.design)["ok"])

    def test_missing_support_capacitor_is_rejected(self):
        del self.design["components"]["C7"]
        self.reject("component set")

    def test_model_cannot_claim_manufacture_ready(self):
        self.design["manufacturing_ready"]=True
        self.reject("qualification status")

    def test_actual_export_pin_mutation_is_detected(self):
        tree=ET.parse(OUT/"netlist.xml")
        for net in tree.findall("nets/net"):
            for node in net.findall("node"):
                if node.get("ref")=="C6" and node.get("pin")=="2":
                    net.remove(node)
                    next(n for n in tree.findall("nets/net") if n.get("name").removeprefix("/")=="FIELD_GND").append(node)
                    break
            else:continue
            break
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"wrong.xml";tree.write(path)
            r=HW.validate(self.design,netlist=path)
        self.assertFalse(r["ok"],r)
        self.assertIn("C6 exported pins differs",r["errors"])

    def test_erc_violation_and_suppression_are_detected(self):
        report=json.loads((OUT/"erc.json").read_text(encoding="utf-8"))
        for change in ("violation","suppression","no_sheet"):
            changed=copy.deepcopy(report)
            if change=="violation":changed["sheets"][0]["violations"]=[{"severity":"error"}]
            elif change=="suppression":changed["ignored_checks"].append({"key":"pin_not_connected"})
            else:changed["sheets"]=[]
            with self.subTest(change=change),tempfile.TemporaryDirectory() as td:
                path=Path(td)/"erc.json";path.write_text(json.dumps(changed),encoding="utf-8")
                self.assertFalse(HW.validate(self.design,erc=path)["ok"])

    def test_frozen_ledger_hash_tamper_is_detected(self):
        self.design["frozen_inputs"]["input-electrical-design.json"]="0"*64
        r=HW.validate(self.design,evidence_dir=OUT)
        self.assertFalse(r["ok"],r)
        self.assertTrue(any("hash mismatch" in e for e in r["errors"]))

    def test_enable_corner_arithmetic_and_caps_are_bounded(self):
        c=HW.bounded_calculations(self.design)
        # Independent simple envelopes, not calculated by the production function.
        self.assertGreater(c["en_released_normal_v"][0],1.57)
        self.assertLess(c["en_released_normal_v"][1],2.84)
        self.assertLess(c["en_asserted_surge_screen_max_v"],.08)
        self.assertLess(c["entry_pg_sink_screen_max_a"],.001)
        self.assertLess(c["r1_surge_screen_max_w"],.04)
        self.assertAlmostEqual(c["output_cap_max_no_bias_f"],44.1e-6*1.1*1.15,places=12)
        self.assertGreater(c["input_charge_at_entry_max_ramp_a"],.007)
        self.assertLess(c["input_charge_at_entry_max_ramp_a"],.008)
        self.assertIn("PFM", " ".join(c["limitations"]))


if __name__=="__main__":
    unittest.main()
