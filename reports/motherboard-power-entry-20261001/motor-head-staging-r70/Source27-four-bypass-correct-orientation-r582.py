"""Report-only exact rotation and electrical reattachment of four new Source27 local bypasses."""
import sys,json,math,hashlib,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy,pad_identity
from hardware_route_local_signals import paths,GeometryIndex
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-A-slow-local-circuit-r552/motherboard-Source27-A-slow-local-candidate.kicad_pcb');ROOT=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-four-bypass-correct-orientation-r582');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,ROOT,Path(__file__),Path('hardware/motherboard/design.json')]};b0=pcbnew.LoadBoard(str(B));b0.BuildConnectivity();oldCu={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};rootCu={t.m_Uuid.AsString()for t in pcbnew.LoadBoard(str(ROOT)).GetTracks()};fs0={f.GetReference():f for f in b0.GetFootprints()};oldpads={(r,p.GetNumber()):mm(p.GetPosition())for r in ['C11089','C11090','C11091','C11092']for p in fs0[r].Pads()};cap_refs=set(r for r,p in oldpads);ret=set();terminals=[]
# Only newly added cap-terminal leaves, including exact duplicate leaves, are replaceable.
added27={q['uuid']for q in json.loads(Path('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r524/actual-Cu.json').read_text())['new_Cu']}
for t in b0.GetTracks():
 if t.m_Uuid.AsString()in added27 and t.GetNetname()in ['/LOGIC_GND','/motherboard_power_entry/MOTION_5V_RAW']:ret.add(t.m_Uuid.AsString())
assert all(u not in rootCu for u in ret)
tree=parse(without_generated_fills(B.read_text()));tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in ['segment','via']and value(child(x,'uuid')[1])in ret)]
for x in tree:
 if not(isinstance(x,list)and x and x[0]=='footprint'):continue
 prop=[p for p in x if isinstance(p,list)and p and p[0]=='property'and value(p[1])=='Reference'];r=value(prop[0][2])if prop else None
 if r in cap_refs:
  at=child(x,'at');at.append('180'if r=='C11091'else'0')if len(at)==3 else at.__setitem__(3,'180'if r=='C11091'else'0')
initial=O/'four-new-cap-terminal-leaves-retired.kicad_pcb';initial.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(initial));g=m.InnerGeometry(b)
for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
 g.tracks[layer]=GeometryIndex()
 for item in b.GetTracks():
  if item.IsOnLayer(layer):
   a,c=mm(item.GetStart()),mm(item.GetEnd());w=pcbnew.ToMM(item.GetWidth(layer)if isinstance(item,pcbnew.PCB_VIA)else item.GetWidth());g.tracks[layer].add((item.GetNetname(),a,c,w),(min(a[0],c[0])-w/2,min(a[1],c[1])-w/2,max(a[0],c[0])+w/2,max(a[1],c[1])+w/2))
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};added=[];routes=[]
def debug():pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(retired=sorted(ret),terminal_rows=terminals,new_Cu=added,routes=routes),indent=2))
def route(a,c,n,role,l=pcbnew.B_Cu):
 if math.dist(a,c)<1e-8:return
 pt=next((p for p in paths(a,c)if g.clear(p,n,l,.25)),None)
 if pt is None:pt=g.grid(a,c,n,l,.25,step=.1,padding=5,max_nodes=80000)
 if pt is None:debug();raise AssertionError(('Actual new-cap reattachment blocked',role,a,c))
 ids=[]
 for p,q in zip(pt,pt[1:]):
  if math.dist(p,q)<1e-8:continue
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(p));t.SetEnd(xy(q));t.SetWidth(pcbnew.FromMM(.25));t.SetLayer(l);t.SetNet(b.FindNet(n));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),points_mm=pt,actual_Cu_UUIDs=ids));print('ROUTE',role,len(ids),flush=True)
raw_original=[]
source_cap=next(p for p in b0.GetPads()if p.GetParentFootprint().GetReference()=='C11083'and p.GetNumber()=='1');source_ids={q.m_Uuid.AsString()for q in b0.GetConnectivity().GetConnectedItems(source_cap)}
raw_original=[q for q in b.GetTracks()if isinstance(q,pcbnew.PCB_VIA)and q.m_Uuid.AsString()in source_ids and q.m_Uuid.AsString()not in added27]
def via(pt,n,role):
 sh=pcbnew.SHAPE_CIRCLE(xy(pt),pcbnew.FromMM(.25)+1)
 assert not any(q.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(q.IsOnLayer(l)and q.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for q in b.GetPads()),('Actual shaped registration',pt)
 assert all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]),('All-Cu via',pt)
 assert not any(isinstance(q,pcbnew.PCB_VIA)and math.dist(pt,mm(q.GetPosition()))<.4495 for q in b.GetTracks()),('Hole gap',pt)
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
for por in ['U11035','U11037']:
 for pin in ['3','5']:route(mm(ps[por,pin].GetPosition()),mm(ps[por,'6'].GetPosition()),ps[por,pin].GetNetname(),'Actual POR MR/SENSE source tie '+por+'.'+pin)
caps=[('C11089','U11035','6','2','C11083'),('C11090','U11036','5','3','C11083'),('C11091','U11037','6','2','C11086'),('C11092','U11038','5','3','C11086')]
for cap,owner,power,ground,raw in caps:
 route(mm(ps[cap,'1'].GetPosition()),mm(ps[owner,power].GetPosition()),ps[cap,'1'].GetNetname(),'Short exact owning-VDD local bypass '+cap)
 a=mm(ps[cap,'1'].GetPosition());n=ps[cap,'1'].GetNetname();choices=[]
 for d in[.9,1.0,1.1,1.3,1.5]:
  for k in range(16):
   q=(round(a[0]+d*math.cos(k*math.pi/8),6),round(a[1]+d*math.sin(k*math.pi/8),6));sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
   if not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]):continue
   if not g.clear([a,q],n,pcbnew.B_Cu,.25):continue
   if any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()):continue
   if any(isinstance(p,pcbnew.PCB_VIA)and math.dist(q,mm(p.GetPosition()))<.4495 for p in b.GetTracks()):continue
   for source in raw_original:
    c=mm(source.GetPosition())
    if math.dist(q,c)>20:continue
    pt=next((p for p in paths(q,c)if g.clear(p,n,pcbnew.In2_Cu,.25)),None)
    if pt is not None:choices.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:]))+d,q,c,source.m_Uuid.AsString()))
 assert choices,('No actual inner Source feed',cap);choices.sort();score,q,c,source=choices[0];via(q,n,'Actual local bypass supply transfer '+cap);route(a,q,n,'Short actual cap feed '+cap);route(q,c,n,'Actual retained Source barrel inner feed '+cap,pcbnew.In2_Cu)
ground_cap=next(p for p in b0.GetPads()if p.GetParentFootprint().GetReference()=='C11083'and p.GetNumber()=='2');ground_ids={q.m_Uuid.AsString()for q in b0.GetConnectivity().GetConnectedItems(ground_cap)}
ground_original=[q for q in b.GetTracks()if isinstance(q,pcbnew.PCB_VIA)and q.m_Uuid.AsString()in ground_ids and q.m_Uuid.AsString()not in added27]
ground_anchors={}
def anchor_ground(key):
 if key in ground_anchors:return ground_anchors[key]
 p=ps[key];n=p.GetNetname();a=mm(p.GetPosition());assert n=='/LOGIC_GND';choices=[]
 source_ref='C11086'if key[0]in['C11091','C11092','U11037','U11038','R11083']else'C11083';actual_source=next(v for v in b0.GetPads()if v.GetParentFootprint().GetReference()==source_ref and v.GetNumber()=='2');actual_ids={v.m_Uuid.AsString()for v in b0.GetConnectivity().GetConnectedItems(actual_source)};ground_original=[v for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and v.m_Uuid.AsString()in actual_ids and v.m_Uuid.AsString()not in added27]
 for d in[.85,.9,1.,1.1,1.3,1.5]:
  for k in range(16):
   q=(round(a[0]+d*math.cos(k*math.pi/8),6),round(a[1]+d*math.sin(k*math.pi/8),6));sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
   if not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]):continue
   if not g.clear([a,q],n,pcbnew.B_Cu,.25):continue
   if any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()):continue
   if any(isinstance(p,pcbnew.PCB_VIA)and math.dist(q,mm(p.GetPosition()))<.4495 for p in b.GetTracks()):continue
   for source in ground_original:
    c=mm(source.GetPosition())
    if math.dist(q,c)>25:continue
    pt=next((v for v in paths(q,c)if g.clear(v,n,pcbnew.In4_Cu,.25)),None)
    if pt is not None:choices.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:]))+d,q,c,source.m_Uuid.AsString()))
 
 if not choices:
  debug();print('GROUND_ORIGINAL',len(ground_original),'closest',sorted([(math.dist(a,mm(v.GetPosition())),mm(v.GetPosition()))for v in ground_original])[:8],flush=True)
 assert choices,('No actual own-domain Ground Source anchor',key,a);choices.sort();score,q,c,source=choices[0];via(q,n,'Actual off-land Source27 Ground receiving transfer '+str(key));route(a,q,n,'Actual short numbered Ground receiving escape '+str(key));route(q,c,n,'Actual own-domain retained Source Ground connection '+str(key),pcbnew.In4_Cu);ground_anchors[key]=q;return q
for cap,owner,power,ground,raw in caps:
 ca=anchor_ground((cap,'2'));oa=anchor_ground((owner,ground));route(ca,oa,'/LOGIC_GND','Actual local owning-IC bypass return '+cap,pcbnew.In4_Cu)
for pd,cap in [('R11082','C11090'),('R11083','C11092')]:
 a=anchor_ground((pd,'2'));c=ground_anchors[cap,'2'];route(a,c,'/LOGIC_GND','Actual pulldown Source return '+pd,pcbnew.In4_Cu)
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
