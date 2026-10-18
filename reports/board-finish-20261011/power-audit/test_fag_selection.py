"""Cheap host tests: reject unsafe selections without running KiCad or changing inputs."""
import copy
import json
import unittest
from pathlib import Path

from run_fag_subset import BASE_SHA, NET, validate_selection

HERE = Path(__file__).resolve().parent


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.analysis = json.loads((HERE / "fag-r06/source/0-analysis.json").read_text())
        self.design = json.loads((HERE / "fag-r06/source/1-design.json").read_text())
        self.routes = json.loads((HERE / "fag-r06/source/2-routes.json").read_text())

    def test_actual_subset(self):
        selected = validate_selection(self.analysis, self.design, self.routes)["tracks"]
        self.assertEqual(len(selected), 261)
        self.assertEqual(sum(item.get("kind") == "via" for item in selected), 8)
        self.assertEqual({item["net"] for item in selected}, {NET})

    def test_stale_board(self):
        self.analysis["input"]["board_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_unrefilled_source(self):
        self.analysis["input"]["refilled"] = False
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_foreign_domain(self):
        self.design["nets"]["FAG"]["domain"] = "DOM_FIELD_B"
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_under_counted_array(self):
        self.design["nets"]["FAG"]["via_groups"][0].update(amps=1.5, n=2, ok=True)
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_narrowed_trunk(self):
        item = next(item for item in self.routes["tracks"] if item["net"] == NET and item.get("kind") != "via")
        item["width"] = 0.24
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_changed_via_drill(self):
        item = next(item for item in self.routes["tracks"] if item["net"] == NET and item.get("kind") == "via")
        item["drill"] = 0.2
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_missing_via(self):
        item = next(item for item in self.routes["tracks"] if item["net"] == NET and item.get("kind") == "via")
        self.routes["tracks"].remove(item)
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_larger_claimed_current(self):
        self.design["nets"]["FAG"]["current_reaching_source_a"] = 4.58
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)

    def test_over_temperature(self):
        self.design["nets"]["FAG"]["summary"]["segments_over_10C"] = 1
        with self.assertRaises(ValueError):
            validate_selection(self.analysis, self.design, self.routes)


if __name__ == "__main__":
    unittest.main()
