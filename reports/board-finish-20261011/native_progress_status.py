"""Publish current isolated PCB attempt state without promoting partial checks."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("Z:/pcb-runs/claude-finish")
BASE = ROOT / "integrate/measure/r06-stitch-plane-pads-2"
CASES = (
    ("r06 plus In3 bridges", HERE / "revisions/c01-r06-in3-bridges.kicad_pcb", HERE / "measure/c01"),
    ("r06 plus placement and silk corrections", HERE / "revisions/c02a-r06-dfm.kicad_pcb", HERE / "measure/c02a"),
    ("recovered r07 routing", ROOT / "agent-work/codex-recovery-20261011/candidate.kicad_pcb", ROOT / "agent-work/codex-recovery-20261011/measure"),
    ("r06 plus selected FIELD_GND return branch", HERE / "power-audit/fag-r06/candidate/board.kicad_pcb", HERE / "power-audit/fag-r06/measure"),
    ("combined recovery, In3, return and placement candidate", HERE / "recovery-composite/c03-recovery-in3-fag-dfm.kicad_pcb", HERE / "measure/c03-shared"),
    ("combined candidate plus four indicator groups", HERE / "recovery-composite/e1/c04-four-net-e1-dfm.kicad_pcb", HERE / "measure/c04-main"),
    ("recovery, In3 and DFM with conflicting whole groups withdrawn", HERE / "recovery-composite/c05/c05-fag-e1-rollback-dfm.kicad_pcb", HERE / "measure/c05-shared"),
    ("live r07 plus two zero-via signal repairs", HERE / "recovery-composite/c06/two-zero-via/r07-two-zero-via.kicad_pcb", HERE / "measure/r07-two-zero-via"),
    ("live r07 plus four signals and repaired partial FIELD_A return", HERE / "power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb", HERE / "measure/r07-four-fag-shared"),
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main():
    records = []
    for name, board, measurement in CASES:
        record = {"name": name, "board": str(board), "measurement": str(measurement), "phase": "PENDING"}
        if board.exists():
            record["source_sha256"] = hashlib.sha256(board.read_bytes()).hexdigest()
            record["phase"] = "SOURCE_BUILT_NATIVE_CHECKS_PENDING"
        run = read(measurement / "status.json")
        if run and run.get("candidate_sha256") == record.get("source_sha256"):
            record["native_runner"] = run
            if run.get("phase") == "NATIVE_MEASUREMENT_RUNNING":
                record["phase"] = "NATIVE_MEASUREMENT_RUNNING"
        partitions, summary = read(measurement / "partitions.json"), read(measurement / "summary.json")
        if partitions:
            if record.get("source_sha256") != partitions["sha256"]:
                record["phase"] = "INVALID_SOURCE_BINDING"
            else:
                record.update(phase="REFILLED_CONNECTIVITY_AVAILABLE_DRC_PENDING",
                              missing_joins=partitions["pad_island_joins"], api_unconnected=partitions["api_unconnected_count"])
        if summary:
            if record.get("source_sha256") != summary["board_sha256"]:
                record["phase"] = "INVALID_SOURCE_BINDING"
            else:
                record.update(phase="NATIVE_DRC_AND_CONNECTIVITY_AVAILABLE_REVIEW_REQUIRED",
                              ordinary_drc_errors=summary["drc_errors"], unresolved_drc_warnings=summary["drc_warnings"])
        proof = read(measurement / "proof.json")
        if proof and record.get("source_sha256") == proof.get("candidate_sha256"):
            safe_guard = proof.get("connectivity_r06", proof.get("connectivity", {}))
            record.update(phase="NATIVE_PASS" if proof.get("verdict") == "PASS" else "NATIVE_REJECTED",
                          completed=safe_guard.get("completed"), lost=safe_guard.get("lost"))
            if proof.get("connectivity_r07_live"):
                record["live_transition"] = proof["connectivity_r07_live"]
        live = read(measurement / "live-transition-diagnostic.json")
        if live and live.get("after_sha256") == record.get("source_sha256"):
            record["live_transition"] = live
        if record.get("live_transition", {}).get("verdict") == "FAIL":
            record["adoption_status"] = "WITHHELD_FAILED_LIVE_CONTINUITY"
        elif proof and proof.get("candidate_sha256") == record.get("source_sha256") and proof.get("connectivity_r06", {}).get("verdict") == "FAIL":
            record["adoption_status"] = "WITHHELD_FAILED_R06_CONTINUITY"
        else:
            record["adoption_status"] = "NOT_ADOPTED"
        parity_dirs = {"c05-shared": "c05", "r07-two-zero-via": "r07-two-zero-via"}
        parity = read(HERE / "parity-repair" / parity_dirs.get(measurement.name, "absent") / "native-receipt.json")
        if parity and parity.get("board_sha256") == record.get("source_sha256"):
            record["separate_native_API_parity"] = parity["verdict"]
        source_proof = read(measurement / "source-proof.json")
        if source_proof and source_proof.get("candidate_sha256") == record.get("source_sha256"):
            record["same_hash_source_proof"] = source_proof.get("verdict")
            record["separate_native_API_parity"] = source_proof.get("native_api", {}).get("verdict", "not established")
        log = measurement / "drc.log"
        if log.exists() and "Failed to fetch schematic netlist" in log.read_text(errors="replace"):
            record["cli_schematic_parity"] = "NOT_EXECUTED; explicit source/native netlist comparison required"
        record["manufacturing_ready"] = False
        record["adopted"] = False
        records.append(record)
    status = {"updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "ROOT106 experimental native board; separate from adopted Source26/ROOT104/CAD30",
              "manufacturing_ready": False, "candidates": records,
              "baseline": read(BASE / "summary.json"),
              "installed_gate": read(HERE / "gate-install-receipt.json"),
              "open": ["Remaining required joins and unresolved DRC warnings",
                       "Full power/load accounting, return paths and via-current capacity",
                       "Controlled pairs, SI, analog review and isolation",
                       "DFM, fresh stored zone fills and same-revision final verification",
                       "Fabricator stackup/process confirmation and physical qualification"]}
    (HERE / "CURRENT_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    lines = ["PCB finishing attempt, 11 October 2026", "",
             "These are isolated ROOT106 candidates. The adopted Source26/ROOT104/CAD30 record and external IS-1 archive remain separate.",
             "Manufacturing readiness: FALSE. Native checks do not prove electrical capacity, SI, FPGA fit/timing or physical behavior.", ""]
    for r in records:
        lines += [r["name"] + ": " + r["phase"],
                  "  " + r["board"],
                  "  SHA256: " + r.get("source_sha256", "not yet saved"),
                  "  Missing pad joins: " + str(r.get("missing_joins", "pending")) +
                  "; ordinary DRC errors: " + str(r.get("ordinary_drc_errors", "pending")) +
                  "; unresolved warnings: " + str(r.get("unresolved_drc_warnings", "pending")),
                  "  Completed/lost vs r06: " + str(r.get("completed", "pending")) + "/" + str(r.get("lost", "pending")),
                  "  CLI parity: " + r.get("cli_schematic_parity", "not established"),
                  "  Separate native API parity: " + r.get("separate_native_API_parity", "not established"),
                  "  Adoption: " + r["adoption_status"]]
        if r.get("live_transition"):
            live = r["live_transition"]
            lines += ["  Direct live completed/lost: " + str(live["completed"]) + "/" + str(live["lost"]) + "; " + live["verdict"]]
        lines += [""]
    lines += ["Routing tool repairs installed with backups; live board/ledger were unchanged during installation.",
              "A combined candidate must be reconstructed, frozen, refilled and checked again before being selected.",
              "Updated UTC: " + status["updated_utc"]]
    (HERE / "CURRENT_STATUS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_states": {r["name"]: r["phase"] for r in records}, "manufacturing_ready": False}))


if __name__ == "__main__":
    main()
