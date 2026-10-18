"""Actual two local Source-connected Ground partners for moved C87/clock VDD."""
import sys,json,hashlib,math,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_route_local_signals import GeometryIndex,paths
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-power-repair-native-proof-r616/motherboard-Source27-private-power-repair-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-C87-local-return-support-r626');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,Path(__file__)]};b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};ts={t.m_Uuid.AsString():t for t in b.GetTracks()};source=ps['C11086','2'];sourceids={v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(source)}|{source.m_Uuid.AsString()};anchors=[t for u,t in ts.items()if u in sourceids and isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()=='/LOGIC_GND'];g=m.InnerGeometry(b)
for l in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
 g.tracks[l]=GeometryIndex()
 for t in b.GetTracks():
  if t.IsOnLayer(l):
   a,c=mm(t.GetStart()),mm(t.GetEnd());w=pcbnew.ToMM(t.GetWidth(l)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth());g.tracks[l].add((t.GetNetname(),a,c,w),(min(a[0],c[0])-w/2,min(a[1],c[1])-w/2,max(a[0],c[0])+w/2,max(a[1],c[1])+w/2))
added=[];rows=[]
def drill(pt):
 sh=pcbnew.SHAPE_CIRCLE(xy(pt),pcbnew.FromMM(.25)+1)
 return not any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads())and not any(isinstance(t,pcbnew.PCB_VIA)and math.dist(pt,mm(t.GetPosition()))<.4495 for t in b.GetTracks())
def via(pt,role):
 v=pcbnew.PCB_VIA(b);v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(b.FindNet('/LOGIC_GND'));v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),actual=identity(v),role=role));return v
def route(points,layer,role):
 for a,c in zip(points,points[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(.25));t.SetNet(b.FindNet('/LOGIC_GND'));b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),actual=identity(t),role=role))
for key,origin,receiving in [('C87 cap-return',mm(ps['C11087','2'].GetPosition()),True),('C87 owning VDD Source transfer',mm(ts['408?'].GetPosition())if False else(265.1375,149.3),False)]:
 choices=[]
 for d in[.85,.90,.95]:
  for k in range(32):
   p=(round(origin[0]+d*math.cos(k*math.pi/16),6),round(origin[1]+d*math.sin(k*math.pi/16),6))
   if not drill(p)or not all(g.clear([p,p],'/LOGIC_GND',l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]):continue
   if receiving and not g.clear([origin,p],'/LOGIC_GND',pcbnew.B_Cu,.25):continue
   for sourcevia in anchors:
    end=mm(sourcevia.GetPosition())
    if math.dist(p,end)>15:continue
    path=next((x for x in paths(p,end)if g.clear(x,'/LOGIC_GND',pcbnew.In4_Cu,.25)),None)
    if path:choices.append((sum(math.dist(a,c)for a,c in zip(path,path[1:])),p,path,sourcevia.m_Uuid.AsString()))
 assert choices,('No actual own-source off-land return support',key,origin)
 choices.sort();cost,p,path,sid=choices[0];v=via(p,key)
 if receiving:route([origin,p],pcbnew.B_Cu,'Actual C87 cap Ground short receiving escape')
 route(path,pcbnew.In4_Cu,'Actual C87 Ground Source branch '+key);rows.append(dict(role=key,receiving_point_mm=origin,new_ground_uuid=v.m_Uuid.AsString(),new_ground_position_mm=p,distance_mm=math.dist(origin,p),retained_Source_ground_uuid=sid,actual_ground_source_path=path))
dest=O/'motherboard-Source27-C87-return-supported-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
assert all(sha(Path(p))==h for p,h in inputs.items());(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,new_Cu=added,actual_two_Source_return_targets=rows,no_existing_Cu_poses_pads_or_Source_change=True,native_Source_reference_power_pending=True,manufacturing_ready=False),indent=2));print('C87_RETURN_SUPPORT',len(added),rows,flush=True)
