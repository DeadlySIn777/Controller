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
B=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r490/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');OLD=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb');ROW=Path('reports/motherboard-power-entry-20261001/Source27-local-native-repair-r488/actual-Cu.json');O=Path('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r518');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in [B,OLD,ROW,Path(__file__),Path('hardware/motherboard/design.json')]};b0=pcbnew.LoadBoard(str(B));r=json.loads(ROW.read_text());new={v['uuid']for v in r['new_Cu']};private={'/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B'};removed={t.m_Uuid.AsString()for t in b0.GetTracks()if t.m_Uuid.AsString()in new and t.GetNetname()in private}
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
slow=ps['U11037','1'].GetNetname();fast=ps['U11038','4'].GetNetname()
route(mm(ps['U11037','1'].GetPosition()),mm(ps['U11038','2'].GetPosition()),slow,pcbnew.B_Cu,'POR_RESET_to_Schmitt_B_surface')
sv=next(t for t in b.GetTracks()if t.m_Uuid.AsString()=='424d779e-50eb-4af0-a169-7d81bb3b571f');assert sv.GetNetname()==slow;porv=via((257.9,152.05),slow,'POR_slow_actual_B_In3_transition');route(mm(ps['U11037','1'].GetPosition()),porv,slow,pcbnew.B_Cu,'POR_slow_short_B_surface');route(mm(sv.GetPosition()),porv,slow,pcbnew.In3_Cu,'Actual_slow_RC_Source_to_POR_In3_requires_own_In4_reference')
route(mm(ps['U11038','4'].GetPosition()),mm(ps['R11083','1'].GetPosition()),fast,pcbnew.B_Cu,'FAST_output_to_pulldown_B_surface')
fv=via((263.599999,155.4),fast,'FAST_actual_Source_B_In3_transition');route(mm(ps['U11038','4'].GetPosition()),fv,fast,pcbnew.B_Cu,'FAST_Source_short_B_surface');pv=via((267.9,155.05),fast,'FAST_actual_receiving_F_B_transition');route(fv,pv,fast,pcbnew.In3_Cu,'FAST_Source_In3_to_actual_receiving_transition_requires_own_In4_reference');route(pv,mm(ps['U11034','6'].GetPosition()),fast,pcbnew.F_Cu,'Only_short_FAST_receiving_F_surface')
gv=via((266.95,155.05),'/LOGIC_GND','FAST_actual_receiving_return_transition');route(gv,mm(ps['C11086','2'].GetPosition()),'/LOGIC_GND',pcbnew.B_Cu,'FAST_receiving_return_to_actual_old_Source_cap')
dest=O/'motherboard-staged-Source27-B-controls-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
shutil.copyfile(B.parent/'fp-lib-table',O/'fp-lib-table');a=pcbnew.LoadBoard(str(OLD));old={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};actual={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert set(old)-set(actual)==set(r['retired']);assert all(old[u]==actual[u]for u in set(old)&set(actual));(O/'actual-Cu.json').write_text(json.dumps(dict(retired=r['retired'],routes=routes,new_Cu=[dict(uuid=u,identity=actual[u],role='Actual Source27 reset Cu')for u in sorted(set(actual)-set(old))]),indent=2));assert all(sha(Path(p))==h for p,h in inputs.items());(O/'repair-ledger.json').write_text(json.dumps(dict(input_hashes=inputs,retired_only_prior_added_B_private_Cu=sorted(removed),new_short_F_receiving_transition_mm=pv,actual_receiving_return_mm=gv,all_original_Cu_unchanged_except_exact_seven_old_CLR_leaves=True,native_Source_reference_power_pending=True,manufacturing_ready=False),indent=2));print('DRAWN',len(added),'F_CORE5 fill/Source proof pending',flush=True)




