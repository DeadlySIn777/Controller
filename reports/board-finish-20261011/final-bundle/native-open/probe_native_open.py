"""Read-only native measured-board versus motherboard alias settings comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew

from open_check_shared import inventory, require


def plain(obj):
    if obj is None or isinstance(obj, (str, bool, int, float)):
        return obj
    if isinstance(obj, dict):
        return {str(key): plain(item) for key, item in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [plain(item) for item in obj]
    return str(obj)


def value(call):
    try:
        return plain(call())
    except Exception as exc:
        return {"api_error": str(exc)}


def netclass(nc):
    if nc is None:
        return None
    return {name: value(lambda name=name: getattr(nc, name)()) for name in
            ("GetName", "GetClearance", "GetTrackWidth", "GetViaDiameter", "GetViaDrill", "GetDiffPairWidth", "GetDiffPairGap")}


def snapshot(board, manager, project_path):
    ds = board.GetDesignSettings()
    fields = ("m_MinClearance", "m_TrackMinWidth", "m_ViasMinAnnularWidth", "m_ViasMinSize", "m_MinThroughDrill",
              "m_CopperEdgeClearance", "m_HoleClearance", "m_HoleToHoleMin", "m_SilkClearance", "m_MinSilkTextHeight",
              "m_MinSilkTextThickness", "m_MaxError", "m_MinConn", "m_MinResolvedSpokes")
    settings = {field: value(lambda field=field: getattr(ds, field)) for field in fields}
    settings.update({name: value(lambda name=name: getattr(ds, name)()) for name in
                     ("GetSmallestClearanceValue", "GetBiggestClearanceValue", "GetCurrentTrackWidth", "GetDRCEpsilon")})
    classes = value(lambda: {str(name): netclass(nc) for name, nc in board.GetAllNetClasses().items()})
    names = ("/LOGIC_GND", "/motherboard_motors{slash}FIELD_GND", "/motherboard_power_entry{slash}SBC_5V",
             "/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED", "/motherboard_analog_output{slash}AO0_COM")
    effective = {name: value(lambda name=name: netclass(ds.m_NetSettings.GetEffectiveNetClass(name))) for name in names}
    pads = {}
    wanted = {("U11012", "8"), ("J11003", "2"), ("U1001", "A1")}
    for footprint in board.GetFootprints():
        if footprint.GetReference() not in {ref for ref, pad in wanted}:
            continue
        for pad in footprint.Pads():
            if (footprint.GetReference(), pad.GetNumber()) in wanted:
                pads[f"{footprint.GetReference()}.{pad.GetNumber()}"] = {
                    "net": str(pad.GetNetname()), "class": str(pad.GetNetClassName()),
                    "own_clearance_F_nm": value(lambda: pad.GetOwnClearance(pcbnew.F_Cu)),
                    "own_clearance_In3_nm": value(lambda: pad.GetOwnClearance(pcbnew.In3_Cu))}
    return {"loaded_board_filename": str(board.GetFileName()), "project_is_none": board.GetProject() is None,
            "settings_manager_open": manager.IsProjectOpen(), "settings_manager_open_not_dummy": manager.IsProjectOpenNotDummy(),
            "requested_project_present_in_manager": manager.GetProject(str(project_path)) is not None,
            "settings_nm": settings, "netclasses": classes,
            "representative_effective_classes": effective, "representative_pads": pads}


def inspect(path, manager):
    path = path.resolve()
    project_path, rules_path = path.with_suffix(".kicad_pro"), path.with_suffix(".kicad_dru")
    before = inventory(path.parent)
    raw = json.loads(project_path.read_text(encoding="utf-8"))
    print("NATIVE_LOAD " + path.name, flush=True)
    # Intentionally rely on the actual LoadBoard sibling-stem path, with no manual LoadProject/SetProject.
    board = pcbnew.LoadBoard(str(path))
    require(board is not None, "Native board load failed")
    observations = snapshot(board, manager, project_path)
    project = manager.GetProject(str(project_path))
    require(project is not None, "Native sibling project was not found")
    board.ClearProject()
    unloaded = manager.UnloadProject(project, False)
    del board
    after = inventory(path.parent)
    return {"board_path": str(path), "project_path": str(project_path), "rules_path": str(rules_path),
            "directory_before_sha256": before, "directory_after_sha256": after, "input_directory_unchanged": before == after,
            "raw_project_meta_filename": raw["meta"]["filename"], "snapshot": observations,
            "project_unloaded_without_save": bool(unloaded)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--measured-board", type=Path, required=True)
    ap.add_argument("--alias-board", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    output = args.out.resolve()
    require(not output.exists() and not output.is_relative_to(args.measured_board.resolve().parent)
            and not output.is_relative_to(args.alias_board.resolve().parent),
            "Native report must be a new file outside both input directories")
    manager = pcbnew.GetSettingsManager()
    result = {"schema_version": 1, "native_build_version": str(pcbnew.GetBuildVersion()),
              "measured": inspect(args.measured_board, manager), "alias": inspect(args.alias_board, manager),
              "probe_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "native_refill_started": False, "native_drc_started": False, "board_saved": False, "project_saved": False, "GUI_started": False}
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("NATIVE_OPEN_OBSERVATIONS_WRITTEN", flush=True)


if __name__ == "__main__":
    main()
