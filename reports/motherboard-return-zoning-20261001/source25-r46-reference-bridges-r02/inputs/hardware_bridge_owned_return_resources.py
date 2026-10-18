"""Join source-bearing local return resources by explicit own-domain copper.

These are low-current reference connections, not load-current distribution.
No foreign component/outer-copper projection, floating thermal/contact island,
package isolation barrier or raw converter corridor may be crossed. A new
inner track physically contacts its own reference piece and
must reach a genuinely source-anchored same-net piece on the same layer.
Native DRC, flashed layer contacts and all original source clusters decide
acceptance. No same-name or package-internal connection is assumed.
"""
from __future__ import annotations
import argparse,collections,heapq,json,math,shutil
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import sha,write,RAW_RETURNS
from hardware_validate_motherboard_return_planes_r02 import validate,physical_reference_contact
from hardware_classify_unanchored_return_pockets import classify
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import return_net,pad_supports_reference,reference_envelopes,rectangle,inflation,split_polygons
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_stitch_owned_return_planes import definitions,ALLOWED_RETURNS,candidate_points
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive

class ReferenceGuard:
 def __init__(self,b,mapping):
  self.indices={};self.geometry=Geometry(b);self.board=b
  self.domains={p['net']:p['domain']for p in mapping['pads']}
  for name in('In1.Cu','In4.Cu'):
   layer=b.GetLayerID(name);index=GeometryIndex();self.indices[layer]=index
   def add(net,shape):
    q=shape.BBox();box=[pcbnew.ToMM(v)for v in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())];index.add((net,shape),box)
   for env in reference_envelopes(mapping,name):add(env['net'],rectangle(env['bounds'],.25))
   for p in mapping['pads']:
    if p['domain'].startswith(('SUB:','CONTACT:'))or p['domain']=='CHASSIS':add(None,rectangle(p['copper_aabb_mm'],.3))
   outer=pcbnew.F_Cu if name=='In1.Cu'else pcbnew.B_Cu
   for t in b.GetTracks():
    if isinstance(t,pcbnew.PCB_VIA)or t.GetLayer()!=outer:continue
    ret=return_net(dict(net=t.GetNetname(),domain=self.domains.get(t.GetNetname())))
    add(ret,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.25)))
   for z in b.Zones():
    if z.GetZoneName().startswith('FLOATING_SUB_'):add(None,inflation(z.Outline(),.25))
    if not z.GetIsRuleArea()and z.GetNetname()!='/LOGIC_GND'and z.HasFilledPolysForLayer(outer):
     ret=return_net(dict(net=z.GetNetname(),domain=self.domains.get(z.GetNetname())))
     actual=z.GetFilledPolysList(outer)
     if actual.Area():add(ret,inflation(actual,.15))
 def clear(self,points,net,layer,width=.5):
  if net not in ALLOWED_RETURNS:return False
  if not self.geometry.clear(points,net,layer,width):return False
  for s,e in zip(points,points[1:]):
   actual=corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(width/2))
   for other,shape in self.indices[layer].candidates(s,e,width/2+.3):
    if other!=net and actual.Collide(shape):return False
  return True

def compact_path(points):
 out=[]
 for p in points:
  if len(out)>1:
   a,b=out[-2:]
   if abs((b[0]-a[0])*(p[1]-b[1])-(b[1]-a[1])*(p[0]-b[0]))<1e-7:out[-1]=p;continue
  out.append(p)
 return out

def legal_path(start,end,net,layer,guard,max_span,search=True):
 if math.dist(start,end)>max_span:return None
 for path in paths(start,end):
  if sum(math.dist(a,b)for a,b in zip(path,path[1:]))<=max_span and guard.clear(path,net,layer):return compact_path(path)
 if not search:return None
 # Bounded sparse search; final exact native corridor/DRC still governs.
 step=.5;origin=(round(start[0]/step)*step,round(start[1]/step)*step)
 if not guard.clear([start,origin],net,layer):return None
 bounds=(min(start[0],end[0])-8,min(start[1],end[1])-8,max(start[0],end[0])+8,max(start[1],end[1])+8)
 todo=[(math.dist(origin,end),0.,origin)];best={origin:0.};parent={origin:None};count=0
 while todo and count<14000:
  _,cost,at=heapq.heappop(todo)
  if cost!=best.get(at):continue
  count+=1
  if math.dist(at,end)<=1. and guard.clear([at,end],net,layer):
   route=[end,at]
   while parent[route[-1]]is not None:route.append(parent[route[-1]])
   route.append(start);route.reverse();route=compact_path(route)
   if sum(math.dist(a,b)for a,b in zip(route,route[1:]))<=max_span:return route
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   q=(round(at[0]+dx*step,6),round(at[1]+dy*step,6));new=cost+step*math.hypot(dx,dy)
   if new>max_span or not(bounds[0]<=q[0]<=bounds[2]and bounds[1]<=q[1]<=bounds[3])or new>=best.get(q,1e9):continue
   if not guard.clear([at,q],net,layer):continue
   best[q]=new;parent[q]=at;heapq.heappush(todo,(new+math.dist(q,end),new,q))
 return None

def source_start_points(piece,guard,net,layer):
 safe=inflation(piece,-.15);result=[]
 if not safe.Area():safe=piece
 for part in split_polygons(safe):
  for p in candidate_points(part):
   if not part.Contains(xy(p))or not guard.clear([p,p],net,layer):continue
   if piece.Contains(xy(p)):result.append(p)
   if len(result)>=18:return result
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in('board','map','out'):ap.add_argument('--'+k,type=Path,required=True)
 ap.add_argument('--max-span-mm',type=float,default=60.);a=ap.parse_args();out=a.out.resolve();base=a.board.resolve()
 if out.exists():raise ValueError('Fresh immutable output required')
 inputs=[base,a.map,Path(__file__),Path(__file__).parent/'hardware_collect_native_reference_fills.py',Path(__file__).parent/'hardware_validate_motherboard_return_planes_r02.py'];frozen={str(p.resolve()):sha(p)for p in inputs}
 out.mkdir(parents=True);(out/'inputs').mkdir()
 for p in inputs:shutil.copy2(p,out/'inputs'/p.name)
 b=pcbnew.LoadBoard(str(base));mapping=json.loads(a.map.read_text());initial=validate(b,mapping);classes=classify(b,mapping);needed={(r['net'],b.GetLayerID(r['reference_layer']),r['filled_piece'])for r in classes['rows']if r['source_projection_needed']}
 oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};olddefs=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
 fills=collect_native_reference_fills(b,ALLOWED_RETURNS,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pieces={k:list(split_polygons(v))for k,v in fills.items()};anchored={(r['net'],b.GetLayerID(r['reference_layer']),r['filled_piece'])for r in initial['filled_components']if r['passed']};guard=ReferenceGuard(b,mapping);groups=[];skips=[]
 # Endpoints are exact source-connected, flashed existing vias in that piece.
 ends=collections.defaultdict(list)
 for row in initial['filled_components']:
  if row['passed']:
   key=(row['net'],b.GetLayerID(row['reference_layer']))
   for v in row['actual_source_connected_through_stitch_anchors']:ends[key].append(tuple(v['position_mm']))
   for pad in row['actual_numbered_through_pad_anchors']:
    p=next(x for x in b.GetPads()if x.m_Uuid.AsString()==pad['pad_uuid']);ends[key].append(mm(p.GetPosition()))
 print(dict(unanchored_source_bearing=len(needed-anchored)),flush=True)
 tasks=sorted(needed-anchored,key=lambda k:pieces[k[:2]][k[2]].Area(),reverse=True)
 for net,layer,index in tasks:
  starts=source_start_points(pieces[net,layer][index],guard,net,layer);options=sorted(((math.dist(s,e),s,e)for s in starts for e in ends[net,layer]if math.dist(s,e)<=a.max_span_mm),key=lambda r:r[0]);chosen=None
  for _,s,e in options[:80]:
   route=legal_path(s,e,net,layer,guard,a.max_span_mm,False)
   if route:chosen=(s,route);break
  if chosen is None:
   for _,s,e in options[:4]:
    route=legal_path(s,e,net,layer,guard,a.max_span_mm)
    if route:chosen=(s,route);break
  if chosen is None:skips.append(dict(net=net,reference_layer=b.GetLayerName(layer),filled_piece=index,reason='No bounded legal own-domain source-anchored return path'));continue
  start,route=chosen;items=[]
  for s,e in zip(route,route[1:]):
   if math.dist(s,e)<1e-6:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(.5));b.Add(t);guard.geometry.add(t);items.append(t)
  groups.append(dict(net=net,reference_layer=b.GetLayerName(layer),filled_piece=index,new_copper_UUIDs=[t.m_Uuid.AsString()for t in items],route_mm=route,length_mm=sum(math.dist(s,e)for s,e in zip(route,route[1:])),new_dummy_or_single_layer_vias=0,retained=True));ends[net,layer].append(start)
  print(dict(own_return_bridges=len(groups),unclosed=len(skips),net=net,piece=index),flush=True)
 write(out/'generation.json',dict(groups=groups,required_remaining=skips,input_sha256=frozen));dest=out/'motherboard-own-return-bridges-candidate.kicad_pcb'
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
 for p in base.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
  elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
 expected={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()if t.m_Uuid.AsString()not in oldcu};rejected=[]
 for attempt in range(5):
  pcbnew.SaveBoard(str(dest),b);native=drc(dest,out,'native-'+str(attempt));b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();errors=[r for r in native['violations']if r['severity']=='error']
  if not errors:break
  lookup={u:i for i,r in enumerate(groups)if r['retained']for u in r['new_copper_UUIDs']};bad=set()
  for issue in errors:
   hit={lookup[r['uuid']]for r in issue['items']if r['uuid']in lookup}
   if not hit:raise ValueError('Native error outside exact own-return bridge scope '+issue['type'])
   bad|=hit
  for i in bad:
   for t in list(b.GetTracks()):
    if t.m_Uuid.AsString()in groups[i]['new_copper_UUIDs']:b.Remove(t)
   groups[i]['retained']=False;rejected.append(i)
 else:raise ValueError('Native new-group repair bound exceeded')
 now={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};kept={u for r in groups if r['retained']for u in r['new_copper_UUIDs']}
 if set(now)!=set(oldcu)|kept or any(now.get(u)!=v for u,v in oldcu.items())or any(now[u]!=expected[u]for u in kept):raise ValueError('Old/new exact native copper changed')
 if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or olddefs!=definitions(dest):raise ValueError('Source pads or zone definitions changed')
 clusters=native_pad_clusters(b,nets);survived=clusters_survive(oldclusters,clusters);write(out/'all-source-pad-cluster-proof.json',dict(before=oldclusters,after=clusters,passed=survived))
 if not survived:raise ValueError('A previous actual source-pad cluster split')
 actual={t.m_Uuid.AsString():t for t in b.GetTracks()};fills=collect_native_reference_fills(b,ALLOWED_RETURNS,[pcbnew.In1_Cu,pcbnew.In4_Cu]);proof=[]
 for row in groups:
  if not row['retained']:continue
  track=actual[row['new_copper_UUIDs'][0]];layer=b.GetLayerID(row['reference_layer']);pads=[x for x in b.GetConnectivity().GetConnectedItems(track)if isinstance(x,pcbnew.PAD)and x.GetNumber()and x.IsOnCopperLayer()and x.GetNetname()==row['net']]
  if not pads or track.GetLayer()!=layer or not b.GetConnectivity().IsConnectedOnLayer(track,layer)or not fills[row['net'],layer].Collide(track.GetEffectiveShape()):raise ValueError('New return bridge lacks actual source/filled native same-layer contact')
  proof.append(dict(track_uuid=track.m_Uuid.AsString(),reference_layer=row['reference_layer'],source_pad_witness=dict(reference=pads[0].GetParentFootprint().GetReference(),pin=pads[0].GetNumber(),pad_uuid=pads[0].m_Uuid.AsString()),actual_source_connected=True,actual_filled_native_same_layer_contact=True))
 if any(sha(Path(p))!=v for p,v in frozen.items()):raise ValueError('Frozen input changed')
 anchors=validate(b,mapping);anchors['board_sha256']=sha(dest);write(out/'physical-reference-anchors.json',anchors)
 write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason=__doc__,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(kept),reviewed_added_zone_UUIDs=[]))
 receipt=dict(input_sha256=frozen,board_sha256=sha(dest),own_return_bridge_groups=groups,native_actual_source_contact_proofs=proof,required_remaining=skips,native_rejected_groups=rejected,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),native_errors=sum(r['severity']=='error'for r in native['violations']),ignored_checks=native['ignored_checks'],all_old_Cu_pads_zones_actual_source_clusters_retained=True,remaining_unanchored_resources=len(anchors['unanchored_components']),uncapped_missing_joins=b.GetConnectivity().GetUnconnectedCount(False),global_return_current_capacity_qualified=False,manufacturing_ready=False);write(out/'receipt.json',receipt)
 print(json.dumps({k:v for k,v in receipt.items()if k not in('input_sha256','own_return_bridge_groups','native_actual_source_contact_proofs','required_remaining')},indent=2))

if __name__=='__main__':main()
