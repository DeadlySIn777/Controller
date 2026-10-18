"""Cheap controls for qualification rejection boundaries; no native jobs."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import qualify_bundle as bundle
from partition_guard import compare
from symbol_resources import canonical as symbol_canonical


class TestQualification(unittest.TestCase):
    def test_cli_custom_rule_parse_failures(self):
        for line in ("Error parsing custom rules", "Failed to load board.kicad_dru", "Invalid DRC rule condition", "Syntax error at line 10"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                bundle.check_cli_rule_diagnostics(line)
        bundle.check_cli_rule_diagnostics("Failed to fetch schematic netlist for parity tests.\nSchematic parity tests require a fully annotated schematic.")
        bundle.check_cli_rule_diagnostics("No errors in custom rules.")

    def test_binding_receipt_effective_state_identity_version(self):
        path = bundle.WORK / "power-audit/project-binding-audit.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        roles = {"board.kicad_pro": receipt["input"]["project_sha256"], "board.kicad_dru": receipt["input"]["rules_sha256"]}
        bundle.assert_binding_receipt(receipt, roles, "10.0.4")
        mutations = [("verdict", "FAIL"), ("input.input_directory_unchanged", False),
                     ("effective_settings.all_observed_groups_equal", False),
                     ("effective_settings.api_observation_errors", ["API failure"]),
                     ("runtime.native_build_version", "10.0.5"),
                     ("rule_initialization.complete_rule_equivalence_proved", True),
                     ("rule_initialization.LoadBoard_implicitly_binds_sibling_project", False),
                     ("refill_required_due_to_observed_binding_difference", True)]
        for target, value in mutations:
            modified = copy.deepcopy(receipt)
            node = modified
            keys = target.split(".")
            for key in keys[:-1]:
                node = node[key]
            node[keys[-1]] = value
            with self.subTest(target=target), self.assertRaises(ValueError):
                bundle.assert_binding_receipt(modified, roles, "10.0.4")
        with self.assertRaises(ValueError):
            bundle.assert_binding_receipt(receipt, {**roles, "board.kicad_dru": "0" * 64}, "10.0.4")
        with self.assertRaises(ValueError):
            bundle.assert_binding_receipt(receipt, roles, "10.0.5")

    def test_actual_binding_source_runtime_hashes(self):
        receipt = json.loads((bundle.WORK / "power-audit/project-binding-audit.json").read_text())
        args = SimpleNamespace(binding_audit=bundle.WORK / "power-audit/project-binding-audit.json",
                               measure=Path("Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2"))
        roles = {"board.kicad_pro": receipt["input"]["project_sha256"], "board.kicad_dru": receipt["input"]["rules_sha256"]}
        reads = bundle.ReadSet()
        result = bundle.bind_project_state(args, roles, "10.0.4", reads)
        self.assertEqual(result["status"], "PASS_OBSERVED_BINDING_AND_SETTINGS_EQUIVALENCE")
        self.assertFalse(result["complete_rule_equivalence_proved"])
        reads.verify()

    def test_actual_c03_failed_native_proof_rejected_before_bundle(self):
        board = bundle.WORK / "recovery-composite/c03-recovery-in3-fag-dfm.kicad_pcb"
        out = bundle.HERE / "host-negative-c03-no-bundle"
        args = SimpleNamespace(board=board, sha256="8f1e03225429422199edc52c3c1ceb476818948c7a5f920e7d71b7cc8d7640c9",
                measure=bundle.WORK / "measure/c03-shared", parity=bundle.WORK / "parity-repair/c03",
                source_export=bundle.WORK / "parity-repair/root106/source-export", out=out,
                symbol_library_root=Path("Z:/pcb-runs/claude-finish/review/schematic/erc_full"),
                binding_audit=bundle.WORK / "power-audit/project-binding-audit.json")
        before = bundle.digest(board.read_bytes())
        self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError, "native measurement is incomplete or failed"):
            bundle.evaluate(args)
        self.assertFalse(out.exists())
        self.assertEqual(bundle.digest(board.read_bytes()), before)

    def test_symbol_geometry_only_numeric_normalisation(self):
        self.assertEqual(symbol_canonical(["at", "0.0", "1.00", "0"]), ["at", "0", "1", "0"])
        self.assertNotEqual(symbol_canonical(["number", "01"]), symbol_canonical(["number", "1"]))
        self.assertNotEqual(symbol_canonical(["property", "Value", "1.00"]), symbol_canonical(["property", "Value", "1"]))
    def test_complete_identity_scope(self):
        status = {"phase": "COMPLETE", "verdict": "PASS"}
        proof = {"verdict": "PASS", "candidate_sha256": "a" * 64, "adopted": False, "manufacturing_ready": False}
        bundle.assert_complete(status, proof, "a" * 64)
        for key, value in [("verdict", "FAIL"), ("candidate_sha256", "b" * 64),
                           ("adopted", True), ("manufacturing_ready", True)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                bundle.assert_complete(status, {**proof, key: value}, "a" * 64)
        for phase in ("NATIVE_MEASUREMENT_RUNNING", "EVALUATING_NATIVE_RECEIPTS", "FAILED"):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                bundle.assert_complete({**status, "phase": phase}, proof, "a" * 64)

    def test_exact_r06_candidate(self):
        inputs = {"before_sha256": bundle.R06_SHA, "after_sha256": "a" * 64}
        bundle.assert_identity(inputs, "a" * 64)
        for key in inputs:
            with self.subTest(key=key), self.assertRaises(ValueError):
                bundle.assert_identity({**inputs, key: "b" * 64}, "a" * 64)
        with self.assertRaises(ValueError):
            bundle.assert_identity(inputs, "invalid")

    def test_lost_even_total_improves_and_api_truth(self):
        before = {"sha256": "a" * 64, "refilled": True, "pad_island_joins": 2, "api_unconnected_count": 2,
                  "nets": {"A": [["a", "b"], ["c", "d"]], "B": [["e"], ["f"]]}}
        after = {"sha256": "b" * 64, "refilled": True, "pad_island_joins": 1, "api_unconnected_count": 1,
                 "nets": {"A": [["a", "c", "d"], ["b"]], "B": [["e", "f"]]}}
        with self.assertRaises(ValueError):
            bundle.assert_guard(compare(before, after))
        after = {**before, "sha256": "b" * 64, "api_unconnected_count": 1}
        with self.assertRaises(ValueError):
            compare(before, after)
        after = copy.deepcopy(before)
        after["nets"]["A"][0][1] = "wrong-pad-identity"
        with self.assertRaises(ValueError):
            compare(before, after)

    def test_source_semantic_export_rejects_changed_nodes(self):
        saved = {"components": {"U1": {}}, "nets": {"A": [("U1", "1")]}, "node_assignments": [("U1", "1", "A")]}
        receipt = {"verdict": "PASS", "native_exit_code": 0, "frozen_source_inputs_unchanged": True,
                   "saved_export_sha256": "a" * 64, "fresh_export_sha256": "b" * 64,
                   "semantic_difference_sections": {k: False for k in saved}}
        bundle.bind_export(receipt, "a" * 64, "b" * 64, saved, saved)
        for key, value in [("verdict", "FAIL"), ("fresh_export_sha256", "c" * 64),
                           ("frozen_source_inputs_unchanged", False), ("native_exit_code", 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                bundle.bind_export({**receipt, key: value}, "a" * 64, "b" * 64, saved, saved)
        mutated = copy.deepcopy(saved)
        mutated["node_assignments"][0] = ("U1", "1", "B")
        with self.assertRaises(ValueError):
            bundle.bind_export(receipt, "a" * 64, "b" * 64, saved, mutated)

    def test_pinned_bytes_change_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input"
            path.write_bytes(b"native-evidence")
            reads = bundle.ReadSet()
            expected = bundle.digest(path.read_bytes())
            bundle.tracked(reads, path, expected)
            path.write_bytes(b"modified-evidence")
            with self.assertRaises(ValueError):
                reads.verify()

    def test_output_existing_or_outside_rejected_before_mutation(self):
        args = SimpleNamespace(out=bundle.HERE)
        with self.assertRaises(ValueError):
            bundle.create_bundle(args, {}, bundle.ReadSet())
        args.out = bundle.WORK
        with self.assertRaises(ValueError):
            bundle.create_bundle(args, {}, bundle.ReadSet())


if __name__ == "__main__":
    unittest.main()
