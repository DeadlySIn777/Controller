"""Native actual health-driver supply/return pass; no source or placement change."""
import argparse,collections,json,math,shutil,subprocess,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_local_signals import paths
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
 hashes={str(p):sha(p)for p in[a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
 b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};groups=[];seen=set();pids=set(op)
 for p in b.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group=({uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T})&pids;seen|=group
  if len(group)>1:groups.append((uid,group))
 g=FastGeometry(b);added=[];routes=[];checks=[];vias=[];anchors={};alive=[]
 def debug():
  pcbnew.SaveBoard(str(a.out/'debug.kicad_pcb'),b);(a.out/'debug.json').write_text(json.dumps(dict(routes=routes,exact_added_copper=added),indent=2))
 def points(pts,n,l,w,role,auto=True,step=.25,padding=7,max_nodes=17000):
  pts=[tuple(v)for v in pts]
  if auto:
   s,e=pts[0],pts[-1];pts=next((p for p in paths(s,e)if g.clear(p,n,l,w)),None)
   if pts is None:pts=g.grid(s,e,n,l,w,step=step,padding=padding,max_nodes=max_nodes)
  if pts is None or not g.clear(pts,n,l,w):debug();raise AssertionError(('Path',role,pts,n,b.GetLayerName(l),w))
  ids=[]
  for s,e in zip(pts,pts[1:]):
   if math.dist(s,e)<1e-7:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(l);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),role=role))
  routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=pts,uuids=ids,length_mm=sum(math.dist(s,e)for s,e in zip(pts,pts[1:]))));print('ROUTE',role,round(routes[-1]['length_mm'],2),flush=True);return pts
 def via(pt,n,role):
  if not all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):debug();raise AssertionError(('Via',pt,n,role))
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));vias.append(dict(uuid=v.m_Uuid.AsString(),net=n,point_mm=pt));return v
 def anchor(r,pn,l,role):
  p=ps[r,str(pn)];n=p.GetNetname();pt=mm(p.GetPosition());k=(r,str(pn),l)
  if k in anchors:return anchors[k]
  if (r,str(pn))==('U11026','2'):
   z=(329.,189.);via(z,n,role+'_via');points([pt,z],n,pcbnew.F_Cu,.25,role+'_escape',step=.125,padding=4,max_nodes=15000);anchors[k]=z;return z
  if p.IsOnLayer(l):anchors[k]=pt;return pt
  for v in b.GetTracks():
   if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()==n and math.dist(mm(v.GetPosition()),pt)<1e-5:anchors[k]=pt;return pt
  side=pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu)else pcbnew.B_Cu
  cand=[]
  for d in [.75,1.,1.25,1.5,2.,2.5]:
   for dx,dy in [(1,0),(-1,0),(0,-1),(0,1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)]:
    z=(pt[0]+d*dx,pt[1]+d*dy)
    if all(g.clear([z,z],n,ly,.5)for ly in[pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([pt,z],n,side,.25):cand.append(z)
  if not cand:debug();raise AssertionError(('No conventional own pin barrel',r,pn,n,pt))
  z=cand[0];via(z,n,role+'_via');points([pt,z],n,side,.25,role+'_escape',False);anchors[k]=z;return z
 def wire(r,pn,s,qn,w=.2,l=pcbnew.F_Cu,role=None,**opts):
  p,q=ps[r,str(pn)],ps[s,str(qn)];n=p.GetNetname();assert n and n==q.GetNetname(),(r,pn,s,qn,n,q.GetNetname());role=role or r+'.'+str(pn)+'_to_'+s+'.'+str(qn)
  x=anchor(r,pn,l,role+'_from');y=anchor(s,qn,l,role+'_to');points([x,y],n,l,w,role,**opts);checks.append(dict(from_ref=r,from_pin=str(pn),to_ref=s,to_pin=str(qn),role=role));return

 # Each actual driver is joined to its own designated 100 nF bypass first.
 for u,c in [('U11019','C11078'),('U11020','C11079'),('U11025','C11080'),('U11026','C11081')]:
  wire(u,'5',c,'1',.25,pcbnew.B_Cu,role=u+'_own_bypass_positive')
  wire(u,'2',c,'2',.25,pcbnew.B_Cu,role=u+'_own_bypass_return')
 # Actual source power; these are supply/return conductors, never clock references.
 for u,c in [('U11019','C11078'),('U11020','C11079')]:
  wire(u,'5','C11029','1',.3,pcbnew.F_Cu,role=c+'_actual_CORE_source',step=.5,padding=35,max_nodes=130000)
 for c in ['C11080','C11081']:
  wire(c,'1','C11055','1',.3,pcbnew.B_Cu,role=c+'_actual_FIELD_source',step=.5,padding=35,max_nodes=130000)
 # Native reference fills only receive a ground barrel when actually SOURCE-backed.
 for r,pn,source in [('U11019','2','C11088'),('U11020','2','C11088'),('U11025','2','C11055'),('U11026','2','C11055'),('R11048','2','C11088'),('R11068','2','C11088'),('R11070','2','C11055'),('R11072','2','C11055')]:
  anchor(r,pn,pcbnew.B_Cu,role=r+'_actual_ground_receive');checks.append(dict(from_ref=r,from_pin=pn,to_ref=source,to_pin='2',role=r+'_actual_SOURCE_return'))
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();qc=b.GetConnectivity();allpads={p.m_Uuid.AsString():p for p in b.GetPads()};preserved=0
 for row in checks:
  p,q=ps[row['from_ref'],row['from_pin']],ps[row['to_ref'],row['to_pin']]
  if q.m_Uuid.AsString()not in{v.m_Uuid.AsString()for v in qc.GetConnectedItems(p)}:debug();raise AssertionError(('Actual SOURCE endpoint missing',row))
 for uid,group in groups:
  assert group<=({uid}|{t.m_Uuid.AsString()for t in qc.GetConnectedItems(allpads[uid])if t.Type()==pcbnew.PCB_PAD_T}),('Prior SOURCE cluster',uid);preserved+=1
 dest=a.out/'motor-health-supply-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();new={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert {p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==op;assert all(new[k]==v for k,v in old.items());assert set(new)-set(old)=={v['uuid']for v in added}
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];assert all(sha(Path(p))==h for p,h in hashes.items())
 receipt=dict(input_hashes=hashes,board_sha256=sha(dest),all_old_poses_pads_copper_zone_definitions_preserved=True,prior_source_clusters_preserved=preserved,exact_added_copper=added,exact_retired_copper=[],routes=routes,actual_endpoint_checks=checks,native_errors=errors,native_types=dict(collections.Counter(v['type']for v in d['violations'])),native_uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),engineering_gates=['Loaded MC-health pull-up correction required before aggregate input fanout is accepted','Actual upstream field/core health producers still require complete signal routing and reference proof','Loaded rail/partial-power/20 ms measurements remain incomplete'],manufacturing_ready=False)
 (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');(a.out/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Actual upstream health-driver power, designated local bypass loops and SOURCE-backed return/default bias closure',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[v['uuid']for v in added],reviewed_added_zone_UUIDs=[]),indent=2)+'\n');print('RESULT',len(added),len(errors),receipt['native_uncapped_joins'],flush=True)
if __name__=='__main__':main()
