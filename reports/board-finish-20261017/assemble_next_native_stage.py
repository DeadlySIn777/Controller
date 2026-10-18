"""Compose only exact reviewed sparse operations; full native AFTER is required."""
from pathlib import Path
from decimal import Decimal
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil

H = Path(__file__).resolve().parent
OLD = H.parent / "board-finish-20261011"
BASE = H / "corrected-baseline-r1/native"
OUT = H / "combined-route-stage-r1"
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def digest(x):
    return hashlib.sha256(x).hexdigest()


def integer(value):
    x = Decimal(value.decode()) * 1000000
    assert x == x.to_integral_value()
    return int(x)


def cu_row(chunk, kind):
    def values(tag, n):
        hit = re.search(rb'\(' + tag.encode() + rb' ([^()]*)\)', chunk)
        assert hit
        v = hit[1].split()
        assert len(v) == n
        return [integer(x) for x in v]
    net = re.search(rb'\(net "((?:[^"\\]|\\.)*)"\)', chunk)
    assert net
    row = {"raw_net": json.loads(b'"' + net[1] + b'"'), "locked_yes": b"(locked yes)" in chunk,
           "kind": kind, "chunk_sha256": digest(chunk)}
    if kind == "via":
        row.update(at_IU=values("at", 2), drill_IU=values("drill", 1)[0],
                   diameters_IU={ly: values("size", 1)[0] for ly in LAYERS})
    else:
        row.update(start_IU=values("start", 2), end_IU=values("end", 2), width_IU=values("width", 1)[0],
                   layer=re.search(rb'\(layer "([^"]+)"\)', chunk)[1].decode())
        if kind == "arc":
            row["mid_IU"] = values("mid", 2)
    return row


def main():
    assert not OUT.exists()
    helper_path = OLD / "parity-repair/root106/tools/pcbtext.py"
    spec = importlib.util.spec_from_file_location("exact_pcbtext", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    native_check = H / "corrected-baseline-r1/native-check/receipt.json"
    check = json.loads(native_check.read_bytes())
    board = BASE / "board.kicad_pcb"
    assert sha(board) == check["corrected_board_SHA256"]
    raw = board.read_bytes()
    head, chunks, tail = helper.split(raw)
    index = {helper.chunk_uuid(c): c for c in chunks if helper.chunk_uuid(c)}
    adds = {}
    deletes = {}
    replacements = {}
    pins = {str(p): sha(p) for p in (board, helper_path, native_check, Path(__file__))}
    operations = []
    def read_manifest(p):
        pins[str(p)] = sha(p)
        return json.loads(p.read_bytes())
    def load_chunk(p, expected):
        p = Path(p)
        assert sha(p) == expected
        pins[str(p)] = sha(p)
        return p.read_bytes()
    ao = read_manifest(H / "power-review/AO1-R28-current-host-gates-r4/current-gates-and-minimal-sparse-packet.json")
    assert ao["verdict"] == "R28_CURRENT_FULL_R299_ORIGINAL_SCOPED_HOST_GATES_PASS_NATIVE_AFTER_CURRENT_SI_OPEN"
    for op in ao["operations"]:
        chunk = load_chunk(op["exact_chunk_file"], op["exact_chunk_SHA256"])
        uid = op["UUID"]
        assert helper.chunk_uuid(chunk) == uid
        if op["action"] == "remove":
            assert index[uid] == chunk
            deletes[uid] = chunk
        else:
            assert op["action"] == "add" and uid not in index and uid not in adds
            adds[uid] = chunk
        operations.append({"group": "AO1_R28", "action": op["action"], "UUID": uid, "chunk_SHA256": digest(chunk)})
    route = read_manifest(H / "routing/actual-R299-original-frozen-R310-candidate-r2/native-add-only-manifest.json")
    for op in route["operations"]:
        uid = op["UUID"]
        chunk = load_chunk(op["file"], op["SHA256"])
        assert uid not in index and uid not in adds and helper.chunk_uuid(chunk) == uid
        adds[uid] = chunk
        operations.append({"group": "R310", "action": "add", "UUID": uid, "chunk_SHA256": digest(chunk)})
    holes = read_manifest(H / "power-review/overlapping-scl-holes-r1/repair-receipt.json")
    read_manifest(H / "release-review/overlap-retirement-independent-r1/receipt.json")
    removed = holes["retire_original_via"]
    retired_file = H / "power-review/overlapping-scl-holes-r1" / ("filled-copy-" + removed + ".exact-retirement-chunk")
    assert index[removed] == retired_file.read_bytes()
    pins[str(retired_file)] = sha(retired_file)
    deletes[removed] = index[removed]
    operations.append({"group": "overlap_drill_repair", "action": "remove", "UUID": removed, "chunk_SHA256": digest(index[removed])})
    stub = holes["added_stub"]
    stub_file = retired_file.parent / (stub["uuid"] + ".add-track-chunk")
    chunk = load_chunk(stub_file, stub["file_sha256"])
    assert stub["uuid"] not in index and stub["uuid"] not in adds
    adds[stub["uuid"]] = chunk
    operations.append({"group": "overlap_drill_repair", "action": "add", "UUID": stub["uuid"], "chunk_SHA256": digest(chunk)})
    angles = read_manifest(H / "release-review/0603-canonical-angles-r2/exact-native-angle-metadata-manifest.json")
    for op in angles["operations"]:
        before = load_chunk(op["before_file"], op["before_SHA256"])
        after = load_chunk(op["after_file"], op["after_SHA256"])
        uid = op["UUID"]
        assert index[uid].count(before) == 1 and uid not in deletes and uid not in adds
        replacements[uid] = index[uid].replace(before, after)
        operations.append({"group": "equivalent_pad_angle_metadata", "action": "replace", "UUID": uid,
            "before_SHA256": digest(before), "after_SHA256": digest(after)})
    assert len(deletes) == 5 and len(adds) == 27 and len(replacements) == 3
    result = head + b"".join(replacements.get(helper.chunk_uuid(c), c) for c in chunks if helper.chunk_uuid(c) not in deletes) + b"".join(adds.values()) + tail
    rh, rc, rt = helper.split(result)
    assert head == rh and tail == rt
    afterindex = {helper.chunk_uuid(c): c for c in rc if helper.chunk_uuid(c)}
    assert set(afterindex) == (set(index) - set(deletes)) | set(adds)
    retained = set(index) - set(deletes) - set(replacements)
    assert all(afterindex[u] == index[u] for u in retained)
    assert [c for c in chunks if helper.chunk_kind(c) == "zone"] == [c for c in rc if helper.chunk_kind(c) == "zone"]
    copper = {helper.chunk_uuid(c): cu_row(c, helper.chunk_kind(c)) for c in rc if helper.chunk_kind(c) in ("via", "segment", "arc")}
    knownnets = {cu_row(c, helper.chunk_kind(c))["raw_net"] for c in chunks if helper.chunk_kind(c) in ("via", "segment", "arc")}
    # A previously unrouted net can exist only on pads. Bind its literal native
    # spelling as well; never normalize slash aliases into a new physical net.
    poses = OLD / "continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json"
    pins[str(poses)] = sha(poses)
    knownnets.update(row[1] for row in json.loads(poses.read_bytes())["pads"].values())
    assert {row["raw_net"] for row in copper.values()} <= knownnets
    OUT.mkdir()
    native = OUT / "native"
    shutil.copytree(BASE, native)
    (native / "board.kicad_pcb").write_bytes(result)
    (OUT / "filled-copy").mkdir()
    for p in native.iterdir():
        if p.name == "board.kicad_pcb":
            continue
        if p.is_dir():
            shutil.copytree(p, OUT / "filled-copy" / p.name)
        else:
            shutil.copy2(p, OUT / "filled-copy" / p.name)
    newordinary = [u for u in adds if copper[u]["kind"] == "via"]
    assert len(newordinary) == 2
    original = OLD / "continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299"
    mask = original / "native-full/actual-full-refill-via-flashes.json"
    dup = json.loads((H / "release-review/duplicate-via-r2/exact-native-retirement-manifest.json").read_bytes())
    retirements = {dup["operations"][0]["UUID"]: dup["operations"][0]["surviving_equivalent_UUID"],
                   removed: holes["retained_original_via"]}
    expected = {"board_sha256": digest(result), "copper": copper,
        "baseline_full_native_mask_file": str(mask), "baseline_full_native_mask_SHA256": sha(mask),
        "authorized_removed_actual_full_R157_via_UUIDs": list(retirements),
        "exact_physical_retirement_survivors": retirements, "required_NEW_ordinary_all6": newordinary}
    (OUT / "all-copper-expected.json").write_text(json.dumps(expected, indent=1) + "\n", encoding="utf-8")
    assert all(sha(Path(p)) == h for p, h in pins.items())
    receipt = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "COMPOSED_ISOLATED_DIAGNOSTIC_NATIVE_FULL_AFTER_REQUIRED", "parent_SHA256": sha(board),
        "candidate_SHA256": digest(result), "operations": operations, "retained_original_chunks_exact": len(retained),
        "tracks_added": len(adds) - 2, "vias_added": 2, "tracks_removed": 4, "vias_removed_this_stage": 1,
        "footprints_with_only_equivalent_pad_angle_changes": 3, "all850_zone_chunks_exact_but_cache_stale_for_new_geometry": True,
        "old_via_retirements_including_parent_exact_duplicate": retirements,
        "source_names_pads_FPposes_profile_rules_and_other_native_chunks_preserved": True,
        "expected_native_copper_SHA256": sha(OUT / "all-copper-expected.json"),
        "input_SHA256": pins, "parent_raw_R763_failures": "RETAINED_NOT_WAIVED", "native_after": "PENDING",
        "actual_missing_joins_on_this_new_revision": "UNMEASURED", "adopted": False, "manufacturing_ready": False}
    (OUT / "construction-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "candidate_SHA256", "tracks_added", "vias_added", "tracks_removed", "vias_removed_this_stage")}))


if __name__ == "__main__":
    main()
