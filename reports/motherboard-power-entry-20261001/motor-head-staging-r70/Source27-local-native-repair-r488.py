"""Bounded report-only correction of actual first-pass Source27 native conflicts."""
import sys,json,hashlib,math,shutil
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board
B=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r468/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb')
OLD=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb')
ROWS=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-route-r454/debug.json')
O=Path('reports/motherboard-power-entry-20261001/Source27-local-native-repair-r488');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,OLD,ROWS,Path(__file__),Path('hardware/motherboard/design.json')]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();a=pcbnew.LoadBoard(str(OLD));old={t.m_Uuid.AsString():identity(t)for t in a.GetTracks()};rows=json.loads(ROWS.read_text());added={v['uuid']for v in rows['new_Cu']};ret=set(rows['retired']);ret_new=[];snap=[];merged=[];retired_native=[]
f=next(f for f in b.GetFootprints()if f.GetReference()=='R11082');assert mm(f.GetPosition())==(266.5,209.2);pads={p.GetNumber():p.GetPosition()for p in f.Pads()};f.SetPosition(xy((266.,209.2)))
for p in f.Pads():
 for t in b.GetTracks():
  if t.m_Uuid.AsString()not in added or isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()!=p.GetNetname():continue
  for edge in ['Start','End']:
   if getattr(t,'Get'+edge)()==pads[p.GetNumber()]:getattr(t,'Set'+edge)(p.GetPosition());snap.append(dict(uuid=t.m_Uuid.AsString(),edge=edge,reason='Only added resistor footprint moved clear of retained CORE5 copper',pin=p.GetNumber()))
# Reuse the actual existing same-net barrel rather than drilling a second overlap.
while True:
 vias=list(t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.m_Uuid.AsString()not in retired_native);pair=None
 for i,v in enumerate(vias):
  for q in vias[i+1:]:
   if v.GetNetname()!=q.GetNetname()or math.dist(mm(v.GetPosition()),mm(q.GetPosition()))>=.4495:continue
   vu,qu=v.m_Uuid.AsString(),q.m_Uuid.AsString()
   if vu not in added and qu not in added:continue
   keep,drop=(v,q)if vu not in added else (q,v)if qu not in added else(v,q)
   pair=(keep,drop);break
  if pair:break
 if not pair:break
 keep,drop=pair;dp=drop.GetPosition();kp=keep.GetPosition();du=drop.m_Uuid.AsString();assert du in added
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA)or t.m_Uuid.AsString()not in added or t.GetNetname()!=keep.GetNetname():continue
  for edge in ['Start','End']:
   if getattr(t,'Get'+edge)()==dp:getattr(t,'Set'+edge)(kp);snap.append(dict(uuid=t.m_Uuid.AsString(),edge=edge,reason='Added branch follows literal retained same-net barrel',keeper=keep.m_Uuid.AsString()))
 merged.append(dict(retired_added_via=du,actual_keeper=keep.m_Uuid.AsString(),old_position_mm=mm(dp),keeper_position_mm=mm(kp),net=keep.GetNetname()));retired_native.append(drop.m_Uuid.AsString());added.remove(du);ret_new.append(du)
# Source27 FAST outputs currently stay on F copper at the receiving latch.
# These exact two redundant barrels had no actual B contact; retire them.
for u in ['f6652942-7b4b-467e-b5ec-0509996342d6','18e242a8-0992-40ca-98d8-2df889d77497']:
 t=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==u);assert isinstance(t,pcbnew.PCB_VIA)and u in added;assert 'MOTOR_FEED_CLEAR_FAST_N_'in t.GetNetname();retired_native.append(t.m_Uuid.AsString());added.remove(u);ret_new.append(u)
# Exact obsolete old slow-CLR leaf terminates at the now-remapped old CLR handoff.
u='a9438811-a75d-4590-96e6-69040d1ee322';t=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==u);assert identity(t)==old[u]and t.GetNetname().endswith('MOTOR_FEED_CLEAR_N_A');retired_native.append(t.m_Uuid.AsString());ret.add(u)
# Added low-current ground paths must not cut the retained CORE5 In3 power bank.
# Their actual receiving barrels use the existing own-ground reference layers.
removed_inner_ground=[];raw_layer_delta=[]
for t in list(b.GetTracks()):
 u=t.m_Uuid.AsString()
 if u not in added or isinstance(t,pcbnew.PCB_VIA)or t.GetLayer()!=pcbnew.In3_Cu:continue
 if t.GetNetname()=='/LOGIC_GND':removed_inner_ground.append(dict(uuid=u,identity=identity(t)));retired_native.append(t.m_Uuid.AsString());added.remove(u);ret_new.append(u)
 elif t.GetNetname().endswith('/MOTION_5V_RAW'):
  raw_layer_delta.append(dict(uuid=u,before=identity(t)));t.SetLayer(pcbnew.In2_Cu);raw_layer_delta[-1]['after']=identity(t)
# Snap only newly added branch ends physically inside an actual same-net barrel.
vias=[t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.m_Uuid.AsString()not in retired_native]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()not in added or isinstance(t,pcbnew.PCB_VIA):continue
 for edge in ['Start','End']:
  pos=getattr(t,'Get'+edge)();near=[v for v in vias if v.GetNetname()==t.GetNetname()and math.dist(mm(pos),mm(v.GetPosition()))<=.249999]
  if near:
   v=min(near,key=lambda q:math.dist(mm(pos),mm(q.GetPosition())))
   if pos!=v.GetPosition():getattr(t,'Set'+edge)(v.GetPosition());snap.append(dict(uuid=t.m_Uuid.AsString(),edge=edge,reason='Added terminal centered on actual connected barrel',keeper=v.m_Uuid.AsString()))
 if t.GetStart()==t.GetEnd():u=t.m_Uuid.AsString();retired_native.append(t.m_Uuid.AsString());added.remove(u);ret_new.append(u)
dest=O/'motherboard-staged-Source27-local-repaired-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
# Exact old project library context plus the one new reviewed DBV library.
table=parse((OLD.parent/'fp-lib-table').read_text());table.append(['lib',['name','"CNC_MB_FeedReset"'],['type','"KiCad"'],['uri','"'+(B.parent/'CNC_MB_FeedReset.pretty').resolve().as_posix()+'"'],['options','""'],['descr','"TI exact DBV manufacturer lands, Source27 report-only"']]);(O/'fp-lib-table').write_text(dump_board(table))
tree=parse(dest.read_text());tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in['segment','via']and value(child(x,'uuid')[1])in set(retired_native))];dest.write_text(dump_board(tree));new={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()if t.m_Uuid.AsString()not in retired_native};assert set(old)-set(new)==ret;assert set(new)-set(old)==added;assert all(old[u]==new[u]for u in set(old)&set(new))
assert all(sha(Path(p))==h for p,h in inputs.items())
actual=dict(retired=sorted(ret),routes=rows['routes'],new_Cu=[dict(uuid=u,identity=new[u],role='Source27 native-repaired actual Cu')for u in sorted(added)])
(O/'actual-Cu.json').write_text(json.dumps(actual,indent=2));(O/'repair-ledger.json').write_text(json.dumps(dict(input_hashes=inputs,new_resistor_pose=dict(ref='R11082',before_mm=[266.5,209.2],after_mm=[266.,209.2]),reused_actual_barrels=merged,actual_added_endpoint_changes=snap,retired_added_redundant_Cu=ret_new,retired_added_In3_ground=removed_inner_ground,new_low_current_RAW_layer_changes=raw_layer_delta,exact_unchanged_old_Cu_except_seven_proven_old_CLR_leaves=True,Source_clusters_reference_and_global_power_still_require_fresh_native_qualification=True,manufacturing_ready=False),indent=2));print('REPAIRED_UNFILLED',len(added),len(ret),len(merged),'Native/Source/power pending',flush=True)

