"""Read-only bounded actual ADS1115 bypass placement and ground escape search."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm
from hardware_route_owned_bypass_loops import Geometry
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_route_selected_additive import corridor_polygon

bp=Path('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/source26-r69-C19042-ADC-cell-feasibility-r01.json')
if out.exists():raise ValueError('Fresh evidence required')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();original=next(f for f in b.GetFootprints()if f.GetReference()=='C19042')
conn=b.GetConnectivity()
if any(any(isinstance(t,pcbnew.PCB_TRACK)and t.GetNetname()==p.GetNetname()for t in conn.GetConnectedItems(p))for p in original.Pads()):raise ValueError('Actual C19042 now has attached old Source copper; new preservation review required')
clone=pcbnew.Cast_to_FOOTPRINT(original.Duplicate(False));b.Remove(original);clone.Flip(clone.GetPosition(),False);g=Geometry(b)
pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};vcc=pads['U19026','8'];ret='/motherboard_do/FIELD_B_0V';fills=collect_native_reference_fills(b,{ret},[pcbnew.In1_Cu,pcbnew.In4_Cu]);rows=[]
if vcc.GetNetname()!='/motherboard_do/DOB_FIELD_3V3':raise ValueError('Actual ADC rail differs')
for orientation in(0,180,90,-90):
 clone.SetOrientationDegrees(orientation)
 for xstep in range(499,515):
  for ystep in range(672,693):
   center=(xstep/4,ystep/4);clone.SetPosition(xy(center));caps={p.GetNumber():p for p in clone.Pads()};p=mm(caps['1'].GetPosition());r=mm(caps['2'].GetPosition())
   length=math.dist(p,mm(vcc.GetPosition()))
   if length>2.5 or not g.clear([mm(vcc.GetPosition()),p],vcc.GetNetname(),pcbnew.F_Cu,.2):continue
   lands=True
   for pad in clone.Pads():
    shape=pad.GetEffectiveShape(pcbnew.F_Cu);bb=pad.GetBoundingBox();a=mm(pad.GetPosition())
    for old in b.GetPads():
     if old.IsOnLayer(pcbnew.F_Cu)and old.GetNetname()!=pad.GetNetname()and shape.Collide(old.GetEffectiveShape(pcbnew.F_Cu),pcbnew.FromMM(.2)):lands=False;break
    if not lands:break
   if not lands:continue
   powercorr=corridor_polygon(tuple(vcc.GetPosition()),tuple(caps['1'].GetPosition()),pcbnew.FromMM(.5))
   if not covered(powercorr,fills[ret,pcbnew.In1_Cu]):continue
   ground=[]
   for radius in(.7,.9,1.1,1.4):
    for angle in range(0,360,45):
     rad=math.radians(angle);q=(round(r[0]+radius*math.cos(rad),6),round(r[1]+radius*math.sin(rad),6))
     if not g.via(q,ret)or not g.clear([r,q],ret,pcbnew.F_Cu,.2):continue
     own=circle(tuple(xy(q)),pcbnew.FromMM(.26))
     if not covered(own,fills[ret,pcbnew.In1_Cu]):continue
     # The proposed capacitor lands also cannot contain the new barrel.
     if any(own.Collide(pad.GetEffectiveShape(pcbnew.F_Cu),pcbnew.FromMM(.1))for pad in clone.Pads()):continue
     ground.append(dict(via_mm=list(q),direct_F_ground_branch_mm=[list(r),list(q)],own_In1_full_point26_ring=True))
    if ground:break
   if not ground:continue
   rows.append(dict(cap_center_mm=list(center),cap_orientation_deg=orientation,cap_layer='F.Cu',actual_cap_power_mm=list(p),actual_cap_ground_mm=list(r),actual_owner='U19026.8',actual_power_length_mm=length,strict_own_In1_power_corridor_margin_mm=.4,ground_candidates=ground[:2],native_full_DRC_courtyard_refill_Source_proof_still_required=True))
   print(center,orientation,length,flush=True)
   if len(rows)>=8:break
  if len(rows)>=8:break
 if len(rows)>=8:break
write(out,dict(board_sha256=sha(bp),read_only=True,actual_C19042_has_no_attached_Cu=True,actual_ADS1115_owner='U19026.8',actual_return_node='U19026.3',candidate_source_pin_land_or_MPN_changes=False,candidates=rows,manufacturing_ready=False))
