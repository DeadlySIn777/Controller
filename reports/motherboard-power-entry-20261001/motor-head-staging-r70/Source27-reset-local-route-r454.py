import sys,json,hashlib,shutil,math,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import importlib.util
inner_spec=importlib.util.spec_from_file_location("source27_inner_geometry",Path("reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r350.py"));inner_module=importlib.util.module_from_spec(inner_spec);inner_spec.loader.exec_module(inner_module)
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity,pad_identity
from hardware_route_local_signals import paths,GeometryIndex
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
B=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-bypass-poses-r434/motherboard-staged-Source27-local-bypass-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-route-r454');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in[B,Path(__file__)]};b0=pcbnew.LoadBoard(str(B));b0.BuildConnectivity();ps0={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b0.GetPads()if p.GetNumber()};ret=set()
for bank,latch in[('A','U11032'),('B','U11034')]:
 p=ps0[latch,'6'];slow='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_'+bank
 for t in b0.GetTracks():
  if t.GetNetname()==slow and (p.HitTest(t.GetStart())or p.HitTest(t.GetEnd())):ret.add(t.m_Uuid.AsString())
assert ret
# Exact obsolete former CLR terminal leaf; no fitted Source pin except C82 attachment.
extra=[]
for t in b0.GetTracks():
 if t.GetNetname()=='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A'and set([mm(t.GetStart()),mm(t.GetEnd())])=={(267.075,199.5),(267.075,197.25)}:extra.append(t.m_Uuid.AsString())
assert len(extra)==1;ret.update(extra)
for u in ['7b6a1e6b-9e97-4b78-b930-d04343f73728','9739b3cd-2bde-410e-b617-a083edcee7b6','4506b7cc-f971-468a-aab8-9e8145f5f031']:
 t=next(t for t in b0.GetTracks()if t.m_Uuid.AsString()==u);assert t.GetNetname()=='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_B';ret.add(u)
tree=parse(without_generated_fills(B.read_text()));tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in['segment','via']and value(child(x,'uuid')[1])in ret)];temp=O/'old-two-CLR-terminal-retired.kicad_pcb';temp.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(temp));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};g=inner_module.InnerGeometry(b);added=[];routes=[];alive=[]
def debug():pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(retired=sorted(ret),routes=routes,new_Cu=added),indent=2))
def route(s,e,n,l,role,width=.25):
 pts=next((p for p in paths(s,e)if g.clear(p,n,l,width)),None)
 if pts is None:pts=g.grid(s,e,n,l,width,step=.20,padding=8,max_nodes=45000)
 if pts is None:return False
 ids=[]
 for a,c in zip(pts,pts[1:]):
  if math.dist(a,c)<1e-7:continue
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetLayer(l);t.SetWidth(pcbnew.FromMM(width));t.SetNet(b.FindNet(n));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),points_mm=pts,actual_Cu_UUIDs=ids));print('ROUTE',role,len(ids),flush=True);return True
anchors={}
def registration_clear(pt):
 sh=pcbnew.SHAPE_CIRCLE(xy(pt),pcbnew.FromMM(.25)+1)
 return not any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads())
def anchor(p,layer,role):
 key=(p.m_Uuid.AsString(),layer)
 if key in anchors:return anchors[key]
 if p.IsOnLayer(layer):return mm(p.GetPosition())
 pt=mm(p.GetPosition());n=p.GetNetname();side=p.GetParentFootprint().GetLayer()
 for d in [.9,1.1,1.4,1.8,2.2,2.8,3.4]:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)]:
   q=(pt[0]+d*dx,pt[1]+d*dy)
   if not registration_clear(q)or not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu])or not g.clear([pt,q],n,side,.25):continue
   via(q,n,role+'_actual_layer_transfer');assert route(pt,q,n,side,role+'_actual_surface_escape');anchors[key]=q;return q
 return None
def pair(r,p,q,k,role,width=.25):
 a,c=ps[r,str(p)],ps[q,str(k)];assert a.GetNetname()==c.GetNetname(),(role,a.GetNetname(),c.GetNetname());side=a.GetParentFootprint().GetLayer();assert side==c.GetParentFootprint().GetLayer()
 if route(mm(a.GetPosition()),mm(c.GetPosition()),a.GetNetname(),side,role,width):return
 layer=pcbnew.F_Cu if side==pcbnew.B_Cu else pcbnew.B_Cu
 def cluster_anchor(p,suffix):
  x=anchor(p,layer,role+suffix)
  if x is not None:return x
  b.BuildConnectivity();group={t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T}
  others=sorted((t for t in b.GetPads()if t.m_Uuid.AsString()in group and math.dist(mm(t.GetPosition()),mm(p.GetPosition()))<5.),key=lambda t:math.dist(mm(t.GetPosition()),mm(p.GetPosition())))
  for t in others:
   x=anchor(t,layer,role+suffix+'_actual_connected_cluster')
   if x is not None:return x
  debug();raise AssertionError(('NoActualConnectedClusterAnchor',role,p.GetParentFootprint().GetReference(),p.GetNumber()))
 x=cluster_anchor(a,'_from');y=cluster_anchor(c,'_to')
 if not route(x,y,a.GetNetname(),layer,role+'_opposite_layer_source_route',width):
  if a.GetNetname()in['/LOGIC_GND','/motherboard_power_entry/MOTION_5V_RAW']:
   if route(x,y,a.GetNetname(),pcbnew.In3_Cu,role+'_actual_inner_low_current_POWER',width):return
  debug();raise AssertionError(('Opposite route',role,x,y))
def wire_on_layer(r,p,q,k,role,layer):
 a,c=ps[r,p],ps[q,k];assert a.GetNetname()==c.GetNetname();x=anchor(a,layer,role+'_from');y=anchor(c,layer,role+'_to');assert x is not None and y is not None
 if route(x,y,a.GetNetname(),layer,role):return
 assert a.GetNetname()in['/LOGIC_GND','/motherboard_power_entry/MOTION_5V_RAW']and route(x,y,a.GetNetname(),pcbnew.In3_Cu,role+'_actual_inner_low_current_POWER')
def via(pt,n,role):
 if not(g.clear([pt,pt],n,pcbnew.F_Cu,.50)and g.clear([pt,pt],n,pcbnew.B_Cu,.50)):debug();raise AssertionError(('Via',role,pt))
 assert registration_clear(pt),('Drill_native_150um',role,pt)
 v=pcbnew.PCB_VIA(b);v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.50));v.SetDrill(pcbnew.FromMM(.20));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(b.FindNet(n));v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
for bank,latch,por,sch,cap1,cap2,pd,slowcap,rawcap,sv,gv in[('A','U11032','U11035','U11036','C11089','C11090','R11082','C11082','C11083',(266.85,197.25),(267.7,197.25)),('B','U11034','U11037','U11038','C11091','C11092','R11083','C11085','C11086',(270.35,154.25),(271.2,154.25))]:
 n=ps[latch,'6'].GetNetname();ground=ps[cap2,'2'].GetNetname()
 # Reserve only exact short outer escapes for control; B local bypass loops stay available.
 control_vias={}
 for rr,pn,dx,role in [(por,'1',-0.9 if bank=='A'else 0.9,'POR_slow_RESET'),(sch,'2',-0.9,'Schmitt_slow_CLR'),(sch,'4',0.9,'Schmitt_FAST_CLR')]:
  p=ps[rr,pn];pt=mm(p.GetPosition());vpt=(pt[0]+dx,pt[1])
  if not(registration_clear(vpt)and all(g.clear([vpt,vpt],p.GetNetname(),l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([pt,vpt],p.GetNetname(),pcbnew.B_Cu,.25)):
   vpt=anchor(p,pcbnew.F_Cu,bank+'_'+role);assert vpt is not None
  else:
   via(vpt,p.GetNetname(),bank+'_'+role+'_transfer');assert route(pt,vpt,p.GetNetname(),pcbnew.B_Cu,bank+'_'+role+'_short_surface_escape');anchors[p.m_Uuid.AsString(),pcbnew.F_Cu]=vpt
  control_vias[role]=vpt
 sv=(266.8,197.25)if bank=='A'else(266.8,155.6);via(sv,n,bank+'_FAST_DFF_receive_transfer');assert route(mm(ps[latch,'6'].GetPosition()),sv,n,pcbnew.F_Cu,bank+'_FAST_DFF_receive_escape')
 gchoices=[]
 for d in [.85,.95]:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)]:
   q=(sv[0]+d*dx,sv[1]+d*dy)
   if registration_clear(q)and all(g.clear([q,q],ground,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):gchoices.append(q)
 assert gchoices,('No actual FAST Ground stitch',bank,sv);gv=gchoices[0];via(gv,ground,bank+'_FAST_DFF_actual_return_stitch')
 assert route(control_vias['Schmitt_FAST_CLR'],sv,n,pcbnew.F_Cu,bank+'_FAST_CLR_actual_F_control')
 sc=anchor(ps[slowcap,'1'],pcbnew.F_Cu,bank+'_actual_slow_RC_Source_transfer');assert sc is not None
 for role in ['POR_slow_RESET','Schmitt_slow_CLR']:
  assert route(control_vias[role],sc,ps[slowcap,'1'].GetNetname(),pcbnew.F_Cu,bank+'_'+role+'_actual_F_control')
 pair(por,'6',cap1,'1',bank+'_POR_actual_local_VDD_bypass')
 pair(por,'5',por,'6',bank+'_POR_SENSE_actual_RAW_tie')
 pair(por,'3',por,'6',bank+'_POR_MR_actual_RAW_tie')
 wire_on_layer(por,'2',cap1,'2',bank+'_POR_actual_local_Ground_bypass',pcbnew.F_Cu)
 pair(sch,'5',cap2,'1',bank+'_Schmitt_actual_local_VDD_bypass')
 wire_on_layer(sch,'3',cap2,'2',bank+'_Schmitt_actual_local_Ground_bypass',pcbnew.F_Cu)
 pair(pd,'1',sch,'4',bank+'_FAST_missing_conditioner_default')
 assert route(gv,mm(ps[cap2,'2'].GetPosition()),ground,pcbnew.B_Cu,bank+'_FAST_DFF_return_actual_Source')
 wire_on_layer(cap1,'1',rawcap,'1',bank+'_POR_actual_existing_RAW_source',pcbnew.In3_Cu);wire_on_layer(cap2,'1',rawcap,'1',bank+'_Schmitt_actual_existing_RAW_source',pcbnew.In3_Cu)
 wire_on_layer(cap1,'2',rawcap,'2',bank+'_POR_actual_Ground_source',pcbnew.In3_Cu);wire_on_layer(cap2,'2',rawcap,'2',bank+'_Schmitt_actual_Ground_source',pcbnew.In3_Cu);pair(pd,'2',cap2,'2',bank+'_FAST_default_Ground')


debug();print('LOCAL_ROUTES',len(routes),len(added),'old_terminal',len(ret),flush=True)




