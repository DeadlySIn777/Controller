"""Compare protected files with the start-of-work inventory; never edit them."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[1]
before = json.loads((REPORT / "protected-source-before.json").read_text(encoding="utf-8-sig"))
changed = [name for name, expected in before.items()
           if not (ROOT / name).is_file() or
           hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected]
receipt = {"finished_utc": datetime.now(timezone.utc).isoformat(),
           "scope": "Original hardware, firmware, gateware and CNC1 source bytes only; not a routing or physical qualification check",
           "checked_files": len(before), "changed_or_missing": changed}
(REPORT / "protected-source-verification.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))
raise SystemExit(bool(changed))
