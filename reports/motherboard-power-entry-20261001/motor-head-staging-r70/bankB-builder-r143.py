"""Bounded Bank A receiving circuit on a native copy; no electrical changes."""
import argparse,collections,json,math,shutil,subprocess,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_local_signals import paths
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
POSEFILE=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankB-poses-r136.json')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
 hashes={str(p):sha(p)for p in [a.board,Path(__file__),POSEFILE,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]}
 b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};poses=json.loads(POSEFILE.read_text());refs=set(poses);owned={p.m_Uuid.AsString()for r in refs for p in fs[r].Pads()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpose={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in refs}
 groups=[];seen=set();pids=set(op)
 for p in b.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group=({uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T})&pids;seen|=group
  if len(group)>1:groups.append((uid,group))
 ret=set();private=set()
 for r in refs:
  for p in fs[r].Pads():
   n=p.GetNetname();allp=[v for v in b.GetPads()if v.GetNetname()==n]
   if n.startswith('/')and all(v.m_Uuid.AsString()in owned for v in allp):private.add(n)
   cc=list(co.GetConnectedItems(p));pp={v.m_Uuid.AsString()for v in cc if v.Type()==pcbnew.PCB_PAD_T}
   if pp<=owned:ret|={v.m_Uuid.AsString()for v in cc if v.Type()in[pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T]}
   for t in b.GetTracks():
    if t.GetNetname()==n and any(p.HitTest(z)for z in[t.GetStart(),t.GetEnd()]):ret.add(t.m_Uuid.AsString())
 for t in b.GetTracks():
  if t.GetNetname()in private:ret.add(t.m_Uuid.AsString())
 tree=parse(without_generated_fills(a.board.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)]
 staged=a.out/'literal-retired-input.kicad_pcb';staged.write_text(dump_board(tree))
 for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),staged.with_suffix(ext))
 originalboard=b;b=pcbnew.LoadBoard(str(staged));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()}
 for r,(point,angle)in poses.items():
  f=fs[r]
  if r.startswith('C')and f.GetLayer()!=pcbnew.B_Cu:f.Flip(f.GetPosition(),False)
  f.SetPosition(xy(point));f.SetOrientationDegrees(angle)
 for r in refs:
  f=fs[r]
  for q in b.GetFootprints():
   if q.GetReference()!=r and q.GetLayer()==f.GetLayer():assert not intersects(side_box(f),side_box(q),0),('Court',r,q.GetReference())
 g=FastGeometry(b);added=[];routes=[];checks=[];vias=[];anchors={};alive=[]
 def debug():
  pcbnew.SaveBoard(str(a.out/'debug.kicad_pcb'),b);(a.out/'debug.json').write_text(json.dumps(dict(routes=routes,exact_added_copper=added,retired=sorted(ret),new_poses=poses),indent=2))
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
 raw=ps['U11011','11'].GetNetname();ground=ps['U11011','6'].GetNetname();assert raw=='/motherboard_power_entry/MOTION_5V_RAW'and ground=='/LOGIC_GND'
 # Actual compact B head; the existing A circuit and 3 power barrels remain immutable.
 points([(266,177),(266,174),(274.4,173)],raw,pcbnew.B_Cu,2.,'B_RAW_receiving_source_feeder',False)
 points([(274.4,173),(276,173)],raw,pcbnew.B_Cu,1.,'B_RAW_loaded_head_short_neck',False)
 for y in[171.7,172.3,173]:via((276,y),raw,'B_RAW_three_power_barrels')
 points([(276,171.7),(276,173)],raw,pcbnew.B_Cu,.7,'B_RAW_power_barrel_join',False)
 for pn in['3','4']:wire('U11011',pn,'U11011','11',.25,role='B_VIN_VBIAS_'+pn)
 wire('C11059','1','U11011','11',.5,pcbnew.B_Cu,'B_input_cap_positive')
 ing=mm(ps['C11059','2'].GetPosition());via(ing,ground,'B_input_cap_source_ground');points([ing,mm(ps['C11046','2'].GetPosition())],ground,pcbnew.F_Cu,.5,'B_input_cap_actual_SOURCE_return')
 points([ing,(281,170.225),(281,174.8),(277.5,174.8)],ground,pcbnew.F_Cu,1.,'B_own_SOURCE_ground_head_distribution',False)
 out=ps['U11011','9'].GetNetname();head=(277.8,172.5);points([mm(ps['U11011','9'].GetPosition()),head],out,pcbnew.F_Cu,.25,'B_VOUT_manufacturer_short_neck',False)
 for pt in[(277.8,171.75),(278.5,171.75),(277.8,172.5)]:via(pt,out,'B_output_three_power_barrels')
 for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
  points([(277.8,171.75),(278.5,171.75)],out,l,.6,'B_output_array_join_horizontal',False);points([(277.8,171.75),head],out,l,.6,'B_output_array_join_vertical',False)
 points([head,mm(ps['C11060','1'].GetPosition())],out,pcbnew.B_Cu,.5,'B_output_cap_positive',False)
 gout=mm(ps['C11060','2'].GetPosition());esc=(281,172.5);points([gout,esc],ground,pcbnew.B_Cu,.4,'B_output_cap_return_escape');via(esc,ground,'B_output_cap_return');points([esc,(281,174.8),(277.5,174.8)],ground,pcbnew.F_Cu,.5,'B_output_cap_actual_SOURCE_return',False)
 via((277.5,174.8),ground,'B_switch_actual_SOURCE_return');points([mm(ps['U11011','6'].GetPosition()),(277.5,174.8)],ground,pcbnew.F_Cu,.3,'B_switch_ground_pin')
 # Existing G031/FPGA clock source is preserved; no new input pull-up/authority.
 wire('U11033','4','U11034','1')
 wire('U11034','5','R11045','1',.2,pcbnew.B_Cu,'B_actual_Q_to_ON_bias',step=.25,padding=14,max_nodes=60000)
 wire('R11045','1','U11011','5',.2,pcbnew.B_Cu,'B_actual_ON_receive',step=.25,padding=14,max_nodes=60000)
 wire('R11047','1','C11060','1',.3,pcbnew.B_Cu,'B_actual_receiving_330ohm_bleed')
 # DFF VCC/forcedHIGH and local bypass; original safety latch truth unchanged.
 for row in[('U11034','8','C11086','1'),('U11034','7','U11034','8'),('U11034','2','U11034','8')]:wire(*row,.25,pcbnew.B_Cu)
 wire('C11086','1','C11059','1',.4,pcbnew.B_Cu,'B_DFF_receiving_RAW_supply')
 # Series NO contact withdrawal/RC/default and original direct gate contacts.
 for row in[('R11078','1','C11059','1'),('R11078','2','U11023','3'),('U11023','4','U11029','3'),('U11029','4','R11079','1'),('R11079','1','C11085','1'),('C11085','1','U11034','6'),('U11024','4','U11030','3')]:wire(*row)
 for row in[('R11069','2','U11023','1'),('U11023','2','U11024','1'),('R11073','2','U11029','1'),('U11029','2','U11030','1')]:wire(*row,.3)
 for row in[('C11086','2','U11034','4'),('C11085','2','R11079','2')]:wire(*row,.25,pcbnew.B_Cu)
 for r,pn in[('R11045','2'),('R11047','2')]:anchor(r,pn,pcbnew.B_Cu,'B_local_default_ground_'+r)
 wire('U11024','2','U11020','4',.3,pcbnew.F_Cu,'CORE_LED_B_actual_sink',step=.5,padding=30,max_nodes=90000)
 wire('U11030','2','U11026','4',.3,pcbnew.B_Cu,'FIELD_LED_B_actual_sink',step=.5,padding=30,max_nodes=90000)
 wire('R11069','1','R11067','1',.4,pcbnew.B_Cu,'CORE_LED_B_existing_actual_source',step=.5,padding=30,max_nodes=90000)
 wire('R11073','1','R11071','1',.3,pcbnew.B_Cu,'FIELD_LED_B_existing_actual_source',step=.5,padding=25,max_nodes=90000)
 wire('U11011','7','R11046','2',.2,pcbnew.B_Cu,'B_PG_actual_receiving_pullup',step=.25,padding=15,max_nodes=70000)
 wire('R11046','1','R11043','1',.25,pcbnew.F_Cu,'B_PG_actual_existing_IO3_source')
 # Native fill must join every local ground to the actual converter SOURCE.
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();gc=b.GetConnectivity()
 for r,pn in [('R11045','2'),('R11047','2'),('R11079','2'),('U11034','4'),('C11085','2'),('C11086','2')]:
  p,q=ps[r,pn],ps['C11046','2'];yes=q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in gc.GetConnectedItems(p)}
  if not yes:debug();raise AssertionError(('Actual ground SOURCE missing',r,pn))
  checks.append(dict(from_ref=r,from_pin=pn,to_ref='C11046',to_pin='2',role='actual_SOURCE_ground_'+r))
 debug();b.BuildConnectivity();qc=b.GetConnectivity();allpads={p.m_Uuid.AsString():p for p in b.GetPads()};preserved=0
 for uid,group in groups:
  aftergroup={uid}|{t.m_Uuid.AsString()for t in qc.GetConnectedItems(allpads[uid])if t.Type()==pcbnew.PCB_PAD_T}
  if not group<=aftergroup:
   print('SOURCE_MISSING',[(allpads[v].GetParentFootprint().GetReference(),allpads[v].GetNumber())for v in sorted(group-aftergroup)],flush=True);debug();raise AssertionError(('Prior SOURCE cluster',uid))
  preserved+=1
 for row in checks:
  p,q=ps[row['from_ref'],row['from_pin']],ps[row['to_ref'],row['to_pin']];assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in qc.GetConnectedItems(p)},('New required native endpoint',row)
 b.BuildConnectivity();dest=a.out/'motor-bank-B-receiving-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();np={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};new={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(op[k]==v for k,v in np.items()if k not in owned);assert all(new[k]==v for k,v in old.items()if k not in ret);assert not ret&set(new);assert set(new)-set(old)=={v['uuid']for v in added}
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];assert all(sha(Path(p))==h for p,h in hashes.items())
 receipt=dict(input_hashes=hashes,board_sha256=sha(dest),old_poses=oldpose,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()),courtyard_mm=side_box(fs[r]))for r in refs},all_unrelated_pads_copper_preserved=True,prior_source_clusters_preserved=preserved,exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],routes=routes,actual_endpoint_checks=checks,native_errors=errors,native_types=dict(collections.Counter(v['type']for v in d['violations'])),native_uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,complete_global_power_qualification=False)
 (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');(a.out/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual bank A switch/latch/clock/RC/series contact-cell relocation with unchanged source, manufacturer lands and existing safe-default logic',reviewed_footprint_references=sorted(refs),reviewed_copper_delta_UUIDs=[v['uuid']for v in added]+sorted(ret),reviewed_added_zone_UUIDs=[]),indent=2)+'\n');print('RESULT',len(added),len(ret),len(errors),receipt['native_uncapped_joins'],flush=True)
if __name__=='__main__':main()
