import sys,json,math,collections,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import identity,mm,xy,segment_distance
from hardware_route_local_signals import paths,GeometryIndex
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-two-health-local-anchor-control-repair-r268');O.mkdir(exist_ok=False);o=pcbnew.LoadBoard(str(B));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in o.GetPads()if p.GetNumber()};n=ps['U11020','3'].GetNetname();old={t.m_Uuid.AsString():identity(t)for t in o.GetTracks()};ret={t.m_Uuid.AsString()for t in o.GetTracks()if t.GetNetname()==n};t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-U20-B-input-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};g=FastGeometry(b);base_clear=g.clear;ground=ps['U11020','2'].GetNetname();viaholes=[(mm(v.GetPosition()),pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))/2+.2505,v.GetNetname())for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()!=ground]
holeindex=GeometryIndex()
for c,r,vn in viaholes:holeindex.add((c,r,vn),(c[0]-r,c[1]-r,c[0]+r,c[1]+r))
def guarded_clear(points,net,l,w):
 if not base_clear(points,net,l,w):return False
 if net==n:
  for x,y in zip(points,points[1:]):
   for c,r,vn in holeindex.candidates(x,y,w/2+.40+.03):
    if vn==net:continue
    if segment_distance(x,y,c,c)<r+w/2+.40+.03:return False
 return True
g.clear=guarded_clear;added=[];routes=[]
def route(a,z,net,layer,role,width=.2):
 pts=next((v for v in paths(a,z)if g.clear(v,net,layer,width)),None)
 if pts is None:pts=g.grid(a,z,net,layer,width,step=.1,padding=12,max_nodes=300000)
 assert pts,('ACTUAL_NATIVE_PATH',role,a,z);ids=[]
 for x,y in zip(pts,pts[1:]):
  tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(net));tr.SetStart(xy(x));tr.SetEnd(xy(y));tr.SetLayer(layer);tr.SetWidth(pcbnew.FromMM(width));b.Add(tr);g.add(tr);ids.append(tr.m_Uuid.AsString());added.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role=role))
 routes.append(dict(role=role,net=net,layer=b.GetLayerName(layer),width_mm=width,points_mm=pts,uuids=ids,length_mm=sum(math.dist(x,y)for x,y in zip(pts,pts[1:]))));print('ROUTE',role,pts,flush=True)

a=mm(ps['U11020','3'].GetPosition());z=mm(ps['U11019','4'].GetPosition())
for which,origin,pts in [('RV',a,[(341.4375,173.35),(341.8,173.0),(340.8,173.0),(342.,174.)]),('SV',z,[(347.4,179.15),(347.3,179.25),(347.5,179.0),(346.85,179.5)])]:
 for q in pts:
  nv=all(base_clear([q,q],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]);fp=[p for p in paths(origin,q)if base_clear(p,n,pcbnew.F_Cu,.2)];gp=[p for p in fp if g.clear(p,n,pcbnew.F_Cu,.2)];print(which,q,'VIA',nv,'F',fp,'GUARD',gp,flush=True)
