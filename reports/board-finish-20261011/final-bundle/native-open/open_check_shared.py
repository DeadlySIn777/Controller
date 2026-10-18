"""Pure host/native-open observation validation; no pcbnew import."""
import hashlib
import json
from pathlib import Path

C05_SHA = "95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d"
PRO_SHA = "82bbd7114aa2e6f2d200252cfde3f69d2a1f3905212e6b14437e62ff742d780b"
DRU_SHA = "159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4"
GROUPS = ("settings_nm", "netclasses", "representative_effective_classes", "representative_pads")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(directory):
    directory = Path(directory).resolve()
    result = {}
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), "Alias input contains a symlink")
        if path.is_file():
            require(path.resolve().is_relative_to(directory), "Alias input escapes directory")
            result[path.relative_to(directory).as_posix()] = sha(path)
    require(bool(result), "Empty native input directory")
    return result


def no_api_errors(value):
    if isinstance(value, dict):
        require("api_error" not in value, "Native observation contains an API error")
        for item in value.values():
            no_api_errors(item)
    elif isinstance(value, list):
        for item in value:
            no_api_errors(item)


def require_native_evidence(qualification, status, proof):
    require(qualification.get("verdict") == "PASS_EXPERIMENTAL_NATIVE_EVIDENCE"
            and qualification["selection"]["sha256"] == C05_SHA,
            "Bundle is not explicitly qualified exact c05")
    require(qualification.get("adopted") is False and qualification.get("manufacturing_ready") is False,
            "Experimental bundle scope differs")
    require(status.get("phase") == "COMPLETE" and status.get("verdict") == "PASS"
            and proof.get("verdict") == "PASS" and proof.get("candidate_sha256") == C05_SHA,
            "c05 native measurement is incomplete, failed or for another candidate")
    require(type(proof["connectivity"]["lost"]) is int and proof["connectivity"]["lost"] == 0
            and proof["connectivity"]["verdict"] == "PASS" and proof["drc"]["after"]["errors"] == 0,
            "c05 connectivity/DRC did not pass")


def validate_report(report, expected_native_version="10.0.4"):
    require(report.get("schema_version") == 1 and report.get("native_build_version") == expected_native_version,
            "Unexpected native-open report schema/runtime")
    for role, names in (("measured", ("board.kicad_pcb", "board.kicad_pro", "board.kicad_dru")),
                        ("alias", ("motherboard.kicad_pcb", "motherboard.kicad_pro", "motherboard.kicad_dru"))):
        context = report[role]
        before, after = context["directory_before_sha256"], context["directory_after_sha256"]
        require(before == after and context["input_directory_unchanged"] is True,
                role + " entire input directory changed")
        for name, digest in zip(names, (C05_SHA, PRO_SHA, DRU_SHA)):
            require(before.get(name) == digest, role + " exact source/project/rules SHA differs")
        board = Path(context["board_path"]).resolve()
        require(board.name == names[0] and board.with_suffix(".kicad_pro") == Path(context["project_path"]).resolve()
                and board.with_suffix(".kicad_dru") == Path(context["rules_path"]).resolve(),
                role + " does not use the required sibling stem")
        require(context["raw_project_meta_filename"] == "board.kicad_pro",
                "Original .pro meta.filename was rewritten")
        require(context["project_unloaded_without_save"] is True, role + " project was not unloaded without saving")
        snapshot = context["snapshot"]
        no_api_errors(snapshot)
        require(snapshot["project_is_none"] is False and snapshot["settings_manager_open"] is True
                and snapshot["settings_manager_open_not_dummy"] is True
                and snapshot["requested_project_present_in_manager"] is True,
                role + " did not load a real non-dummy sibling project")
        require(Path(snapshot["loaded_board_filename"]).resolve() == board,
                role + " loaded board filename differs")
        require(len(snapshot["netclasses"]) == 28, "Native netclass set differs")
        require(len(snapshot["representative_effective_classes"]) == 5
                and set(snapshot["representative_pads"]) == {"U1001.A1", "U11012.8", "J11003.2"},
                "Native effective-net/pad observation coverage differs")
        require(snapshot["settings_nm"]["GetSmallestClearanceValue"] == 150000
                and snapshot["settings_nm"]["GetBiggestClearanceValue"] == 1000000,
                "Native aggregate clearance differs")
    measured, alias = report["measured"]["snapshot"], report["alias"]["snapshot"]
    differences = [key for key in GROUPS if measured[key] != alias[key]]
    require(not differences, "Measured/alias effective settings differ: " + repr(differences))
    for key in ("native_refill_started", "native_drc_started", "board_saved", "project_saved", "GUI_started"):
        require(report[key] is False, "Native-open check exceeded read-only scope")
    return {"verdict": "PASS", "scope": "actual native LoadBoard of exact motherboard stem alias; no fill/DRC/save/GUI",
            "board_sha256": C05_SHA, "project_sha256": PRO_SHA, "rules_sha256": DRU_SHA,
            "native_build_version": report["native_build_version"], "different_observation_groups": differences,
            "observed_alias_settings_equivalence": True, "alias_directory_unchanged": True,
            "meta_filename_preserved": "board.kicad_pro", "real_non_dummy_sibling_project": True,
            "complete_custom_rule_equivalence_proved": False,
            "limits": ["No full custom-rule condition enumeration or electrical/routing qualification",
                       "No GUI editor interaction was exercised; the check opens via native pcbnew LoadBoard",
                       "Stored source cached fills remain unchanged; no fresh stored fill is established"]}
