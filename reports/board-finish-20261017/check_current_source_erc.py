"""Run native circuit ERC on the corrected complete portable hierarchy."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess
import psutil

H = Path(__file__).resolve().parent
N = H / "corrected-baseline-r1/native"
O = H / "corrected-baseline-r1/circuit-erc"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    O.mkdir(exist_ok=False)
    psutil.Process().cpu_affinity(list(range(16, 28)))
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    inputs = [p for p in N.iterdir() if p.is_file() and p.suffix in (".kicad_sch", ".kicad_pro", ".kicad_sym")]
    inputs.append(N / "sym-lib-table")
    pins = {str(p): sha(p) for p in inputs}
    args = ["C:/Program Files/KiCad/10.0/bin/kicad-cli.exe", "sch", "erc", "--format", "json", "--severity-all",
            "--output", str(O / "erc.json"), str(N / "board.kicad_sch")]
    with (O / "erc.log").open("w", encoding="utf-8") as log:
        run = subprocess.run(args, cwd=N, stdout=log, stderr=subprocess.STDOUT)
    assert (O / "erc.json").is_file()
    data = json.loads((O / "erc.json").read_bytes())
    rows = [r for sheet in data.get("sheets", []) for r in sheet.get("violations", [])]
    counts = collections.Counter((r.get("severity"), r.get("type")) for r in rows)
    assert all(sha(Path(p)) == h for p, h in pins.items())
    receipt = {"status": "NATIVE_CIRCUIT_ERC_EXECUTED_REVIEW_REQUIRED", "exit_code": run.returncode,
               "native_tool": args[0], "command": args, "sheet_count": len(data.get("sheets", [])),
               "severity_counts": dict(collections.Counter(r.get("severity") for r in rows)),
               "violation_categories": [{"severity": k[0], "type": k[1], "count": v} for k, v in sorted(counts.items())],
               "ERC_SHA256": sha(O / "erc.json"), "input_SHA256": pins,
               "inputs_unchanged": True, "physical_measurements": False, "manufacturing_ready": False}
    (O / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "exit_code", "sheet_count", "severity_counts", "violation_categories")}))


if __name__ == "__main__":
    main()
