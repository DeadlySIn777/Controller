"""Cheap rejection fixtures; no KiCad load and no modification of native inputs."""
import copy
import json
import unittest
from pathlib import Path
from finish_project_binding_audit import validate_probe

HERE = Path(__file__).resolve().parent


class BindingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.probe = json.loads((HERE / "project-binding-probe.json").read_text())
        self.project = json.loads(Path(self.probe["board"]).with_suffix(".kicad_pro").read_text())

    def rejects(self, edit):
        changed = copy.deepcopy(self.probe)
        edit(changed)
        with self.assertRaises((ValueError, KeyError)):
            validate_probe(changed, self.project)

    def test_real_observations_match(self):
        self.assertEqual(validate_probe(self.probe, self.project)["netclass_count"], 28)

    def test_dummy_project(self):
        self.rejects(lambda p: p["unbound_LoadBoard"].update(settings_manager_open_not_dummy=False))

    def test_rule_difference_hidden_by_equivalence_claim(self):
        self.rejects(lambda p: p["explicit_project_bound"]["settings_nm"].update(m_TrackMinWidth=100000))

    def test_stale_producer_source(self):
        self.rejects(lambda p: p.update(native_build_version="9.0.6"))

    def test_api_error(self):
        self.rejects(lambda p: p["unbound_LoadBoard"]["settings_nm"].update(m_HoleClearance={"api_error": "missing"}))

    def test_stale_rules(self):
        self.rejects(lambda p: p["input_directory_before_sha256"].update(**{"board.kicad_dru": "0" * 64}))

    def test_mutated_input_scope(self):
        self.rejects(lambda p: p.update(board_saved=True))

    def test_prebind_difference(self):
        self.rejects(lambda p: p["LoadBoard_after_LoadProject_before_SetProject"]["netclasses"]["DOM_LOGIC"].update(GetClearance=100000))

    def test_wrong_effective_class_in_all_snapshots(self):
        def edit(p):
            for name in ("unbound_LoadBoard", "LoadBoard_after_LoadProject_before_SetProject", "explicit_project_bound"):
                p[name]["representative_effective_classes"]["/LOGIC_GND"]["GetName"] = "Default"
        self.rejects(edit)

    def test_raw_rule_mismatch_even_if_all_snapshots_equal(self):
        def edit(p):
            for name in ("unbound_LoadBoard", "LoadBoard_after_LoadProject_before_SetProject", "explicit_project_bound"):
                p[name]["settings_nm"]["m_HoleClearance"] = 200000
        self.rejects(edit)


if __name__ == "__main__":
    unittest.main()
