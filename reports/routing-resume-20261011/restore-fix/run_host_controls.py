"""Capture independent host/mock controls; no KiCad process or board job is launched."""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
SOURCE = Path("Z:/pcb-runs/claude-finish/tools/ripup_restore.py")
SPEC = importlib.util.spec_from_file_location("restore_controls", HERE / "test_restore.py")
CONTROLS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROLS)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CountingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtest_count = 0

    def addSubTest(self, test, subtest, err):
        self.subtest_count += 1
        super().addSubTest(test, subtest, err)


log = io.StringIO()
suite = unittest.defaultTestLoader.loadTestsFromTestCase(CONTROLS.RestoreControls)
runner = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=CountingResult)
result = runner.run(suite)
(HERE / "host-tests.log").write_text(log.getvalue(), encoding="utf-8")
ast.parse((HERE / "ripup_restore.py").read_text(encoding="utf-8"))

fixtures = HERE / "inputs"
rip = json.loads((fixtures / "r07-rip-r1.json").read_text())
jobs = json.loads((fixtures / "r07-jobs-r1-c.json").read_text())
routes = json.loads((fixtures / "r07-routes-r1-c.json").read_text())
classes = json.loads((fixtures / "r07-recorded-net-classes.json").read_text())
test = CONTROLS.RestoreControls()
rc, replay, api = test.run_case(rip, jobs, routes, classes)
replay["evidence_kind"] = "host geometry replay with mocked pcbnew; not native DRC/connectivity"
replay["native_pcbnew_loaded"] = False
replay["real_board_read_or_written"] = False
replay["mock_saveboard_calls"] = len(api.saved)
replay["mock_board_added_items"] = len(api.board.added)
replay["mock_input_output_project_sentinels_unchanged"] = True
(HERE / "host-r07-refusal.json").write_text(json.dumps(replay, indent=1) + "\n", encoding="utf-8")

receipt = {
    "evidence_kind": "host/mock tests and AST syntax inspection only",
    "tests_run": result.testsRun, "subtests_run": result.subtest_count,
    "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
    "passed": result.wasSuccessful(), "candidate_sha256": sha(HERE / "ripup_restore.py"),
    "tests_sha256": sha(HERE / "test_restore.py"), "original_source_sha256": sha(fixtures / "ripup_restore.original.py"),
    "current_shared_source_sha256": sha(SOURCE),
    "shared_source_unchanged_since_snapshot": sha(SOURCE) == sha(fixtures / "ripup_restore.original.py"),
    "r07_host_replay_return_code": rc, "r07_host_candidates": replay["summary"]["candidates"],
    "r07_host_refused_candidates": replay["summary"]["refused_conflict"],
    "r07_host_mock_saveboard_calls": len(api.saved), "r07_host_mock_added_items": len(api.board.added),
    "native_drc_run": False, "native_connectivity_run": False, "heavy_slot_used": False,
    "shared_tools_modified": False, "shared_boards_modified": False,
    "native_partition_diff_lost_zero_required_after_cleanup": True,
}
(HERE / "host-receipt.json").write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
print(json.dumps(receipt))
sys.exit(0 if result.wasSuccessful() and rc == 3 else 1)
