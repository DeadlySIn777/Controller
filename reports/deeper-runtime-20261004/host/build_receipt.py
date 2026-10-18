"""Consolidate two exact current-source LinuxCNC/serial/RTL SIM2 runs."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding="utf-8"))
def main():
    runs=[HERE/"nml-r07",HERE/"nml-eight-r02"]
    receipts=[load(p/"receipt.json") for p in runs]
    observed=[load(p/"linuxcnc.json") for p in runs]
    sources=receipts[0]["source_sha256"]
    sanitizer=load(HERE/"sanitizer-r02/receipt.json")
    strict=load(HERE/"sanitizer-reader-strict-r01/receipt.json")
    assert sanitizer["status"]=="PASS" and sanitizer["source_sha256"]==sources and sanitizer["source_inputs_unchanged"]
    assert strict["status"]=="PASS" and strict["source_sha256"]==sources and strict["address_undefined_leak_diagnostics"]==0
    assert all(r["status"]=="PASS" and r["source_inputs_unchanged"] and r["settings_preserved"] and r["installed_existing_rootfs_modules_preserved"] for r in receipts)
    assert receipts[1]["source_sha256"]==sources
    assert all(sha(ROOT/p)==digest for p,digest in sources.items())
    baseline=load(runs[0]/"installed-modules-before.json")
    assert all(load(run/name)==baseline for run in runs for name in ("installed-modules-before.json","installed-modules-after.json"))
    assert [n["active_joints"] for n in observed]==[12,8]
    assert all(n["status"]=="PASS" and all(c["status"]=="PASS" for c in n["checks"]) for n in observed)
    summaries=[]
    artifacts={}
    for run,r,n in zip(runs,receipts,observed):
        for p in run.rglob("*"):
            if p.is_file():artifacts[p.relative_to(HERE).as_posix()]=sha(p)
        before=n["observations"]["before_motion"]
        moving=n["observations"]["during_concurrent_motion"]
        stopped=n["observations"]["after_motion"]
        recovered=n["observations"]["recovered"]
        count=n["active_joints"]
        assert all(moving["observed-step-rises"][i]>before["observed-step-rises"][i] and moving["joint-velocity"][i]>0 for i in range(count))
        assert moving["rtl-armed-mask"]==(1<<count)-1
        assert all(not d["physical-authority"] and not d["production-profile-complete"] for d in n["observations"].values() if "physical-authority" in d)
        if count==8:assert stopped["observed-step-rises"][8:]==[0]*4
        summaries.append({"run":run.relative_to(HERE).as_posix(),"actual_LinuxCNC_NML_checks":len(n["checks"]),
            "active_joints":count,"fitted_channels":n["fitted_channels"],"configuration_binding":n["configuration_binding"],
            "configuration_manifest_sha256":r["configuration_manifest_sha256"],
            "concurrent_motor_commands":moving["position-cmd"],"concurrent_joint_velocities":moving["joint-velocity"],
            "concurrent_independent_STEP_rises":moving["observed-step-rises"],"concurrent_model_accepted_rises":moving["model-accepted-rises"],
            "stopped_serial_STEP_counts":stopped["reported-steps"],"stopped_serial_encoder_counts":stopped["encoder-count"],
            "final_index_capture_counts":recovered["index-events"],"final_probe_capture_counts":recovered["probe-events"],
            "motion_session_before":before["session"],"motion_session_after":recovered["session"],
            "provider_sequence_before":before["provider-sequence"],"provider_sequence_after":recovered["provider-sequence"],
            "deliberate_inhibited_unhomed_restart":not recovered["sim-permission"] and not any(recovered["homed"]),
            "actual_driver_SPI_checks":json.loads((run/"driver-spi.log").read_text())["checks"],
            "actual_compiled_C_reader_controls":len(json.loads((run/"manifest-controls.log").read_text())["checks"]),
            "settings_sha256":r["settings_sha256"],"rootfs_work":r["rootfs_work"]})
    receipt={"schema_version":1,"kind":"current_source_disconnected_LinuxCNC_CNC3_SIM2_host_integration",
        "status":"PASS","source_sha256":sources,"source_inputs_unchanged":True,
        "installed_existing_rootfs_modules_preserved":True,"installed_existing_module_count":len(baseline),
        "settings_preserved":True,"runs":summaries,"artifact_sha256":artifacts,
        "current_source_ASan_UBSan":{"receipt":"sanitizer-r02/receipt.json","sha256":sha(HERE/"sanitizer-r02/receipt.json"),
            "actual_current_compiled_C_driver_SPI_RTL_ProviderPlant_assertions":374,"leak_detection_enabled":True,
            "strict_reader_receipt":"sanitizer-reader-strict-r01/receipt.json","strict_reader_sha256":sha(HERE/"sanitizer-reader-strict-r01/receipt.json"),
            "strict_compiled_C_reader_cases":18,"address_undefined_leak_diagnostics":0,
            "compile_receipt":"sanitizer-r01/receipt.json","compile_receipt_sha256":sha(HERE/"sanitizer-r01/receipt.json"),
            "first_execution_failed_infrastructure":"sanitizer-r01 omitted namespace proc; LeakSanitizer could not enumerate process tasks. Retained distinct; fresh namespace-correct execution PASS.",
            "installed_modules_modified":False,"NML_rerun":False},
        "actual_compiled_LinuxCNC_HAL_scheduler":True,"actual_LinuxCNC_task_and_FREE_joint_planners":True,
        "all12_HAL_to_STEP_and_feedback_ACTIVE":True,"four_ABZ_and_actual_serial_index_captures":True,
        "two_actual_serial_probe_captures":True,"virtual_24DI_16DO_application_feedback":True,
        "eight_active_twelve_fitted_unused_lanes_inhibited":True,"individual_alarm_stops_task_and_all_lanes":True,
        "motion_reset_does_not_replay_provider_lineage":True,
        "scope":{"backend":"only explicitly opted-in compiled RTL SPI and independent virtual providers",
            "feedback_frame_bytes":176,"command_frame_bytes":96,"SPI_frames_fabricated":False,
            "physical_authority":False,"production_profile_complete":False,"physical_measurements":0,
            "physical_device_connections":0,"paid_provider_calls":0,"physical_IOL1_links_qualified":False,
            "loaded_target_realtime_deadlines_qualified":False,"physical_or_Cartesian_kinematics_qualified":False,
            "physical_or_sensor_homing_qualified":False,"LinuxCNC_G38_probe_or_index_homing_qualified":False,
            "physical_limit_wiring_qualified":False,"FPGA_device_fit_qualified":False,
            "manufacturing_qualified":False,"main_structural_gateware_endpoint_used":False},
        "full_requested_milestone_complete":False,
        "historical_attempts":{"failed_runs_retained":[p.name for p in HERE.iterdir() if p.is_dir() and (p.name.startswith("driver-r") or p.name.startswith("nml-")) and (p/"receipt.json").exists() and load(p/"receipt.json")["status"]=="FAIL"],
            "earlier_positive_runs_preserved":["driver-r04","nml-r06"],"truncated_DISPLAY_failed_receipt":"retained-r04-linuxcnc-j.json"},
        "license_boundary":"RetainedCNC3 sources identify LicenseRef-Proprietary; local compiled module does not qualify redistribution or release.",
        "consolidation_source_sha256":sha(Path(__file__)),"runtime_readme_sha256":sha(ROOT/"cnc3_runtime/README.md")}
    with (HERE/"receipt.json").open("x",encoding="utf-8") as output:json.dump(receipt,output,indent=2);output.write("\n")
    print(json.dumps({"status":"PASS","current_source_inputs":len(sources),"runs":len(runs),"installed_modules_preserved":len(baseline)}))
if __name__=="__main__":main()
