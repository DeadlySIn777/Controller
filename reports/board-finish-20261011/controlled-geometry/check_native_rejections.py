"""Host replay of final native observation, plus bounded rejection controls."""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import time
import unittest
import plan_geometry as pg
import run_native_classes as rc

HERE=Path(__file__).resolve().parent
OUT=HERE/"native-check-r3"
RAW=json.loads((OUT/"native-classes.json").read_text())
INPUTS=json.loads((OUT/"inputs.json").read_text())
MAP=json.loads((HERE/"controlled-net-map.json").read_text())
GEOM=json.loads((HERE/"geometry.json").read_text())

def check(raw):return rc.validate(raw,INPUTS,MAP,GEOM)

class Rejections(unittest.TestCase):
    def test_actual_report_passes(self):
        r=check(RAW);self.assertEqual(r["verdict"],"PASS_NATIVE_EFFECTIVE_CLASSES_ONLY")
        self.assertEqual(r["selected_controlled_nets_checked"],204)
        self.assertFalse(r["routing_qualified"])

    def test_negative_aggregate_minimum_rejected(self):
        r=copy.deepcopy(RAW);r["proposal"]["binding_and_minima"]["settings_nm"]["GetSmallestClearanceValue"]=-1
        with self.assertRaisesRegex(ValueError,"global minima"):check(r)

    def test_original_class_changed_rejected(self):
        r=copy.deepcopy(RAW);r["proposal"]["declared_classes"]["DOM_LOGIC"]["GetClearance"]=149999
        with self.assertRaisesRegex(ValueError,"original class"):check(r)

    def test_wrong_geometry_domain_clearance_via_rejected(self):
        exact=next(iter(MAP))
        for field in ("GetTrackWidth","GetClearance","GetViaDiameter","GetViaDrill"):
            r=copy.deepcopy(RAW);r["proposal"]["all_named_net_effective_classes"][exact][field]+=1
            with self.subTest(field=field),self.assertRaises(ValueError):check(r)
        r=copy.deepcopy(RAW);r["proposal"]["all_named_net_effective_classes"][exact]["constituents"].remove(MAP[exact]["domain"])
        with self.assertRaisesRegex(ValueError,"domain lost"):check(r)

    def test_wrong_hash_or_changed_input_rejected(self):
        r=copy.deepcopy(RAW);r["proposal"]["directory_before_sha256"]["board.kicad_pcb"]="0"*64
        with self.assertRaisesRegex(ValueError,"input directory"):check(r)
        r=copy.deepcopy(RAW);r["proposal"]["directory_after_sha256"]["board.kicad_dru"]="0"*64
        with self.assertRaisesRegex(ValueError,"input directory"):check(r)

    def test_api_error_dummy_project_or_side_effect_rejected(self):
        r=copy.deepcopy(RAW);r["proposal"]["binding_and_minima"]["settings_nm"]["m_MinClearance"]={"api_error":"not measured"}
        with self.assertRaisesRegex(ValueError,"API error"):check(r)
        r=copy.deepcopy(RAW);r["proposal"]["binding_and_minima"]["project_is_none"]=True
        with self.assertRaisesRegex(ValueError,"dummy/unbound"):check(r)
        for flag in ("refill","DRC","Save","GUI"):
            r=copy.deepcopy(RAW);r[flag]=True
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,"scope"):check(r)

    def test_missing_selected_or_unselected_change_rejected(self):
        r=copy.deepcopy(RAW);r["proposal"]["all_named_net_effective_classes"].pop(next(iter(MAP)))
        with self.assertRaisesRegex(ValueError,"inventory"):check(r)
        name=next(n for n in RAW["baseline"]["all_named_net_effective_classes"] if n not in MAP)
        r=copy.deepcopy(RAW);r["proposal"]["all_named_net_effective_classes"][name]["GetTrackWidth"]+=1
        with self.assertRaisesRegex(ValueError,"unselected"):check(r)

def main():
    start=time.perf_counter();s=io.StringIO();result=unittest.TextTestRunner(stream=s,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Rejections))
    (HERE/"native-host-tests.log").write_text(s.getvalue())
    pg.write(HERE/"native-host-receipt.json",{"verdict":"PASS" if result.wasSuccessful() else "FAIL","tests":result.testsRun,
             "failures":len(result.failures),"errors":len(result.errors),"skips":len(result.skipped),
             "runtime_seconds":time.perf_counter()-start,"actual_native_report_sha256":pg.sha((OUT/"native-classes.json").read_bytes()),
             "script_sha256":pg.sha(Path(__file__).read_bytes()),"additional_native_jobs":0})
    print(s.getvalue());raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=="__main__":main()
