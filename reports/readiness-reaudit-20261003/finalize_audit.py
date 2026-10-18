"""Check report links, retained source hashes and gate coverage; write audit-only receipts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = read("before-docs-manifest.json")
doc_paths = [ROOT / x["path"] for x in before["files"] if x["path"].endswith(".md")]
doc_paths += [ROOT / "docs/AI_SETUP_CONTRACT.md", *HERE.glob("*.md")]
broken = []
checked_links = 0
for p in doc_paths:
    for target in re.findall(r"\]\(([^\n)]+)\)", p.read_text(encoding="utf-8")):
        target = target.split("#", 1)[0].strip("<>")
        if not target or re.match(r"^[a-z]+://", target, re.I):
            continue
        checked_links += 1
        if not (p.parent / target).resolve().exists():
            broken.append({"document": str(p.relative_to(ROOT)), "target": target})

software = read("software-source-snapshot.json")
source_changes = [p for p, expected in software.items() if sha(ROOT / p) != expected]
hardware = read("hardware-release-readonly-evidence.json")
hardware_changes = [x["path"] for x in hardware["hash_comparisons"] if sha(ROOT / x["path"]) != x["actual_sha256"]]
probe = read("external-ai-parser-probe.json")
external_unchanged = sha(Path(probe["source_path"])) == probe["source_sha256"]

gates_text = (ROOT / "docs/CURRENT_ACCEPTANCE_GATES.md").read_text(encoding="utf-8")
gates = []
for line in gates_text.splitlines():
    if not re.match(r"\| G\d\d \|", line):
        continue
    cells = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        raise SystemExit(f"Malformed gate row: {line}")
    gates.append(dict(zip(("id", "requirement", "evidence_required", "current_state"), cells), accepted=False))
expected = [f"G{x:02}" for x in range(1, 27)]
if [x["id"] for x in gates] != expected:
    raise SystemExit("Gate coverage is not exactly G01 through G26")
if "\n\n| G26" in gates_text:
    raise SystemExit("G26 is detached from the table")

ai = (ROOT / "docs/AI_SETUP_CONTRACT.md").read_text(encoding="utf-8")
ai_ids = re.findall(r"^\| (AI\d\d) \|", ai, re.M)
if ai_ids != [f"AI{x:02}" for x in range(1, 20)]:
    raise SystemExit("AI acceptance coverage is not exactly AI01 through AI19")
if "excluded from the model tool schema" not in ai:
    raise SystemExit("Missing explicit commissioning authority boundary")

doc_changes = [{"path": x["path"], "before_sha256": x["sha256"], "after_sha256": sha(ROOT / x["path"]),
                "preserved_snapshot_matches": sha(ROOT / x["snapshot"]) == x["sha256"]} for x in before["files"]]
timestamp = datetime.now(timezone.utc).isoformat()
register = {"schema": "controller-readiness-audit-register/1", "checked_utc": timestamp,
            "scope": "Audit snapshot of declared requirements; not a live capability manifest or an implemented release enforcer",
            "source": "docs/CURRENT_ACCEPTANCE_GATES.md", "source_sha256": sha(ROOT / "docs/CURRENT_ACCEPTANCE_GATES.md"),
            "manufacturing_ready": False, "complete_machine_ready": False, "ai_setup_ready": False,
            "acceptance_status": "No full product gate accepted by this audit; partial evidence is described per gate", "gates": gates}
(HERE / "readiness-register.json").write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
result = {"checked_utc": timestamp, "scope": "Document/link/inventory and retained-byte checks only; no runtime/hardware qualification",
          "documents_checked": len(doc_paths), "local_links_checked": checked_links, "broken_links": broken,
          "software_hashes_checked": len(software), "software_changes": source_changes,
          "hardware_hash_comparisons": len(hardware["hash_comparisons"]), "hardware_changes": hardware_changes,
          "external_candidate_source_unchanged": external_unchanged, "product_gate_ids": expected, "ai_case_ids": ai_ids,
          "readiness_documents": doc_changes}
result["pass"] = not (broken or source_changes or hardware_changes) and external_unchanged and all(x["preserved_snapshot_matches"] for x in doc_changes)
result["audit_artifacts"] = [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p)}
                             for p in sorted(HERE.iterdir()) if p.is_file() and p.name != "final-review.json"]
(HERE / "final-review.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k not in ("audit_artifacts", "readiness_documents", "product_gate_ids", "ai_case_ids")}))
raise SystemExit(0 if result["pass"] else 1)
