"""Apply reviewed BOM and physically redundant-via corrections to an isolated copy."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil

H = Path(__file__).resolve().parent
OLD = H.parent / "board-finish-20261011"
R299 = OLD / "continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299"
PARENT = R299 / "filled-copy"
HEADERS = H / "power-review/shutdown-header-correction-r1"
DUP = H / "release-review/duplicate-via-r2"
LIBS = H / "release-review/portable-libraries-r1/overlay"
OUT = H / "corrected-baseline-r1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert not OUT.exists()
    manifest_path = DUP / "exact-native-retirement-manifest.json"
    m = json.loads(manifest_path.read_bytes())
    board = PARENT / "board.kicad_pcb"
    assert sha(board) == m["saved_R299_parent"]["SHA256"]
    raw = board.read_bytes()
    helper_path = OLD / "parity-repair/root106/tools/pcbtext.py"
    spec = importlib.util.spec_from_file_location("reviewed_pcbtext", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    head, chunks, tail = helper.split(raw)
    ops = m["operations"][0]
    retired_fragment = Path(ops["before_file"]).read_bytes()
    survivor_fragment = Path(ops["survivor_file"]).read_bytes()
    assert digest(retired_fragment) == ops["before_SHA256"]
    assert digest(survivor_fragment) == ops["survivor_SHA256"]
    retired_rows = [c for c in chunks if helper.chunk_uuid(c) == ops["UUID"]]
    survivor_rows = [c for c in chunks if helper.chunk_uuid(c) == ops["surviving_equivalent_UUID"]]
    assert len(retired_rows) == len(survivor_rows) == 1
    retired, survivor = retired_rows[0], survivor_rows[0]
    assert retired.count(retired_fragment) == survivor.count(survivor_fragment) == 1
    assert retired.replace(ops["UUID"].encode(), ops["surviving_equivalent_UUID"].encode()) == survivor
    bom = json.loads((HEADERS / "construction-receipt.json").read_bytes())
    replacements = {}
    changes = []
    for op in bom["native_packet_operations"]:
        selected = [c for c in chunks if helper.chunk_uuid(c) == op["uuid"]]
        assert len(selected) == 1
        before = selected[0]
        # Native save may reformat a footprint. Change the two exact properties
        # in the genuine saved current chunk; never insert an older whole chunk.
        after = before
        for name in ("Value", "MPN"):
            old = f'(property "{name}" "1803578"'.encode()
            new = f'(property "{name}" "1803277"'.encode()
            assert after.count(old) == 1
            after = after.replace(old, new)
        assert after.replace(b'"1803277"', b'"1803578"') == before
        replacements[op["uuid"]] = after
        changes.append({"UUID": op["uuid"], "ref": op["ref"], "before_sha256": digest(before),
                        "after_sha256": digest(after), "only_Value_MPN_changed": True})
    result = head + b"".join(replacements.get(helper.chunk_uuid(c), c) for c in chunks if c != retired) + tail
    rh, rc, rt = helper.split(result)
    assert head == rh and tail == rt
    before_uid = {helper.chunk_uuid(c): c for c in chunks if helper.chunk_uuid(c)}
    after_uid = {helper.chunk_uuid(c): c for c in rc if helper.chunk_uuid(c)}
    assert set(before_uid) - set(after_uid) == {ops["UUID"]}
    assert not set(after_uid) - set(before_uid)
    unchanged = set(after_uid) - set(replacements)
    assert all(before_uid[u] == after_uid[u] for u in unchanged)
    oldzones = [c for c in chunks if helper.chunk_kind(c) == "zone"]
    newzones = [c for c in rc if helper.chunk_kind(c) == "zone"]
    assert oldzones == newzones
    OUT.mkdir()
    native = OUT / "native"
    native.mkdir()
    # Keep the matching native project/profile/rules and source hierarchy.
    for p in PARENT.iterdir():
        if p.name == "board.kicad_pcb" or p.suffix == ".lck":
            continue
        if p.is_dir():
            shutil.copytree(p, native / p.name)
        else:
            shutil.copy2(p, native / p.name)
    corrected_sheet = HEADERS / "source/motherboard_power_entry.kicad_sch"
    shutil.copy2(corrected_sheet, native / corrected_sheet.name)
    for p in LIBS.iterdir():
        target = native / p.name
        if p.is_dir():
            shutil.copytree(p, target, dirs_exist_ok=True)
        else:
            shutil.copy2(p, target)
    (native / "board.kicad_pcb").write_bytes(result)
    # The old sch.net is historical; provide the fresh BOM-corrected export.
    shutil.copy2(HEADERS / "fresh.net", native / "fresh.net")
    recipe = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "ISOLATED_CORRECTED_BASELINE_CREATED_NATIVE_VERIFICATION_PENDING",
        "parent_file": str(board), "parent_SHA256": digest(raw),
        "corrected_file": str(native / "board.kicad_pcb"), "corrected_SHA256": digest(result),
        "retired_exact_duplicate_via": ops["UUID"], "equivalent_survivor": ops["surviving_equivalent_UUID"],
        "retirement_manifest_SHA256": sha(manifest_path), "BOM_changes": changes,
        "all_other_UUID_chunks_byte_identical_count": len(unchanged),
        "all_850_actual_filled_zone_chunks_byte_identical": len(oldzones) == 850,
        "head_tail_and_all_other_unidentified_chunks_preserved": True,
        "physical_Cu_and_drill_union_unchanged": True,
        "all_existing_source_and_live_board_files_unchanged": True,
        "native_parity_DRC_masks_partitions": "PENDING", "adopted": False, "manufacturing_ready": False,
        "input_SHA256": {str(p): sha(p) for p in (board, helper_path, manifest_path,
            HEADERS / "verification-receipt.json", H / "release-review/portable-libraries-r1/receipt.json", Path(__file__))}}
    (OUT / "construction-receipt.json").write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: recipe[k] for k in ("status", "corrected_file", "corrected_SHA256")}))


if __name__ == "__main__":
    main()
