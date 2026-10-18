"""Read-only document/content review; refreshes only this review receipt."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
receipt_path = HERE / "planning-docs-receipt.json"
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
links = []
failures = []
for row in receipt["rows"]:
    archived = (ROOT / row["archive_path"]).read_bytes()
    row["archive_sha256"] = hashlib.sha256(archived).hexdigest()
    row["archive_identical"] = row["archive_sha256"] == row["before_sha256"]
    current = (ROOT / row["path"]).read_bytes()
    row["after_sha256"] = hashlib.sha256(current).hexdigest()
    text = current.decode("utf-8")
    if not row["archive_identical"]:
        failures.append("Changed original archive: " + row["path"])
    for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = raw.strip("<>").split("#", 1)[0]
        if not target or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
            continue
        path = ((ROOT / row["path"]).parent / unquote(target)).resolve()
        links.append({"source": row["path"], "target": raw, "exists": path.exists()})
motion = (ROOT / "docs/MOTION_EXPANSION_8_TO_12.md").read_text(encoding="utf-8")
before = (HERE / "planning-docs-before/docs/MOTION_EXPANSION_8_TO_12.md").read_text(encoding="utf-8-sig")
historical_body_unchanged = motion.split("---\n\n", 1)[1] == before
if not historical_body_unchanged:
    failures.append("Historical motion body changed")
active_docs = [row["path"] for row in receipt["rows"] if row["path"] != "docs/MOTION_EXPANSION_8_TO_12.md"]
stale = []
for p in active_docs:
    text = (ROOT / p).read_text(encoding="utf-8")
    for pattern in ["Architecture clarification still pending", "Pending architecture clarification", "Architecture conflict remains pending", "one-custom-PCB direction remains unresolved"]:
        if pattern in text:
            stale.append({"path": p, "phrase": pattern})
if stale:
    failures.append("Stale active architecture blockers")
receipt["editorial_finalised_at"] = datetime.now(timezone.utc).isoformat()
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
review = {"recorded_at": datetime.now(timezone.utc).isoformat(), "scope": "document preservation, path links and current-decision consistency; no circuit, runtime or physical tests", "documents": len(receipt["rows"]), "archives_identical": all(r["archive_identical"] for r in receipt["rows"]), "historical_motion_body_unchanged": historical_body_unchanged, "local_links_checked": len(links), "missing_local_links": [r for r in links if not r["exists"]], "stale_active_architecture_blockers": stale, "failures": failures}
(HERE / "planning-docs-review.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
print(json.dumps(review, indent=2))
raise SystemExit(bool(failures))
