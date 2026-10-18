"""Canonicalize six equivalent pad angles; no custom land or library-ID change."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "0603-canonical-angles-r2"
REVIEW = HERE / "0603-review-r4"
BOARD = ROOT / "reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', text)
    stack = []; root = None
    for t in tokens:
        if t == "(":
            row = []
            if stack: stack[-1].append(row)
            else: root = row
            stack.append(row)
        elif t == ")": stack.pop()
        else:
            value = json.loads(t) if t.startswith('"') else t
            stack[-1].append(value)
    assert not stack
    return root

def physical(tree):
    kinds = {"attr", "duplicate_pad_numbers_are_jumpers", "fp_line", "fp_rect", "fp_text", "pad", "embedded_fonts", "model"}
    def canon(row):
        if not isinstance(row, list):
            if re.fullmatch(r'-?\d+(?:\.\d+)?', row):
                return str(Decimal(row).normalize())
            return row
        if row and row[0] in {"uuid", "net", "pinfunction", "pintype"}:
            return None
        if row and row[0] == "at" and len(row) == 4 and Decimal(row[-1]) % 180 == 0:
            row = row[:-1]
        return [v for x in row if (v := canon(x)) is not None]
    return [canon(v) for v in tree[2:] if isinstance(v, list) and v and v[0] in kinds]

def first_chunk(text, tag, target):
    i = text.index(target)
    start = text.rfind("(" + tag + " ", 0, i + len("(" + tag + " "))
    depth = 0; quote = escape = False
    for end in range(start, len(text)):
        c = text[end]
        if quote:
            if escape: escape = False
            elif c == "\\": escape = True
            elif c == '"': quote = False
        elif c == '"': quote = True
        elif c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                assert start <= i < end
                return text[start:end + 1]
    raise ValueError("Unclosed chunk")

assert not OUT.exists(); OUT.mkdir()
source = BOARD.read_bytes().decode("utf-8")
inputs = {str(BOARD): sha(BOARD), str(REVIEW / "native-normalized-review.json"): sha(REVIEW / "native-normalized-review.json"), str(Path(__file__)): sha(Path(__file__))}
assert inputs[str(BOARD)] == "6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632"
native_receipt = json.loads((REVIEW / "native-normalized-review.json").read_text())
assert native_receipt["inputs_unchanged"]
stock = REVIEW / "normalized.pretty/stock.kicad_mod"
inputs[str(stock)] = sha(stock)
stock_physics = physical(parse(stock.read_text()))
operations = []
result = source
for row in native_receipt["rows"]:
    ref = row["ref"]
    normalized = REVIEW / ("normalized.pretty/" + ref + ".kicad_mod")
    inputs[str(normalized)] = sha(normalized)
    assert physical(parse(normalized.read_text())) == stock_physics, "All manufactured lands and graphics must match stock after central-symmetry orientation equivalence"
    original = first_chunk(source, "footprint", '(property "Reference" "' + ref + '"')
    updated = original
    changes = []
    for change in row["canonical_pad_orientation_only_native_equivalence"]:
        assert change["actual_native_Cu_mask_paste_polygon_vertices_exact"]
        pin = change["pin"]
        oldpad = first_chunk(original, "pad", '(pad "' + pin + '"')
        at = next(v for v in parse(oldpad) if isinstance(v, list) and v[0] == "at")
        # Preserve every local coordinate and all raw bytes except explicit angle.
        before = "(at " + " ".join(at[1:]) + ")"
        after = "(at " + " ".join(at[1:3]) + " " + str(int(change["after_angle"])) + ")"
        assert oldpad.count(before) == 1
        newpad = oldpad.replace(before, after)
        assert updated.count(oldpad) == 1
        updated = updated.replace(oldpad, newpad)
        changes.append({"pin": pin, "before": before, "after": after, "native_actual_Cu_mask_paste_vertex_sets_exact": True})
    before_file = OUT / (ref + ".before-exact-footprint")
    after_file = OUT / (ref + ".after-canonical-angle-footprint")
    before_file.write_bytes(original.encode()); after_file.write_bytes(updated.encode())
    assert source.count(original) == result.count(original) == 1
    result = result.replace(original, updated)
    operations.append({"action": "replace_exact_footprint_chunk", "ref": ref,
                       "UUID": next(v[1] for v in parse(original) if isinstance(v, list) and v[0] == "uuid"),
                       "before_file": str(before_file), "before_SHA256": sha(before_file),
                       "after_file": str(after_file), "after_SHA256": sha(after_file),
                       "changes": changes, "source_and_native_lib_id_unchanged": "Resistor_SMD:R_0603_1608Metric"})
report = {"verdict": "PASS_NATIVE_EXACT_CU_MASK_PASTE_AND_STOCK_GEOMETRY_EQUIVALENCE_FULL_AFTER_DRC_OPEN",
          "parent_board": str(BOARD), "parent_SHA256": inputs[str(BOARD)], "operations": operations,
          "actual_dimensional_or_manufacturing_changes": [],
          "why_no_custom_footprint_variant": "All stock physical lands, silk, courtyard, Fab, model and intrinsic footprint fields match. Only redundant180degree pad orientation relative to footprint caused mismatch. A custom land variant would falsely imply different geometry.",
          "unchanged": ["all pad/footprint UUIDs", "all pad numbers and nets", "all copper/mask/paste native polygon vertex sets", "pad center/size/shape/radius", "footprint positions/rotations/sides", "all tracks/vias/zones/rules", "all source values/MPNs/footprint IDs", "stock library and all portable library entries"],
          "source_parity": "No schematic or library ID/value/net change; exact prevalidated source membership preserved. Full-current matching-stem native parity to rerun on combined staged board.",
          "hypothetical_exact_saved_result_SHA256": hashlib.sha256(result.encode()).hexdigest(),
          "PCB_emitted": False, "native_full_board_refill_DRC_not_run": True,
          "input_sha256": inputs, "inputs_unchanged": all(sha(Path(p)) == v for p, v in inputs.items()),
          "adopted": False, "manufacturing_ready": False}
(OUT / "exact-native-angle-metadata-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"verdict": report["verdict"], "refs": [r["ref"] for r in operations], "changes": 6,
                  "physical_changes": 0, "source_lib_id_changes": 0, "inputs_unchanged": report["inputs_unchanged"]}))
