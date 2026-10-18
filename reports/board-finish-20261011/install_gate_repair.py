"""Install reviewed routing guard/restore fixes atomically while the queue is idle."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("Z:/pcb-runs/claude-finish")
TOOLS = ROOT / "tools"
BACKUP = TOOLS / "codex-backups/20261011-routing-guard"
EXPECTED = {"integrate_step.sh": "845eac8f45dd8b59508e865e5f05792fe2436639bb92d9f46350efd713ebf296",
            "ripup_restore.py": "330f250f2b4763fe62cf91d87f91fdfb0ce68e77407b23932d0eb578a7e2356f"}
STAGED = {
    "partition_guard.py": (HERE / "gate-repair/partition_guard.py", "40f8df302033a4dd2729acf260c75621a5d1636ebc5d18f24699ab8de4c4a61b"),
    "ripup_restore.py": (HERE.parent / "routing-resume-20261011/restore-fix/ripup_restore.py", "d5fc87ad28a73a7a06d072751abd8b36744a0e7bdaac3df8c73a4ebc0dfae0f9"),
    "integrate_step.sh": (HERE / "gate-repair/integrate_step.sh", "069211a6bf1ef062cf6e2b4562bbaf8b3ecebd7075d383db1bc50ad85971bb6f")}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if list((ROOT / "integrate/queue").glob("*.step")):
        raise RuntimeError("queue has pending work; do not install across a step")
    if BACKUP.exists() or (HERE / "gate-install-receipt.json").exists():
        raise RuntimeError("installation already attempted; inspect receipt")
    if (TOOLS / "partition_guard.py").exists():
        raise RuntimeError("unexpected existing shared guard; reconcile first")
    for name, expected in EXPECTED.items():
        if sha(TOOLS / name) != expected:
            raise RuntimeError("shared source changed: " + name)
    for name, (source, expected) in STAGED.items():
        if sha(source) != expected:
            raise RuntimeError("reviewed source changed: " + name)
        if name.endswith(".py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    saved = {name: sha(ROOT / "integrate" / name) for name in ("board.kicad_pcb", "steps.log", "LEDGER-steps.md")}
    BACKUP.mkdir(parents=True, exist_ok=False)
    for name, expected in EXPECTED.items():
        (BACKUP / name).write_bytes((TOOLS / name).read_bytes())
        if sha(BACKUP / name) != expected:
            raise RuntimeError("backup differs")
    receipt = {"phase": "INSTALLING", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "backup": str(BACKUP), "original_hashes": EXPECTED, "installed": {},
               "board_ledger_hashes_before": saved, "board_adopted": False,
               "limits": ["Existing r07 losses remain; historical receipts are not rewritten",
                          "Restorer preflight is host-tested; every prospective board still requires native gates",
                          "CLI schematic parity is unavailable in copied projects; explicit source/native parity required"]}
    destination = HERE / "gate-install-receipt.json"
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    # Install dependency first; the guarded commit script becomes visible last.
    for name, (source, expected) in STAGED.items():
        temporary = TOOLS / (name + ".codex-install-part")
        with temporary.open("xb") as handle:
            handle.write(source.read_bytes())
        if sha(temporary) != expected:
            raise RuntimeError("staged installation bytes differ")
        os.replace(temporary, TOOLS / name)
        if sha(TOOLS / name) != expected:
            raise RuntimeError("installed source differs")
        receipt["installed"][name] = expected
        destination.write_text(json.dumps(receipt, indent=2) + "\n")
    after = {name: sha(ROOT / "integrate" / name) for name in saved}
    if after != saved:
        raise RuntimeError("live board/ledger changed during tool installation; inspect before proceeding")
    receipt.update(phase="COMPLETE", board_ledger_hashes_after=after,
                   board_and_ledger_unchanged=True, queue_pending_steps=[])
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"phase": receipt["phase"], "installed": receipt["installed"],
                      "board_and_ledger_unchanged": True, "backup": str(BACKUP)}))


if __name__ == "__main__":
    main()
