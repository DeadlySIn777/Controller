"""Bounded motor receiving-head correction on a native PCB copy, source immutable."""
import argparse,json,math,shutil,subprocess,collections,sys
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_local_signals import paths,GeometryIndex
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import identity,pad_identity,mm,xy,segment_distance
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
REFS=['U11010','U11011','C11057','C11058','C11059','C11060']
POSES={'U11010':((272,179),0),'U11011':((272,186),0),'C11057':((270.2,177),90),'C11058':((275.25,178.5),0),'C11059':((270.2,184),90),'C11060':((275.25,185.5),0)}
class FastGeometry(Geometry):
 def __init__(self,b):
  super().__init__(b);self.barrier_index=GeometryIndex()
  for ref,p in self.barriers:self.barrier_index.add((ref,p),(min(x for x,y in p),min(y for x,y in p),max(x for x,y in p),max(y for x,y in p)))
 def clear(self,ps,n,l,w):
  gap=w/2+.16
  for s,e in zip(ps,ps[1:]):
   if any(not(.8+w/2<=p[0]<=459.2-w/2 and .8+w/2<=p[1]<=339.2-w/2)for p in[s,e]):return False
   if any(hits(s,e,poly,w/2)for ref,poly in self.barrier_index.candidates(s,e,w/2)):return False
   for net,polys,top,bot,npth in self.pads.candidates(s,e,gap):
    if net==n and not npth:continue
    if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(s,e,p,gap)for p in polys):return False
   for net,a,c,width in self.tracks[l].candidates(s,e,gap):
    if net!=n and segment_distance(s,e,a,c)<gap+width/2-1e-6:return False
  return True

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
 inputs={str(p):sha(p)for p in[a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
 b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};owned={p.m_Uuid.AsString()for r in REFS for p in fs[r].Pads()};oldposes={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in REFS};groups=[];seen=set();pids=set(op)
 for p in b.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group=({uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T})&pids;seen|=group
  if len(group)>1:groups.append((uid,group))
 local=json.loads(Path('reports/motherboard-power-entry-20261001/motor-supply-cells-priority-r29/receipt.json').read_text());ret={v['uuid']for v in local['new_copper']if v['role'].startswith(('C11057_','C11058_','C11060_'))};assert len(ret)==26
 for ref,producer in [('U11010','U11032'),('U11011','U11034')]:
  n=ps[ref,'5'].GetNetname();actual={(p.GetParentFootprint().GetReference(),p.GetNumber())for p in b.GetPads()if p.GetNetname()==n};assert actual=={(ref,'5'),(producer,'5'),('R11042'if ref=='U11010'else'R11045','1')};ret|={t.m_Uuid.AsString()for t in b.GetTracks()if t.GetNetname()==n}
 retired=[t for t in list(b.GetTracks())if t.m_Uuid.AsString()in ret];assert len(retired)==len(ret)
 for t in retired:b.Remove(t)
 for r,(point,angle)in POSES.items():fs[r].SetPosition(xy(point));fs[r].SetOrientationDegrees(angle)
 for r in REFS:
  for other in b.GetFootprints():
   if other.GetReference()==r or other.GetLayer()!=fs[r].GetLayer():continue
   assert not intersects(side_box(fs[r]),side_box(other),0),('Court',r,other.GetReference())
 g=FastGeometry(b);added=[];routes=[];via_checks=[]
 def save_debug():pcbnew.SaveBoard(str(a.out/'rejected-debug.kicad_pcb'),b)
 def route_points(pts,n,l,w,role,auto=False,step=.25,padding=10,max_nodes=14000):
  pts=[tuple(v)for v in pts]
  if auto:
   s,e=pts[0],pts[-1];pts=next((p for p in paths(s,e)if g.clear(p,n,l,w)),None)
   if pts is None:pts=g.grid(s,e,n,l,w,step=step,padding=padding,max_nodes=max_nodes)
  if pts is None or not g.clear(pts,n,l,w):save_debug();raise AssertionError(('Path',role,pts,n,b.GetLayerName(l),w))
  ids=[]
  for s,e in zip(pts,pts[1:]):
   if math.dist(s,e)<1e-8:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(l);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),role=role))
  routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=pts,uuids=ids,length_mm=sum(math.dist(s,e)for s,e in zip(pts,pts[1:]))));print('ROUTE',role,round(routes[-1]['length_mm'],2),flush=True)
  return pts
 def via(pt,n,role):
  if not all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):save_debug();raise AssertionError(('Via',pt,n,role))
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));via_checks.append(dict(uuid=v.m_Uuid.AsString(),net=n,point_mm=pt));return v
 raw=ps['U11010','11'].GetNetname();ground=ps['U11010','6'].GetNetname();assert raw=='/motherboard_power_entry/MOTION_5V_RAW'and ground=='/LOGIC_GND'
 route_points([(266.2,171),(266,177)],raw,pcbnew.F_Cu,4,'source_F_RAW_positive')
 for y in[176.3,177,177.7]:via((266,y),raw,'source_RAW_three_parallel_barrels')
 route_points([(266,176.3),(266,177.7)],raw,pcbnew.B_Cu,1.2,'source_barrel_B_join')
 route_points([(266,177),(272,179)],raw,pcbnew.B_Cu,1.6,'shared_RAW_B_head_feeder')
 route_points([(272,178.3),(272,186.7)],raw,pcbnew.B_Cu,1.4,'A_B_RAW_B_head_distribution')
 route_points([(271.8,171),(271,173),(269.35,174.5),(269.35,189)],ground,pcbnew.F_Cu,2,'source_F_own_ground_head_return')
 for bank,u,cin,cout,dy in [('A','U11010','C11057','C11058',0),('B','U11011','C11059','C11060',7)]:
  for y in[178.3+dy,179+dy,179.7+dy]:via((272,y),raw,bank+'_VIN_EP_three_parallel_barrels')
  for pin in['3','4']:
   route_points([mm(ps[u,pin].GetPosition()),mm(ps[u,'11'].GetPosition())],raw,pcbnew.F_Cu,.25,bank+'_VIN_VBIAS_local_'+pin,auto=True)
  route_points([mm(ps[cin,'1'].GetPosition()),(272,179+dy)],raw,pcbnew.B_Cu,.5,bank+'_input_cap_RAW',auto=True)
  ing=mm(ps[cin,'2'].GetPosition());via(ing,ground,bank+'_input_cap_ground');route_points([ing,(269.35,ing[1])],ground,pcbnew.F_Cu,.5,bank+'_input_cap_ground_return')
  out=ps[u,'9'].GetNetname();x0=mm(ps[u,'9'].GetPosition());head=(273.8,178.5+dy)
  route_points([x0,head],out,pcbnew.F_Cu,.25,bank+'_VOUT_short_manufacturer_pin_neck')
  for vpt in[(273.8,177.75+dy),(274.5,177.75+dy),(273.8,178.5+dy)]:via(vpt,out,bank+'_VOUT_three_parallel_barrels')
  route_points([(273.8,177.75+dy),(274.5,177.75+dy)],out,pcbnew.F_Cu,.6,bank+'_output_array_F_join')
  route_points([(273.8,177.75+dy),head],out,pcbnew.F_Cu,.6,bank+'_output_array_F_join_vertical')
  route_points([(273.8,177.75+dy),(274.5,177.75+dy)],out,pcbnew.B_Cu,.6,bank+'_output_array_B_join')
  route_points([(273.8,177.75+dy),head],out,pcbnew.B_Cu,.6,bank+'_output_array_B_join_vertical')
  route_points([head,mm(ps[cout,'1'].GetPosition())],out,pcbnew.B_Cu,.5,bank+'_output_cap_positive')
  gout=mm(ps[cout,'2'].GetPosition());esc=(275.025,176.5)if bank=='A'else(275.025,188.5)
  route_points([gout,esc],ground,pcbnew.B_Cu,.4,bank+'_output_cap_ground_escape',auto=True);via(esc,ground,bank+'_output_cap_ground');route_points([esc,(269.35,esc[1])],ground,pcbnew.F_Cu,.4,bank+'_output_cap_ground_return',auto=True)
  ug=mm(ps[u,'6'].GetPosition());via((274,181.5+dy),ground,bank+'_switch_own_ground');route_points([ug,(274,181.5+dy)],ground,pcbnew.F_Cu,.3,bank+'_switch_GND_local',auto=True);route_points([(274,181.5+dy),(269.35,181.5+dy)],ground,pcbnew.F_Cu,.4,bank+'_switch_GND_source_return')
 # Reconnect actual retained push-pull Q controls. No new logic authority.
 for u,producer,ystart in [('U11010','U11032',181.5),('U11011','U11034',188.8)]:
  n=ps[u,'5'].GetNetname();s=mm(ps[producer,'5'].GetPosition());e=mm(ps[u,'5'].GetPosition());sv=(345.5,203.25)if u=='U11010'else(354.6929,195.9571);ev=(270.85,180.8)if u=='U11010'else(270.85,187.8)
  via(sv,n,u+'_ON_source');via(ev,n,u+'_ON_receive');route_points([s,sv],n,pcbnew.F_Cu,.2,u+'_ON_source_escape',auto=True);route_points([ev,e],n,pcbnew.F_Cu,.2,u+'_ON_receive_escape',auto=True)
  route_points([sv,ev],n,pcbnew.B_Cu,.2,u+'_ON_control',auto=True,step=.5,padding=18,max_nodes=32000)
  rp='R11042'if u=='U11010'else'R11045';rpt=mm(ps[rp,'1'].GetPosition());via(rpt,n,u+'_actual_ON_pulldown');route_points([sv,rpt],n,pcbnew.B_Cu,.2,u+'_actual_ON_pulldown_branch',auto=True,step=.5,padding=15,max_nodes=30000)
 b.BuildConnectivity();qc=b.GetConnectivity();allpads={p.m_Uuid.AsString():p for p in b.GetPads()};checks=[]
 for u,producer,cin,cout in [('U11010','U11032','C11057','C11058'),('U11011','U11034','C11059','C11060')]:
  for r,p,s,q in [(u,'3','C11046','1'),(u,'4','C11046','1'),(u,'11','C11046','1'),(u,'5',producer,'5'),(u,'6','C11046','2'),(cin,'1',u,'11'),(cin,'2','C11046','2'),(cout,'2','C11046','2')]+[(cout,'1',u,v)for v in['8','9','10']]:
   p1,p2=ps[r,p],ps[s,q];yes=p2.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in qc.GetConnectedItems(p1)};assert yes,(r,p,s,q);checks.append(dict(from_ref=r,from_pin=p,to_ref=s,to_pin=q,joined=True))
 preserved=0
 for uid,group in groups:
  assert group<=({uid}|{t.m_Uuid.AsString()for t in qc.GetConnectedItems(allpads[uid])if t.Type()==pcbnew.PCB_PAD_T}),('Prior source cluster',uid);preserved+=1
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'motor-head-feed-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();assert all(op[p.m_Uuid.AsString()]==pad_identity(p)for p in q.GetPads()if p.m_Uuid.AsString()not in owned);after={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(after[k]==v for k,v in old.items()if k not in ret);assert not(ret&set(after));assert all(after[v['uuid']]==v['identity']for v in added)
 subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],check=True,capture_output=True,text=True);d=json.loads((a.out/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];assert all(sha(Path(p))==h for p,h in inputs.items())
 receipt=dict(input_hashes=inputs,board_sha256=sha(dest),old_poses=oldposes,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()),courtyard_mm=side_box(fs[r]))for r in REFS},source_unchanged=True,all_unrelated_pads_copper_preserved=True,prior_source_clusters_preserved=preserved,exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],routes=routes,actual_endpoint_checks=checks,native_drc_types=dict(collections.Counter(v['type']for v in d['violations'])),native_errors=errors,native_uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),pending=['Exact ON control reference-corridor proof','Motor monitor receiving branches and remote driver feed/return rated delivery','Full power loss/noise/thermal and startup qualification'],manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary six-part receiving-head relocation and actual MOTION source/bypass/return/ON reconnection without rail or signal logic changes',reviewed_footprint_references=REFS,reviewed_copper_delta_UUIDs=[v['uuid']for v in added]+sorted(ret),reviewed_added_zone_UUIDs=[]);(a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');print('RESULT',len(added),len(ret),len(errors),receipt['native_uncapped_joins'],flush=True)
if __name__=='__main__':main()



