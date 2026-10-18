"""Validate actual browser-downloaded fixture bytes and reset preservation."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from controller_config.package_archive import read_archive

OUT = Path(__file__).resolve().parent / "browser-r01"
FIXTURE = Path(__file__).resolve().parent / "preview-r01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = json.loads((OUT / "observations.json").read_text())
    download = next(row for row in rows if row["check"] == "native_configuration_download_from_files")
    downloaded = Path(download["observed"]["downloadPath"])
    archive = read_archive(downloaded, expected_kind="config")
    with (OUT / "actual-browser-config.tar.zst").open("xb") as stream:
        stream.write(downloaded.read_bytes())
    before = json.loads((OUT / "reset-protected-before.json").read_text())
    after = {name: sha(FIXTURE / name) for name in before}
    current = {p.relative_to(FIXTURE).as_posix() for p in FIXTURE.rglob("*")
               if p.is_file() and "appliance" not in p.relative_to(FIXTURE).parts}
    state = json.loads((FIXTURE / "setup.json").read_text())
    budget = json.loads((FIXTURE / "budget.json").read_text())
    assert before == after and current == set(before)
    assert state["draft"]["machine_name"] == "Motion X12 navigation fixture"
    assert not budget["requests"]
    assert archive["integrity_verified"] and not archive["configuration_applied"]
    result = {"status": "PASS", "protected_fixture_before": before, "protected_fixture_after": after,
              "protected_files_unchanged": True, "saved_machine_name": state["draft"]["machine_name"],
              "paid_requests": 0, "download_sha256": archive["sha256"],
              "download_bytes": archive["archive_bytes"], "package_kind": archive["manifest"]["kind"],
              "package_integrity_verified": True, "package_configuration_applied": False,
              "package_authenticates_sender": False, "runner_sha256": sha(Path(__file__))}
    with (OUT / "artifact-controls.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "PASS", "protected_fixture_files": len(before),
                      "download_bytes": archive["archive_bytes"], "paid_requests": 0}))


if __name__ == "__main__":
    main()
