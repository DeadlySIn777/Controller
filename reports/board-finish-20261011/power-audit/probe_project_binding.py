"""One read-only KiCad API probe: no refill, DRC, save or project modification."""
import hashlib
import json
import sys
from pathlib import Path
import pcbnew

BOARD = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
PRO = BOARD.with_suffix(".kicad_pro")


def inventory(directory):
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob("*")) if path.is_file()}


def value(call):
    try:
        return plain(call())
    except Exception as exc:
        return {"api_error": str(exc)}


def plain(obj):
    if obj is None or isinstance(obj, (str, bool, int, float)):
        return obj
    if isinstance(obj, dict):
        return {str(key): plain(item) for key, item in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [plain(item) for item in obj]
    return str(obj)


def netclass(nc):
    if nc is None:
        return None
    return {name: value(lambda name=name: getattr(nc, name)())
            for name in ("GetName", "GetClearance", "GetTrackWidth", "GetViaDiameter", "GetViaDrill", "GetDiffPairWidth", "GetDiffPairGap")}


def snapshot(board, manager):
    ds = board.GetDesignSettings()
    fields = ("m_MinClearance", "m_TrackMinWidth", "m_ViasMinAnnularWidth", "m_ViasMinSize", "m_MinThroughDrill",
              "m_CopperEdgeClearance", "m_HoleClearance", "m_HoleToHoleMin", "m_SilkClearance", "m_MinSilkTextHeight",
              "m_MinSilkTextThickness", "m_MaxError", "m_MinConn", "m_MinResolvedSpokes")
    settings = {field: value(lambda field=field: getattr(ds, field)) for field in fields}
    settings.update({name: value(lambda name=name: getattr(ds, name)())
                     for name in ("GetSmallestClearanceValue", "GetBiggestClearanceValue", "GetCurrentTrackWidth", "GetDRCEpsilon")})
    classes = value(lambda: {str(name): netclass(nc) for name, nc in board.GetAllNetClasses().items()})
    names = ("/LOGIC_GND", "/motherboard_motors{slash}FIELD_GND", "/motherboard_power_entry{slash}SBC_5V",
             "/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED", "/motherboard_analog_output{slash}AO0_COM")
    effective = {name: value(lambda name=name: netclass(ds.m_NetSettings.GetEffectiveNetClass(name))) for name in names}
    pads = {}
    for footprint in board.GetFootprints():
        if footprint.GetReference() in {"U11012", "J11003", "U1001"}:
            for pad in footprint.Pads():
                if (footprint.GetReference(), pad.GetNumber()) in {("U11012", "8"), ("J11003", "2"), ("U1001", "A1")}:
                    key = f"{footprint.GetReference()}.{pad.GetNumber()}"
                    pads[key] = {"net": str(pad.GetNetname()), "class": str(pad.GetNetClassName()),
                                 "own_clearance_F_nm": value(lambda: pad.GetOwnClearance(pcbnew.F_Cu)),
                                 "own_clearance_In3_nm": value(lambda: pad.GetOwnClearance(pcbnew.In3_Cu))}
    return {"project_is_none": board.GetProject() is None, "project_pointer": str(board.GetProject()),
            "settings_manager_open": manager.IsProjectOpen(), "settings_manager_open_not_dummy": manager.IsProjectOpenNotDummy(),
            "requested_project_present_in_manager": manager.GetProject(str(PRO)) is not None,
            "settings_nm": settings, "netclasses": classes,
            "representative_effective_classes": effective, "representative_pads": pads,
            "direct_rule_engine_api_available": any("DRCEngine" in name or "RuleEngine" in name for name in dir(ds))}


def main():
    before = inventory(BOARD.parent)
    manager = pcbnew.GetSettingsManager()
    print("UNBOUND_LOAD", flush=True)
    unbound = pcbnew.LoadBoard(str(BOARD))
    a = snapshot(unbound, manager)
    print("EXPLICIT_PROJECT_LOAD", flush=True)
    loaded = manager.LoadProject(str(PRO), False)
    project = manager.GetProject(str(PRO))
    if not loaded or project is None:
        raise RuntimeError("native project loading failed")
    bound = pcbnew.LoadBoard(str(BOARD))
    prebind = snapshot(bound, manager)
    bound.SetProject(project)
    b = snapshot(bound, manager)
    print("EXPLICIT_PROJECT_BOUND", flush=True)
    unbound.ClearProject()
    bound.ClearProject()
    unloaded_without_save = manager.UnloadProject(project, False)
    after = inventory(BOARD.parent)
    keys = ("settings_nm", "netclasses", "representative_effective_classes", "representative_pads")
    different = [key for key in keys if a[key] != b[key]]
    raw = json.loads(PRO.read_text())
    result = {"evidence_class": "KiCad10.0.4 API settings binding only; no refill or DRC",
              "native_build_version": str(pcbnew.GetBuildVersion()),
              "probe_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "board": str(BOARD), "board_sha256": before[BOARD.name], "project_sha256": before[PRO.name],
              "input_directory_before_sha256": before, "input_directory_after_sha256": after,
              "input_directory_unchanged": before == after, "loaded_project": loaded,
              "unloaded_project_without_save": unloaded_without_save, "unbound_LoadBoard": a,
              "LoadBoard_after_LoadProject_before_SetProject": prebind, "explicit_project_bound": b,
              "different_observation_groups": different, "observed_settings_equivalence": not different,
              "raw_project_rules": raw["board"]["design_settings"]["rules"],
              "raw_project_netclass_names": [nc["name"] for nc in raw["net_settings"]["classes"]],
              "native_refill_started": False, "native_drc_started": False, "board_saved": False, "project_saved": False,
              "limits": ["This compares loaded design settings and netclasses, not filled geometry or CLI engine state",
                         "ZONE_FILLER custom-rule initialization must be checked separately in the exact KiCad implementation",
                         "A settings difference requires fresh explicitly project-bound native partition receipts before final same-rules connectivity qualification"]}
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"settings_equivalent": not different, "different": different, "input_directory_unchanged": before == after,
                      "unbound_project_none": a["project_is_none"], "bound_project_none": b["project_is_none"]}), flush=True)
    if before != after:
        raise RuntimeError("read-only probe changed project input directory")


if __name__ == "__main__":
    main()
