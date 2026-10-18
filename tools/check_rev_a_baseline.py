"""Hash-only Rev A feature/source preservation; never a qualification result.

Capture once, then verify into a new receipt. This tool does not connect to a
device, edit settings, execute a provider or confer machine/release authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec")
SKIP = {"__pycache__", ".git", "node_modules", "build", "dist", "obj_dir",
        "build-default", "build-uart", "build-uart-check", "vendor-src"}
SOURCE_SUFFIXES = {".py", ".c", ".cpp", ".h", ".hpp", ".v", ".sv", ".json",
                   ".ini", ".hal", ".xml", ".csv", ".kicad_sch", ".kicad_mod",
                   ".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_sym", ".toml",
                   ".yaml", ".yml", ".cfg", ".md", ".txt", ".ld", ".s", ".ys"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths(directory: Path):
    return sorted(p for p in directory.rglob("*") if p.is_file()
                  and not any(part in SKIP for part in p.relative_to(directory).parts)
                  and (p.suffix.lower() in SOURCE_SUFFIXES or p.name in {
                      "CMakeLists.txt", "Kconfig.projbuild", "sdkconfig", "SHA256SUMS",
                      "fp-lib-table", "sym-lib-table"}))


def feature_files():
    return sorted(set((ROOT / "controller_config").rglob("*.py")) | {
        p for p in (ROOT / "controller_config/web").glob("*") if p.is_file()})


def snapshot():
    features = {p.relative_to(ROOT).as_posix(): digest(p) for p in feature_files()}
    protected = {p.relative_to(ROOT).as_posix(): digest(p)
                 for scope in ("hardware", "gateware", "firmware", "config", "schemas")
                 for p in paths(ROOT / scope)}
    external = {p.relative_to(EXTERNAL).as_posix(): digest(p)
                for scope in ("cnc3", "spec") for p in paths(EXTERNAL / scope)}
    spec = EXTERNAL / "docs/CONTROLLER_INTERFACE_SPEC.md"
    if spec.is_file():
        external[spec.relative_to(EXTERNAL).as_posix()] = digest(spec)
    retained = json.loads((ROOT / "reports/deep-upgrade-20261004/source-and-settings-before.json").read_text())
    settings = {name: digest(ROOT / name) for name in retained if name.startswith("reports/")}
    software_receipt = json.loads((ROOT / "reports/deep-upgrade-20261004/host-tests.json").read_text())
    regression = {name: digest(ROOT / name) for name in software_receipt["source_sha256"]
                  if name.startswith("tests/")}
    return {"feature_sha256": features, "protected_source_sha256": protected,
            "external_archive_sha256": external, "existing_settings_sha256": settings,
            "regression_test_sha256": regression}


def write_new(path: Path, value):
    path = path.resolve()
    if not path.is_relative_to((ROOT / "reports").resolve()):
        raise ValueError("Preservation receipts must be in this workspace's reports directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def compare(expected, actual):
    changes = {}
    for group in actual:
        before, after = expected[group], actual[group]
        changed = {name: {"expected": before.get(name), "actual": after.get(name)}
                   for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)}
        changes[group] = {"checked": len(after), "differences": changed}
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--verify", type=Path, metavar="BASELINE")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    actual = snapshot()
    value = {"schema": 1, "utc": datetime.now(timezone.utc).isoformat(),
             "scope": "Source/settings byte preservation only; not execution or qualification",
             "user_facing_features_frozen": True, "physical_measurements": 0,
             "commissioning_promoted": False, "manufacturing_readiness_promoted": False,
             "paid_api_calls": 0, "device_connections": 0}
    if args.capture:
        value.update(actual)
        value["status"] = "BASELINE_CAPTURED"
    else:
        baseline = json.loads(args.verify.read_text(encoding="utf-8"))
        if baseline.get("schema") != 1 or any(not baseline.get(group) for group in actual):
            raise ValueError("Missing or invalid baseline source groups")
        changes = compare(baseline, actual)
        value.update(baseline=str(args.verify.resolve()), baseline_sha256=digest(args.verify),
                     groups=changes, status="FAIL" if any(g["differences"] for g in changes.values()) else "PASS")
    write_new(args.out, value)
    print(json.dumps({k: v for k, v in value.items() if k not in actual and k != "groups"}))
    if "groups" in value:
        print(json.dumps({k: {"checked": v["checked"], "changed": len(v["differences"])}
                          for k, v in value["groups"].items()}))
    return 2 if value["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
