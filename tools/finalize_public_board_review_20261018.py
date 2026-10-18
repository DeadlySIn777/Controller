from pathlib import Path
import json, hashlib, shutil
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/board-finish-20261017"
DEST = ROOT / "tmp/github-controller-public-20261018"
extras = {
 "routing/corrected-R299-baseline-native-raw.dsn": "global-router-handoff-r1/corrected-R299-baseline-native-raw.dsn",
 "evidence/corrected-R299-baseline-export-ready.json": "global-router-handoff-r1/corrected-R299-baseline-export-ready.json",
 "review/REVIEW.md": "release-review/global-routability-review/REVIEW.md",
 "review/global-routability.png": "release-review/global-routability-review/global-routability.png",
 "review/measured-setup.json": "release-review/global-routability-review/measured-setup.json",
}
for name, source in extras.items():
 shutil.copyfile(REPORT / source, DEST / name)
p = DEST / "README.md"
t = p.read_text(encoding="utf-8")
t = t.replace("- [Raw six-layer Specctra DSN]", "- [Baseline six-layer Specctra DSN](routing/corrected-R299-baseline-native-raw.dsn), and [raw staged six-layer Specctra DSN]")
t = t.replace("- [Setup findings](SETUP_REVIEW.md)", "- [Measured whole-board review and figure](review/REVIEW.md), [setup findings](SETUP_REVIEW.md)")
p.write_text(t, encoding="utf-8")
manifest_path = DEST / "MANIFEST.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["files_excluding_this_manifest"] = {
 p.relative_to(DEST).as_posix(): {"bytes": p.stat().st_size, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}
 for p in sorted(DEST.rglob("*")) if p.is_file() and p != manifest_path and ".git" not in p.relative_to(DEST).parts
}
assert all(x["bytes"] < 90 * 1024 * 1024 for x in manifest["files_excluding_this_manifest"].values())
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(manifest["files_excluding_this_manifest"])+1, "total_bytes":sum(x["bytes"] for x in manifest["files_excluding_this_manifest"].values()), "manifest_SHA256":hashlib.sha256(manifest_path.read_bytes()).hexdigest()}))
