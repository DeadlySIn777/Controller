"""Copied-native private feed/return repair; the frozen global guard remains unchanged."""
import sys,json,hashlib,math,shutil,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,xy
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import without_generated_fills,dump_board
spec=importlib.util.spec_from_file_location('geometry',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r596/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-three-power-cut-physical-repair-r614');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,Path(__file__),Path('hardware/motherboard/design.json')]};oldb=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString():identity(t)for t in oldb.GetTracks()}
ret={'d026df8e-7e13-4781-834c-610b2a456892','431984e8-60ae-431b-9e38-0dc5fb100077'}
tree=parse(without_generated_fills(B.read_text()));tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in['segment','via']and value(child(x,'uuid')[1])in ret)]
initial=O/'exact-two-new-RAW-feeds-retired.kicad_pcb';initial.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(initial));ts={t.m_Uuid.AsString():t for t in b.GetTracks()};changed=[]
via=ts['be91e795-0007-4adb-9c00-e7085583a5a5'];p=via.GetPosition();q=xy((279.5,167.6));via.SetPosition(q)
for t in b.GetTracks():
 if isinstance(t,pcbnew.PCB_VIA):continue
 if t.GetStart()==p:t.SetStart(q)
 if t.GetEnd()==p:t.SetEnd(q)
for t in b.GetTracks():
 uid=t.m_Uuid.AsString()
 if uid in old and old[uid]!=identity(t):changed.append(dict(uuid=uid,before=old[uid],after=identity(t)))
assert len(changed)==4
g=m.InnerGeometry(b);added=[]
def route(points,role):
 n='/motherboard_power_entry/MOTION_5V_RAW';assert g.clear(points,n,pcbnew.In2_Cu,.25),(role,points)
 for a,c in zip(points,points[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(pcbnew.FromMM(.25));t.SetLayer(pcbnew.In2_Cu);t.SetNet(b.FindNet(n));b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),actual=identity(t),role=role))
route([(261.3,199),(261.3,199.8),(263.813604,201.813604)],'A POR local RAW feed avoiding exact old sub1mm tongue')
route([(261.3,199.8),(263.980761,206.030761)],'A Schmitt local RAW feed avoiding exact old sub1mm tongue')
# Independent drill registration uses actual native shaped SMD lands.
v=via;sh=pcbnew.SHAPE_CIRCLE(v.GetPosition(),v.GetDrillValue()//2+pcbnew.FromMM(.15)+1)
assert not any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads())
assert all(not isinstance(t,pcbnew.PCB_VIA)or t==v or math.dist(mm(t.GetPosition()),mm(v.GetPosition()))>=.4495 for t in b.GetTracks())
dest=O/'motherboard-Source27-private-power-repair-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
new={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert set(old)-set(new)==ret;assert len(set(new)-set(old))==3;assert{u for u in set(old)&set(new)if old[u]!=new[u]}=={r['uuid']for r in changed};assert all(sha(Path(p))==h for p,h in inputs.items())
(O/'actual-Cu.json').write_text(json.dumps(dict(input_hashes=inputs,retired_Cu=sorted(ret),modified_Cu=changed,new_Cu=added,old_Source_parts_pads_poses_unchanged=True,native_refill_Source_current_and_reference_pending=True,manufacturing_ready=False),indent=2));print('POWER_REPAIR',len(changed),len(ret),len(added),flush=True)
