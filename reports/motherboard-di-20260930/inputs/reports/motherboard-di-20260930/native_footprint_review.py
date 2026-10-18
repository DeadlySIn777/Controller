"""Run with KiCad's bundled Python to inspect actual loaded footprint pads."""
from pathlib import Path
import hashlib
import json
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "hardware/motherboard_di"
model = json.loads((OUT/"design.json").read_text(encoding="utf-8"))
KICAD = Path("C:/Program Files/KiCad/10.0/share/kicad/footprints")
rows = []
errors = []
native_pad_total = 0
for ref,part in model["components"].items():
    library,name = part["footprint"].split(":",1)
    directory = OUT/"CNC_MB_DI.pretty" if library=="CNC_MB_DI" else KICAD/(library+".pretty")
    path = directory/(name+".kicad_mod")
    fp = pcbnew.FootprintLoad(str(directory),name)
    if fp is None:
        errors.append("Failed to load "+ref)
        continue
    pads = sorted([{"number":pad.GetNumber(),"position_mm":[pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)],"size_mm":[pcbnew.ToMM(pad.GetSize().x),pcbnew.ToMM(pad.GetSize().y)],"shape":int(pad.GetShape()),"layers":[pcbnew.LayerName(layer) for layer in pad.GetLayerSet().Seq()]} for pad in fp.Pads()],key=lambda x:int(x["number"]))
    native_pad_total += len(pads)
    numbers = [p["number"] for p in pads]
    if len(numbers)!=len(set(numbers)) or set(numbers)!=set(part["pins"]):
        errors.append(ref+" native footprint pin set differs from source")
    if library=="CNC_MB_DI":
        for pad in pads:
            i = int(pad["number"])
            expected = [-2.7 if i<=8 else 2.7,-2.2225+(i-1)*.635 if i<=8 else 2.2225-(i-9)*.635]
            if any(abs(a-b)>1e-7 for a,b in zip(pad["position_mm"],expected)) or pad["size_mm"]!=[1.6,.41] or pad["shape"]!=int(pcbnew.PAD_SHAPE_RECT) or set(pad["layers"])!={"F.Cu","F.Paste","F.Mask"}:
                errors.append(ref+" loaded pad geometry/layers differ from TI DBQ0016A example")
    rows.append({"reference":ref,"footprint":part["footprint"],"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"pads":pads})
if len(rows)!=120 or native_pad_total!=408:
    errors.append("Actual loaded fitted footprint count/pad total differs from 120/408")
result = {"ok":not errors,"errors":errors,"native_footprints_loaded":len(rows),"native_physical_pads":native_pad_total,"native_nc_pads":24,"unselected_boundaries_excluded":list(model["boundaries"]),"manufacturer_source":"TI ISO1212 SLLSEY7G Fig4-2 / DBQ0016A 4214846/A example board layout","final_solder_mask_stencil_and_assembly_qualified":False,"layout_SUB_islands_fitted":False,"physical_qualification":False,"rows":rows}
(HERE/"native-footprint-review.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2))
raise SystemExit(0 if result["ok"] else 1)
