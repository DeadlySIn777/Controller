"""Bounded source/model rejection controls. No board edits or native KiCad."""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path
import time
import unittest
import plan_geometry as pg
import stage_proposal as sp

HERE=Path(__file__).resolve().parent
RECORDS=pg.read_inputs()
IC=pg.load_calc(RECORDS)
PRO=json.loads(pg.frozen(RECORDS,"project").read_text(encoding="utf-8"))
POLICY=json.loads(pg.frozen(RECORDS,"historical_controlled_nets").read_text(encoding="utf-8"))
PADS=json.loads(pg.frozen(RECORDS,"native_matched_pad_table").read_text(encoding="utf-8"))
MAP=json.loads((HERE/"controlled-net-map.json").read_text(encoding="utf-8"))
GEOM=json.loads((HERE/"geometry.json").read_text(encoding="utf-8"))

class Controls(unittest.TestCase):
    def test_actual_stackup_thickness_gap_remains_visible(self):
        s=pg.stackup(pg.frozen(RECORDS,"board"))
        self.assertEqual(s["copper_plus_dielectric_mm"],1.53)
        self.assertEqual(s["including_masks_mm"],1.55)
        self.assertEqual(s["nominal_mismatch_mm"],.05)
        self.assertEqual(set(s["zone_polygon_counts_not_continuity_evidence"]["In2.Cu"]),{"/IO_3V3"})

    def test_all_controlled_names_are_exact_current_and_paired(self):
        result=pg.map_policy(POLICY,PADS,PRO)
        self.assertEqual(result,MAP); self.assertEqual(len(result),204)
        self.assertEqual(len([x for x in result.values() if x["class"]=="IMP_50"]),100)
        self.assertTrue(any("{slash}" in x for x in result))
        for name,r in result.items():
            with self.subTest(net=name):
                self.assertIn(r["domain"],r["existing_classes"])
                if r["class"].startswith("DIFF"):
                    self.assertEqual(result[r["exact_pair_partner"]]["exact_pair_partner"],name)

    def test_alias_ambiguity_rejected(self):
        p=copy.deepcopy(PADS)
        exact=next(n for n in MAP if "{slash}" in n)
        p["pads"].append({"net":pg.canonical(exact)})
        with self.assertRaisesRegex(ValueError,"ambiguous"):pg.map_policy(POLICY,p,PRO)

    def test_missing_current_net_rejected(self):
        exact=next(iter(MAP));p=copy.deepcopy(PADS)
        p["pads"]=[x for x in p["pads"] if x["net"]!=exact]
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):pg.map_policy(POLICY,p,PRO)

    def test_list_class_schema_required(self):
        exact=next(iter(MAP));p=copy.deepcopy(PRO)
        p["net_settings"]["netclass_assignments"][exact]="DOM_LOGIC"
        with self.assertRaisesRegex(ValueError,"list-valued"):pg.map_policy(POLICY,PADS,p)

    def test_domain_loss_and_pair_mismatch_rejected(self):
        p=copy.deepcopy(PRO);exact=next(iter(MAP))
        p["net_settings"]["netclass_assignments"].pop(exact,None)
        p["net_settings"]["netclass_patterns"]=[r for r in p["net_settings"]["netclass_patterns"] if r["pattern"]!=exact]
        with self.assertRaisesRegex(ValueError,"retain one explicit domain"):pg.map_policy(POLICY,PADS,p)
        policy=copy.deepcopy(POLICY)
        old=next(n for n,r in policy["nets"].items() if r["class"].startswith("DIFF"))
        policy["nets"][old]["pair_partner"]="/NO_SUCH_NET"
        with self.assertRaisesRegex(ValueError,"partner"):pg.map_policy(policy,PADS,PRO)

    def test_project_preserves_old_domains_patterns_and_all_other_fields(self):
        p=sp.proposal_project(PRO,MAP,GEOM)
        sp.verify_project(PRO,p,MAP)
        self.assertEqual(p["net_settings"]["netclass_patterns"],PRO["net_settings"]["netclass_patterns"])
        for c in p["net_settings"]["classes"][-4:]:self.assertEqual(c["clearance"],.15)
        for bad in ("via_diameter","via_drill"):
            q=copy.deepcopy(p);q["net_settings"]["classes"][-1][bad]=.01
            with self.subTest(field=bad),self.assertRaisesRegex(ValueError,"non-geometry"):sp.verify_project(PRO,q,MAP)
        q=copy.deepcopy(p);q["net_settings"]["classes"][-1]["clearance"]=.149
        with self.assertRaisesRegex(ValueError,"effective clearance"):sp.verify_project(PRO,q,MAP)
        q=copy.deepcopy(p);q["net_settings"]["classes"][-1].pop("clearance")
        with self.assertRaisesRegex(ValueError,"non-geometry"):sp.verify_project(PRO,q,MAP)

    def test_other_project_change_and_domain_deletion_rejected(self):
        p=sp.proposal_project(PRO,MAP,GEOM)
        q=copy.deepcopy(p);q["meta"]["filename"]="wrong.kicad_pro"
        with self.assertRaisesRegex(ValueError,"non-netclass"):sp.verify_project(PRO,q,MAP)
        q=copy.deepcopy(p);q["net_settings"]["netclass_patterns"]=[]
        with self.assertRaisesRegex(ValueError,"patterns"):sp.verify_project(PRO,q,MAP)
        q=copy.deepcopy(p);exact=next(iter(MAP));q["net_settings"]["netclass_assignments"][exact]=[]
        with self.assertRaisesRegex(ValueError,"original classes"):sp.verify_project(PRO,q,MAP)

    def test_original_rules_literal_necks_preserved(self):
        original=pg.frozen(RECORDS,"rules").read_bytes()
        result=sp.proposal_rules(original.decode(),GEOM).encode()
        self.assertTrue(result.startswith(original))
        append=result[len(original):].decode()
        self.assertEqual(append.count('(rule "PROVISIONAL '),7)
        self.assertEqual(append.count("U1001_LITERAL_SIGNAL_NECKS"),4)
        self.assertNotIn("(constraint clearance",append)
        self.assertNotIn("(constraint hole_clearance",append)
        self.assertNotIn('(layer "In3.Cu")',append)
        with self.assertRaisesRegex(ValueError,"BGA exception"):sp.proposal_rules("(version 1)\n",GEOM)

    def test_ipc_invalid_inner_never_claimed_as_second_valid_method(self):
        layer=pg.layer_models(IC,pg.stackup(pg.frozen(RECORDS,"board")))["In3.Cu"]
        for w in (.20,.21,.3,.5,1):
            with self.subTest(w=w):self.assertFalse(IC.ipc_stripline_valid(w,layer.h1,layer.h2,layer.t))
        for cls in pg.TARGETS:
            with self.subTest(cls=cls):self.assertNotEqual(pg.choose(IC,layer,cls)["status"],"PROVISIONAL_AB")
        self.assertEqual(GEOM["In3.Cu"]["DIFF_120"]["status"],"HELD_INFEASIBLE_B_MODEL")

    def test_outer_models_ranges_and_all_corners(self):
        for cls,rec in GEOM["F.Cu"].items():
            with self.subTest(cls=cls):
                self.assertEqual(rec,GEOM["B.Cu"][cls]);self.assertEqual(rec["status"],"PROVISIONAL_AB")
                self.assertLessEqual(rec["nominal"]["A_B_difference_pct_of_B"],5)
                for c in rec["corners"]:
                    self.assertTrue(c["A_valid"]);self.assertTrue(c["B_coupled_microstrip_valid"])
                    self.assertTrue(pg.in_tol(c["A_ohm"],rec["target_ohm"]))
                    self.assertTrue(pg.in_tol(c["B_ohm"],rec["target_ohm"]))

    def test_inner_two_mesh_checks_and_scope_no_release(self):
        for cls,rec in GEOM["In3.Cu"].items():
            if "field_nominal" not in rec:continue
            with self.subTest(cls=cls):
                self.assertFalse(rec["nominal"]["A_valid"])
                self.assertLessEqual(rec["B_C_difference_pct_of_C"],5)
                self.assertTrue(rec["mesh_convergence"]["passes"])
                self.assertLessEqual(rec["mesh_convergence"]["two_mesh_max_change_pct"],1)
                for f in [rec["field_nominal"],rec["field_nominal_refined"]]+rec["field_corners"]+rec["field_corners_refined"]:
                    self.assertLessEqual(max(m["nodes"] for m in f["meshes"]),160000)
                    self.assertTrue(pg.in_tol(f["C_ohm"],rec["target_ohm"]))
        proposal=json.loads((HERE/"future-copy-proposal/proposal.json").read_text())
        self.assertFalse(proposal["installed"])
        self.assertEqual(proposal["generic_future_planner_allowed_controlled_layers"],["F.Cu","B.Cu"])
        self.assertIn("HELD_REFERENCE_RETURN",proposal["held_controlled_layers"]["In3.Cu"])

def main():
    start=time.perf_counter();stream=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (HERE/"host-tests.log").write_text(stream.getvalue(),encoding="utf-8")
    # Run only the frozen published/hand-worked closed-form controls. No historical FD sweep.
    import pytest
    with __import__("contextlib").redirect_stdout(stream),__import__("contextlib").redirect_stderr(stream):
        code=pytest.main([str(pg.frozen(RECORDS,"calculator_tests")),"-q","-k","not fd and not solder_mask","-p","no:cacheprovider"])
    (HERE/"host-tests.log").write_text(stream.getvalue(),encoding="utf-8")
    pg.read_inputs()
    receipt={"verdict":"PASS" if result.wasSuccessful() and code==0 else "FAIL","host_tests":result.testsRun,
             "failures":len(result.failures),"errors":len(result.errors),"skips":len(result.skipped),
             "published_calculator_test_exit":code,"read_set_unchanged":True,"KiCad_invoked":False,"GPU_invoked":False,
             "runtime_seconds":time.perf_counter()-start,"executed_script_sha256":pg.sha(Path(__file__).read_bytes()),
             "plan_script_sha256":pg.sha((HERE/"plan_geometry.py").read_bytes()),"stage_script_sha256":pg.sha((HERE/"stage_proposal.py").read_bytes())}
    pg.write(HERE/"host-receipt.json",receipt);print(json.dumps(receipt))
    if receipt["verdict"]!="PASS":raise SystemExit(1)

if __name__=="__main__":main()
