"""Native normalized export of three small footprint objects only; no PCB load."""
from pathlib import Path
import ctypes
import hashlib
import json
import re
import pcbnew

kernel = ctypes.windll.kernel32
kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), ctypes.c_size_t(sum(1 << i for i in range(16, 28))))
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "0603-review-r4"
SOURCE = ROOT / "reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb"
LIB = Path("C:/Program Files/KiCad/10.0/share/kicad/footprints/Resistor_SMD.pretty")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def exact_chunk(text, reference):
    needle = '(property "Reference" "' + reference + '"'
    assert text.count(needle) == 1
    target = text.index(needle)
    start = text.rfind("(footprint ", 0, target)
    quoted = escaped = False
    depth = 0
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
                assert start < target < i
                return text[start:i + 1]
    raise ValueError("Unclosed footprint")

assert not OUT.exists()
OUT.mkdir()
extracts = OUT / "extracts.pretty"
normal = OUT / "normalized.pretty"
extracts.mkdir(); normal.mkdir()
native_io = pcbnew.PCB_IO_KICAD_SEXPR()
inputs = {str(SOURCE): sha(SOURCE), str(LIB / "R_0603_1608Metric.kicad_mod"): sha(LIB / "R_0603_1608Metric.kicad_mod"), str(Path(__file__)): sha(Path(__file__))}
text = SOURCE.read_bytes().decode("utf-8")
tiny_board = OUT / "three-retained-footprints.kicad_pcb"
tiny_board.write_bytes((text[:text.index('(footprint ')] + '\n'.join(exact_chunk(text, ref) for ref in ("R11054", "R9026", "R10007")) + '\n)').encode())
print("LOAD_THREE_OBJECT_BOARD", flush=True)
board = pcbnew.LoadBoard(str(tiny_board))
assert len(list(board.GetFootprints())) == 3
rows = []
def polygon_signature(pad, layer):
    poly = pad.GetEffectivePolygon(layer)
    return sorted(sorted((poly.COutline(i).CPoint(j).x, poly.COutline(i).CPoint(j).y)
                         for j in range(poly.COutline(i).PointCount()))
                  for i in range(poly.OutlineCount()))
for ref in ("R11054", "R9026", "R10007"):
    source = exact_chunk(text, ref)
    file = extracts / (ref + ".kicad_mod")
    file.write_bytes(source.encode())
    fp = next(f for f in board.GetFootprints() if f.GetReference() == ref)
    assert fp
    print("NORMALIZE", ref, flush=True)
    original = {"pose_IU": [fp.GetPosition().x, fp.GetPosition().y], "angle_deg": fp.GetOrientationDegrees(),
                "layer": pcbnew.LayerName(fp.GetLayer()), "pads": []}
    for p in fp.Pads():
        original["pads"].append({"number": p.GetNumber(), "position_IU": [p.GetPosition().x, p.GetPosition().y],
                                 "angle_deg": p.GetOrientationDegrees(), "size_IU": [p.GetSize().x, p.GetSize().y],
                                 "drill_IU": [p.GetDrillSize().x, p.GetDrillSize().y],
                                 "shape": int(p.GetShape()), "roundrect_ratio": p.GetRoundRectRadiusRatio(),
                                 "layers": p.GetLayerSet().FmtBin()})
    fp.NormalizeForCompare()
    fp.SetFPIDAsString("CNC_Reviewed:" + ref)
    native_io.FootprintSave(str(normal), fp)
    normalized = {"pose_IU": [fp.GetPosition().x, fp.GetPosition().y], "angle_deg": fp.GetOrientationDegrees(),
                  "layer": pcbnew.LayerName(fp.GetLayer()), "pads": []}
    for p in fp.Pads():
        normalized["pads"].append({"number": p.GetNumber(), "position_IU": [p.GetPosition().x, p.GetPosition().y],
                                   "angle_deg": p.GetOrientationDegrees(), "size_IU": [p.GetSize().x, p.GetSize().y],
                                   "shape": int(p.GetShape()), "roundrect_ratio": p.GetRoundRectRadiusRatio(),
                                   "layers": p.GetLayerSet().FmtBin()})
    rows.append({"ref": ref, "original": original, "normalized": normalized})
    equality = []
    for pad in fp.Pads():
        layer_ids = [pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_Paste] if fp.GetLayer() == pcbnew.B_Cu else [pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste]
        shapes_before = {pcbnew.LayerName(layer): polygon_signature(pad, layer) for layer in layer_ids}
        before_angle = pad.GetOrientationDegrees()
        pad.SetOrientationDegrees((before_angle - 180) % 360)
        shapes_after = {pcbnew.LayerName(layer): polygon_signature(pad, layer) for layer in layer_ids}
        assert shapes_before == shapes_after, (ref, pad.GetNumber(), 'Native finite polygons must be identical')
        equality.append({"pin": pad.GetNumber(), "before_angle": before_angle,
                         "after_angle": pad.GetOrientationDegrees(), "actual_native_Cu_mask_paste_polygon_vertices_exact": True,
                         "vertices_by_layer": {name: sum(map(len, values)) for name, values in shapes_before.items()}})
    rows[-1]["canonical_pad_orientation_only_native_equivalence"] = equality
stock = pcbnew.FootprintLoad(str(LIB), "R_0603_1608Metric", True)
stock.NormalizeForCompare(); stock.SetFPIDAsString("CNC_Reviewed:stock")
native_io.FootprintSave(str(normal), stock)
report = {"scope": "One isolated three-object board load plus stock footprint load; native normalize/export and pad-angle-only polygon-equivalence checks; no full motherboard load/refill or input save",
          "KiCad": pcbnew.Version(), "rows": rows, "inputs_sha256": inputs,
          "inputs_unchanged": all(sha(Path(p)) == v for p, v in inputs.items()), "adopted": False}
(OUT / "native-normalized-review.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"KiCad": report["KiCad"], "rows": [{"ref": r["ref"], "canonical_pad_orientation_only_native_equivalence": r["canonical_pad_orientation_only_native_equivalence"]} for r in rows], "inputs_unchanged": report["inputs_unchanged"]}, indent=1))
