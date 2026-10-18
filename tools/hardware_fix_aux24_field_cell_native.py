"""Bounded actual seven-part AUX24_A field cell placement and complete local loops.
Source circuit/MPNs/pad UUIDs are immutable. Low-current field source, not an
additional board or an insulated-system certification. Native copy only.
"""
import argparse,json,shutil,subprocess,collections,math
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
from hardware_route_local_signals import paths
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
REFS=['U11015','R11056','R11057','R11058','C11068','C11069','C11070']
POSES={'U11015':((355,205),0),'R11056':((358.2,209),0),'R11057':((350.3,201.5),0),'R11058':((358,201.5),0),'C11068':((360,206.5),0),'C11069':((350.3,204),180),'C11070':((361.5,204),0)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);frozen={str(p):sha(p)for p in[a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]};b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldpose={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in REFS};groups=[];seen=set();alloldpads={p.m_Uuid.AsString()for p in b.GetPads()};owned={p.m_Uuid.AsString()for r in REFS for p in fs[r].Pads()}
 for p in b.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group=({uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T})&alloldpads;seen|=group
  if len(group)>1:groups.append((uid,group))
 retire_ids=set()
 for r in REFS:
  f=fs[r]
  for p in f.Pads():
   connected=co.GetConnectedItems(p);retire_ids|={t.m_Uuid.AsString()for t in connected if t.Type()in[pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T]};assert not({t.m_Uuid.AsString()for t in connected if t.Type()==pcbnew.PCB_PAD_T}-owned),('Already joined external source pads',r,p.GetNumber())
  if r!='C11068'and f.GetLayer()!=pcbnew.F_Cu:f.Flip(f.GetPosition(),False)
  point,angle=POSES[r];f.SetPosition(xy(point));f.SetOrientationDegrees(angle)
 retired=[t for t in list(b.GetTracks())if t.m_Uuid.AsString()in retire_ids];assert len(retired)==4;assert all(t.GetNetname()=='/motherboard_power_entry/AUX24_A_RTN'for t in retired)
 for t in retired:b.Remove(t)
 for r in REFS:
  f=fs[r];box=side_box(f)
  for other in b.GetFootprints():
   if other.GetReference()==r or other.GetLayer()!=f.GetLayer():continue
   assert not intersects(box,side_box(other),0),('Actual courtyard collision',r,other.GetReference())
 outfolder=a.out;g=Geometry(b);ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};added=[];loops=[]
 def route(r,p,s,q,w):
  x,y=ps[r,str(p)],ps[s,str(q)];n=x.GetNetname();assert n==y.GetNetname();start,end=mm(x.GetPosition()),mm(y.GetPosition());path=next((v for v in paths(start,end)if g.clear(v,n,pcbnew.F_Cu,w)),None)
  if path is None:path=g.grid(start,end,n,pcbnew.F_Cu,w,step=.2,padding=6,max_nodes=7000)
  if path is None:pcbnew.SaveBoard(str(outfolder/'rejected-field-debug.kicad_pcb'),b)
  assert path is not None,(r,p,s,q);uids=[]
  for a,c in zip(path,path[1:]):
   if math.dist(a,c)<1e-7:continue
   assert g.clear([a,c],n,pcbnew.F_Cu,w);t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);uids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
  loops.append(dict(from_ref=r,from_pin=str(p),to_ref=s,to_pin=str(q),net=n,width_mm=w,path_mm=path,added_uuids=uids,length_mm=sum(math.dist(a,c)for a,c in zip(path,path[1:]))))
 def own_via(pt,n,size=.5):
  if not all(g.clear([pt,pt],n,l,size)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):pcbnew.SaveBoard(str(outfolder/'rejected-field-debug.kicad_pcb'),b)
  assert all(g.clear([pt,pt],n,l,size)for l in[pcbnew.F_Cu,pcbnew.B_Cu]),('Own field barrel clearance',pt,n)
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(size));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v)));return v
 def layer_route(start,end,n,layer,w=.2):
  def clear(v):
   if layer in[pcbnew.F_Cu,pcbnew.B_Cu]:return g.clear(v,n,layer,w)
   from hardware_route_logic_return import segment_distance
   from hardware_route_power_groups_native import hits
   for s,e in zip(v,v[1:]):
    if any(hits(s,e,poly,w/2)for _,poly in g.barriers):return False
    for t in b.GetTracks():
     if t.GetNetname()==n or not t.IsOnLayer(layer):continue
     tw=pcbnew.ToMM(t.GetWidth(layer)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())
     if segment_distance(s,e,mm(t.GetStart()),mm(t.GetEnd()))<w/2+tw/2+.16:return False
   return True
  pp=next((v for v in paths(start,end)if clear(v)),None)
  if pp is None and layer in[pcbnew.F_Cu,pcbnew.B_Cu]:pp=g.grid(start,end,n,layer,w,step=.2,padding=5,max_nodes=5000)
  assert pp is not None,('Actual same-field private layer path',n,start,end,b.GetLayerName(layer));uids=[]
  for s,e in zip(pp,pp[1:]):
   if math.dist(s,e)<1e-7:continue
   assert clear([s,e]);t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(layer);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);uids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
  return pp,uids
 ilim=ps['U11015','7'].GetNetname();dvd=ps['U11015','8'].GetNetname();rtn=ps['U11015','11'].GetNetname();ground=ps['U11015','6'].GetNetname();assert rtn!=ground
 p7=mm(ps['U11015','7'].GetPosition());p8=mm(ps['U11015','8'].GetPosition());p9=mm(ps['U11015','9'].GetPosition());fault=ps['U11015','9'].GetNetname();a7=(p7[0]+1,p7[1]+.5);a8=(p8[0]+1.6,p8[1]+.05);a9=(p9[0]+1,p9[1]-.2);own_via(a7,ilim);own_via(a8,dvd);own_via(a9,fault);own_via(mm(ps['R11058','2'].GetPosition()),fault);layer_route(p7,a7,ilim,pcbnew.F_Cu);layer_route(p8,a8,dvd,pcbnew.F_Cu);layer_route(p9,a9,fault,pcbnew.F_Cu)
 ar=mm(ps['U11015','11'].GetPosition());own_via(ar,rtn)
 for r,p in[('R11056','1'),('R11056','2'),('C11068','1')]:own_via(mm(ps[r,p].GetPosition()),ps[r,p].GetNetname())
 for row in [('C11069',1,'U11015',1,.3),('C11070',1,'U11015',10,.3),('C11069',2,'U11015',6,.3),('C11070',2,'U11015',6,.3),('R11057',1,'U11015',1,.2),('R11057',2,'U11015',2,.2),('U11015',3,'U11015',11,.2),('U11015',5,'U11015',11,.2)]:route(*row)
 pp,ids=layer_route(a9,mm(ps['R11058','2'].GetPosition()),fault,pcbnew.In3_Cu);loops.append(dict(from_ref='U11015',from_pin='9',to_ref='R11058',to_pin='2',net=fault,width_mm=.2,path_mm=pp,added_uuids=ids,layer='In3.Cu'))
 pp,ids=layer_route(a7,mm(ps['R11056','1'].GetPosition()),ilim,pcbnew.In3_Cu);loops.append(dict(from_ref='U11015',from_pin='7',to_ref='R11056',to_pin='1',net=ilim,width_mm=.2,path_mm=pp,added_uuids=ids,layer='In3.Cu'))
 pp,ids=layer_route(a8,mm(ps['C11068','1'].GetPosition()),dvd,pcbnew.In3_Cu);loops.append(dict(from_ref='U11015',from_pin='8',to_ref='C11068',to_pin='1',net=dvd,width_mm=.2,path_mm=pp,added_uuids=ids,layer='In3.Cu'))
 for r,p in[('R11056','2'),('C11068','2')]:
  pp,ids=layer_route(mm(ps[r,p].GetPosition()),ar,rtn,pcbnew.B_Cu);loops.append(dict(from_ref=r,from_pin=p,to_ref='U11015',to_pin='11',net=rtn,width_mm=.2,path_mm=pp,added_uuids=ids,layer='B.Cu'))
 small_rules=[]
 ground=ps['U11015','6'].GetNetname();assert ground=='/motherboard_motors/FIELD_GND';assert ground!=ps['U11015','11'].GetNetname();pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'aux24-field-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 assert not small_rules,'This cell uses conventional 0.50/0.20 staggered control vias; no new DFM exception'
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();qc=q.GetConnectivity();qp={p.m_Uuid.AsString():p for p in q.GetPads()};assert all(op[k]==pad_identity(p)for k,p in qp.items()if k not in owned);assert {k:v for k,v in old.items()if k not in retire_ids}=={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()if t.m_Uuid.AsString()in old};assert not(retire_ids&{t.m_Uuid.AsString()for t in q.GetTracks()});preserved=0
 for uid,group in groups:
  assert group<=({uid}|{t.m_Uuid.AsString()for t in qc.GetConnectedItems(qp[uid])if t.Type()==pcbnew.PCB_PAD_T}),('Old actual source cluster',uid);preserved+=1
 checks=[]
 for row in loops+ [dict(from_ref='C11069',from_pin='2',to_ref='U11015',to_pin='6'),dict(from_ref='C11070',from_pin='2',to_ref='U11015',to_pin='6')]:
  p=ps[row['from_ref'],row['from_pin']];p2=ps[row['to_ref'],row['to_pin']];yes=p2.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in qc.GetConnectedItems(qp[p.m_Uuid.AsString()])};checks.append(dict(**row,actual_native_joined=yes));assert yes,(row['from_ref'],row['to_ref'])
 subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],check=True,capture_output=True,text=True);d=json.loads((a.out/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];r=dict(input_hashes=frozen,board_sha256=sha(dest),old_poses=oldpose,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()),courtyard_mm=side_box(fs[r]))for r in REFS},all_unrelated_pad_copper_preserved=True,actual_old_source_clusters_preserved=preserved,source_contract_unchanged=True,exact_added_copper=added,exact_retired_private_copper=[dict(uuid=uid,identity=old[uid])for uid in sorted(retire_ids)],exact_added_zones=[],actual_local_endpoint_checks=checks,native_errors=errors,native_types=dict(collections.Counter(v['type']for v in d['violations'])),native_joins=q.GetConnectivity().GetUnconnectedCount(False),external_feed_routing_pending=['FIELD_A_24V_PROTECTED','FIELD_5V','FIELD_GND','AUX_24V_A','AUX24_A_FAULT_N'],present_normal_output_allocation_a=.148,source_output_current_limit_upper_a=.30,field_return_reference_refresh_required=True,loaded_current_limit_timing_physical_qualified=False,manufacturing_ready=False);assert all(sha(Path(p))==h for p,h in frozen.items());(a.out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual U11015 seven-part own-field placement and all local source/return/UVLO/ILIM/DVDT/fault-pullup loops, freeing the retained motor-switch VIN barrel region; exact source/lands/UUIDs preserved',reviewed_footprint_references=REFS,reviewed_copper_delta_UUIDs=[v['uuid']for v in added],reviewed_added_zone_UUIDs=[],reviewed_removed_copper_UUIDs=sorted(retire_ids));(a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in['input_hashes','exact_added_copper','actual_local_endpoint_checks','native_errors']}))
if __name__=='__main__':main()





