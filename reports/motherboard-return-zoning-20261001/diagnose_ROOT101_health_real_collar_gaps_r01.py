"""Literal actual Source/control/receiving reference failures, no mutation."""
from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_map_motherboard_domains import write,sha
from hardware_route_logic_return import mm
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};proof=json.loads((B.parent/'actual-private-input-controls-proof.json').read_text());decl=proof['literal_declarations'];ch=ExactEndpointUnionCheck(b,decl);out=[]
for row in proof['rows']:
 if row['passed']:continue
 t=cu[row['uuid']];d=decl[t.GetNetname()];layer=b.GetLayerID(d['reference_layers'][b.GetLayerName(t.GetLayer())]);aug=pcbnew.SHAPE_POLY_SET(ch.reference(d['return_net'],layer))
 for end in(tuple(t.GetStart()),tuple(t.GetEnd())):
  for v in ch.vias:
   if v.GetNetname()==t.GetNetname()and tuple(v.GetPosition())==end:
    a=ch.via(v,d);aug.BooleanAdd(circle(end,pcbnew.FromMM(a['bounded_antipad_radius_mm'][b.GetLayerName(layer)])))
 miss=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4));miss.BooleanSubtract(aug);bb=miss.BBox();centre=((bb.GetX()+bb.GetRight())//2,(bb.GetY()+bb.GetBottom())//2);near=[]
 for x in b.GetTracks():
  if x.Type()==pcbnew.PCB_VIA_T and math.dist(tuple(x.GetPosition()),centre)<pcbnew.FromMM(2):near.append(dict(uuid=x.m_Uuid.AsString(),net=x.GetNetname(),position_mm=mm(x.GetPosition()),diameter_mm=pcbnew.ToMM(x.GetWidth(0))))
 for p in b.GetPads():
  if p.GetNumber()and math.dist(tuple(p.GetPosition()),centre)<pcbnew.FromMM(2):near.append(dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname(),position_mm=mm(p.GetPosition()),layer=b.GetLayerName(p.GetLayer())))
 out.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layer=b.GetLayerName(t.GetLayer()),start_mm=mm(t.GetStart()),end_mm=mm(t.GetEnd()),missing_reference_layer=b.GetLayerName(layer),exact_missing_shape=miss.Format(False),missing_area_mm2=miss.Area()/1e12,bounds_mm=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())],nearest_actual_native_objects=near))
ret=[]
for owner,cap in [('U11020','C11079'),('U11026','C11081')]:
 for fp,pn in [(owner,'2'),(cap,'2')]:
  p=next(p for p in fps[fp].Pads()if p.GetNumber()==pn);conn={x.m_Uuid.AsString()for x in co.GetConnectedItems(p)};vs=[]
  for v in cu.values():
   if v.Type()!=pcbnew.PCB_VIA_T or v.GetNetname()!=p.GetNetname()or math.dist(tuple(v.GetPosition()),tuple(p.GetPosition()))>pcbnew.FromMM(2):continue
   layers=[]
   for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):layers.append(dict(layer=b.GetLayerName(l),flash=v.FlashLayer(l),connected_layer=co.IsConnectedOnLayer(v,l),Source_ground=bool(ch.source_anchors(v,v.GetNetname())),full_actual_circle=covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.24)),ch.reference(v.GetNetname(),l))))
   vs.append(dict(uuid=v.m_Uuid.AsString(),position_mm=mm(v.GetPosition()),joined_to_actual_pad=v.m_Uuid.AsString()in conn,layers=layers))
  ret.append(dict(reference=fp,pin=pn,position_mm=mm(p.GetPosition()),actual_vias=vs))
write(B.parent/'actual-control-and-Ground-gap-diagnostic.json',dict(board_sha256=sha(B),failed_controls=out,actual_receiving_Ground_pads=ret));print(json.dumps(dict(failed=[{k:r[k]for k in('uuid','net','layer','missing_area_mm2','bounds_mm')}for r in out],ground=ret)),flush=True)
