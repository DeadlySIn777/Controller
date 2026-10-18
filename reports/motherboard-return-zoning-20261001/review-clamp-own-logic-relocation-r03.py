"""Read-only actual-land/clock/filled-reference feasibility for BAT54S relocation."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_local_signals import GeometryIndex
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle,covered
from hardware_map_motherboard_domains import sha,write
base=Path('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(base));f=next(f for f in b.GetFootprints()if f.GetReference()=='U14012');clone=pcbnew.Cast_to_FOOTPRINT(f.Duplicate(False));original=mm(f.GetPosition());b.Remove(f);g=Geometry(b);net='/LOGIC_GND';fills=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu,pcbnew.In4_Cu]);padindex=GeometryIndex();trackindex=GeometryIndex();keep=[]
for p in b.GetPads():
 if not p.IsOnLayer(pcbnew.F_Cu):continue
 q=p.GetBoundingBox();bounds=[pcbnew.ToMM(x)for x in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())];padindex.add(p,bounds)
for t in b.GetTracks():
 if t.IsOnLayer(pcbnew.F_Cu):
  q=t.GetBoundingBox();bounds=[pcbnew.ToMM(x)for x in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())];trackindex.add(t,bounds)
for z in b.Zones():
 if z.GetIsRuleArea()and z.GetDoNotAllowPads()and z.IsOnLayer(pcbnew.F_Cu):keep.append(z)
rows=[]
for x in(108,109,110,111,112,113,114,115):
 for y in(279,280,281,282,283,284,285):
  clone.SetPosition(xy((x,y)));reason=[];pads=list(clone.Pads())
  for p in pads:
   shape=p.GetEffectiveShape(pcbnew.F_Cu);q=p.GetBoundingBox();box=[pcbnew.ToMM(v)for v in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())]
   for other in padindex.candidates(box[:2],box[2:],.15):
    if shape.Collide(other.GetEffectiveShape(pcbnew.F_Cu),pcbnew.FromMM(.15)):reason.append('pad '+other.GetParentFootprint().GetReference()+'.'+other.GetNumber())
   for t in trackindex.candidates(box[:2],box[2:],.15):
    if t.GetNetname()!=p.GetNetname()and shape.Collide(t.GetEffectiveShape(),pcbnew.FromMM(.15)):reason.append('Cu '+t.m_Uuid.AsString())
   if any(shape.Collide(z.Outline())for z in keep):reason.append('native pad keepout')
  if reason:continue
  signal=next(p for p in pads if p.GetNumber()=='3');s=mm(signal.GetPosition());coverage={b.GetLayerName(l):covered(circle(tuple(signal.GetPosition()),pcbnew.FromMM(.50)),fills[net,l])for l in(pcbnew.In1_Cu,pcbnew.In4_Cu)};via_options=[]
  for dx,dy in[(.9,0),(1.2,0),(0,-.9),(0,-1.2),(0,.9),(-.9,0)]:
   q=(round(s[0]+dx,6),round(s[1]+dy,6))
   if not g.via(q,signal.GetNetname())or not g.clear([s,q],signal.GetNetname(),pcbnew.F_Cu,.2):continue
   rings={}
   for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):
    ring=circle(tuple(xy(q)),pcbnew.FromMM(1.07));ring.BooleanSubtract(circle(tuple(xy(q)),pcbnew.FromMM(.87)));rings[b.GetLayerName(l)]=covered(ring,fills[net,l])
   if all(rings.values()):via_options.append(dict(position_mm=q,strict_full_reference_rings=rings))
  rows.append(dict(proposed_pose_mm=[x,y,clone.GetOrientationDegrees()],actual_land_clearance_screen_passed=True,signal_pad_projected_reference=coverage,new_signal_via_options=via_options,displacement_mm=math.dist(original,(x,y))))
r=dict(board_sha256=sha(base),source_reference='U14012',source_MPN='BAT54S',actual_original_pose_mm=list(original),source_pin_nets=[dict(pin=p.GetNumber(),net=p.GetNetname())for p in clone.Pads()],read_only_proposed_poses=sorted(rows,key=lambda r:r['displacement_mm']),native_DRC_not_run_on_pose=True,source_private_leaf_reconciliation_still_required=True,original_clocks_unchanged=True,no_source_or_PCB_mutation=True);write(Path('reports/motherboard-return-zoning-20261001/source26-r56-clamp-relocation-feasibility-r03.json'),r);print(json.dumps(r,indent=2))


