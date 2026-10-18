"""Collect existing disconnected qualification evidence; never rerun or adopt RTL."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
            "bytes": path.stat().st_size}


source_checks = {}


def verify(path, expected):
    path = path.resolve()
    actual = digest(path)
    if actual != expected:
        raise RuntimeError(f"Source/evidence hash changed: {path}")
    key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    prior = source_checks.get(key)
    if prior and prior != expected:
        raise RuntimeError(f"Conflicting source provenance: {path}")
    source_checks[key] = actual


runs = []
definitions = [
    ("current-iol1-r01", {"host_C_checks": 5441, "C_HDL_replay_checks": 78,
                           "ARM_compile_link_profiles": 4},
     "Current C protocol with host sanitizers; four ARM compile/link artifacts; actual C peers and four IOL1 RTL masters in the historical six-motion/two-encoder bringup wrapper; generic Efinix-family mapping."),
    ("cnc3-structural-r01", {"static_C_oracle_vectors": 743, "serial_SPI_checks": 41,
                             "C_response_roundtrip_classes": 2},
     "Current checked-in structural CNC3 RTL command validation, 96/176-byte serial transport and response packing; no motion generators."),
    ("spi-twelve-four-plant-r01", {"scenarios": 18},
     "Unchanged report-local twelve-motion/four-encoder candidate; actual compiled RTL serial transport, emitted step/direction pins, ideal mechanics, encoder waveforms and serial feedback."),
    ("four-abz-filter-r01", {"filter_checks": 80137},
     "Four actual ABZ encoder components plus twelve-lane alarm filtering; local Z capture is not a CNC3 index event implementation."),
    ("twelve-generator-timing-r01", {"equivalence_comparisons": 2400000,
                                      "equivalence_cycles": 200000,
                                      "simultaneous_generators": 12,
                                      "dynamic_timing_checks": 60848},
     "Actual twelve-generator algorithm equivalence and separate dynamic timing/clean-drain component checks."),
    ("explicit-boundaries-r02", {"cases": 22, "fixture_assertions": 684},
     "Actual serial transport after concurrent twelve-lane motion: six unsupported I/O/PWM/probe/index commands refuse, each of twelve alarm lanes inhibits, and each of four encoder-valid losses inhibits; serial feedback is independently decoded."),
]
for name, counts, scope in definitions:
    folder = HERE / name
    receipt = read(folder / "receipt.json")
    if name == "current-iol1-r01":
        assert receipt["tool_exit"] == 0 and receipt["inputs_unchanged"]
        assert receipt["host_C_checks"] == counts["host_C_checks"]
        for entry in receipt["inputs"]:
            verify(ROOT / entry["path"], entry["sha256"])
    else:
        assert receipt["status"] == "PASS"
    if name == "cnc3-structural-r01":
        for relative, expected in receipt["source_stage_hashes"].items():
            verify(ROOT / "gateware/v3" / relative, expected)
    for field in ("input_sha256", "input_hashes", "source_hashes", "source_sha256"):
        for path, expected in receipt.get(field, {}).items():
            verify(ROOT / path, expected)
    if name in ("spi-twelve-four-plant-r01", "explicit-boundaries-r02"):
        assert len(receipt["cases"]) == counts.get("cases", counts.get("scenarios"))
        assert all(case["passed"] for case in receipt["cases"])
    if name == "explicit-boundaries-r02":
        assert sum(case["checks"] for case in receipt["cases"]) == counts["fixture_assertions"]
        for relative, expected in receipt["copied_input_sha256"].items():
            verify(folder / "inputs" / relative, expected)
    if name == "spi-twelve-four-plant-r01":
        for case in receipt["cases"]:
            verify(folder / case["scenario"] / "state.json", case["state_sha256"])
            verify(folder / case["scenario"] / "responses.txt", case["responses_sha256"])
    # Pin all logs, tool versions, receipt/decoded/state data and actual ARM images.
    outputs = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or "obj" in path.relative_to(folder).parts:
            continue
        if "inputs" in path.relative_to(folder).parts or "oracle" in path.relative_to(folder).parts:
            continue
        if path.suffix in (".log", ".json", ".jsonl", ".txt", ".elf", ".bin", ".sh"):
            outputs.append(artifact(path))
    runs.append({"id": name, "status": "PASS_WITHIN_DECLARED_SCOPE", "counts": counts,
                 "counts_are_not_additive_across_runs": True, "scope": scope,
                 "receipt": artifact(folder / "receipt.json"), "artifacts": outputs})

motion = read(HERE / "motion-inputs/provenance.json")
for entry in motion["inputs"]:
    verify(ROOT / entry["source"], entry["sha256"])
    verify(HERE / "motion-inputs" / entry["copy"], entry["sha256"])

failed = HERE / "explicit-boundaries-r01"
assert read(failed / "receipt.json")["status"] == "FAIL"
for name in (entry["copy"] for entry in motion["inputs"]):
    assert digest(failed / "inputs" / name) == digest(HERE / "explicit-boundaries-r02/inputs" / name)

clean = read(HERE / "spi-twelve-four-plant-r01/clean/state.json")
result = {
    "schema_version": 1,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "status": "BOUNDED_SOURCE_QUALIFICATION_PASS_FULL_REV_A_INTEGRATION_BLOCKED",
    "candidate_adopted": False, "full_machine_milestone": False,
    "physical_measurements": 0, "hardware_accessed": False,
    "target_execution": False, "actual_FPGA_device_execution": False,
    "vendor_Efinity_fit_or_STA": False, "manufacturing_ready": False,
    "production_ready": False, "routing_or_CAD_modified": False,
    "evidence_classes": ["source hash inspection", "host C tests and sanitizers",
                         "ARM target compilation/linking", "actual HDL simulation",
                         "generic Efinix-family synthesis mapping for historical IOL1 bringup"],
    "runs": runs,
    "motion_source_provenance": artifact(HERE / "motion-inputs/provenance.json"),
    "source_and_evidence_hash_rechecks": [
        {"path": key.replace("\\", "/"), "sha256": value}
        for key, value in sorted(source_checks.items())],
    "all_rechecked_hashes_match": True,
    "clean_plant_observed_rises_M0_to_M11": [j["observed_rises"] for j in clean["joints"]],
    "fixture_failure_retained": {
        "receipt": artifact(failed / "receipt.json"),
        "log": artifact(failed / "execute.log"),
        "runner": artifact(failed / "runner-source.py"),
        "classification": "test fixture assumption corrected; no RTL source change",
        "cause": "Initial fixture incorrectly required permit_out_req LOW during armed motion. The unchanged state machine defines it as armed_mask != 0. It is motion permission, not general I/O authority.",
        "correction": "Require output_request and progress_o LOW after commissioning during ordinary motion; keep motion permission semantics unchanged. Correct feedback decoder field names to alarm_levels and encoder_fault_mask.",
        "all_eight_RTL_files_identical_to_passing_r02": True,
    },
    "remaining_gaps": [
        {"id": "complete_adopted_top", "status": "BLOCKED", "detail": "No adopted single complete IS-2 top combines these separately evidenced components and current firmware."},
        {"id": "CAP3_identity_and_qualification", "status": "BLOCKED", "detail": "Replayed motion top lacks CAP3 READ_PAGE; separate profile candidate deliberately sets IS2_PROFILE_COMPLETE=0. Real identity, acquisition and qualification are incomplete; real host discovery refusal must remain."},
        {"id": "general_DI_DO", "status": "BLOCKED", "detail": "24 general DI and 16 smart general DO are not functionally integrated in the replayed twelve-motion top. DI/AI are stale, and unsupported DO requests refuse. Diagnostic-only IOL1 replay grants no output authority."},
        {"id": "probe_index_and_events", "status": "BLOCKED", "detail": "No complete actual home/limit/probe/event acquisition or CNC3 index one-shot event ring. Local ABZ Z capture is component evidence only."},
        {"id": "output_authority", "status": "BLOCKED", "detail": "General output/PWM authority and complete IOL1 output application remain unimplemented; ideal external permission/watchdog providers do not establish physical safety."},
        {"id": "machine_host_integration", "status": "BLOCKED", "detail": "This evidence does not execute LinuxCNC or a qualified CNC3 HAL integration; see separately owned host receipts."},
        {"id": "vendor_and_electrical", "status": "BLOCKED", "detail": "No actual selected-device vendor place/route, pin constraints, static timing or bitstream proof; no physical signal, current, watchdog, power or machine measurements."},
    ],
    "interpretation": [
        "Do not sum cycles, fixture assertions, static vectors and scenarios into a unique proof count.",
        "Historical runner field actual_FPGA_integration means actual compiled RTL integration only, not a physical FPGA device.",
        "Legacy installed_input=0xfff, class-1 and qualification_complete bench inputs are authored logical qualification fixtures; they are not IS-2 integrated-region card-presence discovery or physical proof.",
        "Historical six-joint/two-encoder IOL1 wrapper evidence is separate from report-local twelve-generator/four-encoder evidence.",
        "No RTL, firmware, routing, protocol limits, existing historical reports or external IS-1 archive were modified for this qualification work.",
    ],
    "summary_generator": artifact(Path(__file__).resolve()),
}
with (HERE / "receipt.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": result["status"], "runs": len(runs),
                  "rechecked_hashes": len(source_checks),
                  "receipt": str(HERE / "receipt.json")}, indent=2))
