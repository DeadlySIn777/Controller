"""Record reproducible partial-circuit evidence without fabricating a board release."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


TEST_PATTERNS=["test_hardware*.py","test_tx_six.py","test_rx_abz.py"]
TEST_COMMAND="python -m unittest discover -s tests -p <pattern> -v for each of "+", ".join(TEST_PATTERNS)
BLOCKS={"hardware/tx_bank":"erc.json","hardware/tx_six":"validation.json","hardware/rx_abz":"validation.json"}


def erc_violations(block):
    erc=json.loads((ROOT/block/"erc.json").read_text(encoding="utf-8"))
    return erc["kicad_version"],[v for sheet in erc["sheets"] for v in sheet["violations"]]


def main():
    log=[];failed=0
    for pattern in TEST_PATTERNS:
        result=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p",pattern,"-v"],
                              cwd=ROOT,text=True,capture_output=True)
        log.append(f"### {pattern}\n"+result.stdout+result.stderr)
        failed|=result.returncode
    (ROOT/"hardware/test-results.txt").write_text("\n".join(log),encoding="utf-8")
    if failed:raise SystemExit(failed)
    ledger=subprocess.run([sys.executable,"tools/hardware_validate.py"],cwd=ROOT,text=True,capture_output=True)
    log.append("### tools/hardware_validate.py\n"+ledger.stdout+ledger.stderr)
    (ROOT/"hardware/test-results.txt").write_text("\n".join(log),encoding="utf-8")
    if ledger.returncode:raise SystemExit("Ledger validator failed against the current electrical-design.json")
    validation=json.loads((ROOT/"hardware/validation-report.json").read_text(encoding="utf-8"))
    ledger_sha=hashlib.sha256((ROOT/"hardware/electrical-design.json").read_bytes()).hexdigest()
    if validation.get("design_sha256")!=ledger_sha:raise SystemExit("validation-report.json does not describe the current electrical-design.json")
    if not validation["consistency_pass"]:raise SystemExit("Ledger review evidence is not clean")
    kicad_versions=set();violations=[]
    for block,gate in BLOCKS.items():
        version,block_violations=erc_violations(block)
        kicad_versions.add(version);violations+=block_violations
        if gate=="validation.json":
            record=json.loads((ROOT/block/gate).read_text(encoding="utf-8"))
            if not record["consistency_pass"] or record["erc_violations"]!=len(block_violations):
                raise SystemExit(f"{block} validation record is not clean or disagrees with its ERC export")
            for rel,digest in record["source_sha256"].items():
                if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=digest:
                    raise SystemExit(f"{block} source hash for {rel} is stale; rerun its validator")
    if violations:raise SystemExit("Schematic ERC evidence is not clean")
    if len(kicad_versions)!=1:raise SystemExit(f"Mixed KiCad versions in ERC exports: {sorted(kicad_versions)}")
    artifacts=[]
    paths=["hardware/electrical-design.json","hardware/bom-snapshot.csv","hardware/channel-map.csv",
           "hardware/power-budget.csv","hardware/terminal-map.csv","hardware/validation-report.json",
           "hardware/test-results.txt"]
    for block in BLOCKS:
        paths+=[str(path.relative_to(ROOT)).replace("\\","/") for path in sorted((ROOT/block).iterdir()) if path.is_file()]
    paths+=["docs/ELECTRICAL_DESIGN.md","reports/SIX_JOINT_TRANSMITTER.md","reports/ENCODER_RECEIVERS.md",
            "tools/hardware_build_design.py","tools/hardware_build_tx_schematic.py","tools/hardware_build_tx_six.py",
            "tools/hardware_build_rx_abz.py","tools/hardware_validate.py","tools/hardware_validate_tx_six.py",
            "tools/hardware_validate_rx_abz.py","tests/test_hardware_validation.py","tests/test_tx_six.py",
            "tests/test_rx_abz.py"]
    for rel in paths:
        raw=(ROOT/rel).read_bytes()
        artifacts.append({"path":rel,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
    package={
        "schema_version":1,"recorded_utc":datetime.now(timezone.utc).isoformat(),
        "status":"partial_design_review_only","manufacturing_ready":False,
        "scope":"Retained two-joint differential TX review circuit (hardware/tx_bank), the six-joint three-bank transmitter block (hardware/tx_six), the two-ABZ receiver block (hardware/rx_abz) and the full-core proposed electrical/resource ledger",
        "kicad_version":kicad_versions.pop(),"erc_violations":len(violations),
        "schematic_blocks":list(BLOCKS),
        "erc_limit":"KiCad defaults recorded in each block erc.json; no project-specific exclusions. External supply flags declare power at the review boundary connectors. FPGA, permission latch, power tree, line protection and the remaining controller circuitry are absent; block ERC is not full-board ERC.",
        "ledger":validation["counts"],"validation_release_blocker_count":len(validation["release_blockers"]),
        "test_command":TEST_COMMAND,
        "artifacts":artifacts,
        "release_items":[
            {"item":"complete editable controller schematic","state":"blocked","reason":"Only the transmitter and encoder-receiver blocks exist; no combined controller schematic"},
            {"item":"reviewed package/footprint/pin/bank map","state":"blocked","reason":"FPGA/SBC/ESP and remaining parts not assigned"},
            {"item":"complete exact BOM and DNP/approved alternates","state":"blocked","reason":"Support bundles and MPNs unresolved"},
            {"item":"PCB layout, stackup and mechanical drawings","state":"blocked","reason":"No controller PCB designed"},
            {"item":"Gerber copper/mask/silk/paste/outline and drill files","state":"blocked","reason":"Must export from real approved layout; no placeholders"},
            {"item":"SMT centroid/CPL XY rotation side in mm","state":"blocked","reason":"Must export from real approved layout; no placeholders"},
            {"item":"assembly polarity/orientation drawings","state":"blocked","reason":"Full board missing"},
            {"item":"full schematic ERC and board DRC reviewed","state":"blocked","reason":"Partial-circuit ERC is not full-board evidence"},
            {"item":"target FPGA fit/timing/clock/power proof","state":"blocked","reason":"Exact T20 implementation unqualified"},
            {"item":"revisioned FPGA/ESP/Linux programming bundle","state":"blocked","reason":"All target images/recovery process must match actual board"},
            {"item":"factory fixture/procedure/pass limits","state":"blocked","reason":"Physical test plan requires complete circuitry"},
            {"item":"PCBWay sourcing/assembly/program/test quote","state":"blocked","reason":"No supplier submission or actual quote"},
            {"item":"physical power/SI/thermal/fault/EMC evidence","state":"blocked","reason":"No prototype or physical measurements"}
        ],
        "canonical_manufacturing_manifest":"manufacturing/release-manifest.json",
        "no_supplier_contact":True,"no_order":True,"no_physical_connection":True
    }
    (ROOT/"hardware/review-manifest.json").write_text(json.dumps(package,indent=2)+"\n",encoding="utf-8")
    print(f"Recorded {len(artifacts)} hashed review artifacts; manufacturing remains blocked")


if __name__=="__main__":main()
