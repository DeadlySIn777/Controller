"""Read-only exact missing .40-mm envelopes and real nearest via identities."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import identity,xy,mm
from hardware_zone_motherboard_returns import split_polygons

folder=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r120-logic-reference-collars-r04')
bp=folder/'motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb'
manifest=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r121/actual-control-segment-manifest.json')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();items={t.m_Uuid.AsString():t for t in b.GetTracks()}
vias=[v for v in items.values()if v.Type()==pcbnew.PCB_VIA_T]
failed=json.loads((folder/'actual82-control-segment-reference-reviews.json').read_text())['failed'];rows={r['actual_copper_UUIDs'][0]:r for r in json.loads(manifest.read_text())['rows']}
checker=NativeCollectedAnnulusCheck(b,{})
decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
results=[]
for fail in failed:
 t=items[fail['uuid']];row=rows[fail['uuid']];checker.rows[t.GetNetname()]=decl
 layer=b.GetLayerID(row['reference_layer']);fill=checker.reference('/LOGIC_GND',layer)
 shape=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4));endpoint=[]
 for point in (tuple(t.GetStart()),tuple(t.GetEnd())):
  for v in vias:
   if v.GetNetname()!=t.GetNetname()or tuple(v.GetPosition())!=point:continue
   radius=v.GetWidth(pcbnew.F_Cu)/2+checker.zone_clearance['/LOGIC_GND',layer]+pcbnew.FromMM(.02)
   # Diagnostic only: classify the exact same-net endpoint antipad separately.
   # This does not qualify a Ground stitch or grant any checker exemption.
   shape.BooleanSubtract(circle(point,radius));near=[]
   for g in vias:
    if g.GetNetname()!='/LOGIC_GND'or math.dist(tuple(g.GetPosition()),point)>pcbnew.FromMM(1):continue
    full=covered(circle(tuple(g.GetPosition()),pcbnew.FromMM(.24)),fill)
    conn=b.GetConnectivity();sources=[p for p in conn.GetConnectedItems(g)if isinstance(p,pcbnew.PAD)and p.GetNumber()and p.GetNetname()=='/LOGIC_GND']
    near.append(dict(uuid=g.m_Uuid.AsString(),xy_mm=mm(g.GetPosition()),free=g.GetIsFree(),full_Ground_circle_radius_mm=.24,full_ground_circle_in_actual_reference=full,flashed=g.FlashLayer(layer),native_connected_on_layer=conn.IsConnectedOnLayer(g,layer),actual_numbered_Source_witness_count=len(sources)))
   endpoint.append(dict(signal_via_uuid=v.m_Uuid.AsString(),xy_mm=mm(v.GetPosition()),nearby_actual_Ground_stitches=near))
 shape.BooleanSubtract(fill);missing=[]
 for part in split_polygons(shape):
  if part.Area()<=0:continue
  box=part.BBox();bounds=[pcbnew.ToMM(x)for x in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())];center=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2)
  closest=sorted(vias,key=lambda v:math.dist(center,mm(v.GetPosition())))[:4]
  missing.append(dict(bounds_mm=bounds,area_mm2=part.Area()/1e12,nearest_actual_barrels=[identity(v)for v in closest]))
 results.append(dict(**fail,literal_segment_identity=identity(t),diagnostic_only_own_endpoint_antipads=endpoint,unmasked_other_reference_gaps=missing))
write(Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r04-six-control-gap-inspection-r01.json'),dict(read_only=True,board_sha256=sha(bp),rows=results,diagnostic_endpoint_mask_not_qualification=True))
print('actual control gap rows',len(results),flush=True)

