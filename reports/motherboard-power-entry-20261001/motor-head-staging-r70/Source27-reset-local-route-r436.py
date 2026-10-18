import sys,json,hashlib,shutil,math,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity,pad_identity
from hardware_route_local_signals import paths,GeometryIndex
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
B=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-bypass-poses-r434/motherboard-staged-Source27-local-bypass-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-route-r436');assert not O.exists();O.mkdir()
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
tree=parse(without_generated_fills(B.read_text()));tree=[x for x in tree if not(isinstance(x,list)and x and x[0]in['segment','via']and value(child(x,'uuid')[1])in ret)];temp=O/'old-two-CLR-terminal-retired.kicad_pcb';temp.write_text(dump_board(tree));b=pcbnew.LoadBoard(str(temp));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};g=FastGeometry(b);added=[];routes=[];alive=[]
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
 if not route(x,y,a.GetNetname(),layer,role+'_opposite_layer_source_route',width):debug();raise AssertionError(('Opposite route',role,x,y))
def via(pt,n,role):
 if not(g.clear([pt,pt],n,pcbnew.F_Cu,.50)and g.clear([pt,pt],n,pcbnew.B_Cu,.50)):debug();raise AssertionError(('Via',role,pt))
 assert registration_clear(pt),('Drill_native_150um',role,pt)
 v=pcbnew.PCB_VIA(b);v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.50));v.SetDrill(pcbnew.FromMM(.20));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(b.FindNet(n));v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
for bank,latch,por,sch,cap1,cap2,pd,slowcap,rawcap,sv,gv in[('A','U11032','U11035','U11036','C11089','C11090','R11082','C11082','C11083',(266.85,197.25),(267.7,197.25)),('B','U11034','U11037','U11038','C11091','C11092','R11083','C11085','C11086',(270.35,154.25),(271.2,154.25))]:
 pair(por,'6',cap1,'1',bank+'_POR_actual_local_VDD_bypass')
 pair(por,'5',por,'6',bank+'_POR_SENSE_actual_RAW_tie')
 pair(por,'3',por,'6',bank+'_POR_MR_actual_RAW_tie')
 pair(por,'2',cap1,'2',bank+'_POR_actual_local_Ground_bypass')
 pair(sch,'5',cap2,'1',bank+'_Schmitt_actual_local_VDD_bypass')
 pair(sch,'3',cap2,'2',bank+'_Schmitt_actual_local_Ground_bypass')
 n=ps[latch,'6'].GetNetname();ground=ps[cap2,'2'].GetNetname()
 if bank=='B':
  sv=(266.8,156.0);via(sv,n,bank+'_actual_FAST_DFF_receive_transfer');assert route(mm(ps[latch,'6'].GetPosition()),sv,n,pcbnew.F_Cu,bank+'_actual_FAST_DFF_receive_escape')
 else:sv=anchor(ps[latch,'6'],pcbnew.B_Cu,bank+'_actual_FAST_DFF_receive')
 assert sv is not None
 choices=[]
 for d in [.85,.95]:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)]:
   q=(sv[0]+d*dx,sv[1]+d*dy)
   if registration_clear(q)and all(g.clear([q,q],ground,l,.50)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):choices.append(q)
 assert choices,('FAST Ground transfer unavailable',bank,sv);gv=choices[0];via(gv,ground,bank+'_actual_FAST_return_stitch')
 assert route(mm(ps[sch,'4'].GetPosition()),sv,n,pcbnew.B_Cu,bank+'_actual_conditioned_FAST_CLR')
 pair(pd,'1',sch,'4',bank+'_actual_missing_conditioner_FAST_default')
 assert route(gv,mm(ps[cap2,'2'].GetPosition()),ground,pcbnew.B_Cu,bank+'_FAST_CLR_return_actual_Source')
 pair(por,'1',slowcap,'1',bank+'_POR_RESET_actual_slow_CLR');pair(sch,'2',slowcap,'1',bank+'_Schmitt_actual_slow_CLR')
 pair(cap1,'1',rawcap,'1',bank+'_POR_actual_existing_RAW_source');pair(cap2,'1',rawcap,'1',bank+'_Schmitt_actual_existing_RAW_source')
 pair(cap1,'2',rawcap,'2',bank+'_POR_actual_Ground_source');pair(cap2,'2',rawcap,'2',bank+'_Schmitt_actual_Ground_source');pair(pd,'2',cap2,'2',bank+'_FAST_default_Ground')


debug();print('LOCAL_ROUTES',len(routes),len(added),'old_terminal',len(ret),flush=True)



