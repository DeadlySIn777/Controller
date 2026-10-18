"""Five actual control-transfer ground stitches on immutable Bank A r83."""
import sys,json,math,shutil,subprocess,collections
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_local_signals import paths
BASE=Path('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb');OUT=Path('reports/motherboard-power-entry-20261001/motor-bank-A-stitches-r96');OUT.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};pads={p.m_Uuid.AsString():p for p in b.GetPads()};ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};groups=[];seen=set()
for uid,p in pads.items():
 if uid in seen:continue
 group=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T})&set(pads);seen|=group
 if len(group)>1:groups.append((uid,group))
g=FastGeometry(b);n='/LOGIC_GND';added=[];rows=[]
def debug():pcbnew.SaveBoard(str(OUT/'debug.kicad_pcb'),b);(OUT/'debug.json').write_text(json.dumps(rows,indent=2))
def route(pts,l,role):
 for a,z in zip(pts,pts[1:]):
  if math.dist(a,z)<1e-8:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(l);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(.25));b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
def via(pt,role):
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
for uid,pt,targets in [
 ('381a78a0-d4f9-4ad2-84a4-3a3d9cf550c4',(270.85,180.8),[(270.85,181.5,pcbnew.F_Cu)]),
 ('2468aa86-c997-4635-83c2-30cb4518d284',(266.925,181.5),[(267.825,181.5,pcbnew.F_Cu)]),
 ('20bba5d3-e10f-427e-af31-845ad6ff265f',(265.975,199.5),[(270.575,199.5,pcbnew.B_Cu),(262.6,198.5,pcbnew.F_Cu)]),
 ('4ff935f5-094a-47ef-b25a-3e2439dcb6b4',(273.725,179.5),[(272.975,180,pcbnew.F_Cu),(274,181.5,pcbnew.F_Cu)]),
 ('650201eb-f3bc-4fa6-8d8d-fae95bcc1e83',(267.075,193),[(263.225,194,pcbnew.B_Cu),(269.35,189,pcbnew.F_Cu)])]:
 sv=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==uid);assert isinstance(sv,pcbnew.PCB_VIA)and math.dist(mm(sv.GetPosition()),pt)<1e-6
 found=None
 for dist in [.8,.9,1.]:
  for dx,dy in [(0,1),(1,0),(-1,0),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)]:
   z=(pt[0]+dist*dx,pt[1]+dist*dy)
   if not all(g.clear([z,z],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
   for tx,ty,l in targets:
    dest=(tx,ty);pts=next((p for p in paths(z,dest)if g.clear(p,n,l,.25)),None)
    if pts is None:pts=g.grid(z,dest,n,l,.25,step=.125,padding=4,max_nodes=17000)
    if pts is not None and g.clear(pts,n,l,.25):found=(z,pts,l);break
   if found:break
  if found:break
 if not found:debug();raise AssertionError(('No actual own ground stitch',uid,pt))
 z,pts,l=found;v=via(z,'control_source_ground_stitch');route(pts,l,'control_actual_source_ground_branch');rows.append(dict(signal_via_uuid=uid,signal_via_xy_mm=pt,ground_via_uuid=v.m_Uuid.AsString(),ground_via_xy_mm=z,distance_mm=math.dist(z,pt),branch_layer=b.GetLayerName(l),branch_points_mm=pts));print('STITCH',rows[-1],flush=True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();source=ps['C11046','2'];check=[]
for row in rows:
 v=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==row['ground_via_uuid']);assert v.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(source)},('SOURCE ground missing',row);check.append(row['ground_via_uuid'])
for uid,group in groups:assert group<=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(pads[uid])if v.Type()==pcbnew.PCB_PAD_T}),('Old SOURCE cluster',uid)
dest=OUT/'motor-bank-A-stitches-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(ext),dest.with_suffix(ext))
for f in BASE.parent.iterdir():
 if f.name=='fp-lib-table':(OUT/f.name).write_text(f.read_text().replace('${KIPRJMOD}',BASE.parent.resolve().as_posix()))
 elif f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(OUT/'drc.json'),str(dest)],capture_output=True,text=True);assert r.returncode==0
q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();nc={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(nc[k]==v for k,v in old.items());assert{p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==op;assert set(nc)-set(old)=={v['uuid']for v in added}
d=json.loads((OUT/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];receipt=dict(board_sha256=sha(dest),before_sha256=sha(BASE),rows=rows,actual_source_ground_reference=['C11046','2'],all_five_ground_vias_native_SOURCE_connected=True,exact_added_copper=added,exact_retired_copper=[],old_pads_poses_copper_zone_definitions_unchanged=True,prior_SOURCE_clusters_preserved=len(groups),native_errors=errors,native_types=dict(collections.Counter(v['type']for v in d['violations'])),manufacturing_ready=False);(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));(OUT/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[v['uuid']for v in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not errors,errors;print('DONE',len(added),q.GetConnectivity().GetUnconnectedCount(False),flush=True)
