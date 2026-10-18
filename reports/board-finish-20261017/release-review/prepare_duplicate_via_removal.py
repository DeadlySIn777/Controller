"""Freeze exact redundant R299 via retirement with physical equivalence proof."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "duplicate-via-r2"
RUN = ROOT / "reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299"
SOURCE = RUN / "filled-copy/board.kicad_pcb"
UNFILLED = RUN / "copy/board.kicad_pcb"
FLASH = RUN / "native-full/actual-full-refill-via-flashes.json"
GEOMETRY = RUN / "native-full/actual-full-refill-geometry.json"
REMOVE = "2193173a-497d-48d4-8833-92e9133ec64a"
SURVIVE = "217c65fd-34f7-47f6-8ca3-dceac1224ad3"
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def chunk(text, uuid):
    needle = '(uuid "' + uuid + '")'
    assert text.count(needle) == 1, uuid
    index = text.index(needle)
    start = text.rfind("(via", 0, index)
    assert start >= 0
    depth = 0
    quoted = False
    escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                assert start <= index < i
                return start, i + 1, text[start:i + 1]
    raise ValueError("Unbalanced via chunk")

pins = {str(p): sha(p.read_bytes()) for p in (SOURCE, UNFILLED, FLASH, GEOMETRY, Path(__file__))}
assert pins[str(SOURCE)] == "6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632"
assert pins[str(UNFILLED)] == "7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2"
text = SOURCE.read_bytes().decode("utf-8")
start, end, removed = chunk(text, REMOVE)
_, _, survivor = chunk(text, SURVIVE)
canonical = lambda value: re.sub(r'\(uuid "[0-9a-f-]+"\)', '(uuid "UUID")', value)
assert canonical(removed) == canonical(survivor), "All native fields other than UUID must be identical"
unfilled_text = UNFILLED.read_bytes().decode("utf-8")
assert canonical(chunk(unfilled_text, REMOVE)[2]) == canonical(removed)
assert canonical(chunk(unfilled_text, SURVIVE)[2]) == canonical(survivor)
flash = json.loads(FLASH.read_text())
assert flash["actual_all_zone_native_fill"] is True
assert flash["vias"][SURVIVE] == flash["vias"][REMOVE] == LAYERS
geometry = json.loads(GEOMETRY.read_text())
vias = {v["uuid"]: v for v in geometry["vias"]}
assert {k: v for k, v in vias[REMOVE].items() if k != "uuid"} == {k: v for k, v in vias[SURVIVE].items() if k != "uuid"}
assert vias[REMOVE]["at"] == [294.35, 67.75]
assert vias[REMOVE]["w"] == .6 and vias[REMOVE]["drill"] == .3
assert vias[REMOVE]["locked"] and vias[SURVIVE]["locked"]
# Identical circle centers, diameters, net, spans, padstack fields and actual
# flashed masks make every per-layer annulus and the plated drill volume equal.
per_layer = [{"layer": layer, "center_mm": vias[SURVIVE]["at"],
              "retired_copper_diameter_mm": .6, "surviving_copper_diameter_mm": .6,
              "retired_hole_diameter_mm": .3, "surviving_hole_diameter_mm": .3,
              "retired_annulus_subset_of_surviving": True,
              "copper_union_unchanged": True, "drill_union_unchanged": True}
             for layer in LAYERS]
assert not OUT.exists(), "Use a fresh immutable packet directory"
OUT.mkdir()
(OUT / "exact-redundant-via-to-retire.kicad-fragment").write_bytes(removed.encode("utf-8"))
(OUT / "exact-surviving-via.kicad-fragment").write_bytes(survivor.encode("utf-8"))
new_text = text[:start] + text[end:]
assert new_text.count('(uuid "' + SURVIVE + '")') == 1 and REMOVE not in new_text
assert new_text[:start] == text[:start] and new_text[start:] == text[end:]
assert canonical(chunk(new_text, SURVIVE)[2]) == canonical(survivor)
report = {
    "schema": "exact-redundant-via-physical-equivalence-retirement-v1",
    "supersedes": "duplicate-via-r1 physical proof retained; r1 read_text normalized CRLF, so only r2 authorizes byte-exact native replay",
    "verdict": "PASS_HOST_EXACT_UNION_EQUIVALENCE_NATIVE_AFTER_OPEN",
    "saved_R299_parent": {"file": str(SOURCE), "SHA256": pins[str(SOURCE)]},
    "unfilled_R299_parent": {"file": str(UNFILLED), "SHA256": pins[str(UNFILLED)]},
    "operations": [{"action": "delete_exact_chunk", "UUID": REMOVE,
                    "before_file": str(OUT / "exact-redundant-via-to-retire.kicad-fragment"),
                    "before_SHA256": sha(removed.encode()),
                    "surviving_equivalent_UUID": SURVIVE,
                    "survivor_file": str(OUT / "exact-surviving-via.kicad-fragment"),
                    "survivor_SHA256": sha(survivor.encode())}],
    "physical_union_equivalence": {"same_all_native_fields_except_UUID": True,
                                   "actual_full_native_flashes_identical": True,
                                   "per_layer": per_layer,
                                   "holes_before_two_coincident_records_after_one_same_physical_hole": True,
                                   "zero_removed_physical_copper_or_drill_volume": True,
                                   "zero_pad_zone_track_footprint_rule_or_net_changes": True},
    "explicit_via_mask_ledger_delta": {
        "retired_baseline_UUID": REMOVE, "retired_actual_mask": LAYERS,
        "retained_equivalent_UUID": SURVIVE, "retained_required_actual_mask": LAYERS,
        "every_other_original_via_UUID_and_actual_mask_retained": True,
        "retirement_reason": "One exact duplicated physical via record; retained same-net locked barrel is identical on all six copper layers",
        "post_native_obligation": "Survivor must preserve all six actual flashes and all original physical contact groups; no other retirement permitted"},
    "discrete_only_hypothetical_saved_result_SHA256": sha(new_text.encode()),
    "all_other_bytes_CRLF_UTF8_and_spacing_preserved": True,
    "PCB_emitted": False,
    "distinct_overlapping_drills_67c69f6a_and_8f6b8734_untouched": True,
    "native_after_DRC_and_full_refill_not_run": True,
    "input_SHA256": pins, "inputs_unchanged": all(sha(Path(p).read_bytes()) == v for p, v in pins.items()),
    "adopted": False, "manufacturing_ready": False,
}
(OUT / "exact-native-retirement-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"verdict": report["verdict"], "retire": REMOVE, "survive": SURVIVE,
                  "native_layers": LAYERS, "input_files_unchanged": report["inputs_unchanged"],
                  "packet": str(OUT / "exact-native-retirement-manifest.json")}))
