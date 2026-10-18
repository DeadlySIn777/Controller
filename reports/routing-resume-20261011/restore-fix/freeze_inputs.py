"""Freeze saved r07 JSON evidence; read-only on the live shared routing tree."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = Path("Z:/pcb-runs/claude-finish")
WORK = ROOT / "integrate/work/r07-ripup-signals-1/rd/ripup-work"
INPUTS = HERE / "inputs"
INPUTS.mkdir(exist_ok=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


manifest = []
for filename, source in [
    ("r07-rip-r1.json", WORK / "rip-r1.json"),
    ("r07-jobs-r1-c.json", WORK / "jobs-r1-c.json"),
    ("r07-routes-r1-c.json", WORK / "routes-r1-c.json"),
    ("r07-restore-r1.json", WORK / "restore-r1.json"),
    ("r07-partition_diff.json", ROOT / "integrate/measure/r07-ripup-signals-1/partition_diff.json"),
]:
    data = source.read_bytes()
    destination = INPUTS / filename
    destination.write_bytes(data)
    manifest.append({"source": str(source), "snapshot": str(destination), "bytes": len(data),
                     "sha256": digest(data), "source_after_read_sha256": digest(source.read_bytes())})

geom_source = WORK / "geom-r1-c.json"
geom_bytes = geom_source.read_bytes()
geometry = json.loads(geom_bytes)
classes = {}
for pad in geometry["pads"]:
    if pad.get("net") and pad["net"] not in classes:
        classes[pad["net"]] = pad["cls"].split(",")[0]
class_path = INPUTS / "r07-recorded-net-classes.json"
class_path.write_text(json.dumps(classes, indent=1) + "\n", encoding="utf-8")
manifest.append({"source": str(geom_source), "snapshot": str(class_path),
                 "source_sha256": digest(geom_bytes), "snapshot_sha256": digest(class_path.read_bytes()),
                 "transformation": "first nonempty pad net -> first comma-separated recorded cls",
                 "native_board_loaded": False})

original = INPUTS / "ripup_restore.original.py"
shared_source = ROOT / "tools/ripup_restore.py"
source_hash = digest(shared_source.read_bytes())
source = {"source": str(shared_source), "snapshot": str(original),
          "original_sha256": digest(original.read_bytes()), "shared_sha256_at_receipt": source_hash}
source["unchanged_since_copy"] = source["original_sha256"] == source_hash

original_restore = json.loads((INPUTS / "r07-restore-r1.json").read_text())
diff = json.loads((INPUTS / "r07-partition_diff.json").read_text())
decisions = {d["net"]: d for d in original_restore["decisions"]}
losses = [{"net": net, "lost": delta["lost"], "restore_refused": decisions.get(net, {}).get("restored") is False,
           "first_recorded_conflict": decisions.get(net, {}).get("conflict")}
          for net, delta in diff["per_net"].items() if delta["lost"]]
attribution = {"evidence": "inspection of saved source JSON; no new native PCB measurement",
               "completed_joins": diff["completed"], "lost_joins": diff["lost"],
               "every_lost_net_was_a_refused_restore_candidate": all(row["restore_refused"] for row in losses),
               "original_restore_summary": original_restore["summary"], "losses": losses}
(HERE / "r07-attribution.json").write_text(json.dumps(attribution, indent=1) + "\n", encoding="utf-8")
(HERE / "source-manifest.json").write_text(json.dumps({"source_tool": source, "inputs": manifest}, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"shared_source_unchanged": source["unchanged_since_copy"], "saved_r07_losses": diff["lost"],
                  "all_loss_nets_refused_restore": attribution["every_lost_net_was_a_refused_restore_candidate"]}))
