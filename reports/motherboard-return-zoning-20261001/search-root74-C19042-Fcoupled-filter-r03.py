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

bp=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/source26-r74-C19042-Fcoupled-filter-feasibility-r03.json')
if out.exists():raise ValueError('Fresh evidence required')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();original=next(f for f in b.GetFootprints()if f.GetReference()=='C19042')
conn=b.GetConnectivity()
if any(any(isinstance(t,pcbnew.PCB_TRACK)and t.GetNetname()==p.GetNetname()for t in conn.GetConnectedItems(p))for p in original.Pads()):raise ValueError('Actual C19042 now has attached old Source copper; new preservation review required')
clone=pcbnew.Cast_to_FOOTPRINT(original.Duplicate(False));b.Remove(original);clone.Flip(clone.GetPosition(),False)
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};ids=['8afc32f4-2047-4ff3-bf87-aa7153d9627f','c9ad7bff-105f-4b2e-b8a7-94d9c78f2e84','0c5eaaf8-1041-4f68-a66c-19fad00520b1'];old=[cu[i]for i in ids]
for t in old:b.Remove(t)
q=(124.6,172.9);g=Geometry(b)
if not g.via(q,old[1].GetNetname()):raise ValueError('Removed-old-barrel proposed real AIN2 via still obstructed')
old[0].SetEnd(xy(q));old[1].SetPosition(xy(q));old[2].SetStart(xy(q))
for t in old:b.Add(t)
filtercap=next(f for f in b.GetFootprints()if f.GetReference()=='C19037')
oldGround=next(p for p in filtercap.Pads()if p.GetNumber()=='2').GetPosition()
filtercap.SetPosition(xy((128,170.5)));newGround=next(p for p in filtercap.Pads()if p.GetNumber()=='2').GetPosition()
for uid in ['2c77f7c6-4286-46f9-a9b1-aa042be96c8f','79efbcbe-58a9-47ce-b3f1-e2cec8f6a14f']:
 t=cu[uid]
 if t.GetEnd()!=oldGround:raise ValueError('Exact filter ground branch endpoint differs')
 t.SetEnd(newGround)
g=Geometry(b)
from hardware_index_literal_reference_coverage import LiteralReferenceCoverage
from hardware_route_local_signals import paths
layers=pcbnew.LSET();layers.AddLayer(pcbnew.F_CrtYd)
fpboxes=[f.GetLayerBoundingBox(layers)for f in b.GetFootprints()if f.GetLayer()==pcbnew.F_Cu]

pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};vcc=pads['U19026','8'];ret='/motherboard_do/FIELD_B_0V';fills=collect_native_reference_fills(b,{ret},[pcbnew.In1_Cu,pcbnew.In4_Cu]);rows=[]
if vcc.GetNetname()!='/motherboard_do/DOB_FIELD_3V3':raise ValueError('Actual ADC rail differs')
fast=LiteralReferenceCoverage(b,{ret},[pcbnew.In1_Cu,pcbnew.In4_Cu])
for orientation in(0,180,90,-90):
 clone.SetOrientationDegrees(orientation)
 for xstep in range(489,517):
  for ystep in range(674,694):
   center=(xstep/4,ystep/4);clone.SetPosition(xy(center));caps={p.GetNumber():p for p in clone.Pads()};p=mm(caps['1'].GetPosition());r=mm(caps['2'].GetPosition())
   length=math.dist(p,mm(vcc.GetPosition()))
   if length>3.0:continue
   cb=clone.GetLayerBoundingBox(layers)
   if any(cb.Intersects(box)for box in fpboxes):continue
   powerpaths=[ps for ps in paths(mm(vcc.GetPosition()),p)if g.clear(ps,vcc.GetNetname(),pcbnew.F_Cu,.2)]
   if not powerpaths:continue
   lands=True
   for pad in clone.Pads():
    shape=pad.GetEffectiveShape(pcbnew.F_Cu);bb=pad.GetBoundingBox();a=mm(pad.GetPosition())
    for old in b.GetPads():
     if old.IsOnLayer(pcbnew.F_Cu)and old.GetNetname()!=pad.GetNetname()and shape.Collide(old.GetEffectiveShape(pcbnew.F_Cu),pcbnew.FromMM(.2)):lands=False;break
    if not lands:break
   if not lands:continue
   selected=None
   for ps in powerpaths:
    powercorr=pcbnew.SHAPE_POLY_SET()
    for pa,pb in zip(ps,ps[1:]):powercorr.BooleanAdd(corridor_polygon(tuple(xy(pa)),tuple(xy(pb)),pcbnew.FromMM(.5)))
    if fast.candidate_covered(powercorr,ret,pcbnew.In1_Cu):selected=ps;break
   if selected is None:continue
   ground=[]
   for radius in(.7,.9,1.1,1.4):
    for angle in range(0,360,45):
     rad=math.radians(angle);q=(round(r[0]+radius*math.cos(rad),6),round(r[1]+radius*math.sin(rad),6))
     if not g.via(q,ret)or not g.clear([r,q],ret,pcbnew.F_Cu,.2):continue
     own=circle(tuple(xy(q)),pcbnew.FromMM(.26))
     if not fast.candidate_covered(own,ret,pcbnew.In1_Cu):continue
     # The proposed capacitor lands also cannot contain the new barrel.
     if any(own.Collide(pad.GetEffectiveShape(pcbnew.F_Cu),pcbnew.FromMM(.1))for pad in clone.Pads()):continue
     ground.append(dict(via_mm=list(q),direct_F_ground_branch_mm=[list(r),list(q)],own_In1_full_point26_ring=True))
    if ground:break
   if not ground:continue
   rows.append(dict(cap_center_mm=list(center),cap_orientation_deg=orientation,cap_layer='F.Cu',actual_cap_power_mm=list(p),actual_cap_ground_mm=list(r),actual_owner='U19026.8',actual_power_length_mm=length,actual_power_F_path_mm=selected,strict_own_In1_power_corridor_margin_mm=.4,ground_candidates=ground[:2],native_full_DRC_courtyard_refill_Source_proof_still_required=True))
   print(center,orientation,length,flush=True)
   if len(rows)>=8:break
  if len(rows)>=8:break
 if len(rows)>=8:break
write(out,dict(board_sha256=sha(bp),read_only=True,actual_C19042_has_no_attached_Cu=True,actual_ADS1115_owner='U19026.8',actual_return_node='U19026.3',candidate_source_pin_land_or_MPN_changes=False,candidates=rows,manufacturing_ready=False))
