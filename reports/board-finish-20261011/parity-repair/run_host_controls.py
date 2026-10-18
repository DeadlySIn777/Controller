"""Record host controls and immutable-input checks without native execution."""
import ast
import contextlib
import json
from pathlib import Path
import time
import unittest

from prepare_parity import sha, write
import test_parity

HERE = Path(__file__).resolve().parent
FROZEN = HERE / "root106"


class Result(unittest.TextTestResult):
    subtest_executions = 0

    def addSubTest(self, test, subtest, err):
        self.subtest_executions += 1
        super().addSubTest(test, subtest, err)


def main():
    started = time.perf_counter()
    inputs = json.loads((FROZEN / "inputs.json").read_text())
    originals = {p: sha(p) for p in inputs["original_hashes"]}
    originals["Z:/pcb-runs/claude-finish/integrate/sch.net"] = sha("Z:/pcb-runs/claude-finish/integrate/sch.net")
    frozen = {p: sha(FROZEN / p) for p in inputs["snapshots"]}
    files = ["host_parity.py", "prepare_parity.py", "run_native_parity.py", "project_clone.py", "native_bound_entry.py",
             "fresh_export.py", "test_parity.py", "run_host_controls.py"]
    hashes = {p: sha(HERE / p) for p in files}
    for p in files:
        ast.parse((HERE / p).read_text(), filename=p)
    with (HERE / "host-tests.log").open("w", encoding="utf-8") as log, contextlib.redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromModule(test_parity))
    after = {p: sha(p) for p in originals}
    frozen_after = {p: sha(FROZEN / p) for p in inputs["snapshots"]}
    unchanged = originals == after and frozen == frozen_after
    receipt = {"verdict": "PASS" if result.wasSuccessful() and unchanged else "FAIL",
               "tests_run": result.testsRun, "subtest_executions": result.subtest_executions,
               "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
               "elapsed_seconds": round(time.perf_counter() - started, 3),
               "python_syntax": "PASS", "source_and_candidate_unchanged": unchanged,
               "snapshots_unchanged": frozen == frozen_after, "tool_hashes": hashes,
               "original_hashes_before": originals, "original_hashes_after": after,
               "native_jobs_started": 0, "new_gpu_jobs": 0, "adopted": False,
               "native_gate_controls": "Historical API report is adapted only as a synthetic schema fixture; it is not ROOT106 native evidence",
               "existing_native_api_receipts": {n: json.loads((HERE / n / "native-receipt.json").read_text())["verdict"] for n in ["root106", "c03"]},
               "existing_fresh_source_export": json.loads((FROZEN / "source-export/receipt.json").read_text())["verdict"],
               "cli_schematic_parity": "NOT ESTABLISHED by these API/export checks"}
    write(HERE / "host-receipt.json", receipt)
    print(json.dumps({k: receipt[k] for k in ["verdict", "tests_run", "subtest_executions", "failures", "errors", "skips", "elapsed_seconds", "source_and_candidate_unchanged"]}))
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
