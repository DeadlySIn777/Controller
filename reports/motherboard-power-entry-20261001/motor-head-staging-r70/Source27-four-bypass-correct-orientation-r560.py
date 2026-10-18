"""Report-only exact rotation and electrical reattachment of four new Source27 local bypasses."""
import sys,json,math,hashlib,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy,pad_identity
from hardware_route_local_signals import paths
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-A-slow-local-circuit-r552/motherboard-Source27-A-slow-local-candidate.kicad_pcb');ROOT=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-four-bypass-correct-orientation-r560');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,ROOT,Path(__file__),Path('hardware/motherboard/design.json')]};b0=pcbnew.LoadBoard(str(B));oldCu={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};rootCu={t.m_Uuid.AsString()for t in pcbnew.LoadBoard(str(ROOT)).GetTracks()};fs0={f.GetReference():f for f in b0.GetFootprints()};oldpads={(r,p.GetNumber()):mm(p.GetPosition())for r in ['C11089','C11090','C11091','C11092']for p in fs0[r].Pads()};cap_refs=set(r for r,p in oldpads);ret=set();terminals=[]
# Only newly added cap-terminal leaves, including exact duplicate leaves, are replaceable.
for t in b0.GetTracks():
 if t.m_Uuid.AsString()in rootCu or isinstance(t,pcbnew.PCB_VIA):continue
 for key,pos in oldpads.items():
  p=next(p for p in fs0[key[0]].Pads()if p.GetNumber()==key[1])
  if t.GetNetname()!=p.GetNetname():continue
  for edge,other in [('Start','End'),('End','Start')]:
   if mm(getattr(t,'Get'+edge)())==pos:
    ret.add(t.m_Uuid.AsString());terminals.append(dict(cap=key,other_mm=mm(getattr(t,'Get'+other)()),old_uuid=t.m_Uuid.AsString(),net=t.GetNetname()))
tree=parse(without_generated_fills(B.read_text()));tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in ['segment','via']and value(child(x,'uuid')[1])in ret)]
for x in tree:
 if not(isinstance(x,list)and x and x[0]=='footprint'):continue
 prop=[p for p in x if isinstance(p,list)and p and p[0]=='property'and value(p[1])=='Reference'];r=value(prop[0][2])if prop else None
 if r in cap_refs:
  at=child(x,'at');at[3]='180'if r=='C11091'else'0'
initial=O/'four-new-cap-terminal-leaves-retired.kicad_pcb';initial.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(initial));g=m.InnerGeometry(b);ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};added=[];routes=[]
def debug():pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(retired=sorted(ret),terminal_rows=terminals,new_Cu=added,routes=routes),indent=2))
def route(a,c,n,role):
 if math.dist(a,c)<1e-8:return
 pt=next((p for p in paths(a,c)if g.clear(p,n,pcbnew.B_Cu,.25)),None)
 if pt is None:pt=g.grid(a,c,n,pcbnew.B_Cu,.25,step=.1,padding=5,max_nodes=80000)
 if pt is None:debug();raise AssertionError(('Actual new-cap reattachment blocked',role,a,c))
 ids=[]
 for p,q in zip(pt,pt[1:]):
  if math.dist(p,q)<1e-8:continue
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(p));t.SetEnd(xy(q));t.SetWidth(pcbnew.FromMM(.25));t.SetLayer(pcbnew.B_Cu);t.SetNet(b.FindNet(n));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer='B.Cu',points_mm=pt,actual_Cu_UUIDs=ids));print('ROUTE',role,len(ids),flush=True)
seen=set()
for row in terminals:
 key=tuple(row['cap']);other=tuple(row['other_mm']);k=(key,other,row['net'])
 if k in seen:continue
 seen.add(k);route(mm(ps[key].GetPosition()),other,row['net'],'Preserve actual old source branch '+key[0]+'.'+key[1])
for cap,owner,power,ground in [('C11089','U11035','6','2'),('C11090','U11036','5','3'),('C11091','U11037','6','2'),('C11092','U11038','5','3')]:
 route(mm(ps[cap,'1'].GetPosition()),mm(ps[owner,power].GetPosition()),ps[cap,'1'].GetNetname(),'Short exact owning-VDD local bypass '+cap)
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[owner,ground].GetPosition()),ps[cap,'2'].GetNetname(),'Actual exact owning-GND local bypass '+cap)
dest=O/'motherboard-four-new-bypasses-corrected-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
newCu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert set(oldCu)-set(newCu)==ret;assert all(oldCu[u]==newCu[u]for u in set(oldCu)&set(newCu));assert all(sha(Path(p))==h for p,h in inputs.items())
pose_rows=[]
for r in sorted(cap_refs):
 f=next(f for f in b.GetFootprints()if f.GetReference()==r);pose_rows.append(dict(ref=r,old_position_mm=mm(fs0[r].GetPosition()),old_angle=fs0[r].GetOrientationDegrees(),new_position_mm=mm(f.GetPosition()),new_angle=f.GetOrientationDegrees(),old_pads={p:oldpads[r,p]for rr,p in oldpads if rr==r},new_pads={p.GetNumber():mm(p.GetPosition())for p in f.Pads()}))
(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,exact_four_new_cap_pose_changes=pose_rows,retired_previous_added_cap_terminal_Cu=sorted(ret),new_Cu=added,routes=routes,old_actual_source_terminal_rows=terminals,no_Source26_part_pose_pad_Cu_change=True,manufacturer_numeric_maximum_distance=False,engineering_power_pad_target_mm=2,native_Source_reference_power_pending=True),indent=2));print('EXACT_FOUR_BYPASS_POSES',len(ret),len(added),flush=True)
