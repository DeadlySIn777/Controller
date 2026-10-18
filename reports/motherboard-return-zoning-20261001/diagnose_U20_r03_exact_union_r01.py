from pathlib import Path
import sys,json
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
from hardware_check_return_corridors import circle
from hardware_route_selected_additive import corridor_polygon
from hardware_map_motherboard_domains import write
B=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U20-control-collars-r03/motherboard-U20-two-control-reference-candidate.kicad_pcb'); b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};r=json.loads((B.parent/'generation.json').read_text());ids=r['selected_actual_control_UUIDs'];dec=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);ch=ExactEndpointUnionCheck(b,{cu[u].GetNetname():dec for u in ids});out=[]
for u in ids:
 t=cu[u]
 try: a=ch.via(t,dec)if t.Type()==pcbnew.PCB_VIA_T else ch.segment(t,dec);out.append(dict(uuid=u,passed=True))
 except ValueError as e:
  q=dict(uuid=u,passed=False,error=str(e));out.append(q)
  if t.Type()==pcbnew.PCB_TRACE_T:
   layer=b.GetLayerID(dec['reference_layers'][b.GetLayerName(t.GetLayer())]);fill=ch.reference('/LOGIC_GND',layer);aug=pcbnew.SHAPE_POLY_SET(fill)
   for end in(tuple(t.GetStart()),tuple(t.GetEnd())):
    for via in ch.vias:
     if via.GetNetname()==t.GetNetname()and tuple(via.GetPosition())==end:
      try:a=ch.via(via,dec);aug.BooleanAdd(circle(end,pcbnew.FromMM(a['bounded_antipad_radius_mm'][b.GetLayerName(layer)])))
      except ValueError:pass
   miss=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4));miss.BooleanSubtract(aug);bb=miss.BBox();q.update(area=miss.Area()/1e12,shape=miss.Format(False),bbox=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())])
write(B.parent/'diagnostic-exact-union.json',dict(rows=out));print(json.dumps(out))
