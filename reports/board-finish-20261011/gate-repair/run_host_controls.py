"""Produce a reproducible host receipt; never execute the full integration script."""
import ast
import hashlib
import json
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

import test_gate

HERE = Path(__file__).resolve().parent
SHARED = Path("Z:/pcb-runs/claude-finish")
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Result(unittest.TextTestResult):
    subtest_executions = 0

    def addSubTest(self, test, subtest, err):
        self.subtest_executions += 1
        super().addSubTest(test, subtest, err)


def main():
    start = time.perf_counter()
    protected = [SHARED / "tools/integrate_step.sh",
                 ROOT / "reports/routing-resume-20261011/partition_guard.py",
                 SHARED / "integrate/LEDGER-steps.md"]
    for label in ["r05-stitch-plane-pads-1", "r06-stitch-plane-pads-2", "r07-ripup-signals-1"]:
        protected += list(test_gate.read_saved(label))
    before = {str(p): sha(p) for p in protected}
    for name in ["stage_gate.py", "partition_guard.py", "test_gate.py", "run_host_controls.py"]:
        ast.parse((HERE / name).read_text(encoding="utf-8"), filename=name)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_gate)
    with (HERE / "host-tests.log").open("w", encoding="utf-8") as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=Result).run(suite)
    after = {str(p): sha(p) for p in protected}
    saved = {}
    for filename in ["saved-r05-r06-guard.json", "saved-r06-r07-guard.json"]:
        row = json.loads((HERE / filename).read_text(encoding="utf-8"))
        saved[filename] = {k: v for k, v in row.items() if k != "per_net"}
    receipt = {
        "utc": datetime.now(timezone.utc).isoformat(), "scope": "host-only; no native KiCad, GPU, queue or installation",
        "tests_run": result.testsRun, "subtest_executions": result.subtest_executions,
        "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
        "verdict": "PASS" if result.wasSuccessful() and before == after else "FAIL",
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "python_ast": "PASS", "bash_syntax": "covered by test_full_script_shell_syntax",
        "protected_inputs_before": before, "protected_inputs_after": after,
        "protected_inputs_unchanged": before == after,
        "staged_hashes": {name: sha(HERE / name) for name in ["integrate_step.sh", "partition_guard.py", "staged.patch", "test_gate.py", "run_host_controls.py"]},
        "saved_native_receipt_replay": saved,
        "historical_r07_losses_repaired": False,
        "ledger_rewritten": False,
        "schematic_parity": "NOT ESTABLISHED: CLI DRC log reported failure fetching an annotated schematic netlist; an empty schematic_parity category is not an executed parity check. A separate source/native netlist comparison is required.",
    }
    (HERE / "host-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ["verdict", "tests_run", "subtest_executions", "failures", "errors", "skips", "elapsed_seconds", "protected_inputs_unchanged"]}))
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
