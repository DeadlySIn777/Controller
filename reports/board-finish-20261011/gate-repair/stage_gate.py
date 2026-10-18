"""Stage the integration guard without touching shared sources or the queue."""
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHARED = Path("Z:/pcb-runs/claude-finish/tools/integrate_step.sh")
GUARD = ROOT / "reports/routing-resume-20261011/partition_guard.py"
EXPECTED_SCRIPT = "845eac8f45dd8b59508e865e5f05792fe2436639bb92d9f46350efd713ebf296"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    original = SHARED.read_bytes()
    if sha(original) != EXPECTED_SCRIPT:
        raise SystemExit("Shared script changed; review before staging against a new baseline")
    guard_original = GUARD.read_bytes()
    (HERE / "integrate_step.original.sh").write_bytes(original)
    (HERE / "partition_guard.original.py").write_bytes(guard_original)
    source = original.decode("utf-8")
    anchor = 'if [ "$G" = "PASS" ]; then\n  [ "$OUTM" = "$M" ]'
    insertion = '''if [ "$G" = "PASS" ]; then
  # Final board/receipt check applies to every label, after any targeted cleanup.
  if ! $PY "$T/partition_guard.py" "$(cygpath -m "$PREV_M/partitions.json")" \\
      "$(cygpath -m "$OUTM/partitions.json")" --before-board "$(cygpath -m "$PREV_B")" \\
      --after-board "$(cygpath -m "$OUTB")" --out "$(cygpath -m "$OUTM/connectivity_guard.json")" \\
      > "$OUTM/connectivity_guard.out" 2>&1; then
    log "$S REJECTED by connectivity guard (board unchanged; $OUTM/connectivity_guard.json)"
    exit 1
  fi
  [ "$OUTM" = "$M" ]'''
    if source.count(anchor) != 1:
        raise SystemExit("Final commit boundary is not unique")
    patched = source.replace(anchor, insertion)
    (HERE / "integrate_step.sh").write_text(patched, encoding="utf-8", newline="")
    guard = guard_original.decode("utf-8")
    count_anchor = '    return nets\n'
    if guard.count(count_anchor) != 1:
        raise SystemExit("Guard receipt validation boundary is not unique")
    guard = guard.replace(count_anchor,
        '    if receipt["api_unconnected_count"] < missing:\n'
        '        raise ValueError("API unconnected count is below computed pad-island joins")\n'
        '    return nets\n')
    (HERE / "partition_guard.py").write_text(guard, encoding="utf-8", newline="")
    diffs = []
    for old, new, name in [(source, patched, "integrate_step.sh"),
                           (guard_original.decode("utf-8"), guard, "partition_guard.py")]:
        diffs.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                       fromfile=f"original/{name}", tofile=f"staged/{name}"))
    (HERE / "staged.patch").write_text("".join(diffs), encoding="utf-8", newline="")
    receipt = {"scope": "isolated staging only; no shared installation or native jobs",
               "original_shared_script": str(SHARED), "original_script_sha256": sha(original),
               "guard_source": str(GUARD), "original_guard_sha256": sha(guard_original),
               "staged_script_sha256": sha((HERE / "integrate_step.sh").read_bytes()),
               "staged_guard_sha256": sha((HERE / "partition_guard.py").read_bytes()),
               "shared_script_unchanged": SHARED.read_bytes() == original,
               "guard_source_unchanged": GUARD.read_bytes() == guard_original,
               "ledger_modified": False}
    (HERE / "stage-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
