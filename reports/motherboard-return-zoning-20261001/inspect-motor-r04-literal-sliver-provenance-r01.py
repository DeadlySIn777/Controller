"""Read-only literal provenance of the eight repeated motor collar slivers.

This compares exact integer filled contours, never exempts a small island.
The inspection distinguishes inherited native copper from a new collar effect.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import split_polygons
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area

base=Path("reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r120/motor-bank-A-control-repaired-candidate.kicad_pcb")
candidate=Path("reports/motherboard-return-zoning-20261001/motor-bank-A-r120-logic-reference-collars-r04/motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb")
report=Path("reports/motherboard-return-zoning-20261001/motor-bank-A-r120-logic-reference-collars-r04/full-native-resource-review.json")
out=Path("reports/motherboard-return-zoning-20261001/motor-bank-A-r04-literal-sliver-provenance-r01.json")
if out.exists():raise ValueError("Immutable read-only evidence already exists")
boards=[pcbnew.LoadBoard(str(p))for p in(base,candidate)]
def contours(poly):
 return [[list(poly.CVertex(j,i))for j in range(poly.CPointCount(i))]for i in range(poly.OutlineCount())]
rows=[]
for row in json.loads(report.read_text())["unanchored_components"]:
 witness=row["literal_native_positive_metal_provenance"]
 if witness["literal_native_twice_area_nm2"]!=41160:continue
 uid=witness["zone_uuid"];layer=boards[1].GetLayerID(row["reference_layer"])
 z=next(z for z in boards[1].Zones()if z.m_Uuid.AsString()==uid)
 literal=list(split_polygons(z.GetFilledPolysList(layer)))[witness["literal_filled_piece"]]
 exact=contours(literal);oldzone=next(z for z in boards[0].Zones()if z.m_Uuid.AsString()==uid)
 oldpieces=list(split_polygons(oldzone.GetFilledPolysList(layer)))
 matches=[i for i,piece in enumerate(oldpieces)if contours(piece)==exact]
 bounds=literal.BBox()
 rows.append(dict(net=row["net"],layer=row["reference_layer"],zone_uuid=uid,literal_piece=witness["literal_filled_piece"],exact_twice_area_nm2=exact_twice_area(literal),contours_nm=exact,bounds_nm=[bounds.GetX(),bounds.GetY(),bounds.GetRight(),bounds.GetBottom()],inherited_exact_literal_piece_indices=matches,newly_created_by_collar=not bool(matches)))
if len(rows)!=8:raise ValueError("The exact eight reviewed literal positive pieces drifted")
write(out,dict(read_only=True,input_sha256={str(p):sha(p)for p in(base,candidate,report,Path(__file__))},rows=rows,no_area_exemption=True,no_copper_or_source_mutation=True))
print(json.dumps(dict(rows=len(rows),inherited=sum(bool(r["inherited_exact_literal_piece_indices"])for r in rows),new=sum(r["newly_created_by_collar"]for r in rows)),indent=2))
