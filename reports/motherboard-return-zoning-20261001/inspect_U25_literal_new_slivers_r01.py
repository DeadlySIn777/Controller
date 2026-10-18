from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import split_polygons
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
D=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U25-field-collars-r02');B=D/'motherboard-health-U25-field-reference-candidate.kicad_pcb'
b=pcbnew.LoadBoard(str(B));zones={z.m_Uuid.AsString():z for z in b.Zones()};r=json.loads((D/'full-native-resource-review.json').read_text());rows=[]
for row in r['unanchored_components']:
 p=row['literal_native_positive_metal_provenance'];z=zones[p['zone_uuid']];layer=b.GetLayerID(row['reference_layer']);piece=list(split_polygons(z.GetFilledPolysList(layer)))[p['literal_filled_piece']]
 bounds=piece.BBox()
 rows.append(dict(zone_uuid=p['zone_uuid'],zone_name=z.GetZoneName(),layer=row['reference_layer'],net=z.GetNetname(),literal_piece_index=p['literal_filled_piece'],exact_twice_area_nm2=exact_twice_area(piece),literal_contours=piece.Format(False),actual_bounds_mm=[pcbnew.ToMM(v)for v in[bounds.GetX(),bounds.GetY(),bounds.GetRight(),bounds.GetBottom()]]))
write(D/'literal-two-positive-sliver-inspection.json',dict(passed=False,inspection_only=True,board_sha256=sha(B),exact_rows=rows,no_area_or_probe_exemption=True))
print(json.dumps(rows))
