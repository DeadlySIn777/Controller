"""Finalize bounded API project-binding evidence; no KiCad load/fill/save/DRC."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "project-binding-probe.json"
BASE = Path("Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2")
BASE_SHA = "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53"
PRO_SHA = "82bbd7114aa2e6f2d200252cfde3f69d2a1f3905212e6b14437e62ff742d780b"
DRU_SHA = "159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4"
GROUPS = ("settings_nm", "netclasses", "representative_effective_classes", "representative_pads")
RULE_FIELDS = {
    "m_MinClearance": "min_clearance", "m_TrackMinWidth": "min_track_width",
    "m_ViasMinAnnularWidth": "min_via_annular_width", "m_ViasMinSize": "min_via_diameter",
    "m_MinThroughDrill": "min_through_hole_diameter", "m_CopperEdgeClearance": "min_copper_edge_clearance",
    "m_HoleClearance": "min_hole_clearance", "m_HoleToHoleMin": "min_hole_to_hole",
    "m_SilkClearance": "min_silk_clearance", "m_MinSilkTextHeight": "min_text_height",
    "m_MinSilkTextThickness": "min_text_thickness", "m_MaxError": "max_error", "m_MinConn": "min_connection",
    "m_MinResolvedSpokes": "min_resolved_spokes",
}
NC_FIELDS = {"GetClearance": "clearance", "GetTrackWidth": "track_width", "GetViaDiameter": "via_diameter",
             "GetViaDrill": "via_drill", "GetDiffPairWidth": "diff_pair_width", "GetDiffPairGap": "diff_pair_gap"}
EFFECTIVE = {"/LOGIC_GND": "DOM_LOGIC,Default",
             "/motherboard_motors{slash}FIELD_GND": "DOM_FIELD_A,Default",
             "/motherboard_power_entry{slash}SBC_5V": "DOM_LOGIC,Default",
             "/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED": "DOM_FIELD_A,Default",
             "/motherboard_analog_output{slash}AO0_COM": "DOM_AO0,Default"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def walk_errors(value):
    if isinstance(value, dict):
        require("api_error" not in value, "Probe contains an API observation error")
        for child in value.values():
            walk_errors(child)
    elif isinstance(value, list):
        for child in value:
            walk_errors(child)


def validate_probe(probe, raw_project):
    require(probe["native_build_version"] == "10.0.4", "Unexpected native version")
    require(probe["board_sha256"] == BASE_SHA and probe["project_sha256"] == PRO_SHA, "Wrong probe input")
    require(probe["input_directory_unchanged"] is True, "Probe changed inputs")
    require(probe["input_directory_before_sha256"] == probe["input_directory_after_sha256"], "Input inventories differ")
    require(probe["input_directory_before_sha256"]["board.kicad_dru"] == DRU_SHA, "Wrong probe custom rules")
    require(probe["loaded_project"] is True and probe["unloaded_project_without_save"] is True, "Project load/unload failed")
    require(probe["observed_settings_equivalence"] is True and probe["different_observation_groups"] == [], "Binding difference")
    for key in ("native_refill_started", "native_drc_started", "board_saved", "project_saved"):
        require(probe[key] is False, "Probe exceeded read-only scope: " + key)
    snapshots = [probe[name] for name in ("unbound_LoadBoard", "LoadBoard_after_LoadProject_before_SetProject", "explicit_project_bound")]
    raw_rules = raw_project["board"]["design_settings"]["rules"]
    require(probe["raw_project_rules"] == raw_rules, "Stale copied raw rules")
    raw_classes = {row["name"]: row for row in raw_project["net_settings"]["classes"]}
    require(sorted(probe["raw_project_netclass_names"]) == sorted(raw_classes), "Stale class names")
    for snapshot in snapshots:
        walk_errors(snapshot)
        require(snapshot["project_is_none"] is False and snapshot["settings_manager_open"] is True
                and snapshot["settings_manager_open_not_dummy"] is True
                and snapshot["requested_project_present_in_manager"] is True, "Real sibling project not loaded")
        require(all(snapshot[key] == snapshots[0][key] for key in GROUPS), "Observed settings changed")
        ds = snapshot["settings_nm"]
        for native, raw in RULE_FIELDS.items():
            expected = raw_rules[raw] if native == "m_MinResolvedSpokes" else round(raw_rules[raw] * 1_000_000)
            require(ds[native] == expected, "Loaded design rule differs from JSON: " + native)
        require(ds["GetSmallestClearanceValue"] == 150000 and ds["GetBiggestClearanceValue"] == 1000000,
                "Unexpected aggregate clearance observations")
        classes = snapshot["netclasses"]
        require(set(classes) == set(raw_classes) and len(classes) == 28, "Netclass set differs")
        for name, row in raw_classes.items():
            require(classes[name]["GetName"] == name, "Class identity differs")
            for native, raw in NC_FIELDS.items():
                expected = round(row[raw] * 1_000_000) if raw in row else -1
                require(classes[name][native] == expected, "Loaded class value differs: " + name + "." + native)
        require(set(snapshot["representative_effective_classes"]) == set(EFFECTIVE), "Representative net set differs")
        for net, name in EFFECTIVE.items():
            require(snapshot["representative_effective_classes"][net]["GetName"] == name, "Wrong effective class: " + net)
        pads = snapshot["representative_pads"]
        require(set(pads) == {"U1001.A1", "U11012.8", "J11003.2"}, "Representative pad set differs")
        for row in pads.values():
            require(row["class"] == EFFECTIVE[row["net"]] and row["own_clearance_F_nm"] == 150000
                    and row["own_clearance_In3_nm"] == 150000, "Wrong representative pad settings")
    return {"all_observed_groups_equal": True, "raw_project_rules_match": True,
            "raw_project_netclass_values_match": True, "netclass_count": 28,
            "representative_effective_net_count": 5, "representative_pad_count": 3,
            "api_observation_errors": [], "aggregate_smallest_clearance_nm": 150000,
            "aggregate_biggest_clearance_nm": 1000000}


def main():
    inputs = {}
    def read(path):
        path = Path(path).resolve()
        data = path.read_bytes()
        inputs[str(path)] = sha(data)
        return data
    probe = json.loads(read(PROBE))
    board = Path(probe["board"])
    require(board.resolve() == (BASE / "copy/board.kicad_pcb").resolve(), "Unexpected probed path")
    current_inventory = {str(path.relative_to(board.parent)): sha(read(path))
                         for path in sorted(board.parent.rglob("*")) if path.is_file()}
    require(current_inventory == probe["input_directory_after_sha256"], "Probe inputs changed since probe")
    require(inputs[str(board.resolve())] == BASE_SHA, "Baseline board changed")
    require(inputs[str(board.with_suffix(".kicad_pro").resolve())] == PRO_SHA, "Sibling project changed")
    require(inputs[str(board.with_suffix(".kicad_dru").resolve())] == DRU_SHA, "Sibling rules changed")
    probe_script = HERE / "probe_project_binding.py"
    require(sha(read(probe_script)) == probe["probe_script_sha256"], "Probe producer changed")
    effective = validate_probe(probe, json.loads(read(board.with_suffix(".kicad_pro"))))
    source_manifest = HERE / "project-binding-source/sources.json"
    official_sources = json.loads(read(source_manifest))
    require({Path(row["path"]).name for row in official_sources} == {
        "pcbnew_scripting_helpers.cpp", "board.cpp", "pcbnew_jobs_handler.cpp", "zone_filler.cpp", "board_design_settings.cpp"},
        "Incomplete official source snapshots")
    texts = {}
    for row in official_sources:
        require(row["tag"] == "10.0.4" and row["url"].startswith("https://gitlab.com/kicad/code/kicad/-/raw/10.0.4/"), "Wrong official tag/source")
        data = read(row["path"])
        require(sha(data) == row["sha256"] and len(data) == row["bytes"], "Official source snapshot changed")
        texts[Path(row["path"]).name] = data.decode("utf-8")
    helper = texts["pcbnew_scripting_helpers.cpp"]
    require(all(token in helper for token in ("settingsManager.LoadProject( projectPath, aSetActive )", "brd->SetProject( project )",
        "bds.m_DRCEngine = std::make_shared<DRC_ENGINE>( brd, &bds )", "rules.SetExt( FILEEXT::DesignRulesFileExtension )",
        "bds.m_DRCEngine->InitEngine( rules )", "// Best efforts...")), "LoadBoard source binding logic differs")
    require("LoadBoard( aPath, true )" in texts["pcbnew_jobs_handler.cpp"], "CLI helper path differs")
    set_project = texts["board.cpp"].split("void BOARD::SetProject(", 1)[1].split("void BOARD::IncrementTimeStamp", 1)[0]
    require("m_DRCEngine" not in set_project and "GetDesignSettings().m_NetSettings = project.NetSettings()" in set_project,
            "Rebind source behavior differs")
    require("bds.m_DRCEngine->EvalRules" in texts["zone_filler.cpp"], "Filler does not use loaded rule engine")
    require("m_DRCEngine->QueryWorstConstraint" in texts["board_design_settings.cpp"], "Aggregate engine sentinel source differs")
    native_files = [Path("C:/Program Files/KiCad/10.0/bin") / name for name in ("python.exe", "_pcbnew.dll", "kicad-cli.exe")]
    native_files += [Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/pcbnew.py")]
    native_hashes = {str(path): sha(read(path)) for path in native_files}
    log_path = BASE / "drc.log"
    log = read(log_path).decode("utf-8")
    report_path = BASE / "drc.json"
    report = json.loads(read(report_path))
    require(report["kicad_version"] == probe["native_build_version"], "CLI/API native versions differ")
    require("Saved DRC Report" in log and not any(token in log.lower() for token in (
        "error loading drc rules", "error loading design rules", "error parsing", "parse error", "failed to parse", "syntax error")),
        "Baseline CLI rule parse failure or missing completion")
    tools = {}
    for name in ("net_partitions.py", "step_measure.sh"):
        path = Path("Z:/pcb-runs/claude-finish/tools") / name
        tools[str(path)] = sha(read(path))
    require("pcbnew.LoadBoard(board)" in Path(next(path for path in tools if path.endswith("net_partitions.py"))).read_text(),
            "Frozen producer load behavior differs")
    checker = Path(__file__).resolve()
    checker_hash = sha(read(checker))
    for path, expected in inputs.items():
        require(sha(Path(path).read_bytes()) == expected, "Read input changed while finalizing: " + path)
    receipt = {"schema_version": 1, "verdict": "PASS", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Observed KiCad10.0.4 sibling-project binding and settings equivalence; bounded source-backed rule initialization evidence",
        "probe": {"path": str(PROBE), "sha256": inputs[str(PROBE.resolve())], "script_path": str(probe_script),
                  "script_sha256": probe["probe_script_sha256"]},
        "input": {"board_path": str(board), "board_sha256": BASE_SHA, "project_path": str(board.with_suffix(".kicad_pro")),
                  "project_sha256": PRO_SHA, "rules_path": str(board.with_suffix(".kicad_dru")), "rules_sha256": DRU_SHA,
                  "input_directory_unchanged": True, "input_inventory": current_inventory},
        "runtime": {"native_build_version": probe["native_build_version"], "cli_report_version": report["kicad_version"],
                    "installed_file_hashes": native_hashes, "official_tag": "10.0.4"},
        "effective_settings": effective, "official_sources": official_sources,
        "rule_initialization": {"LoadBoard_implicitly_binds_sibling_project": True,
            "LoadBoard_source_initializes_sibling_custom_rules": True, "CLI_source_uses_same_LoadBoard_helper": True,
            "SetProject_source_preserves_existing_rule_engine": True, "ZONE_FILLER_source_uses_existing_rule_engine": True,
            "aggregate_rule_engine_observation_unchanged": True, "direct_rule_engine_api_exposed": False,
            "rule_init_silent_exception_catch": True, "complete_rule_equivalence_proved": False},
        "baseline_cli_evidence": {"log_path": str(log_path), "log_sha256": inputs[str(log_path.resolve())],
            "report_path": str(report_path), "report_sha256": inputs[str(report_path.resolve())],
            "saved_report": True, "rule_parse_failure_observed": False,
            "schematic_parity_skipped": "Failed to fetch schematic netlist for parity tests." in log},
        "frozen_tool_hashes": tools, "checker_path": str(checker), "checker_sha256": checker_hash,
        "refill_required_due_to_observed_binding_difference": False, "native_refill_started": False,
        "native_drc_started": False, "inputs_saved": False, "read_set_sha256": inputs,
        "limits": ["No direct compiled-rule list or every-condition rule evaluation is exposed by this Python API; aggregate observation is a bounded sentinel",
            "Official tagged source corresponds to the observed native version; this is source/runtime evidence, not a reproducible-build attestation",
            "LoadBoard silently catches rule initialization exceptions, so final candidate must retain exact sibling project/rules hashes and completed same-version CLI DRC with no rule parse failure",
            "This probe did not refill zones, rerun DRC, test schematic parity or qualify full electrical/power/SI/DFM/manufacturing readiness",
            "No new refill is required solely for an observed settings binding difference because all sampled groups match; changed inputs or native version invalidate this receipt"]}
    out = HERE / "project-binding-audit.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": receipt["verdict"], "out": str(out), "sha256": sha(out.read_bytes()),
                      "refill_required": False, "scope": receipt["scope"]}))


if __name__ == "__main__":
    main()
