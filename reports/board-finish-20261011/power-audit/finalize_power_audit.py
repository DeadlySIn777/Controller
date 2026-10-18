"""Refresh this workstream's own ranked report with completed, hash-bound facts."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    path = HERE / "ranked-work.json"
    data = json.loads(path.read_text())
    fag = json.loads((HERE / "fag-r06/final-proof.json").read_text())
    sbc = json.loads((HERE / "sbc-bottleneck-receipt.json").read_text())
    data["updated_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["selected_subset_native_result"] = {"candidate_sha256": fag["candidate_sha256"],
        "verdict": fag["native_drc_connectivity_verdict"], "connections_completed": fag["connectivity"]["completed"],
        "connections_lost": fag["connectivity"]["lost"], "drc_errors": fag["drc"]["after"]["errors"],
        "drc_warnings": fag["drc"]["after"]["warnings"], "missing_pad_joins": fag["connectivity"]["missing_after"],
        "unconnected_api_uncapped": 1373, "proof": str(HERE / "fag-r06/final-proof.json"),
        "scope": "Partial 0.096 A FIELD_A return branch; native parity skipped and all full electrical gates open"}
    data["ranked_work"][2].update(task="Completed additive FIELD_A partial return proof",
        action="253 In3 segments and8 vias added with exact source/footprint/copper preservation; native DRC/connectivity PASS +3/-0. Root owns further frozen compositions",
        proof=str(HERE / "fag-r06/final-proof.json"))
    data["ranked_work"][4].update(action="Root owns fresh native DFM on r06. Hardened dfm_contract_v2 source receipt passes exact four cap moves, two fid moves, eight .448mm F.Cu owned ties, 2499 silk edits and one keepout",
        reason="The old DFM donor is not imported as a whole; only bounded proven source edits are transferred. Current native and electrical gates remain required",
        source_receipt=str(HERE / "c02a-dfm-contract-v2.json"))
    data["sbc_root106_next_design_change"] = {
        "current_case_a": 3.6, "load": "J15001", "source": "U11012 VOUT8/9/10", "budget_mv": 100,
        "native_source_candidate_created": False, "current_qualified": False,
        "source_array_bottleneck": "In3 7/2/1 sampled sites; B6/2/2; In2none, at.8mm centres with retained clearances. Single C11061 pad-obstacle counterfactual reaches8 onIn3",
        "minimal_local_relayout_lead": "Reposition C11061 CT/GND capacitor and preserve its exact ramp/ground circuit; tested east nudges.25..2.4mm collide with retained OPI_REARM_TX or fault vias and are rejected",
        "long_corridor_gate": "No shared constant3mm source/load corridor in investigated window onIn3/In2/B. Nearest In3 source/load wide components are95.071491mm apart inside LOGIC reference territory; many locked compute/status/DO signal tracks cross the gap",
        "next_action": "Reserve an adequate power corridor and re-layout owned local source array/CT/GND and bounded blocking signals together; require explicit current-share resistor network/IR+thermal before a native candidate",
        "packing_scope": "0.1mm sampled continuous landing region, up to49starts and12sweep directions; not an exhaustive continuous packing impossibility proof",
        "split_route": sbc["split_path_status"], "receipt": str(HERE / "sbc-bottleneck-receipt.json"),
        "diagram": str(HERE / "sbc-source-bottleneck.png")}
    data["native_parity"] = {"verdict": "OPEN_NATIVE_CHECK_SKIPPED", "reason": "Native logs cannot fetch netlist because full annotation is missing; empty parity lists are not execution proof",
        "next_gate": "Root's independent native API/netlist parity and fresh-export qualification; no borrowed historical parity result"}
    artifacts = ("finish_fag_proof.py", "test_fag_final.py", "fag-r06/final-proof.json", "fag-final-status.json",
                 "sbc-root106-plan.json", "sbc-root106-hubs.json", "sbc-local-change-attribution.json", "sbc-bottleneck-receipt.json",
                 "sbc-source-bottleneck.png", "c02a-dfm-contract-v2.json", "../dfm_contract_v2.py", "../test_dfm_contract_v2.py")
    data["workstream_artifact_sha256"] = {str((HERE / artifact).resolve()): hashlib.sha256((HERE / artifact).read_bytes()).hexdigest() for artifact in artifacts}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"native_fag": "+3/-0,0errors169warnings", "sbc": "source_array_and_wide_corridor_relayout_required", "manufacturing_ready": False}))


if __name__ == "__main__":
    main()
