"""Compose reviewed no-via bridges and equivalent source-grid cleanup separately.

Never change the running stage1 input or claim its stale fill is stage2 evidence.
"""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode = True

H = Path(__file__).resolve().parent
BASE = H / "combined-route-stage-r1/native"
OUT = H / "combined-route-stage-r2"
PACKET = H / "release-review/owned-cap-body-bridges-r5/actual109-native-source-rule-recheck/exact-reviewed-additive-packet.json"
GRID = H / "power-review/late-power-schematic-grid-r3"
BOARD_SHA = "758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad"
PACKET_SHA = "88e472b78794b3cc82da3edf53b3a8ab6f6d77dcfe352c81552dfdd74091dbc8"


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    assert not OUT.exists()
    assert sha(BASE / "board.kicad_pcb") == BOARD_SHA
    assert sha(PACKET) == PACKET_SHA
    spec = importlib.util.spec_from_file_location("stage1_exact_helpers", H / "assemble_next_native_stage.py")
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    helperfile = H.parent / "board-finish-20261011/parity-repair/root106/tools/pcbtext.py"
    spec = importlib.util.spec_from_file_location("exact_pcbtext_stage2", helperfile)
    C = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(C)
    packet = json.loads(PACKET.read_bytes())
    assert packet["status"] == "ACTUAL109_NATIVE_RULES_AND_ACTUAL_NATIVE_SOURCE_OUTLINES_REPLACE_SEED_RULE_GATE"
    assert (packet["new_bridges"], packet["new_nets"], packet["new_tracks"]) == (2, 2, 9)
    assert packet["inputs_unchanged"] and not packet["native_fill_calls"] and not packet["native_save_calls"]
    pins = {str(p): sha(p) for p in (Path(__file__), PACKET, helperfile, H / "assemble_next_native_stage.py")}
    for path, digest in packet["all_input_SHA256"].items():
        assert sha(path) == digest
        pins[path] = digest
    raw = (BASE / "board.kicad_pcb").read_bytes()
    head, chunks, tail = C.split(raw)
    old = {C.chunk_uuid(c): c for c in chunks if C.chunk_uuid(c)}
    parent_expected = H / "combined-route-stage-r1/all-copper-expected.json"
    expected = json.loads(parent_expected.read_bytes())
    assert sha(parent_expected) == "053a5edc92f6134f7dc9589d2fa3adf9f9f0bd664f12c01e617d0fd7feb4be8e"
    pins[str(parent_expected)] = sha(parent_expected)
    expected = copy.deepcopy(expected)
    adds = {}
    for op in packet["exact_additive_operations"]:
        assert op["action"] == "add_exact_segment"
        path = Path(op["file"])
        assert sha(path) == op["SHA256"]
        pins[str(path)] = sha(path)
        chunk = path.read_bytes()
        uid = op["UUID"]
        assert C.chunk_uuid(chunk) == uid and C.chunk_kind(chunk) == "segment"
        assert uid not in old and uid not in adds
        adds[uid] = chunk
        expected["copper"][uid] = A.cu_row(chunk, "segment")
    assert len(adds) == 9
    newraw = head + b"".join(chunks) + b"".join(adds.values()) + tail
    nh, nc, nt = C.split(newraw)
    current = {C.chunk_uuid(c): c for c in nc if C.chunk_uuid(c)}
    assert head == nh and tail == nt and set(current) == set(old) | set(adds)
    assert all(current[uid] == chunk for uid, chunk in old.items())
    assert [c for c in chunks if C.chunk_kind(c) == "zone"] == [c for c in nc if C.chunk_kind(c) == "zone"]
    gridreceipt = GRID / "verification-receipt.json"
    fixed = json.loads(gridreceipt.read_bytes())
    assert fixed["verdict"] == "PASS_NATIVE_EXPORT_EXACT_SEMANTICS_AND_22_GRID_WARNINGS_REMOVED"
    source = Path(fixed["changed_source_file"])
    assert sha(source) == fixed["changed_source_sha256"]
    assert sha(BASE / source.name) == fixed["original_source_sha256"]
    assert fixed["all_components_fields_pin_roles_and_exact_raw_node_membership_unchanged"]
    pins[str(source)] = sha(source)
    pins[str(gridreceipt)] = sha(gridreceipt)
    before_files = {str(p.relative_to(BASE)): sha(p) for p in BASE.rglob("*") if p.is_file() and p.suffix != ".lck"}
    OUT.mkdir()
    native = OUT / "native"
    shutil.copytree(BASE, native, ignore=shutil.ignore_patterns("*.lck", "__pycache__"))
    (native / "board.kicad_pcb").write_bytes(newraw)
    shutil.copyfile(source, native / source.name)
    changed = {name for name, digest in before_files.items() if sha(native / name) != digest}
    assert changed == {"board.kicad_pcb", source.name}
    assert all(sha(BASE / name) == digest for name, digest in before_files.items())
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    expected["board_sha256"] = sha(native / "board.kicad_pcb")
    (OUT / "all-copper-expected.json").write_text(json.dumps(expected, indent=1) + "\n", encoding="utf-8")
    record = {"status": "REVIEWED_BRIDGES_AND_EQUIVALENT_SOURCE_GRID_COMPOSED_NATIVE_AFTER_REQUIRED",
              "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "parent_SHA256": BOARD_SHA,
              "candidate_SHA256": expected["board_sha256"], "new_segments": 9, "new_vias": 0,
              "old_Cu_or_pad_or_zone_chunks_changed": 0, "source_only_changed_file": source.name,
              "source_semantic_change": False, "all_other_project_files_preserved": True,
              "stale_cached_zone_chunks": 850, "new_revision_native_join_count": "UNMEASURED",
              "separate_stage1_native_job_untouched": True,
              "future_native_full_refill_mask_source_reference_parity_current_SI": "REQUIRED_UNEXECUTED",
              "new_source_grid_ERC_evidence": str(gridreceipt), "native_jobs_launched": 0,
              "input_SHA256": pins, "parent_native_file_SHA256": before_files,
              "adopted": False, "manufacturing_ready": False}
    (OUT / "construction-receipt.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "candidate_SHA256": record["candidate_SHA256"], "new_segments": 9, "new_vias": 0}))


if __name__ == "__main__":
    main()
