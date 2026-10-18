"""Read-only outer scope receipt for the current bounded SBC source proposals."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/"sbc-c05-source-proposal"
MODEL=Path("Z:/pcb-runs/claude-finish/tools/verify/rail_model.json")
API=HERE.parent/"electrical-correction/c11061-v2/api-parity-v2/qualification-scope.json"
EXPECTED="95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d"

def main():
    destination=OUT/"bounded-source-scope.json"
    if destination.exists():raise ValueError("distinct immutable receipt required")
    files={}; reports={}
    def read(path):
        path=path.resolve();raw=path.read_bytes();files[str(path)]=hashlib.sha256(raw).hexdigest();return raw
    names=("local-cap-opi-v6.json","south-cap-all-layer-comparison.json","larger-stage-owned-diagnosis.json","targeted-stage-proposal.json","targeted-changed-set-proposal.json","tps22990-census.json")
    for name in names:
        report=json.loads(read(OUT/name))
        if name!="tps22990-census.json" and report["board_sha256"]!=EXPECTED:raise ValueError("wrong pinned source")
        manifest=report.get("read_set_sha256",report.get("source_files_sha256",{}))
        for path,expected in manifest.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError("stale source receipt:"+path)
        reports[name]=report
    api=json.loads(read(API))
    if api["verdict"]!="CORRECTED_SOURCE_NATIVE_API_PARITY_AND_SCOPE_PASS" or api["guard_fixtures_pass"]!=11:raise ValueError("corrected API scope absent")
    model=json.loads(read(MODEL))
    sbc=model["rails"]["/motherboard_power_entry/SBC_5V"]
    core=model["rails"]["/mc_local_power/CORE_5V"]
    extra={r["ref"]:r["w"] for r in sbc["loads"] if r["ref"]!="J15001"}
    full=3.6+sum(extra.values())
    targeted=reports["targeted-changed-set-proposal.json"]
    if targeted["board_emitted"] or targeted["native_jobs"] or targeted["qualified_power"]:raise ValueError("unsafe scope label")
    if targeted["placement"]["physical_native_rules_and_courtyards"]["verdict"]!="HOST_BODY_WITHHELD":raise ValueError("review new physical outcome before freezing")
    additional={r["exact_retained_item"]["uuid"]:r["exact_retained_item"] for r in targeted["additional_retained_copper_changes_required"]}
    if len(additional)!=11 or any(r["moved_ref"]!="C15001" or r["net"]!="/motherboard_power_entry/SBC_5V" for r in targeted["additional_retained_copper_changes_required"]):raise ValueError("new blocker scope differs")
    read(Path(__file__))
    for name in ("test_sbc_exact_path.py","test_sbc_hole_envelope.py","test_corrected_api_guard.py","prepare_sbc_targeted_changed_set.py","prepare_sbc_targeted_stage.py"):
        read(HERE/name)
    report={"schema":"sbc-bounded-source-scope-v1","verdict":"SOURCE_SCOPE_FROZEN_ACTUAL_POWER_LAYOUT_WITHHELD",
            "source_board_sha256":EXPECTED,"corrected_CT_board_sha256":api["board_sha256"],"corrected_CT_native_API_parity":"PASS_ONLY_COMPONENT_NODE_VALUE_MPN_PARITY",
            "current_result":"Explicit3CORE+2SBC segment proposal clears all four relocated switch-stage bodies. The additional C15001 short move is blocked by retained11SBC fanout items and compute connector courtyard; no further ownership expansion or native candidate.",
            "part_poses":targeted["new_component_poses"],"C15001_role":targeted["C15001_role"],"additional_11_SBC_fanout_manifest":additional,"C15001_courtyard_move_limit":"Original Fcourtyard ends165.42mm; J15001 starts166.32mm, so +Y<0.9mm keeps positive separation. This is only a courtyard bound; copper/loop feasibility is still unproved.",
            "retained_ground_via":{k:v for k,v in targeted["retained_ground_via"].items() if k!="unchanged_contacts_by_actual_layer"},
            "electrical_case_distinction":{"requested_compute_branch_A":3.6,"compute_branch_budget_mV":100,"U12_input_branch_budget_mV":70,"per_via_assumption_A":.5,
                "dedicated_compute_branch_minimum_transition_vias":8,"retained_other_SBC_design_load_weights_A":extra,"unreduced_simultaneous_SBC_common_current_lower_bound_A":full,"minimum_common_transition_vias_if_shared":math_ceil(full/.5),
                "operator_case_in_existing_model":sbc["cases"]["operator_3p6"],"existing_CORE_sbc_3p6_case":core["cases"]["sbc_3p6"],"existing_CORE_pe_normal_screen":core["cases"]["pe_normal_screen"],
                "qualification_policy":"The isolated operator3.6A/otherloads-off case does not qualify simultaneous fullrail. Any later paired network must preserve every absolute maximum, derive actual shared/independent branch currents and source/drop budgets, and retain fullCORE source/envelope gates. No equal current split assumed."},
            "proof_limits":["All placement/path/array cases are bounded source planning; no global layout impossibility or qualified3.6A/100mV claim","Old via/hole/endpoint-negative producers remain historical; v6 corrected prospective copper-radius holes and exact connectors only","Pinned r06 native foreign fills/current c05 copper overlay is conservative planning; any new current board needs fresh full native geometry/no-loss/DRC/source/return proof","Current/rooted return, neck/hub capacity, resistance/current-sharing/contact/thermal/load faults and all12interface gates remain open","C11061 current4.7uF25V source is distinct from historical standalone1uF50V CT envelope; parity does not prove effective capacitance/timing","Three overlapped CORE source tracks are one physical1.25mm bus; duplicate source item widths never multiply capacity","Fullfield model capping/overcurrent and unknown relay/island/source loads remain blockers independent of these local SBC proposals"],
            "board_emitted":False,"native_jobs_in_this_source_scope":0,"gpu_jobs":0,"implemented":False,"manufacturing_ready":False,"all_selected_receipts_and_guard_sources_sha256":files}
    for path,expected in files.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError("input changed while freezing")
    destination.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(destination),"sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),"verdict":report["verdict"],"simultaneous_SBC_common_A":full,"minimum_common_vias":math_ceil(full/.5)}))

def math_ceil(n):
    import math
    return math.ceil(n-1e-9)

if __name__=="__main__":main()
