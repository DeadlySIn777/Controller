"""Cheap host fixtures; never load, modify or invoke the live native run."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from finish_bridge_proof import FLAGS, InvalidEvidence, TOOL_NAMES, evaluate
from partition_guard import compare


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Fixture:
    def __init__(self, root):
        self.root = Path(root)
        self.out = self.root / "native"
        self.before = self.root / "baseline"
        self.tools = self.root / "tools"
        for directory in (self.out, self.before, self.tools, self.out / "copy", self.before / "copy"):
            directory.mkdir(parents=True, exist_ok=True)
        fp = b'\t(footprint "fixture"\n\t\t(uuid "fp-1")\n\t\t(pad "1" smd rect (uuid "pad-1"))\n\t)\n'
        self.bboard = self.root / "before.kicad_pcb"
        self.aboard = self.root / "after.kicad_pcb"
        self.bboard.write_bytes(b"(kicad_pcb\n" + fp + b"\t(segment)\n)\n")
        self.aboard.write_bytes(b"(kicad_pcb\n" + fp + b"\t(segment added)\n)\n")
        self.pins = {"before": sha(self.bboard.read_bytes()), "after": sha(self.aboard.read_bytes())}
        sources = {}
        for name in TOOL_NAMES:
            content = ("fixture " + name).encode()
            path = self.tools / name
            path.write_bytes(content)
            (self.out / name).write_bytes(content)
            sources[str(path)] = sha(content)
        self.generator_pin = sources[str(self.tools / "corridor_router_in3sv3.py")]
        self.write(self.out / "inputs.json", {"boards": {str(self.bboard): self.pins["before"],
                   str(self.aboard): self.pins["after"]}, "tools": sources,
                   "slot": "test-kicad (one)", "new_gpu_jobs": 0})
        for directory, board in ((self.before, self.bboard), (self.out, self.aboard)):
            target = directory / "copy"
            (target / "board.kicad_pcb").write_bytes(board.read_bytes())
            for name in ("board.kicad_pro", "board.kicad_dru", "sch.net"):
                (target / name).write_text("fixture " + name)
            (target / "fp-lib-table").write_text('(fp_lib_table (lib (uri "${KIPRJMOD}/Lib.pretty")))')
            lib = target / "Lib.pretty"
            lib.mkdir()
            (lib / "Fixture.kicad_mod").write_text("(footprint fixture)")
            self.update_manifest(directory, board)
        self.bp = {"refilled": True, "sha256": self.pins["before"], "nets": {"n": [["a"], ["b"]]},
                   "pad_island_joins": 1, "api_unconnected_count": 1, "tracks": 1, "vias": 0}
        self.ap = {**self.bp, "sha256": self.pins["after"], "nets": {"n": [["a", "b"]]},
                   "pad_island_joins": 0, "api_unconnected_count": 0, "tracks": 2}
        raw = {"ignored_checks": [], "included_severities": ["error", "warning", "exclusion"],
               "source": "board.kicad_pcb", "kicad_version": "10.0.4", "schematic_parity": [],
               "violations": [], "unconnected_items": []}
        self.write(self.before / "partitions.json", self.bp)
        self.write(self.out / "partitions.json", self.ap)
        self.write(self.before / "drc.json", raw)
        self.write(self.out / "drc.json", raw)
        self.write(self.before / "summary.json", self.summary(self.bp))
        self.write(self.out / "summary.json", self.summary(self.ap))
        for name in ("partitions.json", "summary.json", "sha256.txt"):
            (self.out / ("baseline-" + name)).write_bytes((self.before / name).read_bytes())

    @staticmethod
    def write(path, data):
        path.write_text(json.dumps(data), encoding="utf-8")

    @staticmethod
    def summary(partitions):
        return {"board_sha256": partitions["sha256"], "kicad": "10.0.4", "drc_flags": FLAGS,
                "drc_by_category": {}, "drc_errors": 0, "drc_warnings": 0,
                "drc_violations_total_excluding_unconnected": 0, "unconnected_items_in_drc_report_capped": 0,
                "unconnected_api_uncapped": partitions["api_unconnected_count"],
                "missing_pad_joins": partitions["pad_island_joins"], "schematic_parity_items": 0,
                "tracks": partitions["tracks"], "vias": partitions["vias"], "possibly_capped_categories": []}

    def update_manifest(self, directory, board):
        paths = [board] + [directory / "copy" / name for name in
                         ("board.kicad_pro", "board.kicad_dru", "sch.net", "fp-lib-table")]
        (directory / "sha256.txt").write_text("".join(sha(p.read_bytes()) + " *" + str(p) + "\n" for p in paths))

    def evaluate(self):
        return evaluate(self.out, self.before, self.bboard, self.aboard, pins=self.pins,
                        tool_root=self.tools, generator_pin=self.generator_pin, require_finished=False)


class FinalProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bridge-final-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name)

    def test_clean_fixture_passes_without_adoption(self):
        result = self.f.evaluate()
        self.assertEqual(result["verdict"], "PASS")
        self.assertFalse(result["adopted"])
        self.assertEqual(result["connectivity"]["completed"], 1)

    def test_raw_schematic_parity_rejected_even_when_summary_hides_it(self):
        path = self.f.out / "drc.json"
        raw = json.loads(path.read_text())
        raw["schematic_parity"] = [{"type": "missing_footprint"}]
        self.f.write(path, raw)
        with self.assertRaisesRegex(InvalidEvidence, "schematic parity"):
            self.f.evaluate()

    def test_changed_rules_rejected_even_with_accurate_candidate_manifest(self):
        (self.f.out / "copy/board.kicad_dru").write_text("changed rule")
        self.f.update_manifest(self.f.out, self.f.aboard)
        with self.assertRaisesRegex(InvalidEvidence, "project/rules/resources differ"):
            self.f.evaluate()

    def test_library_bytes_rejected(self):
        (self.f.out / "copy/Lib.pretty/Fixture.kicad_mod").write_text("changed library")
        with self.assertRaisesRegex(InvalidEvidence, "library inventories differ"):
            self.f.evaluate()

    def test_raw_error_cannot_be_hidden_by_zero_summary(self):
        path = self.f.out / "drc.json"
        raw = json.loads(path.read_text())
        raw["violations"] = [{"type": "clearance", "severity": "error"}]
        self.f.write(path, raw)
        with self.assertRaisesRegex(InvalidEvidence, "summary disagrees"):
            self.f.evaluate()

    def test_consistent_error_fails_gate(self):
        path = self.f.out / "drc.json"
        raw = json.loads(path.read_text())
        raw["violations"] = [{"type": "clearance", "severity": "error"}]
        self.f.write(path, raw)
        summary = self.f.summary(self.f.ap)
        summary.update(drc_by_category={"clearance [error]": 1}, drc_errors=1,
                       drc_violations_total_excluding_unconnected=1)
        self.f.write(self.f.out / "summary.json", summary)
        self.assertEqual(self.f.evaluate()["verdict"], "FAIL")

    def test_loss_hidden_by_api_gain_fails(self):
        bp = {**self.f.bp, "nets": {"n": [["a", "b"], ["c"], ["d"]]},
              "pad_island_joins": 2, "api_unconnected_count": 2}
        ap = {**self.f.ap, "nets": {"n": [["a"], ["b", "c", "d"]]},
              "pad_island_joins": 1, "api_unconnected_count": 1}
        self.f.write(self.f.before / "partitions.json", bp)
        self.f.write(self.f.out / "baseline-partitions.json", bp)
        self.f.write(self.f.before / "summary.json", self.f.summary(bp))
        self.f.write(self.f.out / "baseline-summary.json", self.f.summary(bp))
        self.f.write(self.f.out / "partitions.json", ap)
        self.f.write(self.f.out / "summary.json", self.f.summary(ap))
        result = self.f.evaluate()
        self.assertEqual((result["verdict"], result["connectivity"]["lost"]), ("FAIL", 1))

    def test_candidate_board_hash_rejected(self):
        self.f.aboard.write_bytes(b"changed board")
        with self.assertRaisesRegex(InvalidEvidence, "pinned after board changed"):
            self.f.evaluate()

    def test_changed_frozen_tool_rejected(self):
        (self.f.tools / "net_partitions.py").write_text("changed code")
        with self.assertRaisesRegex(InvalidEvidence, "tool differs"):
            self.f.evaluate()

    def test_stale_raw_receipt_rejected(self):
        os.utime(self.f.out / "drc.json", ns=(1, 1))
        with self.assertRaisesRegex(InvalidEvidence, "predates this run"):
            self.f.evaluate()

    def test_ignored_checks_rejected(self):
        raw = json.loads((self.f.out / "drc.json").read_text())
        raw["ignored_checks"] = ["clearance"]
        self.f.write(self.f.out / "drc.json", raw)
        with self.assertRaisesRegex(InvalidEvidence, "ignored"):
            self.f.evaluate()

    def test_changed_footprint_uuid_rejected_even_with_pins_updated(self):
        self.f.aboard.write_bytes(self.f.aboard.read_bytes().replace(b"fp-1", b"fp-2"))
        self.f.pins["after"] = sha(self.f.aboard.read_bytes())
        inputs = json.loads((self.f.out / "inputs.json").read_text())
        inputs["boards"][str(self.f.aboard)] = self.f.pins["after"]
        self.f.write(self.f.out / "inputs.json", inputs)
        with self.assertRaisesRegex(InvalidEvidence, "footprint/pad UUID"):
            self.f.evaluate()

    def test_active_native_runner_cannot_be_finalized(self):
        self.f.write(self.f.root / "bridge-status.json", {"phase": "NATIVE_MEASUREMENT_RUNNING", "adoption": False})
        with self.assertRaisesRegex(InvalidEvidence, "has not completed"):
            evaluate(self.f.out, self.f.before, self.f.bboard, self.f.aboard,
                     pins=self.f.pins, tool_root=self.f.tools, generator_pin=self.f.generator_pin)

    def test_measured_copy_must_match_manifest(self):
        (self.f.out / "copy/board.kicad_pro").write_text("changed after manifest")
        with self.assertRaisesRegex(InvalidEvidence, "measured file differs"):
            self.f.evaluate()

    def test_baseline_snapshot_cannot_be_substituted(self):
        original = json.loads((self.f.out / "baseline-summary.json").read_text())
        original["drc_warnings"] = 1
        self.f.write(self.f.out / "baseline-summary.json", original)
        with self.assertRaisesRegex(InvalidEvidence, "baseline summary snapshot"):
            self.f.evaluate()

    def test_missing_drc_severity_is_rejected(self):
        raw = json.loads((self.f.out / "drc.json").read_text())
        raw["included_severities"] = ["error"]
        self.f.write(self.f.out / "drc.json", raw)
        with self.assertRaisesRegex(InvalidEvidence, "all severities"):
            self.f.evaluate()

    def test_exhaustive_six_pad_partitions_preserve_every_previous_pair(self):
        def partitions(items):
            if not items:
                yield []
                return
            head, *tail = items
            for groups in partitions(tail):
                yield [[head]] + [g[:] for g in groups]
                for index in range(len(groups)):
                    changed = [g[:] for g in groups]
                    changed[index].append(head)
                    yield changed

        def receipt(groups):
            return {"refilled": True, "sha256": "a" * 64, "nets": {"n": groups},
                    "pad_island_joins": len(groups) - 1, "api_unconnected_count": len(groups) - 1}

        all_partitions = list(partitions(list("abcdef")))
        self.assertEqual(len(all_partitions), 203)
        for before in all_partitions:
            for after in all_partitions:
                lookup = {pad: index for index, group in enumerate(after) for pad in group}
                preserves = all(len({lookup[pad] for pad in group}) == 1 for group in before)
                self.assertEqual(compare(receipt(before), receipt(after))["verdict"] == "PASS", preserves)


if __name__ == "__main__":
    unittest.main()
