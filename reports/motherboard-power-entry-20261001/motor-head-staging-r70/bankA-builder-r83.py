"""Bounded Bank A receiving circuit on a native copy; no electrical changes."""
import argparse,collections,json,math,shutil,subprocess,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_local_signals import paths
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
POSEFILE=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankA-poses.json')

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
 ret=set();local=json.loads(Path('reports/motherboard-power-entry-20261001/motor-supply-cells-priority-r29/receipt.json').read_text());ret|={v['uuid']for v in local['new_copper']if v['role'].startswith(('C11057_','C11058_'))};assert len(ret)==17
 # Exact affected private source graphs, never wildcard-net rename/retirement.
 private=set()
 for r in refs:
  for p in fs[r].Pads():
   n=p.GetNetname()
   if not n.startswith('/motherboard_power_entry/'):continue
   pp={v.m_Uuid.AsString()for v in b.GetPads()if v.GetNetname()==n}
   if pp<=owned:private.add(n)
 private.add(ps['U11022','2'].GetNetname()) # actual old external U11020.6 LED sink must reconnect
 assert {(p.GetParentFootprint().GetReference(),p.GetNumber())for p in b.GetPads()if p.GetNetname()==ps['U11022','2'].GetNetname()}=={('U11022','2'),('U11020','6')}
 for t in b.GetTracks():
  if t.GetNetname()in private:ret.add(t.m_Uuid.AsString())
 # Shared rearm's two existing source-bearing groups have moved endpoints only.
 for r,pn in [('U11031','2'),('R11076','1')]:
  conn=co.GetConnectedItems(ps[r,pn]);pads={t.m_Uuid.AsString()for t in conn if t.Type()==pcbnew.PCB_PAD_T};assert pads<=owned
  ret|={t.m_Uuid.AsString()for t in conn if t.Type()in[pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T]}
 # Two moved GND leaves are deliberately bounded; the global source plane is retained.
 for uid in ['90b5918e-ff89-4949-ba4d-d064e6d3c70d','626e9a04-e48d-40da-be67-670da8690ff2']:
  assert old[uid][1]=='/LOGIC_GND';ret.add(uid)
 for uid in ['7884609a-9292-41b9-95e5-a0009b2cde48','93acd529-a0a9-4a31-a114-8f6ff828de3e','bd508bba-85a6-40a5-8b35-314d4b88ac0d']:
  t=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==uid);assert t.GetNetname()=='/LOGIC_GND';assert any(p.GetNetname()=='/LOGIC_GND'and any(p.HitTest(v)for v in[t.GetStart(),t.GetEnd()])for r in refs for p in fs[r].Pads());ret.add(uid)
 # C11087 (bank B buffer bypass) carries a local RAW branch to moved U11033.
 for r in refs:
  for p in fs[r].Pads():
   if p.GetNetname()in ['/LOGIC_GND','/mc_local_power/CORE_5V','/motherboard_power_entry/FIELD_5V','/motherboard_power_entry/MOTION_5V_RAW']:
    cc=co.GetConnectedItems(p);pads={v.m_Uuid.AsString()for v in cc if v.Type()==pcbnew.PCB_PAD_T}
    if pads<=owned:ret|={v.m_Uuid.AsString()for v in cc if v.Type()in[pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T]}
 retired=[t for t in list(b.GetTracks())if t.m_Uuid.AsString()in ret];assert len(retired)==len(ret)
 for t in retired:b.Remove(t)
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
 raw=ps['U11010','11'].GetNetname();ground=ps['U11010','6'].GetNetname();assert raw=='/motherboard_power_entry/MOTION_5V_RAW'and ground=='/LOGIC_GND'
 # Actual high-current source/head/input/output loops; bank B is untouched.
 points([(266.2,171),(266,177)],raw,pcbnew.F_Cu,4,'RAW_converter_source_neck',False)
 for y in[176.3,177,177.7]:via((266,y),raw,'RAW_source_three_barrels')
 points([(266,176.3),(266,177.7)],raw,pcbnew.B_Cu,1.2,'RAW_source_barrel_join',False)
 points([(266,177),(272,179)],raw,pcbnew.B_Cu,2.,'RAW_A_receiving_head',False)
 for y in[178.3,179,179.7]:via((272,y),raw,'RAW_A_VIN_EP_three_barrels')
 for pn in ['3','4']:wire('U11010',pn,'U11010','11',.25,role='A_VIN_VBIAS_'+pn)
 wire('C11057','1','U11010','11',.5,pcbnew.B_Cu,'A_input_cap_positive')
 points([(271.8,171),(271,173),(269.35,174.5),(269.35,189)],ground,pcbnew.F_Cu,2.,'A_source_own_return',False)
 ing=mm(ps['C11057','2'].GetPosition());via(ing,ground,'A_input_cap_return');points([ing,(269.35,ing[1])],ground,pcbnew.F_Cu,.5,'A_input_cap_source_return',False)
 out=ps['U11010','9'].GetNetname();head=(273.8,178.5);points([mm(ps['U11010','9'].GetPosition()),head],out,pcbnew.F_Cu,.25,'A_VOUT_manufacturer_short_neck',False)
 for pt in [(273.8,177.75),(274.5,177.75),(273.8,178.5)]:via(pt,out,'A_output_three_barrels')
 for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
  points([(273.8,177.75),(274.5,177.75)],out,l,.6,'A_output_array_join_horizontal',False);points([(273.8,177.75),head],out,l,.6,'A_output_array_join_vertical',False)
 points([head,mm(ps['C11058','1'].GetPosition())],out,pcbnew.B_Cu,.5,'A_output_cap_positive',False)
 gout=mm(ps['C11058','2'].GetPosition());esc=(275.025,176.5);points([gout,esc],ground,pcbnew.B_Cu,.4,'A_output_cap_return_escape');via(esc,ground,'A_output_cap_return');points([esc,(269.35,esc[1])],ground,pcbnew.F_Cu,.4,'A_output_cap_source_return')
 via((274,181.5),ground,'A_switch_own_return');points([mm(ps['U11010','6'].GetPosition()),(274,181.5)],ground,pcbnew.F_Cu,.3,'A_switch_ground_pin');points([(274,181.5),(269.35,181.5)],ground,pcbnew.F_Cu,.4,'A_switch_source_return')
 # Local DFF, rail bypasses, default resistors and actual rearm graph.
 for row in [('U11031','4','U11032','1'),('U11031','2','U11033','2'),('U11031','2','R11076','1'),('R11076','1','R11080','1'),('U11032','5','R11042','1')]:wire(*row)
 ev=(270.85,180.8);n=ps['U11010','5'].GetNetname();via(ev,n,'A_ON_own_receive');points([ev,mm(ps['U11010','5'].GetPosition())],n,pcbnew.F_Cu,.2,'A_ON_own_receive_escape');anchors[('U11010','5',pcbnew.B_Cu)]=ev;wire('R11042','1','U11010','5',.2,pcbnew.B_Cu,'A_ON_actual_referenced_control')
 # Drain/bias/monitor load paths, no fabricated PGOOD observer.
 wire('R11044','1','C11058','1',.3,pcbnew.B_Cu)
 # Power each bypass and every actual receiving-rail IC power pin.
 for r,pn,s,qn in [('U11031','5','C11084','1'),('U11033','5','C11087','1'),('U11032','8','C11083','1'),('U11032','7','U11032','8'),('U11032','2','U11032','8')]:wire(r,pn,s,qn,.25,pcbnew.B_Cu)
 for r in ['C11083','C11084','C11087']:wire(r,'1','C11057','1',.4,pcbnew.B_Cu)
 # The contact series forms the actual asynchronous withdrawal/reset path.
 for row in [('R11074','1','C11057','1'),('R11074','2','U11021','3'),('U11021','4','U11027','3'),('U11027','4','R11075','1'),('R11075','1','C11082','1'),('C11082','1','U11032','6'),('U11022','4','U11028','3')]:wire(*row)
 # Actual series LED loops remain electrically distinct from the dry contacts.
 for row in [('R11067','2','U11021','1'),('U11021','2','U11022','1'),('R11071','2','U11027','1'),('U11027','2','U11028','1')]:wire(*row,.3)
 debug();print('LOCAL_ROUTE_STAGE_READY',len(added),len(ret),flush=True)
 # Exact short local bypass/return pairs; never run each bypass through a remote thin GND trace.
 for row in [('C11083','2','U11032','4'),('C11084','2','U11031','3'),('C11087','2','U11033','3'),('C11082','2','R11075','2')]:wire(*row,.25,pcbnew.B_Cu)
 for r,pn in [('R11042','2'),('R11044','2'),('R11076','2'),('R11080','2')]:anchor(r,pn,pcbnew.B_Cu,'local_default_ground_'+r)
 # Retained LED sink/source loops are actual low-current power, not logic-clock routes.
 wire('U11022','2','U11020','6',.3,pcbnew.F_Cu,'CORE_LED_A_retained_sink',step=.5,padding=30,max_nodes=90000)
 wire('U11028','2','U11026','6',.3,pcbnew.B_Cu,'FIELD_LED_A_actual_sink',step=.5,padding=30,max_nodes=90000)
 wire('R11067','1','C11088','1',.4,pcbnew.B_Cu,'CORE_LED_A_actual_source',step=.5,padding=30,max_nodes=90000)
 wire('R11071','1','C11055','1',.3,pcbnew.B_Cu,'FIELD_LED_A_actual_source',step=.5,padding=25,max_nodes=60000)
 wire('U11010','7','R11043','2',.2,pcbnew.B_Cu,'A_PG_actual_pullup')
 anchor('R11043','1',pcbnew.B_Cu,'A_PG_IO3_receiving_power')
 # Native fill must join every local ground to the actual converter SOURCE.
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();gc=b.GetConnectivity()
 for r,pn in [('R11042','2'),('R11044','2'),('R11075','2'),('R11076','2'),('R11080','2'),('U11031','3'),('U11032','4'),('U11033','3'),('C11082','2'),('C11083','2'),('C11084','2'),('C11087','2')]:
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
 b.BuildConnectivity();dest=a.out/'motor-bank-A-receiving-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();np={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};new={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(op[k]==v for k,v in np.items()if k not in owned);assert all(new[k]==v for k,v in old.items()if k not in ret);assert not ret&set(new);assert set(new)-set(old)=={v['uuid']for v in added}
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];assert all(sha(Path(p))==h for p,h in hashes.items())
 receipt=dict(input_hashes=hashes,board_sha256=sha(dest),old_poses=oldpose,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()),courtyard_mm=side_box(fs[r]))for r in refs},all_unrelated_pads_copper_preserved=True,prior_source_clusters_preserved=preserved,exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],routes=routes,actual_endpoint_checks=checks,native_errors=errors,native_types=dict(collections.Counter(v['type']for v in d['violations'])),native_uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,complete_global_power_qualification=False)
 (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');(a.out/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual bank A switch/latch/clock/RC/series contact-cell relocation with unchanged source, manufacturer lands and existing safe-default logic',reviewed_footprint_references=sorted(refs),reviewed_copper_delta_UUIDs=[v['uuid']for v in added]+sorted(ret),reviewed_added_zone_UUIDs=[]),indent=2)+'\n');print('RESULT',len(added),len(ret),len(errors),receipt['native_uncapped_joins'],flush=True)
if __name__=='__main__':main()
