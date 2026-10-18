"""Freeze scoped source evidence. This never writes the board, project or bundle."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = {
    "board": ROOT / "reports/board-finish-20261011/recovery-composite/c05/c05-fag-e1-rollback-dfm.kicad_pcb",
    "project": ROOT / "reports/board-finish-20261011/measure/c05-shared/copy/board.kicad_pro",
    "rules": ROOT / "reports/board-finish-20261011/measure/c05-shared/copy/board.kicad_dru",
    "native_matched_pad_table": ROOT / "reports/board-finish-20261011/parity-repair/c05/host-board-table.json",
    "historical_controlled_nets": Path("Z:/pcb-runs/impedance/controlled-nets.json"),
    "historical_citations": Path("Z:/pcb-runs/impedance/work/citations.json"),
    "calculator": Path("Z:/pcb-runs/impedance/impedance_calc.py"),
    "calculator_tests": Path("Z:/pcb-runs/impedance/tests/test_impedance_calc.py"),
    "historical_classifier": Path("Z:/pcb-runs/impedance/tools/classify.py"),
    "current_one_method_geometry": Path("Z:/pcb-runs/claude-finish/impedance-1oz.json"),
    "current_pairs": Path("Z:/pcb-runs/claude-finish/tools/pairs.json"),
    "operator_decisions": Path("Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md"),
    "cm5_datasheet": ROOT / "reports/board-completion-20260930/compute-bay-pin-audit/sources/cm5-datasheet.txt",
    "iso7761_datasheet": ROOT / "reports/motherboard-analog-20260930/sources/iso7761.txt",
    "isow1432_datasheet": ROOT / "reports/motherboard-comms-20260930/sources/isow1432.txt",
}
PINS = {
    "board": "95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d",
    "project": "82bbd7114aa2e6f2d200252cfde3f69d2a1f3905212e6b14437e62ff742d780b",
    "rules": "159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4",
}

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    if (HERE / "inputs.json").exists():
        raise ValueError("already frozen; use the existing immutable inputs")
    out = HERE / "inputs"
    out.mkdir(parents=True, exist_ok=True)
    records = {}
    for role, source in SOURCES.items():
        before = source.read_bytes()
        digest = sha(before)
        if role in PINS and digest != PINS[role]:
            raise ValueError(f"wrong immutable {role}")
        # The real board remains an exact read-set input; only its short setup is copied.
        frozen = None if role == "board" else out / (role + source.suffix)
        if frozen:
            frozen.write_bytes(before)
        if sha(source.read_bytes()) != digest:
            raise ValueError(f"input changed while freezing: {role}")
        records[role] = {"path": source.resolve().as_posix(), "sha256": digest,
                         "bytes": len(before), "frozen": frozen.resolve().as_posix() if frozen else None}
    (HERE / "inputs.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": "PASS_SOURCE_SNAPSHOT", "roles": len(records), "board_sha256": records["board"]["sha256"]}))

if __name__ == "__main__": main()
