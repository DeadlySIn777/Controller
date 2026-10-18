"""Four necessary actual Source27 signal-return stitches on a copied filled board."""
import sys,json,math,hashlib,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_route_local_signals import paths
spec=importlib.util.spec_from_file_location('g',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BASE=Path('reports/motherboard-power-entry-20261001/Source27-combined-current-native-proof-r540/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');OUT=Path('reports/motherboard-power-entry-20261001/Source27-four-return-stitches-r546');assert not OUT.exists();OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in[BASE,Path(__file__),Path('hardware/motherboard/design.json')]};b=pcbnew.LoadBoard(str(BASE));g=m.InnerGeometry(b);ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};ts={t.m_Uuid.AsString():t for t in b.GetTracks()};n='/LOGIC_GND';added=[];pairs=[]
def debug():pcbnew.SaveBoard(str(OUT/'debug.kicad_pcb'),b);(OUT/'debug.json').write_text(json.dumps(dict(new_Cu=added,pairs=pairs),indent=2))
def route(a,c,role):
 pt=next((p for p in paths(a,c)if g.clear(p,n,pcbnew.B_Cu,.25)),None)
 if pt is None:pt=g.grid(a,c,n,pcbnew.B_Cu,.25,step=.15,padding=5,max_nodes=70000)
 if pt is None:debug();raise AssertionError(('Actual Source Ground branch blocked',role,a,c))
 ids=[]
 for a,c in zip(pt,pt[1:]):
  if math.dist(a,c)<1e-7:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(pcbnew.B_Cu);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(pcbnew.FromMM(.25));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
 return ids
for uid,point,target in [('26793be2-e255-4882-952c-2f2a7b8f937c',(259.8,205.1),('U11036','3')),('449d30d1-71d3-4145-9cb6-69157469b099',(264.2,204.15),('U11036','3')),('94f4dbbe-8a80-4846-a72d-ed1e8d4b029d',(267.356921,199.756921),('C11082','2')),('408cc1a6-1af0-4bc8-b2fc-4b67cc074791',(264.5,155.4),('C11092','2'))]:
 signal=ts[uid];sp=mm(signal.GetPosition());assert .75<=math.dist(sp,point)<=1.0
 sh=pcbnew.SHAPE_CIRCLE(xy(point),pcbnew.FromMM(.25)+1);assert not any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()),('Actual native drill registration',point)
 assert all(g.clear([point,point],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]),('Actual all-Cu clearance',point)
 assert not any(isinstance(t,pcbnew.PCB_VIA)and math.dist(point,mm(t.GetPosition()))<.4495 for t in b.GetTracks()),('Actual drill separation',point)
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(point));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='Actual Source27 signal return stitch'));p=ps[target];assert p.GetNetname()==n;ids=route(point,mm(p.GetPosition()),'Actual same-domain numbered-Source Ground receiving branch');pairs.append(dict(signal_via_uuid=uid,signal_point_mm=sp,actual_return_via_uuid=v.m_Uuid.AsString(),actual_return_point_mm=point,signal_return_spacing_mm=math.dist(sp,point),actual_numbered_Source_Ground_target=target,Ground_branch_Cu_UUIDs=ids));print('ACTUAL_RETURN',uid,point,len(ids),flush=True)
dest=OUT/'motherboard-Source27-return-stitches-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(ext),dest.with_suffix(ext))
for p in BASE.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,OUT/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,OUT/p.name)
assert all(sha(Path(p))==h for p,h in frozen.items());(OUT/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=frozen,exact_new_Cu=added,actual_four_signal_return_pairs=pairs,no_Source_pad_part_pose_or_existing_Cu_zone_change=True,native_Source_reference_global_power_pending=True),indent=2));print('ADDITIVE_DRAWN',len(added),flush=True)
