"""Use actual B control copper so new reset controls cannot split the F CORE5 power bank."""
import sys,json,math,shutil,importlib.util,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_route_local_signals import paths
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
spec=importlib.util.spec_from_file_location('actual_inner_geometry',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-combined-current-native-proof-r540/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');OLD=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb');ROW=Path('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r524/actual-Cu.json');O=Path('reports/motherboard-power-entry-20261001/Source27-A-slow-local-circuit-r552');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in [B,OLD,ROW,Path(__file__),Path('hardware/motherboard/design.json')]};b0=pcbnew.LoadBoard(str(B));r=json.loads(ROW.read_text());new={v['uuid']for v in r['new_Cu']};private={'/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A'};removed={t.m_Uuid.AsString()for t in b0.GetTracks()if t.m_Uuid.AsString()in new and t.GetNetname()in private}
tree=parse(without_generated_fills(B.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in ['segment','via']and value(child(v,'uuid')[1])in removed)];initial=O/'new-private-B-controls-retired.kicad_pcb';initial.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(initial));g=m.InnerGeometry(b);ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};added=[];routes=[]
def debug():
 pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(retired_old=r['retired'],retired_prior_added_private=sorted(removed),new_Cu=added,routes=routes),indent=2))
def route(a,c,n,l,role):
 pts=next((p for p in paths(a,c)if g.clear(p,n,l,.25)),None)
 if pts is None:pts=g.grid(a,c,n,l,.25,step=.15,padding=9,max_nodes=80000)
 if pts is None:debug();raise AssertionError(('Actual control path blocked',role,a,c,b.GetLayerName(l)))
 ids=[]
 for p,q in zip(pts,pts[1:]):
  if math.dist(p,q)<1e-8:continue
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(p));t.SetEnd(xy(q));t.SetWidth(pcbnew.FromMM(.25));t.SetLayer(l);t.SetNet(b.FindNet(n));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),points_mm=pts,actual_Cu_UUIDs=ids));print('ROUTE',role,len(ids),flush=True)
def via(p,n,role):
 sh=pcbnew.SHAPE_CIRCLE(xy(p),pcbnew.FromMM(.25)+1)
 assert not any(q.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(q.IsOnLayer(l)and q.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for q in b.GetPads()),('Actual shaped .15 registration',p)
 assert all(g.clear([p,p],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]),('Actual barrel clearance',p)
 assert not any(isinstance(t,pcbnew.PCB_VIA)and math.dist(p,mm(t.GetPosition()))<.4495 for t in b.GetTracks()),('Actual hole spacing',p)
 t=pcbnew.PCB_VIA(b);t.SetPosition(xy(p));t.SetWidth(pcbnew.FromMM(.5));t.SetDrill(pcbnew.FromMM(.2));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);t.SetNet(b.FindNet(n));t.SetIsFree(True);t.SetRemoveUnconnected(False);b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role));return p
slow=ps['U11035','1'].GetNetname()
route(mm(ps['U11035','1'].GetPosition()),mm(ps['U11036','2'].GetPosition()),slow,pcbnew.B_Cu,'A_POR_RESET_to_Schmitt_actual_B_surface')
route(mm(ps['U11035','1'].GetPosition()),mm(ps['C11082','1'].GetPosition()),slow,pcbnew.B_Cu,'A_actual_RC_Source_to_POR_only_B_surface')
dest=O/'motherboard-Source27-A-slow-local-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
actual={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};original={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};assert set(original)-set(actual)==removed;assert all(original[u]==actual[u]for u in set(original)&set(actual));assert all(sha(Path(p))==h for p,h in inputs.items());(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,retired_only_eleven_previous_added_A_slow_Cu=sorted(removed),exact_new_Cu=added,routes=routes,no_component_Source_pose_pad_or_original_Cu_change=True,native_Source_reference_power_pending=True),indent=2));print('DRAWN_A_SLOW',len(added),len(removed),flush=True)
