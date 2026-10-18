from pathlib import Path
import subprocess, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "tmp/github-controller-public-20261018"
OUT = ROOT / "reports/board-finish-20261017/public-github-handoff-r1"
OUT.mkdir(exist_ok=True)
def curl(url):
 return subprocess.run(["curl.exe", "--fail", "--silent", "--show-error", "--max-time", "60", url], check=True, capture_output=True).stdout
repo = json.loads(curl("https://api.github.com/repos/DeadlySIn777/Controller"))
assert not repo["private"]
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SNAPSHOT, text=True).strip()
branch = repo["default_branch"]
remote_manifest = curl(f"https://raw.githubusercontent.com/DeadlySIn777/Controller/{commit}/MANIFEST.json")
local_manifest = (SNAPSHOT / "MANIFEST.json").read_bytes()
assert remote_manifest == local_manifest
tree = json.loads(curl(f"https://api.github.com/repos/DeadlySIn777/Controller/git/trees/{commit}?recursive=1"))
assert not tree["truncated"]
remote_blobs = {x["path"]:x["sha"] for x in tree["tree"] if x["type"] == "blob"}
local = subprocess.check_output(["git", "ls-tree", "-r", "HEAD"], cwd=SNAPSHOT, text=True)
local_blobs = {}
for line in local.splitlines():
 mode_type_hash, path = line.split("\t", 1)
 local_blobs[path] = mode_type_hash.split()[2]
assert local_blobs == remote_blobs
for path, entry in json.loads(local_manifest)["files_excluding_this_manifest"].items():
 data = (SNAPSHOT / path).read_bytes()
 assert len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["SHA256"]
receipt = {"status":"PUBLIC_UPLOAD_VERIFIED", "repository":repo["html_url"], "public":True,
 "commit":commit, "default_branch":branch, "files":len(remote_blobs),
 "unauthenticated_repository_and_manifest_access":True, "remote_manifest_byte_identical":True,
 "all_remote_git_blobs_match_local_commit":True, "all_manifest_file_hashes_pass":True,
 "manifest_SHA256":hashlib.sha256(local_manifest).hexdigest(), "board_complete":False,
 "manufacturing_ready":False, "remaining_verified_joins":1172,
 "independent_native_board_load_review":"power-review/public-package-independent-review-r3/combined-summary.json"}
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
