"""Freeze source hierarchy and a candidate for explicit parity without native jobs."""
import argparse
import hashlib
import json
import stat
from pathlib import Path

from host_parity import load_parser, read_board_text, compare, source_identity

HERE = Path(__file__).resolve().parent
EXTERNAL = Path("Z:/pcb-runs/claude-finish")
SOURCE = EXTERNAL / "final-s3"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def freeze(out, board, expected=None):
    out, board = Path(out).resolve(), Path(board).resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError("Output must be a new child of isolated parity-repair")
    inputs = list(SOURCE.glob("*.kicad_sch"))
    inputs += [SOURCE / name for name in ["sch.net", "motherboard.kicad_pro", "motherboard.kicad_dru", "fp-lib-table", "sym-lib-table"]]
    inputs += [EXTERNAL / "tools/quality/netlist_parity.py", EXTERNAL / "tools/integrate/pcbtext.py", board]
    hashes = {str(p): sha(p) for p in inputs}
    if expected and hashes[str(board)] != expected:
        raise ValueError("Candidate board does not match requested hash")
    integrated = sha(EXTERNAL / "integrate/sch.net")
    if sha(SOURCE / "sch.net") != integrated:
        raise ValueError("final-s3 and integration exports differ")
    s2 = EXTERNAL / "final-s2"
    differences = [p.name for p in SOURCE.glob("*.kicad_sch") if not(s2 / p.name).exists() or sha(p) != sha(s2 / p.name)]
    if differences:
        raise ValueError("Current hierarchy differs from exported final-s2 source: " + str(differences))
    out.mkdir(parents=True, exist_ok=False)
    project, tools = out / "source", out / "tools"
    project.mkdir(); tools.mkdir()
    snapshots = {}
    for p in inputs:
        target = out / "board.kicad_pcb" if p == board else tools / p.name if p.parent in [EXTERNAL / "tools/quality", EXTERNAL / "tools/integrate"] else project / p.name
        target.write_bytes(p.read_bytes())
        snapshots[target.relative_to(out).as_posix()] = sha(target)
        if snapshots[target.relative_to(out).as_posix()] != hashes[str(p)]:
            raise ValueError("Input changed while being copied: " + str(p))
        target.chmod(stat.S_IREAD)
    parser = load_parser(tools / "netlist_parity.py")
    nl = parser["read_netlist"](project / "sch.net")
    identities = source_identity(project, nl, parser)
    board_table = read_board_text(out / "board.kicad_pcb", parser, tools / "pcbtext.py")
    precheck = compare(nl, board_table, parser)
    write(out / "source-identity.json", identities)
    write(out / "host-board-table.json", board_table)
    write(out / "host-parity.json", precheck)
    after = {str(p): sha(p) for p in inputs}
    if hashes != after or sha(EXTERNAL / "integrate/sch.net") != integrated:
        raise ValueError("Original input changed during portable parity checks")
    result = {"scope": "immutable source/netlist/board snapshots and portable source inspection only",
              "board_source": str(board), "board_sha256": snapshots["board.kicad_pcb"],
              "netlist_sha256": snapshots["source/sch.net"], "source_hierarchy_files": len(identities["reachable_files"]),
              "export_metadata": nl["info"], "final_s2_final_s3_hierarchy_hash_equal": True,
              "source_and_integrate_export_hash_equal": True, "original_inputs_unchanged": hashes == after,
              "original_hashes": hashes, "snapshots": snapshots,
              "snapshot_read_only": True, "source_component_identity": identities["verdict"],
              "host_parity": precheck["verdict"], "native_confirmation": "PENDING",
              "fresh_source_export": "NOT RUN; export metadata points to final-s2 and current final-s3 hierarchy is byte-identical",
              "cli_schematic_parity": "NOT ESTABLISHED; API parity is a separate check and does not imply the CLI check executed"}
    write(out / "inputs.json", result)
    (out / "inputs.json").chmod(stat.S_IREAD)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expected-board-sha256")
    args = ap.parse_args()
    result = freeze(args.out, args.board, args.expected_board_sha256)
    print(json.dumps({k: v for k, v in result.items() if k not in ["original_hashes", "snapshots"]}))
    return 0 if result["host_parity"] == result["source_component_identity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
