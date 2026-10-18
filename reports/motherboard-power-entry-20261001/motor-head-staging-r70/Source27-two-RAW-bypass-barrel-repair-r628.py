"""Exact four new-only barrel/attached-leaf repairs from actual annulus gaps."""
import sys,json,hashlib,math,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
B=Path('reports/motherboard-power-entry-20261001/Source27-C87-local-return-support-r626/motherboard-Source27-C87-return-supported-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-two-RAW-bypass-barrel-repair-r628');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,Path(__file__)]};b=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
moves={'41be23ef-d390-4d13-a730-f8e2ead43e48':(263.813604,201.5),'76c5127b-c8d6-43be-b841-fafc25dc71ab':(264.285839,200.65),'ce0a6f1a-17c0-40cc-942e-b66435e0ac23':(262.4,206.05),'f9477e54-179f-4cb5-beda-8aefb5eae656':(262.4,205.15)}
rows=[]
for uid,point in moves.items():
 v=ts[uid];before=v.GetPosition();after=xy(point);v.SetPosition(after);leaves=[]
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA):continue
  if t.GetStart()==before:t.SetStart(after);leaves.append(t.m_Uuid.AsString())
  if t.GetEnd()==before:t.SetEnd(after);leaves.append(t.m_Uuid.AsString())
 sh=pcbnew.SHAPE_CIRCLE(after,v.GetDrillValue()//2+pcbnew.FromMM(.15)+1)
 hits=[(p.GetParentFootprint().GetReference(),p.GetNumber())for p in b.GetPads()if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])]
 assert not hits,('Actual native shaped drill registration',uid,point,hits)
 assert all(not isinstance(t,pcbnew.PCB_VIA)or t==v or math.dist(mm(t.GetPosition()),point)>=.4495 for t in b.GetTracks()),('Actual native holes',uid)
 rows.append(dict(via_uuid=uid,before_mm=mm(before),after_mm=point,exact_attached_leaves=sorted(set(leaves)),ordinary_150um_plus1IU_registration=True))
changed=[dict(uuid=u,before=old[u],after=identity(t))for u,t in ts.items()if old[u]!=identity(t)];dest=O/'motherboard-Source27-two-RAW-bypass-repair-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
assert all(sha(Path(p))==h for p,h in inputs.items());(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,exact_four_new_only_barrel_moves=rows,exact_modified_Cu=changed,no_source_pad_pose_or_old_ROOT103_Cu_change=True,native_Source_control_power_and_reference_pending=True,manufacturing_ready=False),indent=2));print('EXACT_RAW_MOVES',len(changed),flush=True)
