"""Write a read-only source/evidence screen without launching native jobs.

All new files remain beside this script. Completed historical donors are leads,
not evidence for a composed candidate. Power load numbers remain assumptions.
"""
import datetime
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = Path("Z:/pcb-runs/claude-finish")
PROJECT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    source = HERE / "constraint-snapshot"
    source.mkdir(exist_ok=True)
    sources = [EXT / "tools/field_pdn_spec.json", EXT / "tools/power_widths.json",
               EXT / "tools/verify/rail_model.json", EXT / "tools/fix/load_currents.json",
               PROJECT / "hardware/motherboard_do/design.json",
               PROJECT / "hardware/motherboard_power_entry/README.md"]
    captured = {}
    for index, path in enumerate(sources):
        destination = source / (str(index) + "-" + path.name)
        if destination.exists() and sha(destination) != sha(path):
            raise RuntimeError(f"existing constraint snapshot differs: {path}")
        shutil.copyfile(path, destination)
        captured[str(path)] = {"sha256": sha(path), "snapshot": str(destination)}

    spec = read(EXT / "tools/field_pdn_spec.json")
    sums = {rail["id"]: {"design_a": rail["design_a"], "limit_a": rail["limit_a"],
                         "documented_cluster_max_sum_a": round(sum(c["amps"] for c in rail["clusters"]), 3),
                         "model_caps_segment_current_at_design_a": True}
            for rail in spec["rails"]}
    donors = []
    summaries = [
        ("power-reinforce-r3", EXT / "agent-work/power-reinforce-r3/final-summary.json",
         "REJECT_AS_CURRENT_DONOR", ["Historical input: 1675 to1674 missing joins, one gain only",
          "22 higher-priority zones clip182.6 mm2 of other-net pours and add4 other-net islands",
          "No strict whole-board partition no-loss proof, source via target still short",
          "Reported1.2-1.3 A/via differs from retained0.5 A/via field assumption"]),
        ("pairs3-r3 dense-d6", EXT / "agent-work/pairs3-r3/r5/dense-d6/pair-upgrade-d6/final-summary.json",
         "REJECT", ["Historical dense missing joins1675 to1700: regression25",
          "Rips1139 foreign copper items; restore drops267 items on27 nets",
          "Completed pairs still report mismatch/coupling/off-width failures"]),
        ("pairs3-r3 clean-c6", EXT / "agent-work/pairs3-r3/r5/clean-c6/pair-upgrade-c6/final-summary.json",
         "HISTORICAL_GEOMETRY_LEAD_ONLY", ["Clean historical input3973 missing joins to3955, not current dense input",
          "Replace10 nets; not additive preservation of current board",
          "Ethernet/HDMI/USB pairs retain mismatch/coupling/off-width failures"]),
        ("plane-track extension", EXT / "agent-work/plane-track/proof/drc_compare_base_ext.json",
         "REJECT_WITHOUT_FULL_REFILL", ["Only touched-zone refill in source report",
          "Receipts show1676 to2626 missing joins and0 to11 isolated-copper warnings",
          "Dangling-via warnings12 to199; no whole-board strict no-loss proof"]),
    ]
    for name, path, verdict, reasons in summaries:
        donors.append({"name": name, "receipt": str(path), "receipt_sha256": sha(path),
                       "verdict": verdict, "reasons": reasons,
                       "evidence_class": "historical native receipts/source inspection; no current-candidate proof"})
    base = EXT / "integrate/measure/r06-stitch-plane-pads-2/partitions.json"
    partitions = read(base)
    ranked_nets = sorted(({"net": net, "missing_joins": max(0, len(groups) - 1)}
                          for net, groups in partitions["nets"].items()),
                         key=lambda item: (-item["missing_joins"], item["net"]))[:20]
    output = {
        "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_board_sha256": partitions["sha256"], "r06_missing_joins": partitions["pad_island_joins"],
        "r06_top_remaining_nets": ranked_nets, "constraint_snapshots": captured,
        "field_load_model": sums,
        "full_field_power_gate": {"verdict": "OPEN_BLOCKED", "reason":
            "Planner caps downstream segment current at4.58 A/4.82 A, while cluster maximum sums exceed those values. "
            "Supply/return accounting, simultaneous-load allocation, eFuse/fault/transient limits and both current paths "
            "must be reconciled without silently reducing fitted channel or electrical limits. The sums themselves "
            "are design assumptions and are not measured simultaneous source loads."},
        "completed_donor_screen": donors,
        "active_candidate": {"scope": "FAG partial return branch only", "source_model_a": 0.096,
            "records": 261, "tracks": 253, "vias": 8, "via_diameter_mm": 0.6, "via_drill_mm": 0.3,
            "trunk_width_mm": 0.3, "via_tie_width_mm": 0.8,
            "native_status_receipt": str(HERE / "fag-status.json"),
            "adoption": False, "full_rail_electrical_qualification": False,
            "limits": ["JD01 allocation uses equal split of AUX24A/AUX5A maxima and does not limit unknown load transients",
                       "Two joined relay islands have zero/unspecified load allocation; never qualify them from zero current",
                       "35 um copper,60 C resistance and0.5 A/via are model assumptions",
                       "Current-specific full supply and return extraction/IR/thermal/isolation/SI proof remains open"]},
        "live_external_files_modified": False, "new_gpu_jobs": 0, "manufacturing_ready": False,
    }
    (HERE / "donor-screening.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(HERE / "donor-screening.json"), "donors": len(donors),
                      "full_field_power_gate": output["full_field_power_gate"]["verdict"]}))


if __name__ == "__main__":
    main()
