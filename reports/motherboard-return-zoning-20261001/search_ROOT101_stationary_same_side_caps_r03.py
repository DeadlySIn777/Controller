"""Bounded copied-board same-side placement for exact unrouted bypass owners.

The pose search is not electrical acceptance. A candidate must subsequently
route the actual complete receiving loop and pass native/power/Source/cut proof.
"""
import argparse,collections,json,math,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_place_owned_capacitors_native import MutableOccupancy,side_box
from hardware_populate_motherboard_pcb import intersects,sha,write,pad_template
from hardware_route_logic_return import mm,xy,identity,segment_distance,segment_hits_box
from hardware_route_local_signals import GeometryIndex,paths
from hardware_index_literal_reference_coverage import LiteralReferenceCoverage
from hardware_check_return_corridors import corridor_polygon
from hardware_stitch_owned_return_planes import definitions
from hardware_route_owned_bypass_loops import drc

B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb')
OWN=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-stationary-six-same-side-placement-r03')
REFS=['C13006','C13007','C13011','C13012','C13018','C13019']
if O.exists():raise ValueError('Fresh report-local output required')
O.mkdir();assert sha(B)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
inputs={str(p):sha(p)for p in [B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),OWN,Path(__file__),Path('hardware/motherboard/design.json')]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
owner={r['ref']:r for r in json.loads(OWN.read_text())['capacitors']}
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};old={u:identity(t)for u,t in cu.items()}
oldzones=definitions(B);oldposes={r:[mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer()]for r,f in fps.items()}
oldpadnets={p.m_Uuid.AsString():p.GetNetname()for p in b.GetPads()}
occupancy=MutableOccupancy()
for r,f in fps.items():occupancy.update(r,f.GetLayer(),side_box(f))
# These cells are remote from all mating apertures, module bays and power cells;
# use every actual native courtyard and copper as hard occupancy nonetheless.
pads=GeometryIndex();tracks=GeometryIndex()
for p in b.GetPads():
 box=p.GetBoundingBox();bounds=tuple(pcbnew.ToMM(v)for v in[box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]);pads.add((p,bounds),bounds)
for t in b.GetTracks():
 if t.IsOnLayer(pcbnew.F_Cu):
  s,e=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if t.Type()==pcbnew.PCB_VIA_T else t.GetWidth())
  tracks.add((t,s,e,w),(min(s[0],e[0])-w/2,min(s[1],e[1])-w/2,max(s[0],e[0])+w/2,max(s[1],e[1])+w/2))
coverage=LiteralReferenceCoverage(b,{'/LOGIC_GND'},[pcbnew.In1_Cu])
def pin(ref,p):return next(n for n in fps[ref].Pads()if n.GetNumber()==p)
def restore(f,pose):
 if f.GetLayer()!=pose[2]:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
 f.SetPosition(xy(pose[0]));f.SetOrientationDegrees(pose[1])
def pose_clear(f):
 court=side_box(f)
 if occupancy.collision(f.GetReference(),pcbnew.F_Cu,court,.25):return False
 for z in b.Zones():
  if not z.GetIsRuleArea()or not z.IsOnLayer(pcbnew.F_Cu):continue
  if z.GetDoNotAllowFootprints()or z.GetDoNotAllowTracks():
   if z.Outline().BBox().Intersects(f.GetLayerBoundingBox(pcbnew.LSET([pcbnew.F_CrtYd]))):return False
 for pad in f.Pads():
  q=pad.GetBoundingBox();box=tuple(pcbnew.ToMM(v)for v in[q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()])
  for other,bounds in pads.candidates(box[:2],box[2:],.3):
   if other.GetParentFootprint().GetReference()==f.GetReference():continue
   if other.IsOnLayer(pcbnew.F_Cu)and other.GetNetname()!=pad.GetNetname()and intersects(box,bounds,.2):return False
  for t,s,e,w in tracks.candidates(box[:2],box[2:],.35):
   if t.GetNetname()!=pad.GetNetname()and segment_hits_box(s,e,box,w/2+.2):return False
 return True
def short_path(f,cp,device):
 start,end=mm(cp.GetPosition()),mm(device.GetPosition())
 for points in paths(start,end):
  length=sum(math.dist(a,z)for a,z in zip(points,points[1:]))
  if length>4:continue
  accepted=True
  for a,z in zip(points,points[1:]):
   for other,box in pads.candidates(a,z,.3):
    if other.GetParentFootprint().GetReference()==f.GetReference():continue
    if other.IsOnLayer(pcbnew.F_Cu)and other.GetNetname()!=cp.GetNetname()and segment_hits_box(a,z,box,.3):accepted=False;break
   if not accepted:break
   if any(t.GetNetname()!=cp.GetNetname()and segment_distance(a,z,s,e)<.3+w/2-1e-6 for t,s,e,w in tracks.candidates(a,z,.5)):accepted=False;break
   envelope=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(.2))
   if not coverage.candidate_covered(envelope,'/LOGIC_GND',pcbnew.In1_Cu):accepted=False;break
  if accepted:return dict(points_mm=points,path_length_mm=length,search_only=True)
 return None
offsets=sorted([(i*.25,j*.25)for i in range(-14,15)for j in range(-14,15)],key=lambda t:t[0]*t[0]+t[1]*t[1])
changed=[];failed=[]
for ref in REFS:
 f=fps[ref];row=owner[ref];cp=pin(ref,row['cap_power']);cr=pin(ref,row['cap_return'])
 assert row['return_net']=='LOGIC_GND'if 'return_net'in row else True
 assert cr.GetNetname()=='/LOGIC_GND'
 device=pin(row['power_nodes'][0]['ref'],row['power_nodes'][0]['pin']);assert device.IsOnLayer(pcbnew.F_Cu)
 assert len(row['power_nodes'])==1 and device.GetNetname()==cp.GetNetname()
 attached=[u for u,t in cu.items()if any(t.GetNetname()==p.GetNetname()and(t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd()))for p in f.Pads())]
 if attached:failed.append(dict(ref=ref,reason='Actual old copper is attached; not in zero-attached pose scope',uuid=attached));continue
 if f.GetLayer()!=pcbnew.F_Cu:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
 choices=[]
 for angle in(0,90,180,270):
  f.SetOrientationDegrees(angle);f.SetPosition(xy((0,0)));relative=mm(cp.GetPosition());s=mm(device.GetPosition())
  for dx,dy in offsets:
   f.SetPosition(xy((s[0]-relative[0]+dx,s[1]-relative[1]+dy)))
   if not pose_clear(f):continue
   path=short_path(f,cp,device)
   if path:
    choices.append((path['path_length_mm'],math.dist(mm(f.GetPosition()),oldposes[ref][0]),mm(f.GetPosition()),angle,path));break
 if not choices:
  restore(f,oldposes[ref]);failed.append(dict(ref=ref,reason='No source-clear same-side pose with a literal <=4mm referenced short supply path'));continue
 _,_,pos,angle,path=min(choices)
 f.SetPosition(xy(pos));f.SetOrientationDegrees(angle)
 f.Reference().SetLayer(pcbnew.F_Fab)
 occupancy.update(ref,pcbnew.F_Cu,side_box(f))
 changed.append(dict(ref=ref,owner=row['owner'],old_pose=oldposes[ref],new_pose=[pos,angle,pcbnew.F_Cu],proposed_complete_supply_path=path,actual_supply_loop_accepted=False,receiving_ground_proof_pending=True))
 print(json.dumps(dict(proposed=ref,new_pose=pos,angle=angle,path_mm=path['path_length_mm'])),flush=True)
dest=O/'motherboard-six-same-side-pose-candidate.kicad_pcb'
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(suffix),dest.with_suffix(suffix))
for f in B.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,O/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,O/f.name)
pcbnew.SaveBoard(str(dest),b)
write(O/'proposal.json',dict(input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),board=str(dest),board_sha256=sha(dest),exact_zero_attached_capacitor_pose_proposals=changed,failed=failed,source_unchanged=True,all_old_copper_preserved=old=={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()},all_actual_pin_nets_preserved=oldpadnets=={p.m_Uuid.AsString():p.GetNetname()for p in b.GetPads()},manufacturing_ready=False,adopted=False))
print('Refill/native DRC of actual copied poses',flush=True)
n=drc(dest,O,'native')
write(O/'native-pose-receipt.json',dict(native_violations=n['violations'],ignored_checks=n['ignored_checks'],board_sha256=sha(dest),proposal_only=True,actual_complete_loop_and_global_power_Source_proof_required=True))
print(json.dumps(dict(proposed=len(changed),failed=len(failed),native_violations=len(n['violations']))))
