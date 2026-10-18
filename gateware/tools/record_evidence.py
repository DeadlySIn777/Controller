#!/usr/bin/env python3
"""Preserve a successful reference test run and hash its source inputs.

    python gateware/tools/record_evidence.py          # record build/ run into validation/
    python gateware/tools/record_evidence.py --check  # read-only: verify validation/ against the tree

--check writes nothing. It re-verifies the retained validation/simulation.log
markers and PASS count, the rate bound, and every recorded source and evidence
hash. Its historical runner dependency scope is explicit; separately evidenced
characterization is not relabeled as baseline execution. A verifier transition
preserves the originally recorded recorder bytes instead of re-stamping history.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

EXPECTED_V1_CHECKS = 252
EXPECTED_V2_CHECKS = 27

# Reviewed complete input/metadata scope of the exact baseline runner below.
# Its four RTL files, two benches, readmemh vectors and Python decoder are fixed.
# Updating a runner or adding any other baseline input requires a reviewed scope
# revision and fresh execution, not acceptance through a broad wildcard exclusion.
BASELINE_RUNNER_SHA256 = 'b4fe1bcdcf974fb40faa7eca023a6d1463b8726ac0ab4708f650f44dcc12c3f4'
BASELINE_SCOPE = frozenset({
    'PROTOCOL.md', 'rtl/cnc_encoder.v', 'rtl/cnc_endpoint.v',
    'rtl/cnc_spi_frame.v', 'rtl/cnc_stepgen.v', 'tests/tb_cnc_endpoint.sv',
    'tests/tb_cnc_endpoint_v2.sv', 'tests/vectors.hex', 'tests/vectors.json',
    'tools/protocol.py', 'tools/record_evidence.py', 'tools/run_tests.sh',
})
SEPARATE_BENCH = 'tests/tb_stepgen12_characterization.sv'
SEPARATE_BENCH_SHA256 = 'b2af130b67983bdc869f7dcf603e8fdf855a0087d7bbfac5e19c1917fd81757f'
SEPARATE_RECEIPT = 'reports/pre-hardware-characterization-20261001/stepgen12-sweep-r02/receipt.json'
SEPARATE_RECEIPT_SHA256 = '36a7d492c666d41c69f0f272890eb25497df50917e12a068fc820724261c74aa'
TRANSITION = 'reports/readiness-fixes-20261004/rtl-verifier-transition.json'


def historical_scope(root, current):
    """Reject unknown inventory; prove the one independent bench's exact scope."""
    problems = []
    excluded = []
    if current.get('tools/run_tests.sh') != BASELINE_RUNNER_SHA256:
        problems.append('baseline runner changed; complete dependency scope must be reviewed')
    for name in sorted(BASELINE_SCOPE - current.keys()):
        problems.append('missing baseline dependency ' + name)
    for name in sorted(current.keys() - BASELINE_SCOPE):
        if name != SEPARATE_BENCH:
            problems.append('unrecorded baseline-scope inventory ' + name)
            continue
        receipt_path = root.parent / SEPARATE_RECEIPT
        if (current[name] != SEPARATE_BENCH_SHA256 or not receipt_path.is_file() or
                hashlib.sha256(receipt_path.read_bytes()).hexdigest() != SEPARATE_RECEIPT_SHA256):
            problems.append('independent characterization identity/evidence changed: ' + name)
            continue
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        matches = [digest for path, digest in receipt.get('input_sha256', {}).items()
                   if path.replace('\\', '/').endswith('/gateware/' + name)]
        if receipt.get('status') != 'PASS' or matches != [current[name]]:
            problems.append('independent characterization receipt does not bind ' + name)
        else:
            excluded.append(name)
    return problems, excluded


def archived_recorder_matches(root, old_digest, current_digest, manifest_bytes):
    """Explicit migration for the verifier itself, never for simulation inputs."""
    try:
        transition = json.loads((root.parent / TRANSITION).read_text(encoding='utf-8'))
        archive = transition['archived_recorder_path']
        if not isinstance(archive, str) or '\\' in archive or ':' in archive:
            return False
        path = (root.parent / archive).resolve()
        if not path.is_relative_to(root.parent.resolve()):
            return False
        return (transition.get('schema_version') == 1 and
                transition.get('historical_manifest_sha256') == hashlib.sha256(manifest_bytes).hexdigest() and
                transition.get('historical_recorder_sha256') == old_digest and
                transition.get('current_verifier_sha256') == current_digest and
                path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == old_digest)
    except (OSError, ValueError, KeyError, TypeError):
        return False

parser = argparse.ArgumentParser(description="Record or verify gateware RTL simulation evidence.")
parser.add_argument("--check", action="store_true",
                    help="read-only: verify validation/manifest.json against the retained log and current files")
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
out = root / "validation"
# Record mode reads the fresh run in build/; --check reads the retained copy in validation/.
log = ((out if args.check else root / "build") / "simulation.log").read_bytes()
required = (
    f"ALL {EXPECTED_V1_CHECKS} CHECKS PASSED; pulse timing monitors passed on six channels".encode(),
    f"ALL {EXPECTED_V2_CHECKS} V2 CHECKS PASSED".encode(),
    b"Python independently decoded RTL status",
    b"Icarus -g2005 elaboration passed for the default ABI1 and ENABLE_DISCOVERY=1 tops",
    b"V e r i l a t i o n   R e p o r t: Verilator 5.048",
    b"Verilator strict lint passed: default, ENABLE_DISCOVERY=1 and 1364-2005 language mode",
)
if any(marker not in log for marker in required):
    raise SystemExit("Log does not contain the expected successful reference run; do not publish evidence")
text = log.decode("utf-8", errors="replace")
pass_lines = sum(line.startswith("PASS ") for line in text.splitlines())
if "FAIL " in text or pass_lines != EXPECTED_V1_CHECKS + EXPECTED_V2_CHECKS:
    raise SystemExit(f"Unexpected PASS/FAIL lines ({pass_lines}); do not publish evidence")

# Fault-free DDS bound on the production defaults (the testbench checks the
# instantiated parameters; this re-derives it from the source defaults).
rtl = (root / "rtl/cnc_endpoint.v").read_text(encoding="utf-8")
defaults = {name: int(value, 0) for name, value in re.findall(
    r"parameter\s+integer\s+(PULSE_CYCLES|SPACE_CYCLES)\s*=\s*(\d+)", rtl)}
max_rate = int(re.search(r"parameter\s+\[31:0\]\s+MAX_RATE\s*=\s*32'h([0-9a-fA-F_]+)", rtl).group(1).replace("_", ""), 16)
bound = 2**32 // (defaults["PULSE_CYCLES"] + defaults["SPACE_CYCLES"] + 1)
if max_rate > bound:
    raise SystemExit(f"MAX_RATE 0x{max_rate:08X} exceeds fault-free bound 0x{bound:08X}; do not publish evidence")

paths = sorted(path for pattern in ("rtl/*.v", "tests/*", "tools/*.py", "tools/*.sh", "PROTOCOL.md")
               for path in root.glob(pattern) if path.is_file())
source_sha256 = {str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in paths}
scope_problems, excluded = historical_scope(root, source_sha256)
source_sha256 = {name: digest for name, digest in source_sha256.items() if name in BASELINE_SCOPE}

if args.check:
    manifest_bytes = (out / "manifest.json").read_bytes()
    recorded = json.loads(manifest_bytes)
    problems = list(scope_problems)
    if recorded.get("rtl_checks") != EXPECTED_V1_CHECKS or recorded.get("rtl_v2_checks") != EXPECTED_V2_CHECKS:
        problems.append("recorded check counts differ from the expected counts")
    if recorded.get("rate_bound", {}).get("fault_free_bound") != f"0x{bound:08X}":
        problems.append("recorded rate bound differs from the current RTL defaults")
    old_sources = recorded.get("source_sha256", {})
    if set(old_sources) != BASELINE_SCOPE:
        problems.append('manifest does not contain the complete reviewed baseline dependency scope')
    if set(recorded.get('evidence_sha256', {})) != {'simulation.log', 'status_encoder.hex'}:
        problems.append('manifest does not contain both required baseline evidence hashes')
    archived_verifier = False
    for name in sorted(set(old_sources) | set(source_sha256)):
        if old_sources.get(name) != source_sha256.get(name):
            if (name == 'tools/record_evidence.py' and
                    archived_recorder_matches(root, old_sources.get(name), source_sha256.get(name), manifest_bytes)):
                archived_verifier = True
                continue
            problems.append(("changed " if name in old_sources and name in source_sha256 else
                             "unrecorded " if name in source_sha256 else "missing ") + name)
    for name, digest in recorded.get("evidence_sha256", {}).items():
        path = out / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            problems.append("evidence changed or missing: validation/" + name)
    if problems:
        sys.exit("Gateware evidence check FAILED:\n  " + "\n  ".join(problems))
    print(f"Gateware evidence verified: {len(source_sha256)} source and "
          f"{len(recorded.get('evidence_sha256', {}))} evidence hashes; "
          f"{EXPECTED_V1_CHECKS} v1 + {EXPECTED_V2_CHECKS} v2 checks; nothing written.")
    if archived_verifier:
        print('Historical recorder bytes verified from the explicitly bound archive; '
              'current verifier checked through its transition. No test run re-stamped.')
    for name in excluded:
        print('Excluded independent characterization (not consumed by the exact baseline runner): '
              + name + '; exact separate receipt/hash verified. No new simulation claimed.')
    sys.exit(0)

if scope_problems:
    sys.exit('Gateware source scope FAILED:\n  ' + '\n  '.join(scope_problems))
out.mkdir(exist_ok=True)
(out / "simulation.log").write_bytes(log)
(out / "status_encoder.hex").write_bytes((root / "build/status_encoder.hex").read_bytes())
manifest = {
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "scope": ("RTL functional simulation (default ABI1 and ENABLE_DISCOVERY=1 ABI2 testbenches), "
              "default-top and Verilog-2005 elaboration, independent codec check, strict lint only"),
    "tools": {"iverilog": "13.0", "verilator": "5.048", "python": "3.14.7",
              "environment": "WSL GarciaMechBuilder / Alpine Linux 3.24.2"},
    "rtl_checks": EXPECTED_V1_CHECKS,
    "rtl_v2_checks": EXPECTED_V2_CHECKS,
    "uncounted_fatal_monitors": ["STEP high = PULSE_CYCLES", "STEP low >= SPACE_CYCLES", "DIR setup >= DIR_SETUP_CYCLES",
                                 "DIR hold >= DIR_HOLD_CYCLES", "no STEP while disabled"],
    "rate_bound": {"PULSE_CYCLES": defaults["PULSE_CYCLES"], "SPACE_CYCLES": defaults["SPACE_CYCLES"],
                   "MAX_RATE": f"0x{max_rate:08X}", "fault_free_bound": f"0x{bound:08X}",
                   "rule": "MAX_RATE <= floor(2^32/(PULSE_CYCLES+SPACE_CYCLES+1))"},
    "source_sha256": source_sha256,
    "evidence_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                        for name in ("simulation.log", "status_encoder.hex")},
    "not_proven": ["T20 synthesis/resource fit", "place and route/timing closure", "board pin/bank assignment",
                   "CDC metastability/MTBF and minimum capturable inhibit pulse",
                   "physical SPI/encoder/STEP integrity", "physical LinuxCNC realtime SPI transport/target deadlines", "machine safety"],
}
with open(out / "manifest.json", "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(manifest, indent=2) + "\n")
print(f"Recorded {len(source_sha256)} baseline source hashes and two evidence hashes in {out / 'manifest.json'}")
