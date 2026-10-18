"""Bounded actual low-current supply barrel and PG corridor repair; source intact."""
import sys,json,math,shutil,subprocess,collections
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import identity,pad_identity,mm,xy,segment_distance
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_route_local_signals import paths
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
BASE=Path('reports/motherboard-power-entry-20261001/motor-bank-A-stitches-r96/motor-bank-A-stitches-candidate.kicad_pcb');OUT=Path('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r110');OUT.mkdir(exist_ok=False);b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};groups=[];seen=set();padids={p.m_Uuid.AsString()for p in b.GetPads()}
for p in b.GetPads():
 uid=p.m_Uuid.AsString()
 if uid in seen:continue
 group=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T})&padids;seen|=group
 if len(group)>1:groups.append((uid,group))
source=json.loads(Path('reports/motherboard-power-entry-20261001/motor-bank-A-r83/receipt.json').read_text());pathsold=json.loads(Path('reports/motherboard-power-entry-20261001/motor-bank-A-r83/debug.json').read_text())['routes'];ret=set();supplyuids={'26c92cb1-0b80-41de-b79d-68147f7dd7f9','4663a883-a66a-476c-b1bd-3247507a0165','55f03bbb-d922-42e0-a26d-d42e25a4f8e1','5ac34f9f-13bd-4b81-81be-893145e8318a','d297e46c-39cf-4517-9efc-382fb9a4a32d'}
positions={tuple(next(t for t in b.GetTracks()if t.m_Uuid.AsString()==uid).GetPosition())for uid in supplyuids};ret|=supplyuids
for t in b.GetTracks():
 if not isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()=='/motherboard_power_entry/MOTION_5V_RAW'and (tuple(t.GetStart())in positions or tuple(t.GetEnd())in positions):ret.add(t.m_Uuid.AsString())
assert len(ret)==15
ret.add('553cd15c-0379-434b-b682-5fba3c9485e2')
for r in pathsold:
 if r['role'].startswith('A_PG_actual_pullup'):ret|=set(r['uuids'])
ret.add('4ff935f5-094a-47ef-b25a-3e2439dcb6b4');ret.add('cf23aad1-587e-4cb5-a5ca-b8946ad6aef5');ret.add('17179fc3-d2ee-44ec-854b-57290f4abdee')if False else None
# The exact redundant R11042 pad-to-via leg is removed; the new long segment traverses that real pad.
for r in pathsold:
 if r['role']=='A_ON_actual_referenced_control_from_escape':ret|=set(r['uuids'])
removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()in ret:removed.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
assert len(removed)==len(ret),(len(removed),len(ret))
tree=parse(without_generated_fills(BASE.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];staged=OUT/'literal-retired-input.kicad_pcb';staged.write_text(dump_board(tree));baseboard=b;b=pcbnew.LoadBoard(str(staged));b.BuildConnectivity();ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};g=FastGeometry(b);added=[];routes=[];vias=[]
def debug():pcbnew.SaveBoard(str(OUT/'debug.kicad_pcb'),b);(OUT/'debug.json').write_text(json.dumps(dict(routes=routes,retired=removed,added=added),indent=2))
def route(points,n,l,role,w=.25,auto=False,step=.125,padding=5,maxnodes=22000,guard=False):
 points=[tuple(p)for p in points]
 def clear(p):
  if not g.clear(p,n,l,w):return False
  if guard:
   for t in b.GetTracks():
    if not isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()in[n,'/LOGIC_GND']:continue
    if any(segment_distance(a,z,mm(t.GetPosition()),mm(t.GetPosition()))<1.051 for a,z in zip(p,p[1:])):return False
  return True
 if auto:
  s,e=points[0],points[-1];points=next((p for p in paths(s,e)if clear(p)),None)
  if points is None:
   original=g.clear;g.clear=lambda p,net,layer,width:original(p,net,layer,width)and (not guard or all(segment_distance(a,z,mm(t.GetPosition()),mm(t.GetPosition()))>=1.051 for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()not in[net,'/LOGIC_GND']for a,z in zip(p,p[1:])));points=g.grid(s,e,n,l,w,step=step,padding=padding,max_nodes=maxnodes);g.clear=original
 if points is None or not clear(points):debug();raise AssertionError(('Route',role,points))
 ids=[]
 for a,z in zip(points,points[1:]):
  if math.dist(a,z)<1e-8:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(l);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=points,uuids=ids));print('ROUTE',role,points,flush=True)
def via(pt,n,role):
 if not all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):debug();raise AssertionError(('Via',pt,role))
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));vias.append(v.m_Uuid.AsString());return v
raw='/motherboard_power_entry/MOTION_5V_RAW'
for u,c,z in [('U11031','C11084',(257.95,194.3)),('U11033','C11087',(252.95,194.3))]:
 via(z,raw,u+'_VDD_clean_barrel');route([mm(ps[u,'5'].GetPosition()),z],raw,pcbnew.F_Cu,u+'_actual_VCC_F',auto=True);route([z,mm(ps[c,'1'].GetPosition())],raw,pcbnew.B_Cu,u+'_own_bypass_positive_B',auto=True)
z=(265.7,195.9);via(z,raw,'DFF_VCC_PRE_clean_barrel');route([mm(ps['U11032','8'].GetPosition()),z],raw,pcbnew.F_Cu,'DFF_VCC_actual_F',auto=True);route([mm(ps['U11032','7'].GetPosition()),mm(ps['U11032','8'].GetPosition())],raw,pcbnew.F_Cu,'DFF_PRE_actual_tie_F');route([z,mm(ps['C11083','1'].GetPosition())],raw,pcbnew.B_Cu,'DFF_VCC_own_bypass_B',auto=True)
route([(263.225,194.),(262.1,194.),(262.1,198.5),(262.6,198.5)],'/LOGIC_GND',pcbnew.B_Cu,'DFF_own_bypass_return_clear_supply_barrel',auto=True)
z2=(263.2,195.1);via(z2,raw,'DFF_D_clean_barrel');route([mm(ps['U11032','2'].GetPosition()),(263.2,196.75),z2],raw,pcbnew.F_Cu,'DFF_D_actual_HIGH_F');route([z2,z],raw,pcbnew.B_Cu,'DFF_D_actual_VCC_B',auto=True)
onn=ps['U11010','5'].GetNetname();route([(264.4,181.5),(266.925,181.5)],onn,pcbnew.F_Cu,'ON_Q_actual_R11042_pad_and_via',w=.2)
pgn=ps['U11010','7'].GetNetname();pg=(274.3,179.85);via(pg,pgn,'PG_actual_clean_source_barrel');route([mm(ps['U11010','7'].GetPosition()),pg],pgn,pcbnew.F_Cu,'PG_actual_source_F',w=.2,auto=True)
route([pg,(269.5,193.)],pgn,pcbnew.B_Cu,'PG_actual_reference_clean_B',w=.2,auto=True,step=.25,padding=10,maxnodes=70000,guard=True);route([(269.5,193.),(267.075,193.)],pgn,pcbnew.B_Cu,'PG_actual_receiver_final_B',w=.2,guard=True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();padmap={p.m_Uuid.AsString():p for p in b.GetPads()}
for uid,group in groups:
 assert group<=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(padmap[uid])if v.Type()==pcbnew.PCB_PAD_T}),('PreviousSOURCE',uid)
dest=OUT/'motor-bank-A-control-repaired-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(ext),dest.with_suffix(ext))
for f in BASE.parent.iterdir():
 if f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
 elif f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(OUT/'drc.json'),str(dest)],capture_output=True,text=True);assert r.returncode==0;d=json.loads((OUT/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();nc={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(nc[k]==v for k,v in old.items()if k not in ret);assert{p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==op;assert set(nc)-set(old)=={v['uuid']for v in added};assert set(old)-set(nc)==ret
rec=dict(before_board_sha256=sha(BASE),board_sha256=sha(dest),source_components_pads_poses_unchanged=True,exact_added_copper=added,exact_retired_copper=removed,routes=routes,native_errors=errors,native_uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),all_previous_SOURCE_clusters_preserved=len(groups),reference_collars_not_yet_rebuilt=True,manufacturing_ready=False);(OUT/'receipt.json').write_text(json.dumps(rec,indent=2));(OUT/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[v['uuid']for v in added+removed],reviewed_added_zone_UUIDs=[]),indent=2));assert not errors,errors;print('DONE',len(added),len(removed),rec['native_uncapped_joins'],flush=True)



