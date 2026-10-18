"""Add reviewed outer-layer current-delivery paths on a native COPY.

Widths/current/temperature are explicit engineering screens, never a DRC
ampacity certification. No source, pose, old copper or existing zone changes.
"""
import argparse,collections,hashlib,heapq,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_route_power_groups_native import hits
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_logic_return import identity,pad_identity,mm,xy,segment_distance
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Geometry:
 def __init__(self,b):
  self.b=b;self.pads=GeometryIndex();self.tracks={l:GeometryIndex()for l in [pcbnew.F_Cu,pcbnew.B_Cu]};self.barriers=[]
  for p in b.GetPads():
   bb=p.GetBoundingBox();box=tuple(pcbnew.ToMM(v)for v in [bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()]);ps=p.GetEffectivePolygon(pcbnew.F_Cu);polys=[[mm(ps.Outline(k).CPoint(i))for i in range(ps.Outline(k).PointCount())]for k in range(ps.OutlineCount())]
   self.pads.add((p.GetNetname(),polys,p.IsOnLayer(pcbnew.F_Cu),p.IsOnLayer(pcbnew.B_Cu),p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH),box)
  for f in b.GetFootprints():
   name=str(f.GetFPID().GetLibItemName()).upper()
   if not any(k in name for k in ['ISO1212','ISO772','ISO774','ISO776','ISO1540','ISOW','TLP3640','TLP4176']):continue
   a=f.GetOrientationDegrees()%360;assert a in [0,90,180,270],f.GetReference();x,y=mm(f.GetPosition());pts=[mm(p.GetPosition())for p in f.Pads()if p.GetNumber()]
   poly=[(x-.3,min(v[1]for v in pts)-.5),(x+.3,min(v[1]for v in pts)-.5),(x+.3,max(v[1]for v in pts)+.5),(x-.3,max(v[1]for v in pts)+.5)]if a in [0,180]else[(min(v[0]for v in pts)-.5,y-.3),(max(v[0]for v in pts)+.5,y-.3),(max(v[0]for v in pts)+.5,y+.3),(min(v[0]for v in pts)-.5,y+.3)]
   self.barriers.append((f.GetReference(),poly))
  for z in b.Zones():
   if z.GetIsRuleArea()and z.GetDoNotAllowTracks():
    o=z.Outline();self.barriers.extend([(z.m_Uuid.AsString(),[mm(o.Outline(k).CPoint(i))for i in range(o.Outline(k).PointCount())])for k in range(o.OutlineCount())])
  for t in b.GetTracks():self.add(t)
 def add(self,t):
  via=isinstance(t,pcbnew.PCB_VIA);w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if via else t.GetWidth());s,e=mm(t.GetStart()),mm(t.GetEnd())
  for l,index in self.tracks.items():
   if t.IsOnLayer(l):index.add((t.GetNetname(),s,e,w),(min(s[0],e[0])-w/2,min(s[1],e[1])-w/2,max(s[0],e[0])+w/2,max(s[1],e[1])+w/2))
 def clear(self,ps,n,l,w):
  gap=w/2+.16
  for s,e in zip(ps,ps[1:]):
   if any(not(.8+w/2<=p[0]<=459.2-w/2 and .8+w/2<=p[1]<=339.2-w/2)for p in [s,e]):return False
   if any(hits(s,e,poly,w/2)for ref,poly in self.barriers):return False
   for net,polys,top,bot,npth in self.pads.candidates(s,e,gap):
    if net==n and not npth:continue
    if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(s,e,p,gap)for p in polys):return False
   for net,a,b,width in self.tracks[l].candidates(s,e,gap):
    if net!=n and segment_distance(s,e,a,b)<gap+width/2-1e-6:return False
  return True
 def grid(self,s,e,n,l,w,step=1.,padding=35.,max_nodes=14000):
  low=(min(s[0],e[0])-padding,min(s[1],e[1])-padding);high=(max(s[0],e[0])+padding,max(s[1],e[1])+padding);q=[(math.dist(s,e),0,(0,0))];cost={(0,0):0};prev={};end=None;memo={}
  def point(k):return(s[0]+k[0]*step,s[1]+k[1]*step)
  while q and len(cost)<max_nodes:
   _,d,k=heapq.heappop(q)
   if d>cost[k]+1e-8:continue
   p=point(k)
   if math.dist(p,e)<=step*1.5 and self.clear([p,e],n,l,w):end=k;break
   for dx,dy in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
    kk=(k[0]+dx,k[1]+dy);r=point(kk);key=(k,kk)
    if not(low[0]<=r[0]<=high[0]and low[1]<=r[1]<=high[1]):continue
    if key not in memo:memo[key]=self.clear([p,r],n,l,w)
    if not memo[key]:continue
    nd=d+step*math.hypot(dx,dy)
    if nd>=cost.get(kk,float('inf'))-1e-8:continue
    cost[kk]=nd;prev[kk]=k;heapq.heappush(q,(nd+math.dist(r,e),nd,kk))
  if end is None:return None
  pp=[e,point(end)];k=end
  while k!=(0,0):k=prev[k];pp.append(point(k))
  pp.reverse();simple=[]
  for p in pp:
   if simple and math.dist(simple[-1],p)<1e-8:continue
   while len(simple)>1:
    a,b=simple[-2:]
    if abs((b[0]-a[0])*(p[1]-b[1])-(b[1]-a[1])*(p[0]-b[0]))>1e-8:break
    simple.pop()
   simple.append(p)
  assert self.clear(simple,n,l,w);return simple
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--spec',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);source_sha=sha(a.board);spec_sha=sha(a.spec);tool_sha=sha(Path(__file__));b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};fps={f.GetReference():f for f in b.GetFootprints()};pad={(r,p.GetNumber()):p for r,f in fps.items()for p in f.Pads()if p.GetNumber()};g=Geometry(b);spec=json.loads(a.spec.read_text());added=[];routes=[];pending=[]
 observers=[];seen=set();pad_uuids={p.m_Uuid.AsString()for p in b.GetPads()}
 for p in b.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group=({uid}|{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T})&pad_uuids;seen.update(group)
  if len(group)>1:observers.append((uid,group))
 def endpoint(v):
  ps=[p for p in fps[v['ref']].Pads()if p.GetNumber()==str(v['pin'])];p=ps[v.get('pin_occurrence',-1)];return p,tuple(v.get('point_mm',mm(p.GetPosition())))
 for row in spec['routes']:
  p,s=endpoint(row['from']);q,e=endpoint(row['to']);n=p.GetNetname();assert n and n==q.GetNetname(),row;w=row['width_mm'];chosen=None
  if q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)}:
   routes.append({**row,'net':n,'from_pad_uuid':p.m_Uuid.AsString(),'to_pad_uuid':q.m_Uuid.AsString(),'already_connected_before':True,'current_geometry_qualified':False});continue
  for layer in [b.GetLayerID(v)for v in row.get('layers',['F.Cu','B.Cu'])]:
   def actual_anchor(node,pt,side):
    if node.IsOnLayer(layer)and pt==mm(node.GetPosition()):return True
    if not row[side].get('validated_copper_anchor'):return False
    return any(t.IsOnLayer(layer)and t.GetNetname()==node.GetNetname()and (t.GetFilledPolysList(layer).Contains(xy(pt))if isinstance(t,pcbnew.ZONE)else t.HitTest(xy(pt)))for t in co.GetConnectedItems(node))
   if not actual_anchor(p,s,'from')or not actual_anchor(q,e,'to'):continue
   proposed=row.get('screened_path_sections',{}).get(b.GetLayerName(layer))
   if proposed:
    assert tuple(proposed[0]['points_mm'][0])==s and tuple(proposed[-1]['points_mm'][-1])==e
    assert all(tuple(x['points_mm'][-1])==tuple(y['points_mm'][0])for x,y in zip(proposed,proposed[1:]))
    if all(g.clear([tuple(p)for p in sec['points_mm']],n,layer,sec['width_mm'])for sec in proposed):
     chosen=(layer,[([tuple(p)for p in sec['points_mm']],sec['width_mm'])for sec in proposed]);break
   if row.get('explicit_only'):continue
   pp=next((pp for pp in paths(s,e)if g.clear(pp,n,layer,w)),None)
   if pp is None and g.clear([s,s],n,layer,w)and g.clear([e,e],n,layer,w):pp=g.grid(s,e,n,layer,w,step=row.get('grid_step_mm',1.),padding=row.get('padding_mm',40.))
   if pp:chosen=(layer,[(pp,w)]);break
   # Only source-reviewed short pad-constrained necks may be narrower. The
   # rail cannot silently become a signal-width trace around an obstruction.
   nw=row.get('pad_neck_width_mm');nd=row.get('pad_neck_max_length_mm',0)
   if not nw or not nd:continue
   def escapes(pt):
    vv=[]
    for d in [nd/2,nd]:
     for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(.707107,-.707107),(-.707107,.707107),(-.707107,-.707107)]:
      z=(pt[0]+d*dx,pt[1]+d*dy)
      if g.clear([pt,z],n,layer,nw)and g.clear([z,z],n,layer,w):vv.append(z)
    return vv
   ss,ee=escapes(s),escapes(e);candidates=sorted(((math.dist(x,y),x,y)for x in ss for y in ee))
   for _,x,y in candidates:
    pp=next((pp for pp in paths(x,y)if g.clear(pp,n,layer,w)),None)
    if pp:chosen=(layer,[([s,x],nw),(pp,w),([y,e],nw)]);break
   if chosen:break
   for _,x,y in candidates[:2]:
    pp=g.grid(x,y,n,layer,w,step=row.get('grid_step_mm',1.),padding=row.get('padding_mm',40.))
    if pp:chosen=(layer,[([s,x],nw),(pp,w),([y,e],nw)]);break
   if chosen:break
  if chosen is None:pending.append({**row,'net':n,'reason':'No screened outer-layer route at required width'});print('PENDING',row['name'],flush=True);continue
  layer,sections=chosen;ids=[];res=0;length=0;legacy=float('inf');th=spec['engineering_screen']['minimum_finished_outer_copper_um'];rho=1.724e-8*(1+.00393*(spec['engineering_screen']['copper_temperature_c']-20))
  for pp,ww in sections:
   ll=sum(math.dist(x,y)for x,y in zip(pp,pp[1:]));length+=ll;res+=rho*(ll/1000)/((ww/1000)*(th/1e6));area=(ww/.0254)*(th/25.4);legacy=min(legacy,.048*spec['engineering_screen']['legacy_temperature_rise_c']**.44*area**.725)
   for ss,ee in zip(pp,pp[1:]):
    if math.dist(ss,ee)<1e-8:continue
    t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(layer);t.SetStart(xy(ss));t.SetEnd(xy(ee));t.SetWidth(pcbnew.FromMM(ww));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),route=row['name']))
  b.BuildConnectivity();co=b.GetConnectivity();assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)},row
  routes.append({**row,'net':n,'from_pad_uuid':p.m_Uuid.AsString(),'to_pad_uuid':q.m_Uuid.AsString(),'layer':b.GetLayerName(layer),'path_sections':[dict(points_mm=pp,width_mm=ww)for pp,ww in sections],'length_mm':length,'added_uuids':ids,'resistance_screen_ohm':res,'IR_screen_volts':res*row['planning_current_a'],'legacy_IPC2221_current_screen_a':legacy,'physical_ampacity_qualified':False});print('ROUTED',row['name'],len(ids),round(length,2),flush=True)
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'current-delivery-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 qq=pcbnew.LoadBoard(str(dest));qq.BuildConnectivity();after={t.m_Uuid.AsString():identity(t)for t in qq.GetTracks()};assert all(after[k]==v for k,v in old.items());assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in qq.GetPads()};assert all(after[r['uuid']]==r['identity']for r in added);assert sha(a.board)==source_sha
 pp={p.m_Uuid.AsString():p for p in qq.GetPads()};cc=qq.GetConnectivity()
 for uid,group in observers:
  reach={uid}|{v.m_Uuid.AsString()for v in cc.GetConnectedItems(pp[uid])if v.Type()==pcbnew.PCB_PAD_T};assert group<=reach,'Actual prior pad cluster disconnected '+uid
 for row in routes:
  uid=row['from_pad_uuid'];assert row['to_pad_uuid']in({uid}|{v.m_Uuid.AsString()for v in cc.GetConnectedItems(pp[uid])}),row['name']
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not d.get('ignored_checks')
 assert sha(Path(__file__))==tool_sha,'Routing tool changed during execution'
 result=dict(source_board=str(a.board),source_sha256=source_sha,spec_sha256=spec_sha,tool_sha256=tool_sha,candidate_sha256=sha(dest),all_old_pad_and_copper_identities_preserved=True,prior_actual_pad_clusters_preserved=len(observers),exact_added_copper=added,routes=routes,pending=pending,native_drc_types=dict(collections.Counter(r['type']for r in d['violations'])),native_errors=[r for r in d['violations']if r['severity']=='error'],native_uncapped_joins=qq.GetConnectivity().GetUnconnectedCount(False),engineering_screen=spec['engineering_screen'],manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Reviewed current-delivery paths, exact additive copper only; no source/pad/pose/old-copper/existing-zone changes',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[r['uuid']for r in added],reviewed_added_zone_UUIDs=[]);(a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['exact_added_copper','routes','pending','native_errors']}))
if __name__=='__main__':main()
