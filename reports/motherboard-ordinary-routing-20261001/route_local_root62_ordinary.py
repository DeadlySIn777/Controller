"""Actual bounded F-side routes from the frozen112 allowlist and eligible fill."""
from pathlib import Path
import sys,json,copy,math,shutil
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,segment_distance
from hardware_check_return_corridors import covered
e=o.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb')
MAN=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root62-r01/manifest.json')
OUT=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root62-local-r02');OUT.mkdir(exist_ok=False)
m=e.read(MAN);o.INPUT_BOARD=BASE;o.frozen_review_check(m,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'));proof=e.read(m['plane_review']['path']);o.MAPPING=e.read(proof['source_map']['path'])
b=pcbnew.LoadBoard(str(BASE));o.engine.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'));checker=o.LiteralPieces(b,m['nets']);g=w.Geometry(b);fill=checker.reference('/LOGIC_GND',b.GetLayerID('In1.Cu'))
added=[];groups=[];blocked=[];already=[]
def clear(points,name,row):
 width=row['width_mm'];space=row['clearance_mm']
 for s,z in zip(points,points[1:]):
  seg=pcbnew.SEG(xy(s),xy(z))
  for p,box in g.pads.candidates(s,z,width/2+space+.1):
   if p.IsOnLayer(pcbnew.F_Cu)and p.GetNetname()!=name and p.GetEffectiveShape(pcbnew.F_Cu).Collide(seg,pcbnew.FromMM(width/2+space-1e-6)):return False
  for name2,a,c,width2 in g.tracks[pcbnew.F_Cu].candidates(s,z,width/2+.5):
   if name2!=name and segment_distance(s,z,a,c)<width/2+width2/2+space-1e-6:return False
  copper=e.corridor_polygon(tuple(xy(s)),tuple(xy(z)),pcbnew.FromMM(width/2))
  for zone in g.keepouts:
   if zone.IsOnLayer(pcbnew.F_Cu)and zone.GetDoNotAllowTracks():
    hit=pcbnew.SHAPE_POLY_SET();hit.Append(copper);hit.BooleanIntersection(zone.Outline())
    if hit.Area():return False
  projected=e.corridor_polygon(tuple(xy(s)),tuple(xy(z)),pcbnew.FromMM(width/2+row['reference_corridor_margin_mm']))
  if not covered(projected,fill):return False
 return True
def peers(p):return{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
def add(points,name,row):
 ids=[]
 for s,z in zip(points,points[1:]):
  if math.dist(s,z)<1e-6:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(s));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(row['width_mm']));b.Add(t);added.append(t);g.add(t);ids.append(t.m_Uuid.AsString())
 return ids
pads={}
for p in b.GetPads():
 if p.GetNetname()in m['nets']:pads.setdefault(p.GetNetname(),[]).append(p)
jobs=[]
for name,row in m['nets'].items():
 ps=pads[name]
 for i,p in enumerate(ps):
  for q in ps[i+1:]:
   dist=math.dist(mm(p.GetPosition()),mm(q.GetPosition()))
   if dist<=25 and p.IsOnLayer(pcbnew.F_Cu)and q.IsOnLayer(pcbnew.F_Cu):jobs.append((dist,name,p,q))
for _,name,p,q in sorted(jobs,key=lambda v:v[0]):
 b.BuildConnectivity()
 if q.m_Uuid.AsString()in peers(p):already.append(dict(net=name,pair=[p.m_Uuid.AsString(),q.m_Uuid.AsString()]));continue
 row=m['nets'][name];s,z=mm(p.GetPosition()),mm(q.GetPosition());path=next((pts for pts in paths(s,z)if clear(pts,name,row)),None)
 if path is None:blocked.append(dict(net=name,source_pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()],span_mm=math.dist(s,z),reason='No bounded native-clear F path wholly inside actual eligible own reference'));continue
 ids=add(path,name,row);groups.append(dict(net=name,source_pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()],source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],points_mm=path,new_copper_UUIDs=ids,width_mm=row['width_mm'],clearance_mm=row['clearance_mm'],reference_corridor_margin_mm=row['reference_corridor_margin_mm']))
print(json.dumps(dict(actual_groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
tree=e.parse(BASE.read_text());old=copy.deepcopy(tree)
for t in added:tree.append(['segment',['start',str(pcbnew.ToMM(t.GetStart().x)),str(pcbnew.ToMM(t.GetStart().y))],['end',str(pcbnew.ToMM(t.GetEnd().x)),str(pcbnew.ToMM(t.GetEnd().y))],['width',str(pcbnew.ToMM(t.GetWidth()))],['layer','"F.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]])
if e.immutable_objects(old)!=e.immutable_objects(tree):raise ValueError('Authoritative native source/lands/zone geometry changed')
dest=OUT/'motherboard-ordinary-local-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n',encoding='utf8')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposed-local-groups.json',dict(base_sha256=e.sha(BASE),manifest_sha256=e.sha(MAN),tool_sha256=e.sha(__file__),groups=groups,added_copper_UUIDs=[t.m_Uuid.AsString()for t in added],blocked=blocked,already_joined_pairs=already,maximum_considered_source_span_mm=25,only_exact_frozen112_source_nets=True,whole_board_reference_qualification=False,full_failed_reference_ledger=proof['complete_unanchored_components'],native_validation_pending=True,manufacturing_ready=False))
