"""Host fixtures/rejection controls only; no native call or native board creation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import open_check_shared as shared

HERE = Path(__file__).resolve().parent
WORK = HERE.parent.parent


def fixture():
    # Genuine saved settings observations, synthetic alias paths/identity envelopes.
    # This fixture never creates board/project files or establishes native-open proof.
    source = json.loads((WORK / "power-audit/project-binding-probe.json").read_text(encoding="utf-8"))
    settings = source["unbound_LoadBoard"]
    contexts = {}
    for role, stem in (("measured", "board"), ("alias", "motherboard")):
        root = HERE / "host-fixture-no-files" / role
        board = root / (stem + ".kicad_pcb")
        snapshot = copy.deepcopy(settings)
        snapshot["loaded_board_filename"] = str(board)
        inv = {stem + ext: value for ext, value in ((".kicad_pcb", shared.C05_SHA), (".kicad_pro", shared.PRO_SHA), (".kicad_dru", shared.DRU_SHA))}
        contexts[role] = {"board_path": str(board), "project_path": str(board.with_suffix(".kicad_pro")),
                "rules_path": str(board.with_suffix(".kicad_dru")), "raw_project_meta_filename": "board.kicad_pro",
                "snapshot": snapshot, "directory_before_sha256": inv, "directory_after_sha256": dict(inv),
                "input_directory_unchanged": True, "project_unloaded_without_save": True}
    return {"schema_version": 1, "native_build_version": "10.0.4", **contexts,
            "native_refill_started": False, "native_drc_started": False, "board_saved": False,
            "project_saved": False, "GUI_started": False}


class TestNativeOpen(unittest.TestCase):
    def test_host_observation_fixture(self):
        result = shared.validate_report(fixture())
        self.assertEqual(result["verdict"], "PASS")
        self.assertFalse(result["complete_custom_rule_equivalence_proved"])

    def test_reject_alias_minimum_class_or_samples_difference(self):
        for group in shared.GROUPS:
            report = fixture()
            report["alias"]["snapshot"][group] = {}
            with self.subTest(group=group), self.assertRaises((ValueError, KeyError)):
                shared.validate_report(report)
        report = fixture()
        report["alias"]["snapshot"]["settings_nm"]["m_MinClearance"] += 1
        with self.assertRaises(ValueError):
            shared.validate_report(report)

    def test_reject_dummy_missing_project_and_api_error(self):
        for key, value in (("project_is_none", True), ("settings_manager_open", False),
                           ("settings_manager_open_not_dummy", False), ("requested_project_present_in_manager", False)):
            report = fixture()
            report["alias"]["snapshot"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                shared.validate_report(report)
        report = fixture()
        report["alias"]["snapshot"]["settings_nm"]["m_MinClearance"] = {"api_error": "unavailable"}
        with self.assertRaises(ValueError):
            shared.validate_report(report)

    def test_reject_meta_rewrite_wrong_hash_stem_or_directory_change(self):
        cases = (("raw_project_meta_filename", "motherboard.kicad_pro"), ("project_unloaded_without_save", False),
                 ("input_directory_unchanged", False), ("project_path", str(HERE / "board.kicad_pro")))
        for key, value in cases:
            report = fixture()
            report["alias"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                shared.validate_report(report)
        report = fixture()
        report["alias"]["directory_after_sha256"]["new-file"] = "0" * 64
        with self.assertRaises(ValueError):
            shared.validate_report(report)
        report = fixture()
        for key in ("directory_before_sha256", "directory_after_sha256"):
            report["alias"][key]["motherboard.kicad_pro"] = "0" * 64
        with self.assertRaises(ValueError):
            shared.validate_report(report)

    def test_reject_runtime_or_scope(self):
        for key, value in (("native_build_version", "10.0.5"), ("native_refill_started", True), ("native_drc_started", True),
                           ("board_saved", True), ("project_saved", True), ("GUI_started", True)):
            report = fixture()
            report[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                shared.validate_report(report)

    def test_native_evidence_prerequisite_never_accepts_pending_or_fail(self):
        q = {"verdict": "PASS_EXPERIMENTAL_NATIVE_EVIDENCE", "selection": {"sha256": shared.C05_SHA},
             "adopted": False, "manufacturing_ready": False}
        status = {"phase": "COMPLETE", "verdict": "PASS"}
        proof = {"verdict": "PASS", "candidate_sha256": shared.C05_SHA,
                 "connectivity": {"verdict": "PASS", "lost": 0}, "drc": {"after": {"errors": 0}}}
        shared.require_native_evidence(q, status, proof)
        for phase in ("NATIVE_MEASUREMENT_RUNNING", "FAILED", "EVALUATING_NATIVE_RECEIPTS"):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                shared.require_native_evidence(q, {**status, "phase": phase}, proof)
        with self.assertRaises(ValueError):
            shared.require_native_evidence(q, {**status, "verdict": "FAIL"}, {**proof, "verdict": "FAIL"})
        bad = copy.deepcopy(proof)
        bad["drc"]["after"]["errors"] = 1
        with self.assertRaises(ValueError):
            shared.require_native_evidence(q, status, bad)

    def test_inventory_detects_plain_input_change(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "sentinel.txt"
            file.write_text("unchanged")
            before = shared.inventory(temp)
            file.write_text("changed")
            self.assertNotEqual(before, shared.inventory(temp))


if __name__ == "__main__":
    unittest.main()
