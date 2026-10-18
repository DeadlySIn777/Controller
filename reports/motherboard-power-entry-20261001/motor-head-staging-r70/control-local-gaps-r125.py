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
BASE=Path('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r120/motor-bank-A-control-repaired-candidate.kicad_pcb')
OUT=Path('reports/motherboard-power-entry-20261001/motor-bank-A-local-gaps-r125');OUT.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};padids=set(op);groups=[];seen=set()
for p in b.GetPads():
 uid=p.m_Uuid.AsString()
 if uid in seen:continue
 group=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T})&padids;seen|=group
 if len(group)>1:groups.append((uid,group))
ret={'8c9a5cc8-ae5b-4c09-992c-674dd77f141d','45cf7e03-0aca-4392-9815-e285af0e7efb','70c204e0-9a26-45e0-a11e-0ef2eea07b8e','2981b720-d782-4814-97d7-ffa52809adb8','e08264ee-8ed8-4114-ac2a-550e76d7a638','d218fc26-a6f4-4858-84a1-89b7383ebeb0','1e5edf46-94df-46ee-8822-ceb5201dd05a','83997739-bb91-41fb-989e-fb9e739e4067','b15e17a6-6c69-441d-8fdb-b69483c87622','02111491-8ec2-4c45-b76f-ed6fdcd27a50','376db329-1ae7-4bfc-9d00-22b844ce0ea6'}
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
on='/motherboard_power_entry/MOTOR_FEED_ON_A';pg='/motherboard_power_entry/MOTOR_FEED_PG_A';clr='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A';ground='/LOGIC_GND'
route([(270.85,180.8),(269.7,180.8),(269.7,180),(271.025,180)],on,pcbnew.F_Cu,'ON_actual_RAW_antipad_avoidance_F')
route([(274.1,179.7),(274.1,180.8),(270.1,183.2)],pg,pcbnew.B_Cu,'PG_actual_full_transfer_escape_B')
route([(267.1,183.2),(266.45,183.2),(265.85,183.95)],pg,pcbnew.B_Cu,'PG_actual_output_power_antipad_avoidance_B')
route([(265.975,199.5),(267.075,199.5),(267.075,197.25),(265.4,197.25)],clr,pcbnew.F_Cu,'CLR_actual_full_transfer_escape_and_cap_F')
via((275.0,179.7),ground,'PG_SOURCE_return_stitch_0p9mm')
route([(275.0,179.7),(275.0,180.3),(272.975,180.0)],ground,pcbnew.F_Cu,'PG_SOURCE_ground_actual_switch_pin_F',w=.25)
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
