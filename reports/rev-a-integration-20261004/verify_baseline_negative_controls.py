"""Executable preservation controls; mutate copied manifests, never sources."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = HERE / "baseline.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(name, baseline, output):
    log = HERE / (name + ".log")
    command = [sys.executable, str(ROOT / "tools/check_rev_a_baseline.py"),
               "--verify", str(baseline), "--out", str(output)]
    with log.open("x", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=60)
    return {"name": name, "command": command, "exit_code": result.returncode,
            "log": str(log.relative_to(ROOT)), "log_sha256": sha(log)}


def main():
    original = BASELINE.read_bytes()
    baseline = json.loads(original)
    checks = []
    for group in ("feature_sha256", "protected_source_sha256", "external_archive_sha256",
                  "existing_settings_sha256", "regression_test_sha256"):
        changed = json.loads(original)
        name = next(iter(changed[group]))
        changed[group][name] = "0" * 64
        mutation = HERE / ("negative-" + group + "-baseline.json")
        with mutation.open("x", encoding="utf-8") as handle:
            json.dump(changed, handle)
        receipt = HERE / ("negative-" + group + "-receipt.json")
        check = execute("negative-" + group, mutation, receipt)
        observed = json.loads(receipt.read_text())
        check.update(mutated_expected_path=name, passed=check["exit_code"] == 2
                     and observed["status"] == "FAIL"
                     and set(observed["groups"][group]["differences"]) == {name}
                     and all(not value["differences"] for key, value in observed["groups"].items()
                             if key != group))
        checks.append(check)
    check = execute("negative-existing-output", BASELINE, BASELINE)
    check["passed"] = check["exit_code"] != 0 and BASELINE.read_bytes() == original
    checks.append(check)
    outside = ROOT / "rev-a-qualification-should-not-exist.json"
    if outside.exists():
        raise RuntimeError("Negative-control destination already exists")
    check = execute("negative-output-outside-reports", BASELINE, outside)
    check["passed"] = check["exit_code"] != 0 and not outside.exists()
    checks.append(check)
    summary = {"finished_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "Copied-manifest hash mutations and exclusive/path-limited evidence writes",
               "checks": checks, "checks_run": len(checks),
               "all_passed": all(c["passed"] for c in checks),
               "original_baseline_unchanged": BASELINE.read_bytes() == original,
               "baseline_sha256": sha(BASELINE), "tool_sha256": sha(ROOT / "tools/check_rev_a_baseline.py"),
               "source_mutations": 0, "physical_measurements": 0, "api_calls": 0}
    with (HERE / "baseline-negative-controls.json").open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "checks"}))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
