import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import split_polygons,rectangle,reference_envelopes,return_net
from hardware_route_logic_return import xy,mm
from hardware_route_local_signals import paths
from hardware_route_owned_bypass_loops import Geometry
from hardware_check_return_corridors import circle,covered
bp=Path("reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb");mp=Path("reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json");op=Path("reports/motherboard-return-zoning-20261001/source26-r74-OUT9-actual-inner-power-contact-proposal-r01.json")
b=pcbnew.LoadBoard(str(bp));g=Geometry(b);m=json.load(open(mp));net="/motherboard_do/FIELD_B_0V";z=next(z for z in b.Zones()if z.m_Uuid.AsString()=="70779225-3f58-41c9-9ef5-f15169383fc2");target=list(split_polygons(z.GetFilledPolysList(pcbnew.In4_Cu)))[0];end=(352.0625,107.85);rows=[]
for xs in range(359*5,367*5):
 for ys in range(105*5,111*5):
  q=(xs/5,ys/5)
  if not g.via(q,net)or not covered(circle(tuple(xy(q)),pcbnew.FromMM(.24)),target):continue
  for path in paths(q,end):
   if not g.clear(path,net,pcbnew.In3_Cu,.2):continue
   metal=[];crossings=[]
   for s,e in zip(path,path[1:]):
    from hardware_route_selected_additive import corridor_polygon
    shape=corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.1))
    for row in m["pads"]:
     if return_net(row)==net:continue
     # Preserve every actual foreign component/contact/SUB metal projection.
     if shape.Collide(rectangle(row["copper_aabb_mm"],.15)):metal.append((row["reference"],row["pin"],row["domain"]))
    for t in b.GetTracks():
     if t.Type()!=pcbnew.PCB_TRACE_T or t.GetLayer()not in(pcbnew.F_Cu,pcbnew.B_Cu)or t.GetNetname()==net:continue
     ts=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2)
     if shape.Collide(ts):crossings.append(dict(crossed_native_UUID=t.m_Uuid.AsString(),crossed_net=t.GetNetname(),crossed_layer=t.GetLayerName(),power_return_layer="In3.Cu",actual_stackup_dielectric_required=True,no_signal_reference_credit=True))
   if metal:continue
   rows.append(dict(new_own_ground_via_mm=q,new_In3_low_current_reference_power_return_path_mm=path,existing_Source_ground_via_mm=end,existing_Source_ground_via_UUID="2f0c15c4-740a-421e-a265-e4bed1456cc3",opposite_layer_dielectric_power_return_crossings=crossings,own_In4_actual_full_annulus_prefilter=True,no_In1_or_signal_via_reference_claim=True));break
  if rows:break
 if rows:break
write(op,dict(read_only=True,board_sha256=sha(bp),literal_target_zone=z.m_Uuid.AsString(),low_current_power_return_only=True,proposal=rows,actual_native_Source_annulus_oldclusters_DRC_required=True));print(rows,flush=True)
