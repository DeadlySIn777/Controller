import sys,json,math,shutil,subprocess,collections,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_merge_bounded_pcb_delta import zone_definition
from hardware_build_assembly import parse
from hardware_fix_motor_receiving_heads_native import FastGeometry
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-actual-Source-collars-r14/motherboard-facing-health-Source-collars-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-health-six-registration-r362');assert not O.exists();O.mkdir();b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();old=source_clusters(b);c0={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads0={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};zones0={z.m_Uuid.AsString():zone_definition(z)for z in b.Zones()};frozen={str(v):sha(v)for v in[B,Path(__file__)]}
move={'2abd7d17-f54f-42af-ae0c-d3a8cc238aee':(340.6375,175),'c11a1795-b5ee-4973-8d80-690235c74581':(344.4375,175),'101c36f7-6e92-4bf8-833a-1dc8991187db':(331.8625,187.6),'da3ee2fc-3b76-47c0-ab4d-da8cd2d563bd':(337.3625,175),'e19f5a4a-8797-4ce8-a00d-4c884cc46739':(335.1375,187.6),'84d7ee84-6b83-427c-889a-8b85dcea2e34':(271.725,234.635)}
ts={t.m_Uuid.AsString():t for t in b.GetTracks()};changed=set(move);ledger=[]
for u,pt in move.items():
 v=ts[u];assert isinstance(v,pcbnew.PCB_VIA);before=v.GetPosition();net=v.GetNetname();v.SetPosition(xy(pt));attached=[]
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()!=net:continue
  ends=[]
  if t.GetStart()==before:t.SetStart(xy(pt));ends.append('start')
  if t.GetEnd()==before:t.SetEnd(xy(pt));ends.append('end')
  if ends:attached.append(dict(uuid=t.m_Uuid.AsString(),endpoints=ends));changed.add(t.m_Uuid.AsString())
 assert attached;ledger.append(dict(via_uuid=u,before_mm=mm(before),after_mm=pt,net=net,exact_attached_leaves=attached))
registration=[]
for u in move:
 v=ts[u];pt=mm(v.GetPosition());dr=pcbnew.ToMM(v.GetDrillValue())/2;closest=None
 for p in b.GetPads():
  if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  px,py=mm(p.GetPosition());a=math.radians(p.GetOrientationDegrees());dx=pt[0]-px;dy=pt[1]-py;x=dx*math.cos(a)+dy*math.sin(a);y=-dx*math.sin(a)+dy*math.cos(a);w,h=mm(p.GetSize());gap=math.hypot(max(abs(x)-w/2,0),max(abs(y)-h/2,0))-dr;assert gap>.15+1e-9,('Registration',u,p.GetParentFootprint().GetReference(),p.GetNumber(),gap)
  if closest is None or gap<closest['conservative_gap_mm']:closest=dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),conservative_gap_mm=gap)
 registration.append(dict(via_uuid=u,position_mm=pt,minimum_drill_registration_screen_mm=.15,closest=closest))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());dest=O/'motherboard-health-registration-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for f in B.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,O/f.name)
 elif f.name=='fp-lib-table':(O/f.name).write_text(f.read_text().replace('${KIPRJMOD}',B.parent.resolve().as_posix()))
q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();c1={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert set(c0)==set(c1);assert {u for u in c0 if c0[u]!=c1[u]}==changed;assert all(c0[u][1]==c1[u][1]for u in changed);assert {p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==pads0;assert {z.m_Uuid.AsString():zone_definition(z)for z in q.Zones()}==zones0;source=clusters_preserved(old,q)
run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((O/'drc.json').read_text());assert not d['violations'],d['violations'];assert all(sha(Path(v))==h for v,h in frozen.items());r=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_six_barrel_moves=ledger,exact_changed_Cu_UUIDs=sorted(changed),registration=registration,all_pads_parts_lands_poses_nets_and_unrelated_Cu_preserved=True,all_old_Source_clusters_preserved=source,native_errors=0,native_warnings=0,strict_receiving_controls_reference_and_power_requalification_pending=True,Source26_unchanged=True,manufacturing_ready=False);(O/'receipt.json').write_text(json.dumps(r,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(changed),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact six newly added health barrels outward registration-clearance correction and only attached leaf endpoints; all Source/parts/lands/poses/nets/other Cu/zones preserved.'),indent=2));print('PASS',len(changed),sha(dest),flush=True)
