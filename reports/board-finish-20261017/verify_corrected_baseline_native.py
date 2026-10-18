"""Check the exact corrected board in native KiCad without refilling or saving."""
import ctypes
from ctypes import wintypes
import datetime as dt
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time

kt = ctypes.windll.kernel32
kt.GetCurrentProcess.restype = wintypes.HANDLE
kt.SetProcessAffinityMask.argtypes = (wintypes.HANDLE, ctypes.c_size_t)
assert kt.SetProcessAffinityMask(kt.GetCurrentProcess(), sum(1 << i for i in range(16, 28)))
kt.SetPriorityClass.argtypes = (wintypes.HANDLE, wintypes.DWORD)
assert kt.SetPriorityClass(kt.GetCurrentProcess(), 0x4000)
import pcbnew

H = Path(__file__).resolve().parent
OLD = H.parent / "board-finish-20261011/continuation-r2"
BASE = OLD / "combined-R753-one-full-native-fill-cached-DRC-r299"
OUT = H / "corrected-baseline-r1/native-check"
BOARD = H / "corrected-baseline-r1/native/board.kicad_pcb"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def put(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def pose(b):
    return {"footprints": {str(f.m_Uuid.AsString()): [str(f.GetReference()), str(f.GetValue()),
        int(f.GetPosition().x), int(f.GetPosition().y), float(f.GetOrientation().AsDegrees()),
        str(b.GetLayerName(f.GetLayer()))] for f in b.GetFootprints()},
        "pads": {str(p.m_Uuid.AsString()): [str(p.GetNumber()), str(p.GetNetname()),
            int(p.GetPosition().x), int(p.GetPosition().y), sorted(str(b.GetLayerName(l)) for l in p.GetLayerSet().Seq())]
            for f in b.GetFootprints() for p in f.Pads()}}


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    recipe_path = H / "corrected-baseline-r1/construction-receipt.json"
    recipe = json.loads(recipe_path.read_bytes())
    assert sha(BOARD) == recipe["corrected_SHA256"]
    expected_path = OLD / "combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json"
    expected = json.loads(expected_path.read_bytes())["copper"]
    retired = recipe["retired_exact_duplicate_via"]
    survivor = recipe["equivalent_survivor"]
    expected.pop(retired)
    oldmask_path = BASE / "native-full/saved-native-reload-via-flashes.json"
    oldmask = json.loads(oldmask_path.read_bytes())["vias"]
    oldmask.pop(retired)
    pins = {str(p): sha(p) for p in (BOARD, BOARD.with_suffix(".kicad_pro"), BOARD.with_suffix(".kicad_dru"),
        recipe_path, expected_path, oldmask_path, Path(__file__))}
    put("status.json", {"phase": "NATIVE_LOAD_RUNNING", "utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    manager = pcbnew.GetSettingsManager()
    assert manager.LoadProject(str(BOARD.with_suffix(".kicad_pro")))
    project = manager.GetProject(str(BOARD.with_suffix(".kicad_pro")))
    b = pcbnew.LoadBoard(str(BOARD))
    b.SetProject(project)
    stack = list(b.GetEnabledLayers().CuStack())
    errors = []
    state = {}
    masks = {}
    for t in b.GetTracks():
        uid = str(t.m_Uuid.AsString())
        row = {"raw_net": str(t.GetNetname()), "locked_yes": bool(t.IsLocked())}
        if isinstance(t, pcbnew.PCB_VIA):
            row.update(kind="via", at_IU=[int(t.GetPosition().x), int(t.GetPosition().y)],
                drill_IU=int(t.GetDrillValue()), diameters_IU={str(b.GetLayerName(l)): int(t.GetWidth(l)) for l in stack})
            masks[uid] = [str(b.GetLayerName(l)) for l in stack if t.FlashLayer(l)]
        else:
            row.update(kind="arc" if isinstance(t, pcbnew.PCB_ARC) else "segment",
                start_IU=[int(t.GetStart().x), int(t.GetStart().y)], end_IU=[int(t.GetEnd().x), int(t.GetEnd().y)],
                width_IU=int(t.GetWidth()), layer=str(b.GetLayerName(t.GetLayer())))
            if row["kind"] == "arc":
                row["mid_IU"] = [int(t.GetMid().x), int(t.GetMid().y)]
        assert uid not in state
        state[uid] = row
    assert set(state) == set(expected)
    for uid, row in expected.items():
        for k, value in row.items():
            if k != "chunk_sha256" and state[uid].get(k) != value:
                errors.append({"UUID": uid, "field": k, "expected": value, "actual": state[uid].get(k)})
    put("exact-Cu-errors.json", errors)
    assert not errors
    masklosses = [{"UUID": uid, "old": value, "after": masks.get(uid)} for uid, value in oldmask.items()
                  if set(masks.get(uid, [])) != set(value)]
    put("actual-via-mask-differences.json", masklosses)
    assert not masklosses
    assert set(masks[survivor]) == {str(b.GetLayerName(l)) for l in stack}
    before = json.loads((BASE / "native-full/before-native-all-FP-pad-pose.json").read_bytes())
    after = pose(b)
    assert before["pads"] == after["pads"]
    allowed = {x["UUID"] for x in recipe["BOM_changes"]}
    assert set(before["footprints"]) == set(after["footprints"])
    changed = []
    for uid, row in before["footprints"].items():
        now = after["footprints"][uid]
        if row != now:
            assert uid in allowed and row[0] == now[0] and row[2:] == now[2:]
            assert row[1] == "1803578" and now[1] == "1803277"
            changed.append(uid)
    assert set(changed) == allowed
    original_load = pcbnew.LoadBoard
    def current_board(path):
        assert Path(path).resolve() == BOARD.resolve()
        return b
    pcbnew.LoadBoard = current_board
    argv = sys.argv
    helper = Path("Z:/pcb-runs/claude-finish/tools/net_partitions.py")
    try:
        sys.argv = [str(helper), str(BOARD), str(OUT / "partitions.json")]
        runpy.run_path(str(helper), run_name="__main__")
    finally:
        pcbnew.LoadBoard = original_load
        sys.argv = argv
    parts = json.loads((OUT / "partitions.json").read_bytes())
    original = json.loads((BASE / "native-full/partitions.json").read_bytes())
    assert parts["nets"] == original["nets"]
    assert parts["api_unconnected_count"] == original["api_unconnected_count"]
    assert all(sha(Path(p)) == value for p, value in pins.items())
    put("receipt.json", {"status": "NATIVE_EXACT_CU_POSES_MASKS_AND_ALL_PAD_PARTITIONS_PASS_DRC_PENDING",
        "corrected_board_SHA256": sha(BOARD), "retired_exact_duplicate_via": retired,
        "survivor": survivor, "all_other_actual_via_masks_identical": True,
        "all_9971_pad_poses_layers_and_raw_nets_identical": True,
        "all_native_pad_partitions_identical": True, "BOM_only_changed_footprints": len(changed),
        "native_API_unconnected": parts["api_unconnected_count"], "native_fill_calls": 0,
        "native_save_calls": 0, "cached_fill_basis": "Identical physical Cu/drill union and identical 850 native zone chunks",
        "input_SHA256": pins, "elapsed_seconds": time.monotonic() - started,
        "adopted": False, "manufacturing_ready": False})
    put("status.json", {"phase": "COMPLETE_NATIVE_SCOPE_PASS_DRC_PENDING"})
    print("Corrected baseline native scope passes; full design remains unfinished.", flush=True)
    b.ClearProject()
    manager.UnloadProject(project, False)


if __name__ == "__main__":
    main()
