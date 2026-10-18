"""Read-only literal Source-ground witness and local via access inspection."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import mm,xy
from hardware_route_owned_bypass_loops import Geometry
from hardware_check_return_corridors import circle,covered
from hardware_zone_motherboard_returns import split_polygons

bp=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-clipped-reference-collars-r02/motherboard-motor-bank-A-clipped-reference-candidate.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-field-source-anchor-inspection-r01.json')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();conn=b.GetConnectivity();g=Geometry(b)
net='/motherboard_motors/FIELD_GND';tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
sources=[]
for p in b.GetPads():
 if not p.GetNumber() or p.GetNetname()!=net:continue
 if math.dist(mm(p.GetPosition()),(290,231))>55:continue
 connected={v.m_Uuid.AsString()for v in conn.GetConnectedItems(p)}
 vias=[tracks[u]for u in connected if u in tracks and tracks[u].Type()==pcbnew.PCB_VIA_T]
 sources.append(dict(source=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),xy_mm=mm(p.GetPosition()),source_pad_uuid=p.m_Uuid.AsString(),connected_ground_vias=[dict(uuid=v.m_Uuid.AsString(),xy_mm=mm(v.GetPosition()),flashed_native_layers=[b.GetLayerName(l)for l in (pcbnew.In1_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu)if v.FlashLayer(l)and conn.IsConnectedOnLayer(v,l)])for v in vias]))
fill=pcbnew.SHAPE_POLY_SET()
for z in b.Zones():
 if not z.GetIsRuleArea()and z.GetNetname()==net and z.HasFilledPolysForLayer(pcbnew.In1_Cu):fill.BooleanAdd(z.GetFilledPolysList(pcbnew.In1_Cu))
spots=[];outside=[]
for ix in range(2870,2951,2):
 for iy in range(2270,2361,2):
  q=(ix/10,iy/10)
  if g.via(q,net):
   outside.append(q)
   if covered(circle(tuple(xy(q)),pcbnew.FromMM(.24)),fill):spots.append(q)
sourcevias={v['uuid']:v for r in sources for v in r['connected_ground_vias']}
write(out,dict(read_only=True,board_sha256=sha(bp),literal_return_net=net,actual_numbered_Source_witnesses=sorted(sources,key=lambda r:math.dist(r['xy_mm'],(290,231))),clear_local_In1_full_annulus_candidates_mm=spots,actual_clear_external_barrel_candidates_mm=outside,nearby_Source_backed_ground_vias=sorted(sourcevias.values(),key=lambda r:math.dist(r['xy_mm'],(290,231)))[:25]))
print('nearby Sources',len(sources),'actual clear .24 mm local annuli',len(spots),flush=True)

