"""Read-only source/evidence checks; writes only new files beside this script."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    result = {}
    for name in ("cnc1", "gateware", "firmware", "controller_lab", "controller_backend", "controller_config", "tests", "tools", "schemas", "config"):
        for path in (ROOT / name).rglob("*"):
            if not path.is_file() or any(part in {"__pycache__", ".build", "build", ".pytest_cache", "evidence", "validation", "results"} or part.startswith("before-") for part in path.relative_to(ROOT).parts):
                continue
            if path.suffix.lower() in {".pyc", ".o", ".so", ".dll", ".exe", ".bin", ".elf", ".vcd"}:
                continue
            result[path.relative_to(ROOT).as_posix()] = sha(path)
    return result


def manifest_map(path, base, field="files"):
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = []
    for relative, expected in data[field].items():
        target = base / relative
        actual = sha(target) if target.is_file() else None
        entries.append({"path": str(target), "expected": expected, "actual": actual, "matches": actual == expected})
    return {"manifest": str(path), "manifest_sha256": sha(path), "count": len(entries), "all_match": all(row["matches"] for row in entries), "differences": [row for row in entries if not row["matches"]]}


def references(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    def walk(value):
        if isinstance(value, dict):
            candidate = next((value.get(k) for k in ("path", "report", "receipt", "artifact", "evidence") if isinstance(value.get(k), str)), None)
            expected = value.get("sha256")
            if candidate and isinstance(expected, str) and len(expected) == 64:
                target = Path(candidate)
                if not target.is_absolute():
                    target = ROOT / target
                actual = sha(target) if target.is_file() else None
                rows.append({"path": str(target), "expected": expected, "actual": actual, "matches": actual == expected})
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)
    return {"manifest": str(path), "manifest_sha256": sha(path), "count": len(rows), "all_match": all(row["matches"] for row in rows), "differences": [row for row in rows if not row["matches"]]}


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    before = snapshot()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    commands = [
        ("cnc1-manifest", ["cnc1/tools/record_evidence.py", "--check"]),
        ("cnc1-spidev-manifest", ["cnc1/tools/record_spidev_evidence.py", "--check"]),
        ("baseline-rtl-manifest", ["gateware/tools/record_evidence.py", "--check"]),
        ("baseline-synthesis-manifest", ["gateware/synthesis/record_results.py", "--check"]),
        ("baseline-postmap-manifest", ["gateware/synthesis/postmap/record_results.py", "--check"]),
        ("cnc3-readonly-source-tests", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_cnc3_rtl.py", "-v"]),
        ("iol1-readonly-source-tests", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_motherboard_iol1_readonly.py", "-v"]),
    ]
    runs = []
    for name, args in commands:
        command = [sys.executable, "-B", *args]
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        log = OUT / ("software-" + name + ".log")
        log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
        runs.append({"name": name, "command": command, "exit_code": proc.returncode, "log": log.name, "log_sha256": sha(log)})
        print(name, proc.returncode, flush=True)
    bundles = []
    for relative in (
        "reports/cnc3-is2-profile-20261002/profile-candidate-r02",
        "reports/cnc3-iol1-integrated-records-20261002/prefix-motion-candidate-r01",
        "reports/cnc3-iol1-integrated-records-20261002/prefix-record-candidate-r01",
    ):
        base = ROOT / relative
        bundles.append(manifest_map(base / "bundle-manifest.json", base))
    manifests = []
    for relative in (
        "reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-handoff-r01/receipt.json",
        "reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-peer-addendum-r01/receipt.json",
        "reports/cnc3-is2-profile-20261002/profile-handoff-r02/receipt.json",
    ):
        manifests.append(references(ROOT / relative))
    esp = manifest_map(ROOT / "firmware/esp32_service/evidence/manifest.json", ROOT, "source_sha256")
    after = snapshot()
    changes = {k: {"before": before.get(k), "after": after.get(k)} for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)}
    result = {"started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "scope": "source inspection, host source-negative tests, retained manifest/hash verification only", "physical_interfaces_opened": False, "new_target_build_or_HDL_simulation_or_synthesis": False, "new_vendor_fit_or_physical_measurement": False, "source_snapshot_count": len(before), "source_hashes_unchanged": not changes, "source_changes": changes, "runs": runs, "bundle_integrity": bundles, "referenced_evidence_integrity": manifests, "esp_source_integrity": esp}
    (OUT / "software-source-snapshot.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    (OUT / "software-checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
