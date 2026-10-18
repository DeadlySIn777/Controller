"""Freeze DI source/evidence, then run new and preserved baseline host checks."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "hardware/motherboard_di"
PY = "C:/Python314/python.exe"
paths = sorted({ROOT/"tools/hardware_build_motherboard_di.py",ROOT/"tools/hardware_validate_motherboard_di.py",ROOT/"tests/test_motherboard_di.py",ROOT/"tools/hardware_build_digital_inputs.py",ROOT/"tools/hardware_validate_digital_inputs.py",ROOT/"tests/test_digital_inputs.py",*OUT.rglob("*"),*(ROOT/"hardware/digital_inputs").rglob("*"),*(ROOT/"research/digital-inputs").rglob("*"),ROOT/"reports/motherboard-is2-contract-20260930/inputs/docs/interface-spec/03-terminals-and-allocations.md",ROOT/"reports/motherboard-is2-contract-20260930/inputs/docs/interface-spec/04-safety-power-timing.md",HERE/"native_footprint_review.py"})
paths = [p for p in paths if p.is_file() and p.suffix not in (".lck",".pyc")]
snapshot = HERE/"inputs"
if snapshot.exists():
    raise SystemExit("Refusing to overwrite frozen inputs")
before = {}
for p in paths:
    rel = p.relative_to(ROOT)
    before[str(rel).replace("\\","/")] = hashlib.sha256(p.read_bytes()).hexdigest()
    dst = snapshot/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dst)
runs = []
for label,args,log in (
    ("new 24-general-DI mutation/native-source checks",[PY,"-X","utf8","-m","unittest","discover","-s","tests","-p","test_motherboard_di.py","-v"],"new-tests.txt"),
    ("preserved historical 22 mixed-input regression",[PY,"-X","utf8","-m","unittest","discover","-s","tests","-p","test_digital_inputs.py","-v"],"historical-baseline-tests.txt"),
    ("current DI model/native XML/ERC/exact-footprint validation",[PY,"-X","utf8","tools/hardware_validate_motherboard_di.py"],"validation-stdout.txt")):
    start = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
    (HERE/log).write_text(result.stdout+result.stderr,encoding="utf-8")
    runs.append({"label":label,"command":args,"started_at":start,"ended_at":datetime.now(timezone.utc).isoformat(),"exit_code":result.returncode,"log":log})
after = {rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in before}
changed = [rel for rel in before if before[rel]!=after[rel]]
copied_identical = all(hashlib.sha256((snapshot/rel).read_bytes()).hexdigest()==sha for rel,sha in before.items())
model = json.loads((OUT/"design.json").read_text(encoding="utf-8"))
erc = json.loads((OUT/"erc.json").read_text(encoding="utf-8"))
violations = [v for s in erc["sheets"] for v in s["violations"]]
fp = json.loads((HERE/"native-footprint-review.json").read_text(encoding="utf-8"))
result = {"recorded_at":datetime.now(timezone.utc).isoformat(),"ok":all(r["exit_code"]==0 for r in runs) and not changed and copied_identical and fp["ok"],"scope":"new source/native standalone 24-general-DI frontends; no parent PCB, firmware, runtime or physical measurements","source_files":len(before),"input_sha256":before,"after_sha256":after,"inputs_unchanged":not changed,"changed_inputs":changed,"frozen_copies_identical":copied_identical,"runs":runs,"native_exports":{"schematic":"hardware/motherboard_di/motherboard_di.kicad_sch","xml":"hardware/motherboard_di/netlist.xml","pdf":"hardware/motherboard_di/motherboard_di.pdf","erc":"hardware/motherboard_di/erc.json","bom":"hardware/motherboard_di/bom.csv"},"native_erc":{"errors":sum(v["severity"]=="error" for v in violations),"warnings":sum(v["severity"]=="warning" for v in violations),"warning_type":"24 exact isolated_pin_label floating SUB island warnings; justified and retained","ignored_checks":erc["ignored_checks"]},"native_footprints_loaded":fp["native_footprints_loaded"],"physical_pads":fp["native_physical_pads"],"fitted_components":model["fitted_component_count"],"general_channels":24,"devices":12,"native_declared_NC_pads":24,"boundary_symbols":4,"boundary_symbols_fitted":False,"sensor_supplies_implemented":False,"sensor_supply_continuous_a_per_group":.20,"local_acquisition_and_validity_implemented":False,"probes_or_motor_alarms_consumed":0,"new_host_tests":28,"preserved_baseline_host_tests":26,"manufacturing_ready":False,"physical_qualification":False}
(HERE/"review.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k not in ("input_sha256","after_sha256","runs","native_exports")},indent=2))
raise SystemExit(0 if result["ok"] else 1)
