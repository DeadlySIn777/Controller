import sys,json,math,hashlib,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_route_local_signals import paths,GeometryIndex
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-cap-native-library-rotation-r592/motherboard-Source27-native-cap-rotation-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-receiving-return-pairs-r594');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,Path(__file__),Path('hardware/motherboard/design.json')]};b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();g=m.InnerGeometry(b)
for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
 g.tracks[layer]=GeometryIndex()
 for t in b.GetTracks():
  if t.IsOnLayer(layer):
   a,c=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(layer)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth());g.tracks[layer].add((t.GetNetname(),a,c,w),(min(a[0],c[0])-w/2,min(a[1],c[1])-w/2,max(a[0],c[0])+w/2,max(a[1],c[1])+w/2))
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};ts={t.m_Uuid.AsString():t for t in b.GetTracks()};old={u:identity(t)for u,t in ts.items()};added=[];pairs=[];routes=[]
def debug():pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(new_Cu=added,pairs=pairs,routes=routes),indent=2))
def route(a,c,n,role):
 pt=next((p for p in paths(a,c)if g.clear(p,n,pcbnew.In4_Cu,.25)),None)
 if pt is None:pt=g.grid(a,c,n,pcbnew.In4_Cu,.25,step=.15,padding=5,max_nodes=60000)
 if pt is None:debug();raise AssertionError(('Physical Source Ground path blocked',role,a,c))
 ids=[]
 for a,c in zip(pt,pt[1:]):
  if math.dist(a,c)<1e-8:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(pcbnew.In4_Cu);t.SetWidth(pcbnew.FromMM(.25));t.SetStart(xy(a));t.SetEnd(xy(c));b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role));ids.append(t.m_Uuid.AsString())
 routes.append(dict(role=role,points_mm=pt,actual_Cu_UUIDs=ids));return ids
items=[('41be23ef-d390-4d13-a730-f8e2ead43e48','A','C11089_power'),('ce0a6f1a-17c0-40cc-942e-b66435e0ac23','A','C11090_power'),('5a0f5004-e761-43e0-b209-8497e6754258','B','C11091_power'),('418206a1-923d-4d4e-9fac-090c3b63c520','B','C11092_power'),('449d30d1-71d3-4145-9cb6-69157469b099','A','FAST_A_Source'),('408cc1a6-1af0-4bc8-b2fc-4b67cc074791','B','FAST_B_Source'),('bc89a5de-9f18-4bb5-aab4-ec27b03b3138','B','FAST_B_receive'),('424d779e-50eb-4af0-a169-7d81bb3b571f','B','SLOW_B_RC_Source'),('d12a5c04-9449-446e-944c-c57e3577076a','B','SLOW_B_old_RC_input')]
for uid,bank,role in items:
 signal=ts[uid];a=mm(signal.GetPosition());target=ps['C11083'if bank=='A'else'C11086','2'];n=target.GetNetname();ids={q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(target)};source=[q for q in b.GetTracks()if isinstance(q,pcbnew.PCB_VIA)and q.GetNetname()==n and(q.m_Uuid.AsString()in ids or q.m_Uuid.AsString()in{p['ground_via_uuid']for p in pairs})];close=sorted((math.dist(a,mm(q.GetPosition())),q.m_Uuid.AsString(),mm(q.GetPosition()))for q in source if math.dist(a,mm(q.GetPosition()))<=1.)
 if close:
  pairs.append(dict(signal_via_uuid=uid,signal_point_mm=a,role=role,ground_via_uuid=close[0][1],actual_ground_point_mm=close[0][2],spacing_mm=close[0][0],already_physical_Source_connected=True));print('RETAIN_PAIR',role,close[0],flush=True);continue
 options=[]
 for d in[.85,.9,.95,.99]:
  for k in range(32):
   q=(round(a[0]+d*math.cos(k*math.pi/16),6),round(a[1]+d*math.sin(k*math.pi/16),6));sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
   if not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In1_Cu,pcbnew.In4_Cu]):continue
   if any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()):continue
   if any(isinstance(v,pcbnew.PCB_VIA)and math.dist(q,mm(v.GetPosition()))<.4495 for v in b.GetTracks()):continue
   for v in source:
    c=mm(v.GetPosition())
    if math.dist(q,c)>12:continue
    pt=next((p for p in paths(q,c)if g.clear(p,n,pcbnew.In4_Cu,.25)),None)
    if pt is not None:options.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:])),q,c,v.m_Uuid.AsString()))
 if not options:debug();raise AssertionError(('No physical <=1mm own Source return pair',uid,a,role))
 options.sort();length,q,c,source_uuid=options[0];v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(q));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='Actual own-domain receiving return '+role));path=route(q,c,n,'Actual Source-ground partner '+role);pairs.append(dict(signal_via_uuid=uid,signal_point_mm=a,role=role,ground_via_uuid=v.m_Uuid.AsString(),actual_ground_point_mm=q,spacing_mm=math.dist(a,q),retained_Source_ground_uuid=source_uuid,Source_connection_Cu_UUIDs=path));print('NEW_SOURCE_PAIR',role,q,flush=True)
dest=O/'motherboard-Source27-paired-return-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
current={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert all(current[u]==v for u,v in old.items());assert all(sha(Path(p))==h for p,h in inputs.items());(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,exact_new_Cu=added,actual_return_pairs=pairs,actual_Source_Ground_routes=routes,no_old_Cu_Source_pad_pose_or_zone_changes=True,native_Source_reference_power_pending=True),indent=2));print('DRAWN_PAIRED_RETURNS',len(added),len(pairs),flush=True)
