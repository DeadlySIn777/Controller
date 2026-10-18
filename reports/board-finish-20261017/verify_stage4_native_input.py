"""Read stage4 once in KiCad; check every discrete integer and all pad poses.

No fill, save, connectivity-result or manufacturing qualification is performed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

H = Path(__file__).resolve().parent
WORK = H / "combined-route-stage-r4"
BOARD = WORK / "native/board.kicad_pcb"
OUT = WORK / "native-input-check"


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    assert not OUT.exists()
    import ctypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    process = kernel.GetCurrentProcess()
    assert kernel.SetProcessAffinityMask(process, (1 << 16) | (1 << 17))
    assert kernel.SetPriorityClass(process, 0x4000)
    helper = H / "verify_corrected_baseline_native.py"
    spec = importlib.util.spec_from_file_location("native_input_identity_helpers", helper)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    pcbnew = A.pcbnew
    def forbidden(*args, **kwargs):
        raise AssertionError("Native input read may not fill or save")
    pcbnew.ZONE_FILLER = forbidden
    pcbnew.SaveBoard = forbidden
    expectedfile = WORK / "all-copper-expected.json"
    recipefile = WORK / "construction-receipt.json"
    posefile = H / "combined-route-stage-r1/native-full/before-native-all-FP-pad-pose.json"
    expected = json.loads(expectedfile.read_bytes())
    recipe = json.loads(recipefile.read_bytes())
    assert sha(BOARD) == expected["board_sha256"] == recipe["candidate_SHA256"] == "ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55"
    pins = {str(p): sha(p) for p in (Path(__file__), helper, BOARD, BOARD.with_suffix(".kicad_pro"), BOARD.with_suffix(".kicad_dru"), expectedfile, recipefile, posefile)}
    manager = pcbnew.GetSettingsManager()
    assert manager.LoadProject(str(BOARD.with_suffix(".kicad_pro")))
    project = manager.GetProject(str(BOARD.with_suffix(".kicad_pro")))
    b = pcbnew.LoadBoard(str(BOARD))
    b.SetProject(project)
    layers = list(b.GetEnabledLayers().CuStack())
    state = {}
    for t in b.GetTracks():
        uid = str(t.m_Uuid.AsString())
        row = {"raw_net": str(t.GetNetname()), "locked_yes": bool(t.IsLocked())}
        if isinstance(t, pcbnew.PCB_VIA):
            row.update(kind="via", at_IU=[int(t.GetPosition().x), int(t.GetPosition().y)],
                       drill_IU=int(t.GetDrillValue()), diameters_IU={str(b.GetLayerName(ly)): int(t.GetWidth(ly)) for ly in layers})
        else:
            row.update(kind="arc" if isinstance(t, pcbnew.PCB_ARC) else "segment", layer=str(b.GetLayerName(t.GetLayer())),
                       start_IU=[int(t.GetStart().x), int(t.GetStart().y)], end_IU=[int(t.GetEnd().x), int(t.GetEnd().y)], width_IU=int(t.GetWidth()))
            if row["kind"] == "arc":
                row["mid_IU"] = [int(t.GetMid().x), int(t.GetMid().y)]
        assert uid not in state
        state[uid] = row
    assert set(state) == set(expected["copper"])
    errors = [{"UUID": uid, "field": k, "expected": value, "observed": state[uid].get(k)}
              for uid, row in expected["copper"].items() for k, value in row.items()
              if k != "chunk_sha256" and state[uid].get(k) != value]
    assert not errors
    pose = A.pose(b)
    assert pose == json.loads(posefile.read_bytes())
    zonefile = WORK / "changed-zone-native-contours-expected.json"
    pins[str(zonefile)] = sha(zonefile)
    zoneexpected = json.loads(zonefile.read_bytes())
    zspec = importlib.util.spec_from_file_location("native_expected_zone_profile", H / "zone_profile_guard_r1.py")
    Z = importlib.util.module_from_spec(zspec)
    zspec.loader.exec_module(Z)
    pins[str(H / "zone_profile_guard_r1.py")] = sha(H / "zone_profile_guard_r1.py")
    from fractions import Fraction
    def ring_key(r):
        r = tuple(map(tuple, r)); rev = tuple(reversed(r)); m = min(r)
        return min([r[i:] + r[:i] for i, x in enumerate(r) if x == m] + [rev[i:] + rev[:i] for i, x in enumerate(rev) if x == m])
    def polygon_key(rings):
        return ring_key(rings[0]), tuple(sorted(ring_key(r) for r in rings[1:]))
    zones = {z.m_Uuid.AsString(): z for z in b.Zones()}
    assert len(zones) == 857 and len(zoneexpected) == 14
    zonechecks = []
    for row in zoneexpected:
        z = zones[row["UUID"]]; ps = z.Outline()
        assert ps.OutlineCount() == 1 and ps.HoleCount(0) == row["expected_holes"]
        chains = [ps.COutline(0)] + [ps.CHole(0, i) for i in range(ps.HoleCount(0))]
        actual = [[[int(c.CPoint(i).x), int(c.CPoint(i).y)] for i in range(c.PointCount())] for c in chains]
        assert polygon_key(actual) == polygon_key(row["native_rings_IU"])
        assert not z.GetIsRuleArea()
        zonechecks.append({"UUID": row["UUID"], "outer_contours": 1, "hole_count": ps.HoleCount(0),
            "native_integer_points_edges_and_hole_ownership_match": True,
            "actual_raw_net": str(z.GetNetname()), "layer": str(b.GetLayerName(z.GetLayer())),
            "minimum_thickness_IU": int(z.GetMinThickness()), "local_clearance_IU": int(z.GetLocalClearance()),
            "priority": int(z.GetAssignedPriority()), "name": str(z.GetZoneName())})
    b.ClearProject()
    manager.UnloadProject(project, False)
    assert all(sha(Path(p)) == digest for p, digest in pins.items())
    OUT.mkdir()
    result = {"status": "NATIVE_INPUT_EXACT_DISCRETE_CU_AND_POSES_PASS_FILLS_STALE_AFTER_OPEN",
              "board_SHA256": sha(BOARD), "native_discrete_items": len(state), "exact_integer_Cu_errors": errors,
              "all_9971_pad_poses_layers_raw_nets_and_2723_footprint_poses_values_unchanged": True,
              "native_Fill_calls": 0, "native_Save_calls": 0, "native_new_join_count": "UNMEASURED",
              "masks_full_actual_fill_DRC_parity_source_reference_current_SI": "OPEN_UNEXECUTED_FOR_STAGE4",
              "input_SHA256": pins, "frozen_inputs_unchanged": True, "adopted": False, "manufacturing_ready": False}
    result["all14_changed_or_new_zones_exact_native_contours_and_hole_ownership"] = zonechecks
    result["native_top_level_zones_and_rule_areas"] = 857
    (OUT / "receipt.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "native_discrete_items": len(state), "exact_integer_Cu_errors": len(errors)}))


if __name__ == "__main__":
    main()
