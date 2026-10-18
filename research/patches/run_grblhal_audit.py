"""Run small, bounded tests against the compiled upstream host executables."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parents[1] / "vendor-src/grblhal-simulator/build-local"
cases = {
    "linear_mm": ("G21 G90\nG1 X10 Y5 Z-1 F600\n", 0),
    "arc_ij": ("G21 G90 G17\nG0 X0 Y0\nG2 X10 Y0 I5 J0 F300\n", 0),
    "inch_incremental": ("G20 G91\nG1 X0.1 Y0.2 F10\n", 0),
    "expression_default_config_disabled": ("G21 G90\n#1=2\nG1 X[#1*3] F100\n", 1),
    "bad_gcode": ("G999\n", 20),
    "missing_feed": ("G21 G90\nG1 X1\n", 22),
    "impossible_arc": ("G21 G90 G17\nG2 X10 Y0 R1 F100\n", 34),
    "rigid_tap_unavailable": ("G21 G90\nM3 S500\nG33.1 Z-5 K1\n", 20),
}
results = []
for name, (gcode, expected) in cases.items():
    folder = root / "audit" / name
    folder.mkdir(parents=True, exist_ok=True)
    # Keep programs free of buffer-synchronizing M2: this target is a parser check.
    (folder / "input.ngc").write_text(gcode)
    try:
        p = subprocess.run([str(root / "grblHAL_validator"), "-e", "input.ngc"], cwd=folder, capture_output=True, text=True, timeout=3)
    except subprocess.TimeoutExpired:
        results.append({"case": name, "timeout_seconds": 3, "asserted_pass": False})
        continue
    (folder / "output.txt").write_text(p.stdout + p.stderr)
    results.append({"case": name, "exit_code": p.returncode, "expected": expected, "asserted_pass": p.returncode == expected if expected is not None else None, "output": p.stdout + p.stderr})

folder = root / "audit" / "simulated_motion"
folder.mkdir(parents=True, exist_ok=True)
gcode = "$X\n$22=0\n$20=0\n$100=200\n$101=200\n$102=200\nG21 G90 G17\nG1 X1 Y0.5 Z-0.1 F600\nG2 X2 Y0.5 I0.5 J0 F300\n\x06"
(folder / "input.ngc").write_text(gcode)
try:
    p = subprocess.run([str(root / "grblHAL_sim"), "-n", "-t", "10", "-r", "0.01", "-s", "steps.txt", "-b", "blocks.txt"], input=gcode, cwd=folder, capture_output=True, text=True, timeout=20)
    sim_output = p.stdout + p.stderr
    sim_exit = p.returncode
except subprocess.TimeoutExpired as exc:
    sim_output = "TIMEOUT 20s\n" + (exc.stdout or b"").decode(errors="replace") + (exc.stderr or b"").decode(errors="replace")
    sim_exit = None
(folder / "output.txt").write_text(sim_output)
step_lines = (folder / "steps.txt").read_text().splitlines()
position_lines = [line for line in step_lines if line and not line.startswith("#")]
last_position = position_lines[-1] if position_lines else None
coords = [int(x) for x in re.findall(r"-?\d+", last_position)[2:5]] if last_position else None
results.append({"case": "simulated_motion", "exit_code": sim_exit, "output": sim_output, "step_record_count": len(position_lines), "last_step_record": last_position, "final_step_counts": coords, "asserted_pass": sim_exit == 0 and coords == [400, 100, -20], "note": "200 steps/mm; expected final XYZ step counts 400,100,-20. Timing is host simulation only."})
for name, (gcode, expected) in cases.items():
    folder = root / "audit" / ("sim_parser_" + name)
    folder.mkdir(parents=True, exist_ok=True)
    stream = "$X\n$22=0\n$20=0\n$C\n" + gcode + "\x06"
    (folder / "input.ngc").write_text(stream)
    try:
        p = subprocess.run([str(root / "grblHAL_sim"), "-n", "-t", "10", "-s", "steps.txt", "-b", "blocks.txt"], input=stream, cwd=folder, capture_output=True, text=True, timeout=10)
        output = p.stdout + p.stderr
        # Fresh EEPROM may report settings-read error 7 before the startup banner.
        # Preserve startup diagnostics separately; do not mistake them for parser responses.
        startup, separator, responses = output.partition("GrblHAL 1.1f ['$' or '$HELP' for help]")
        codes = [int(v) for v in re.findall(r"error:(\d+)", responses)]
        startup_codes = [int(v) for v in re.findall(r"error:(\d+)", startup)]
        passed = p.returncode == 0 and (not codes if expected == 0 else expected in codes) if expected is not None else None
        results.append({"case": "sim_parser_" + name, "exit_code": p.returncode, "startup_errors": startup_codes, "reported_errors": codes, "expected": expected, "asserted_pass": bool(separator) and passed, "output": output})
        (folder / "output.txt").write_text(output)
    except subprocess.TimeoutExpired:
        results.append({"case": "sim_parser_" + name, "timeout_seconds": 10, "asserted_pass": False})
(root / "audit" / "results.json").write_text(json.dumps(results, indent=2))
# Identify exactly which executables these results belong to, so the evidence record can
# refuse to pair them with a later rebuild.
(root / "audit" / "binaries.json").write_text(json.dumps({
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in ("grblHAL_validator", "grblHAL_sim")}, indent=2) + "\n")
print(json.dumps(results, indent=2))
if any(r.get("asserted_pass") is False for r in results):
    raise SystemExit(1)
