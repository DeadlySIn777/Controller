"""Regression tests for the research generators and the grblHAL evidence record.

Covers tools/build_feature_catalog.py, tools/build_hardware_cost_data.py and
tools/build_compute_display_matrix.py (their read-only --check modes and failure
detection), research/patches/record_firmware_sources.py, and the .gitignore /
.gitattributes rules that keep cited evidence tracked and byte-exact.

Evidence class: source inspection and host arithmetic only; nothing here is hardware
evidence. Every mutation happens in a temporary copy; the repository is never written.
The tests read only the research-data files these generators own, never hardware/ or
the in-progress power/connected-hardware records.
"""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FEATURE_NOTE = "research/user-notes/2026-09-28-feature-platform.txt"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def run_tool(script, *args):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True)


class TempTree(unittest.TestCase):
    def make_tree(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name)

    @staticmethod
    def copy(tree, *rels):
        for rel in rels:
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, tree / rel)


# ---- feature catalogue -------------------------------------------------------------

class FeatureCatalogTests(TempTree):
    def catalog_tree(self):
        tree = self.make_tree()
        self.copy(tree, "tools/build_feature_catalog.py", "research/feature-roadmap.json",
                  "research/expanded-hardware-target.json", "docs/FEATURE_CATALOG.md")
        shutil.copytree(REPO / "research/user-notes", tree / "research/user-notes")
        return tree

    @staticmethod
    def run_catalog(tree, *args):
        return run_tool(tree / "tools/build_feature_catalog.py", *args)

    def test_check_passes_on_repository_without_warnings(self):
        result = run_tool(REPO / "tools/build_feature_catalog.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("read-only check passed", result.stdout)
        self.assertNotIn("WARNING", result.stderr)

    def test_hashes_every_archived_note_and_retains_original_six(self):
        notes = sorted((REPO / "research/user-notes").glob("*.txt"))
        required_originals = {"2026-09-28-esp-industrial-direction.txt", "2026-09-28-feature-platform.txt",
                              "2026-09-28-integration-priority.txt", "2026-09-28-modbus-expansion.txt",
                              "2026-09-28-plasma-upgrades.txt", "2026-09-28-repairability-memory.txt"}
        self.assertTrue(required_originals.issubset({p.name for p in notes}))
        self.assertEqual({s["path"]: s["sha256"] for s in read_json("research/feature-roadmap.json")["sources"]},
                         {p.relative_to(REPO).as_posix(): sha(p) for p in notes})

    def test_characterization_and_virtual_bench_requests_have_exact_sha_provenance(self):
        sources = {s["path"]: s["sha256"] for s in read_json("research/feature-roadmap.json")["sources"]}
        for name in ("2026-10-01-pre-hardware-characterization.txt", "2026-10-01-virtual-machine-bench.txt"):
            path = "research/user-notes/" + name
            self.assertIn(path, sources)
            self.assertEqual(sources[path], sha(REPO / path))

    def test_package_a_features_are_not_backlog(self):
        features = {f["number"]: f for f in read_json("research/feature-roadmap.json")["features"]}
        for number in (193, 195, 200):
            self.assertEqual(features[number]["delivery_focus"], "configuration_foundation")
        # Package A members already in a demonstration keep that more specific focus.
        self.assertEqual(features[1]["delivery_focus"], "first_core_demonstration")
        self.assertEqual(features[59]["delivery_focus"], "first_plasma_module_demonstration")

    def test_expanded_target_cites_repository_note_with_matching_hash(self):
        ref = read_json("research/expanded-hardware-target.json")["source_notes"]
        path = REPO / ref["path"]
        self.assertFalse(Path(ref["path"]).is_absolute())
        self.assertEqual(ref["path"], FEATURE_NOTE)
        self.assertEqual(ref["sha256"], sha(path))
        data = path.read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        # The architecture notes run from line 372 to the final line 750, which has no
        # trailing newline (so `wc -l` prints 749).
        self.assertEqual((len(lines), data.count(b"\n"), data.endswith(b"\n")), (750, 749, False))
        self.assertEqual((ref["line_start"], ref["line_end"]), (372, 750))
        self.assertTrue(lines[371].startswith("For your product"))

    def test_expanded_target_document_cites_the_recorded_range(self):
        text = (REPO / "docs/EXPANDED_HARDWARE_TARGET.md").read_text(encoding="utf-8")
        self.assertIn(f"lines 372\u2013750 of `{FEATURE_NOTE}`", text)
        self.assertNotIn("372\u2013749", text)

    def test_check_detects_edited_note(self):
        tree = self.catalog_tree()
        note = tree / "research/user-notes/2026-09-28-integration-priority.txt"
        self.assertTrue(note.is_file())
        note.write_bytes(note.read_bytes() + b"edit\n")
        result = self.run_catalog(tree, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("feature-roadmap.json: stale", result.stderr)

    def test_check_rejects_bad_expanded_target_reference(self):
        cases = [
            ("path", "C:/Users/someone/.codex/attachments/x/Pasted text.txt", "not a repository archived note"),
            ("sha256", "0" * 64, "sha256 mismatch"),
            ("line_end", 751, "outside 1-750"),
        ]
        for key, value, message in cases:
            with self.subTest(key=key):
                tree = self.catalog_tree()
                path = tree / "research/expanded-hardware-target.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                data["source_notes"][key] = value
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                result = self.run_catalog(tree, "--check")
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_records_an_added_note_instead_of_crashing(self):
        tree = self.catalog_tree()
        before = {p.relative_to(tree).as_posix(): sha(p) for p in (tree / "research/user-notes").glob("*.txt")}
        (tree / "research/user-notes/2026-10-01-new-note.txt").write_bytes(b"new note\n")
        result = self.run_catalog(tree, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("feature-roadmap.json: stale", result.stderr)
        self.assertNotIn("AssertionError", result.stderr)
        self.assertEqual(self.run_catalog(tree).returncode, 0)
        data = json.loads((tree / "research/feature-roadmap.json").read_text(encoding="utf-8"))
        expected = dict(before, **{"research/user-notes/2026-10-01-new-note.txt": sha(tree / "research/user-notes/2026-10-01-new-note.txt")})
        self.assertEqual({s["path"]: s["sha256"] for s in data["sources"]}, expected)
        self.assertEqual(self.run_catalog(tree, "--check").returncode, 0)

    def test_warns_when_document_cites_a_different_line_range(self):
        tree = self.catalog_tree()
        doc = tree / "docs/EXPANDED_HARDWARE_TARGET.md"
        doc.write_bytes(f"It translates lines 372\u2013749 of `{FEATURE_NOTE}` into work.\n".encode())
        result = self.run_catalog(tree, "--check")
        self.assertIn("WARNING docs/EXPANDED_HARDWARE_TARGET.md: cites lines 372-749", result.stderr)
        doc.write_bytes(f"It translates lines 372\u2013750 of `{FEATURE_NOTE}` into work.\n".encode())
        self.assertNotIn("WARNING", self.run_catalog(tree, "--check").stderr)

    def test_writes_lf(self):
        tree = self.catalog_tree()
        self.assertEqual(self.run_catalog(tree).returncode, 0)
        for rel in ["research/feature-roadmap.json", "docs/FEATURE_CATALOG.md"]:
            self.assertNotIn(b"\r\n", (tree / rel).read_bytes(), rel)


# ---- hardware cost model -----------------------------------------------------------

COST_INPUTS = ["research/motion-io-cost-sources.json", "research/compute-cost-sources.json",
               "research/display-cost-sources.json"]
COST_OUTPUTS = ["research/hardware-cost-model.json", "research/manufacturing-cost-sources.json"]


class HardwareCostTests(TempTree):
    def test_check_passes_and_mains_cord_source_is_unrecorded(self):
        result = run_tool(REPO / "tools/build_hardware_cost_data.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = {l["id"]: l for l in read_json("research/hardware-cost-model.json")["lines"]}
        cord = lines["mains_cord"]
        self.assertEqual((cord["url"], cord["price_source"]), ("", "unrecorded"))
        self.assertEqual(cord["prices"][0], 5.89)  # value kept, flagged rather than silently removed
        self.assertIn("not recorded", cord["notes"])
        # No priced line may borrow another part's listing.
        owners = {}
        for line in lines.values():
            if line["url"]:
                self.assertEqual(owners.setdefault(line["url"], line["mpn"]), line["mpn"], line["id"])
            if any(p is not None for p in line["prices"]) and not line["url"]:
                self.assertEqual(line["price_source"], "unrecorded", line["id"])
        manufacturing = read_json("research/manufacturing-cost-sources.json")
        self.assertEqual(manufacturing["sources"][0]["url"], lines["main_psu"]["url"])

    def test_check_detects_stale_output(self):
        tree = self.make_tree()
        self.copy(tree, "tools/build_hardware_cost_data.py", *COST_INPUTS, *COST_OUTPUTS)
        self.assertEqual(run_tool(tree / "tools/build_hardware_cost_data.py", "--check").returncode, 0)
        model = tree / "research/hardware-cost-model.json"
        model.write_bytes(model.read_bytes().replace(b'"unrecorded"', b'"url_recorded"'))
        result = run_tool(tree / "tools/build_hardware_cost_data.py", "--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hardware-cost-model.json", result.stderr)


# ---- compute/display matrix --------------------------------------------------------

class ComputeDisplayMatrixTests(unittest.TestCase):
    def test_check_is_read_only_and_passes(self):
        output = REPO / "research/compute-display-matrix.json"
        before = sha(output)
        result = run_tool(REPO / "tools/build_compute_display_matrix.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["action"], "read-only check passed")
        self.assertEqual(summary["case_count"], 144)
        self.assertEqual(summary["complete_costs"], 0)
        self.assertEqual(sha(output), before)


# ---- firmware evidence record ------------------------------------------------------

TARGETS = ["grblHAL_sim", "grblHAL_validator"]


def make_build(root, exit_codes=None, log_exit=None):
    exit_codes = exit_codes or {}
    record = {"recorded_utc": "t", "distro": "Distro X", "compiler": "gcc (X) 1.0",
              "machine": "x86_64", "targets": {}}
    for target in TARGETS:
        code = exit_codes.get(target, 0)
        log = root / f"{target}-build.log"
        log.write_bytes(f"COMMAND: gcc\nEXIT: {log_exit if log_exit is not None else code}\n".encode())
        binary = root / target
        if code == 0:
            binary.write_bytes(b"ELF" + target.encode())
        record["targets"][target] = {"exit_code": code, "log": log.name, "log_sha256": sha(log),
                                     "binary": target, "binary_sha256": sha(binary) if code == 0 else None,
                                     "warnings": ["modbus.c:266:20: warning: x"]}
    (root / "build-record.json").write_text(json.dumps(record))
    return record


class FirmwareRecordTests(TempTree):
    @classmethod
    def setUpClass(cls):
        cls.record = load("research/patches/record_firmware_sources.py", "record_firmware_sources")

    def test_derives_success_and_environment(self):
        root = self.make_tree()
        make_build(root)
        build, env, problems = self.record.derive_build(root)
        self.assertEqual(problems, [])
        self.assertEqual((build["grblHAL_sim"], build["grblHAL_validator"]), ("success", "success"))
        self.assertEqual((env["compiler"], env["distro"]), ("gcc (X) 1.0", "Distro X"))
        self.assertEqual(build["compiler_warnings"], ["modbus.c:266:20: warning: x"])

    def test_reports_failed_build(self):
        root = self.make_tree()
        make_build(root, exit_codes={"grblHAL_validator": 1})
        build, _, problems = self.record.derive_build(root)
        self.assertEqual(build["grblHAL_validator"], "failed_exit_1")
        self.assertTrue(problems)

    def test_rejects_missing_build_record(self):
        build, env, problems = self.record.derive_build(self.make_tree())
        self.assertEqual(build["grblHAL_sim"], "not_recorded")
        self.assertIsNone(env["compiler"])
        self.assertTrue(problems)

    def test_rejects_rebuilt_binary_and_inconsistent_log(self):
        root = self.make_tree()
        make_build(root)
        (root / "grblHAL_sim").write_bytes(b"different")
        build, _, problems = self.record.derive_build(root)
        self.assertEqual(build["grblHAL_sim"], "binary_missing_or_changed_since_build")
        self.assertTrue(problems)
        make_build(root, log_exit=2)
        build, _, _ = self.record.derive_build(root)
        self.assertIn(build["grblHAL_sim"], ("log_missing_or_changed_since_build",
                                              "log_exit_status_missing_or_inconsistent"))

    def test_refuses_audit_of_other_binaries(self):
        root = self.make_tree()
        make_build(root)
        build, _, _ = self.record.derive_build(root)
        (root / "audit").mkdir()
        (root / "audit/results.json").write_text("[]")
        (root / "audit/binaries.json").write_text(json.dumps({t: "0" * 64 for t in TARGETS}))
        _, identity, problems = self.record.derive_audit(root, build)
        self.assertIs(identity["results_match_recorded_binaries"], False)
        self.assertTrue(problems)
        (root / "audit/binaries.json").write_text(json.dumps({t: build[t + "_binary_sha256"] for t in TARGETS}))
        _, identity, problems = self.record.derive_audit(root, build)
        self.assertIs(identity["results_match_recorded_binaries"], True)
        self.assertEqual(problems, [])

    def test_removes_stale_evidence_copy(self):
        root = self.make_tree()
        build_dir, evidence_dir = root / "build-local", root / "research/evidence/grblhal"
        build_dir.mkdir()
        make_build(build_dir)
        (build_dir / "audit").mkdir()
        (build_dir / "audit/results.json").write_text("[]")
        (build_dir / "audit/binaries.json").write_text("{}")
        kept, problems = self.record.copy_evidence(build_dir, evidence_dir, root)
        self.assertEqual(problems, [])
        self.assertEqual(len(kept), 5)
        # A later run without an audit identity or build log must not keep the old copies.
        (build_dir / "audit/binaries.json").unlink()
        (build_dir / "grblHAL_sim-build.log").unlink()
        kept, problems = self.record.copy_evidence(build_dir, evidence_dir, root)
        self.assertFalse((evidence_dir / "binaries.json").exists())
        self.assertFalse((evidence_dir / "grblHAL_sim-build.log").exists())
        self.assertNotIn("research/evidence/grblhal/binaries.json", kept)
        self.assertEqual(len(kept), 3)
        self.assertTrue(any("removed stale evidence copy research/evidence/grblhal/binaries.json" in p
                            for p in problems))
        self.assertEqual(len(problems), 2)

    def test_checked_in_firmware_record_is_derived(self):
        data = read_json("research/firmware-sources.json")
        self.assertEqual(data["record_problems"], [])
        self.assertIs(data["audit_identity"]["results_match_recorded_binaries"], True)
        evidence = REPO / "research/evidence/grblhal"
        record = json.loads((evidence / "build-record.json").read_text(encoding="utf-8"))
        self.assertEqual(data["environment"]["compiler"], record["compiler"])
        self.assertEqual(data["environment"]["distro"], record["distro"])
        for rel, digest in data["evidence_copies_sha256"].items():
            self.assertEqual(sha(REPO / rel), digest, rel)
        for target in TARGETS:
            log = (evidence / f"{target}-build.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(log[-1], "EXIT: 0")
            self.assertEqual(data["build"][target], "success")


# ---- git hygiene -------------------------------------------------------------------

@unittest.skipUnless(shutil.which("git") and git("rev-parse", "--git-dir").returncode == 0,
                     "git working tree not available")
class GitHygieneTests(unittest.TestCase):
    EVIDENCE_LOGS = [
        "reports/offline-tests-2026-09-28-0105.log",
        "reports/root-verification-20260928/source/gateware/synthesis/results/synthesis.log",
        "cnc1/evidence/spidev/tests.log",
        "gateware/synthesis/postmap/results/tests.log",
        "gateware/validation/simulation.log",
        "firmware/esp32_service/evidence/default-build.log",
        "research/evidence/grblhal/grblHAL_sim-build.log",
        "research/before-audit-fixes-2026-09-28/grblhal-build-local/grblHAL_sim-build.log",
        # Cited by reports/LINUXCNC_INTEGRATION.md for the task-loop excursion figures.
        "controller_backend/evidence/linuxcnc-raw.log",
    ]
    BUILD_OUTPUTS = [
        "scratch.log", "outputs/x.xlsx", "gateware/build/simulation.log",
        "firmware/esp32_service/.build/default-build.log", "research/vendor-src/x",
        "controller_backend/.runtime/x", "controller_backend/profiles/sim/position.txt",
        "controller_backend/profiles/sim/linuxcnc.var", "controller_backend/__pycache__/x.pyc",
    ]

    def test_evidence_logs_are_not_ignored(self):
        for path in self.EVIDENCE_LOGS:
            with self.subTest(path=path):
                self.assertTrue((REPO / path).is_file())
                self.assertEqual(git("check-ignore", "-q", "--no-index", path).returncode, 1)

    def test_build_output_stays_ignored(self):
        for path in self.BUILD_OUTPUTS:
            with self.subTest(path=path):
                self.assertEqual(git("check-ignore", "-q", "--no-index", path).returncode, 0)

    def test_gitignore_files_have_no_duplicate_entries(self):
        for rel in [".gitignore", "controller_backend/.gitignore"]:
            with self.subTest(file=rel):
                lines = [l for l in (REPO / rel).read_text(encoding="utf-8").splitlines()
                         if l.strip() and not l.startswith("#")]
                self.assertEqual(len(lines), len(set(lines)))

    def test_line_ending_attributes(self):
        cases = [
            ("gateware/synthesis/synth.ys", "set", "lf"),
            # gateware/.gitattributes makes all of gateware/ LF.
            ("gateware/synthesis/results/synthesis.log", "set", "lf"),
            ("gateware/synthesis/manifest.json", "set", "lf"),
            ("gateware/tests/vectors.hex", "set", "lf"),
            # Archived evidence stays byte-exact both inside and outside gateware/.
            # eol=lf is inherited from gateware/.gitattributes, but git ignores eol when
            # text is unset, so these archived bytes are not converted (gitattributes(5)).
            ("gateware/synthesis/before-audit-fixes-2026-09-28/manifest.json", "unset", "lf"),
            ("reports/root-verification-20260928/source/gateware/synthesis/manifest.json", "unset", "unspecified"),
            ("research/before-audit-fixes-2026-09-28/firmware-sources.json", "unset", "unspecified"),
            ("tools/build_compute_display_matrix.py", "unset", "unspecified"),
            (FEATURE_NOTE, "unset", "unspecified"),
            ("cnc1/src/cnc1.c", "set", "lf"),
        ]
        for path, text, eol in cases:
            with self.subTest(path=path):
                out = git("check-attr", "text", "eol", "--", path).stdout.decode()
                self.assertIn(f"{path}: text: {text}", out)
                self.assertIn(f"{path}: eol: {eol}", out)


if __name__ == "__main__":
    unittest.main()
