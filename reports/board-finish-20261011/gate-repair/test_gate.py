"""Host-only tests of the guard and the exact final shell commit boundary."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("staged_partition_guard", HERE / "partition_guard.py")
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)
PY = Path("C:/Python314/python.exe")
BASH = Path("C:/Program Files/Git/bin/bash.exe")
INTEGRATE = Path("Z:/pcb-runs/claude-finish/integrate")


def receipt(nets, api=None):
    missing = sum(len(groups) - 1 for groups in nets.values())
    return {"refilled": True, "sha256": "a" * 64, "nets": nets,
            "pad_island_joins": missing, "api_unconnected_count": missing if api is None else api}


def simple_before():
    return receipt({"lost": [["U1.1#0", "U2.1#0"]],
                    "gained": [["U3.1#0"], ["U4.1#0"], ["U5.1#0"]]})


def net_gain_with_loss():
    return receipt({"lost": [["U1.1#0"], ["U2.1#0"]],
                    "gained": [["U3.1#0", "U4.1#0", "U5.1#0"]]})


def clean_gain():
    return receipt({"lost": [["U1.1#0", "U2.1#0"]],
                    "gained": [["U3.1#0", "U4.1#0", "U5.1#0"]]})


def read_saved(label):
    return (INTEGRATE / "measure" / label / "partitions.json",
            INTEGRATE / "revs" / f"{label}.kicad_pcb")


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class ReceiptTests(unittest.TestCase):
    def test_net_gain_does_not_hide_loss(self):
        r = GUARD.compare(simple_before(), net_gain_with_loss())
        self.assertEqual((r["verdict"], r["completed"], r["lost"]), ("FAIL", 2, 1))

    def test_clean_gain_and_unchanged_pass(self):
        self.assertEqual(GUARD.compare(simple_before(), clean_gain())["verdict"], "PASS")
        self.assertEqual(GUARD.compare(simple_before(), simple_before())["verdict"], "PASS")

    def test_crossed_partition_preserves_count_but_loses_connection(self):
        b = receipt({"n": [["a", "b"], ["c", "d"]]})
        a = receipt({"n": [["a", "c"], ["b", "d"]]})
        r = GUARD.compare(b, a)
        self.assertEqual((r["completed"], r["lost"], r["verdict"]), (1, 1, "FAIL"))

    def test_changed_pad_identity_rejected(self):
        a = simple_before()
        a["nets"]["lost"][0][1] = "U99.1#0"
        with self.assertRaisesRegex(ValueError, "pad identities"):
            GUARD.compare(simple_before(), a)

    def test_changed_net_identity_rejected(self):
        a = simple_before()
        a["nets"]["renamed"] = a["nets"].pop("lost")
        with self.assertRaisesRegex(ValueError, "net sets"):
            GUARD.compare(simple_before(), a)

    def test_duplicate_identity_rejected(self):
        a = simple_before()
        a["nets"]["lost"][0].append("U1.1#0")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            GUARD.compare(simple_before(), a)

    def test_lying_api_below_pad_joins_rejected(self):
        a = simple_before()
        a["api_unconnected_count"] = 0
        with self.assertRaisesRegex(ValueError, "below computed"):
            GUARD.compare(simple_before(), a)

    def test_api_improvement_cannot_hide_loss(self):
        b = simple_before()
        b["api_unconnected_count"] = 20
        a = net_gain_with_loss()
        a["api_unconnected_count"] = 1
        r = GUARD.compare(b, a)
        self.assertTrue(r["api_not_increased"])
        self.assertEqual((r["verdict"], r["lost"]), ("FAIL", 1))

    def test_api_regression_with_clean_partitions_rejected(self):
        a = simple_before()
        a["api_unconnected_count"] += 1
        r = GUARD.compare(simple_before(), a)
        self.assertEqual(r["verdict"], "FAIL")
        self.assertFalse(r["api_not_increased"])

    def test_receipt_validation(self):
        for key, value in [("refilled", False), ("sha256", "bad"),
                           ("pad_island_joins", 99), ("api_unconnected_count", True),
                           ("api_unconnected_count", -1)]:
            with self.subTest(key=key, value=value):
                a = simple_before()
                a[key] = value
                with self.assertRaises((ValueError, TypeError)):
                    GUARD.compare(simple_before(), a)

    def test_actual_r05_to_r06_and_r06_to_r07(self):
        rows = {}
        for label in ["r05-stitch-plane-pads-1", "r06-stitch-plane-pads-2", "r07-ripup-signals-1"]:
            partition, board = read_saved(label)
            rows[label] = json.loads(partition.read_text(encoding="utf-8"))
            GUARD.check_board(rows[label], board)
        r06 = GUARD.compare(rows["r05-stitch-plane-pads-1"], rows["r06-stitch-plane-pads-2"])
        r07 = GUARD.compare(rows["r06-stitch-plane-pads-2"], rows["r07-ripup-signals-1"])
        self.assertEqual((r06["verdict"], r06["completed"], r06["lost"]), ("PASS", 4, 0))
        self.assertEqual((r07["verdict"], r07["completed"], r07["lost"]), ("FAIL", 29, 17))
        for name, result in [("saved-r05-r06-guard.json", r06), ("saved-r06-r07-guard.json", r07)]:
            write_json(HERE / name, result)


class ShellBoundaryTests(unittest.TestCase):
    def boundary(self, b, a, label="ripup-signals-test", repaired=False, stale=False, missing=False):
        """Run only the exact final block, with mutation commands recorded as mocks."""
        with tempfile.TemporaryDirectory(prefix="gate-host-", dir=HERE) as tmp:
            directory = Path(tmp)
            prev = directory / "prev"
            applied = directory / "measure"
            final = directory / "measure-repaired" if repaired else applied
            for d in {prev, applied, final, directory / "revs"}:
                d.mkdir(parents=True, exist_ok=True)
            before_board = directory / "before.kicad_pcb"
            applied_board = directory / "applied.kicad_pcb"
            final_board = directory / "repaired.kicad_pcb" if repaired else applied_board
            before_board.write_bytes(b"synthetic-before-board")
            applied_board.write_bytes(b"synthetic-applied-board")
            if repaired:
                final_board.write_bytes(b"synthetic-final-repaired-board")
            b, a = copy.deepcopy(b), copy.deepcopy(a)
            b["sha256"] = hashlib.sha256(before_board.read_bytes()).hexdigest()
            a["sha256"] = hashlib.sha256(final_board.read_bytes()).hexdigest()
            write_json(prev / "partitions.json", b)
            write_json(final / "partitions.json", a)
            write_json(applied / "report.json", {"gate": "PASS", "connections_lost": 0})
            if repaired:
                # Distinct applied receipt proves final OUTM is selected after cleanup.
                write_json(applied / "partitions.json", b)
            if stale:
                final_board.write_bytes(b"synthetic-changed-after-receipt")
            if missing:
                (final / "partitions.json").unlink()
            live = directory / "board.kicad_pcb"
            ledger = directory / "LEDGER-steps.md"
            revision = directory / "revs" / f"r99-{label}.kicad_pcb"
            sentinels = {live: b"live sentinel", ledger: b"old ledger sentinel", revision: b"old revision sentinel",
                         applied / "report.json": (applied / "report.json").read_bytes()}
            for path, data in sentinels.items():
                path.write_bytes(data)
            mutations = directory / "mutations.log"
            log = directory / "steps.log"
            variables = {"I": directory, "IW": directory, "T": HERE, "PY": PY,
                         "PREV_M": prev, "PREV_B": before_board, "OUTM": final,
                         "OUTB": final_board, "M": applied, "M2": directory / "measure-repaired",
                         "S": f"r99-{label}", "LABEL": label, "G": "PASS", "NET": "999",
                         "MUTATIONS": mutations, "LOG": log}
            prelude = "set -u\n" + "\n".join(f"{k}={shlex.quote(str(v).replace(chr(92), '/'))}" for k, v in variables.items()) + "\n"
            prelude += '''cygpath() { printf '%s\\n' "$2"; }
log() { printf '%s\\n' "$*" >> "$LOG"; }
cp() { printf 'cp %s\\n' "$*" >> "$MUTATIONS"; }
mv() { printf 'mv %s\\n' "$*" >> "$MUTATIONS"; }
rm() { printf 'rm %s\\n' "$*" >> "$MUTATIONS"; }
powershell.exe() { printf 'powershell %s\\n' "$*" >> "$MUTATIONS"; }
sha256sum() { printf 'host-sentinel-hash  %s\\n' "$1"; }
'''
            script = (HERE / "integrate_step.sh").read_text(encoding="utf-8")
            marker = 'if [ "$G" = "PASS" ]; then\n'
            self.assertEqual(script.count(marker), 1)
            boundary = script[script.index(marker):]
            path = directory / "boundary.sh"
            path.write_text(prelude + boundary, encoding="utf-8", newline="")
            run = subprocess.run([str(BASH), "--noprofile", "--norc", str(path)], capture_output=True, text=True, timeout=20)
            result_path = final / "connectivity_guard.json"
            result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
            calls = mutations.read_text() if mutations.exists() else ""
            for sentinel, data in sentinels.items():
                self.assertEqual(sentinel.read_bytes(), data)
            return run.returncode, result, calls, log.read_text() if log.exists() else "", run.stderr

    def test_every_label_rejects_loss_before_copy_or_rename(self):
        for label in ["ripup-signals", "power", "stitch-plane", "cleanup", "arbitrary-label"]:
            with self.subTest(label=label):
                rc, result, mutations, log, stderr = self.boundary(simple_before(), net_gain_with_loss(), label, True)
                self.assertEqual(rc, 1, stderr)
                self.assertEqual(result["lost"], 1)
                self.assertEqual(mutations, "")
                self.assertIn("REJECTED by connectivity guard", log)

    def test_clean_final_pass_uses_actual_boards_and_receipts(self):
        for repaired in [False, True]:
            with self.subTest(repaired=repaired):
                rc, result, mutations, log, stderr = self.boundary(simple_before(), clean_gain(), repaired=repaired)
                self.assertEqual(rc, 0, stderr)
                self.assertEqual((result["verdict"], result["completed"], result["lost"]), ("PASS", 2, 0))
                self.assertEqual(mutations.count("cp "), 2)
                self.assertEqual(mutations.count("mv "), 2 if repaired else 0)
                self.assertIn("COMMITTED", log)

    def test_invalid_receipts_and_stale_boards_fail_before_mutation(self):
        invalid = []
        a = simple_before(); a["nets"]["lost"][0][1] = "changed-pad"; invalid.append(a)
        a = simple_before(); a["nets"]["changed-net"] = a["nets"].pop("lost"); invalid.append(a)
        a = simple_before(); a["api_unconnected_count"] = 0; invalid.append(a)
        for a in invalid:
            with self.subTest(invalid=a):
                rc, result, mutations, _, stderr = self.boundary(simple_before(), a, repaired=True)
                self.assertEqual(rc, 1, stderr)
                self.assertEqual(result["verdict"], "INVALID")
                self.assertEqual(mutations, "")
        for option in ["stale", "missing"]:
            with self.subTest(option=option):
                rc, result, mutations, _, stderr = self.boundary(simple_before(), clean_gain(), **{option: True})
                self.assertEqual(rc, 1, stderr)
                self.assertEqual(result["verdict"], "INVALID")
                self.assertEqual(mutations, "")

    def test_api_regression_rejects_before_mutation(self):
        a = simple_before(); a["api_unconnected_count"] += 1
        rc, result, mutations, _, stderr = self.boundary(simple_before(), a)
        self.assertEqual(rc, 1, stderr)
        self.assertEqual((result["verdict"], result["lost"]), ("FAIL", 0))
        self.assertEqual(mutations, "")

    def test_existing_drc_flow_and_parent_guard_unchanged(self):
        original = (HERE / "integrate_step.original.sh").read_text(encoding="utf-8")
        staged = (HERE / "integrate_step.sh").read_text(encoding="utf-8")
        start = staged.index('  # Final board/receipt check applies')
        end = staged.index('  [ "$OUTM" = "$M" ]', start)
        self.assertEqual(staged[:start] + staged[end:], original)

    def test_full_script_shell_syntax(self):
        run = subprocess.run([str(BASH), "-n", str(HERE / "integrate_step.sh")], capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
