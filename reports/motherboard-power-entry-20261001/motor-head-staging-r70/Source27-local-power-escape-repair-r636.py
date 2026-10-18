"""Actual track-aware copied repairs; rejected r628/r630 remain unchanged."""
import sys,json,hashlib,math,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_route_local_signals import GeometryIndex,paths
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import without_generated_fills,dump_board
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-C87-local-return-support-r626/motherboard-Source27-C87-return-supported-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-local-power-escape-repair-r636');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,Path(__file__)]};b0=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};ret={'2a89c372-2653-4dd5-bc0d-a7e3f6c3f341'}
tree=parse(without_generated_fills(B.read_text()));tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in['segment','via']and value(child(x,'uuid')[1])in ret)];initial=O/'exact-short-positive-branch-retired.kicad_pcb';initial.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(initial));ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
moves={'ce0a6f1a-17c0-40cc-942e-b66435e0ac23':(265.2,205.9),'f9477e54-179f-4cb5-beda-8aefb5eae656':(266.0,205.9),'431d7a91-7923-41e0-9160-c07839f3f27f':(265.35,148.5)};move_rows=[]
for uid,point in moves.items():
 v=ts[uid];before=v.GetPosition();after=xy(point);v.SetPosition(after);leaves=[]
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA):continue
  if t.GetStart()==before:t.SetStart(after);leaves.append(t.m_Uuid.AsString())
  if t.GetEnd()==before:t.SetEnd(after);leaves.append(t.m_Uuid.AsString())
 sh=pcbnew.SHAPE_CIRCLE(after,v.GetDrillValue()//2+pcbnew.FromMM(.15)+1);hits=[(p.GetParentFootprint().GetReference(),p.GetNumber())for p in b.GetPads()if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])];assert not hits,('Actual shaped registration',uid,hits)
 assert all(not isinstance(t,pcbnew.PCB_VIA)or t==v or math.dist(mm(t.GetPosition()),point)>=.4495 for t in b.GetTracks()),('Actual hole separation',uid)
 move_rows.append(dict(via_uuid=uid,before_mm=mm(before),after_mm=point,exact_attached_Cu=sorted(set(leaves))))
g=m.InnerGeometry(b)
for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
 g.tracks[layer]=GeometryIndex()
 for t in b.GetTracks():
  if t.IsOnLayer(layer):
   a,c=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(layer)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth());g.tracks[layer].add((t.GetNetname(),a,c,w),(min(a[0],c[0])-w/2,min(a[1],c[1])-w/2,max(a[0],c[0])+w/2,max(a[1],c[1])+w/2))
changed=[dict(uuid=u,before=old[u],after=identity(t))for u,t in ts.items()if old[u]!=identity(t)]
for row in changed:
 t=ts[row['uuid']]
 if isinstance(t,pcbnew.PCB_VIA):
  assert all(g.clear([mm(t.GetPosition())]*2,t.GetNetname(),l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu]),('Actual track-aware barrel',row['uuid'])
 else:assert g.clear([mm(t.GetStart()),mm(t.GetEnd())],t.GetNetname(),t.GetLayer(),pcbnew.ToMM(t.GetWidth())),('Actual attached-leaf clearance',row['uuid'])
points=[(264.45,202.45),(264.45,202.75),(262.8,202.75),(262.8,202.45)];assert g.clear(points,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.B_Cu,.25),'Actual C89 below-antipad receiving dogleg';added=[]
for a,c in zip(points,points[1:]):
 t=pcbnew.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetLayer(pcbnew.B_Cu);t.SetWidth(pcbnew.FromMM(.25));t.SetNet(b.FindNet('/motherboard_power_entry/MOTION_5V_RAW'));b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),actual=identity(t),role='C89 actual short owning-VDD escape below its own positive antipad'))
dest=O/'motherboard-Source27-local-power-escape-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
assert all(sha(Path(p))==h for p,h in inputs.items());(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,retired_Cu=sorted(ret),new_Cu=added,exact_three_new_only_barrel_moves=move_rows,exact_modified_Cu=changed,no_Source_pad_pose_or_old_ROOT103_Cu_change=True,native_Source_current_reference_power_pending=True,manufacturing_ready=False),indent=2));print('LOCAL_POWER_ESCAPE',len(changed),len(added),flush=True)
