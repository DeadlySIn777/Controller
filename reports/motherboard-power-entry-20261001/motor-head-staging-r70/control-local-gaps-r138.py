"""Actual six literal BankA corridor gaps; no Source/part/land changes."""
import sys,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
BASE=Path('reports/motherboard-power-entry-20261001/motor-bank-A-local-gaps-r128/motor-bank-A-local-gap-candidate.kicad_pcb')
OUT=Path('reports/motherboard-power-entry-20261001/motor-bank-A-local-gaps-r138');OUT.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};padids=set(op);groups=[];seen=set()
for p in b.GetPads():
 uid=p.m_Uuid.AsString()
 if uid in seen:continue
 group=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T})&padids;seen|=group
 if len(group)>1:groups.append((uid,group))
ret={'06e9df2d-4502-4110-a45d-5fea57ebe207','abbb1f20-b8a3-420d-82bb-7fda797117af','af6062e8-9c25-44c3-b186-c28bfe934844'}
assert ret<=set(old)
removed=[dict(uuid=k,identity=old[k])for k in sorted(ret)]
tree=parse(without_generated_fills(BASE.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)]
staged=OUT/'literal-retired-input.kicad_pcb';staged.write_text(dump_board(tree));shutil.copyfile(BASE.with_suffix('.kicad_pro'),staged.with_suffix('.kicad_pro'));shutil.copyfile(BASE.with_suffix('.kicad_dru'),staged.with_suffix('.kicad_dru'));baseboard=b;b=pcbnew.LoadBoard(str(staged));b.BuildConnectivity();g=FastGeometry(b);added=[];routes=[]
def debug():
 pcbnew.SaveBoard(str(OUT/'debug.kicad_pcb'),b);(OUT/'debug.json').write_text(json.dumps(dict(routes=routes,retired=removed,added=added),indent=2))
def route(points,n,l,role,w=.2):
 if not g.clear(points,n,l,w):debug();raise AssertionError(('Native geometry',role,points))
 ids=[]
 for a,z in zip(points,points[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(l);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=points,uuids=ids));print(role,points,flush=True)
def via(pt,n,role):
 assert all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]),('Via',pt,role)
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
pg='/motherboard_power_entry/MOTOR_FEED_PG_A';raw='/motherboard_power_entry/MOTION_5V_RAW'
via((272,177.7),raw,'RAW_third_power_barrel_above_EP_control_envelopes')
route([(272,177.7),(272,178.3)],raw,pcbnew.B_Cu,'RAW_third_power_barrel_actual_B_source_branch',w=.6)
route([(274.1,179.7),(274.1,180.9),(272.7,180.9),(270.1,183.2)],pg,pcbnew.B_Cu,'PG_actual_full_axis_escape_and_ground_barrel_avoidance_B')
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();padmap={p.m_Uuid.AsString():p for p in b.GetPads()};debug()
for uid,group in groups:
 reached={uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(padmap[uid])if v.Type()==pcbnew.PCB_PAD_T};assert group<=reached,('PreviousSOURCE',uid,[(padmap[x].GetParentFootprint().GetReference(),padmap[x].GetNumber(),padmap[x].GetNetname())for x in sorted(group-reached)])
dest=OUT/'motor-bank-A-local-gap-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(ext),dest.with_suffix(ext))
for f in BASE.parent.iterdir():
 if f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
 elif f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(OUT/'drc.json'),str(dest)],capture_output=True,text=True);assert r.returncode==0;d=json.loads((OUT/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();nc={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(nc[k]==v for k,v in old.items()if k not in ret);assert{p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==op;assert set(nc)-set(old)=={v['uuid']for v in added};assert set(old)-set(nc)==ret
rec=dict(before_board=str(BASE),before_board_sha256=sha(BASE),board_sha256=sha(dest),source_components_pads_poses_unchanged=True,exact_added_copper=added,exact_retired_copper=removed,routes=routes,native_errors=errors,native_uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),all_previous_SOURCE_clusters_preserved=len(groups),reference_collars_not_yet_rebuilt=True,manufacturing_ready=False);(OUT/'receipt.json').write_text(json.dumps(rec,indent=2));(OUT/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[v['uuid']for v in added+removed],reviewed_added_zone_UUIDs=[]),indent=2));assert not errors,errors;print('DONE',len(added),len(removed),rec['native_uncapped_joins'],flush=True)
