"""Close only the C14012 pendant-enable filter at its actual U14014 input.

The old private pad-only leaf and its now-unused F/B transition are retired.
Native source-pad cluster retention proves the shared B trunk survives.
All existing clock copper,
source endpoints and all prior unmoved source clusters remain invariant.
No source pin, land, value or unrelated pose changes. A single local ground
via must physically join the actual adjacent In1 own-reference copper and
the actual U14014.7 source ground after refill. Signal copper stays on F.
The declared 8mm signal and 20mm return search bounds are engineering layout
screens, not manufacturer guarantees or a measured filtering/EMC assertion.
"""
import argparse,collections,copy,heapq,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,children,child,value,q,dump
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills,zone_definition
from hardware_route_owned_bypass_loops import Geometry,connected
from hardware_route_local_signals import paths
from hardware_populate_motherboard_pcb import sha,write,pad_template,footprint_name,intersects
from hardware_place_owned_capacitors_native import MutableOccupancy,side_box
from hardware_anchor_owned_cmos_returns import source_clusters
from hardware_route_logic_return import identity,mm,xy,segment_distance,distance,segment_hits_box
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_owned_bypass_loops_wip_r03 import reviewed_wip_warnings,new_route_defects

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
LEAF='82cde8bc-14e0-4619-8f22-f833a5d6578b'
STALE_VIA='2505e35e-2db7-4d2d-a376-61cce620d25d'
OLD_B_STUB='18586bb6-4db0-4106-bfa6-3faabc36fecc'
ORIGIN_VIA='920f4b9d-b026-4188-bd6a-ef0f92361cd5'
OLD_SOURCE_F_FEED='f45620a4-572b-41d0-869f-2730975cb46a'
RETIRED={LEAF,STALE_VIA,OLD_B_STUB,ORIGIN_VIA,OLD_SOURCE_F_FEED}
def ref(f):return next(value(p[2])for p in children(f,'property')if value(p[1])=='Reference')
def path_length(points):return sum(math.dist(a,b)for a,b in zip(points,points[1:]))
def grid_path(geometry,start,end,net,max_length,other_routes=(),extra_pad=None):
 step=.25;point=lambda n:(round(start[0]+step*n[0],7),round(start[1]+step*n[1],7))
 def legal(s,e):
  if extra_pad is not None:
   box=tuple(pcbnew.ToMM(v)for v in(extra_pad.GetBoundingBox().GetX(),extra_pad.GetBoundingBox().GetY(),extra_pad.GetBoundingBox().GetRight(),extra_pad.GetBoundingBox().GetBottom()))
   if segment_hits_box(s,e,box,.25):return False
  if any(segment_distance(s,e,a,b)<.35-1e-6 for route in other_routes for a,b in zip(route,route[1:])):return False
  return geometry.clear([s,e],net,pcbnew.F_Cu)
 queue=[(math.dist(start,end),0.,(0,0))];cost={(0,0):0.};prev={};edges={}
 while queue:
  _,travelled,n=heapq.heappop(queue)
  if travelled!=cost.get(n):continue
  s=point(n)
  if math.dist(s,end)<=.4 and travelled+math.dist(s,end)<=max_length and legal(s,end):
   result=[end,s]
   while n!=(0,0):n=prev[n];result.append(point(n))
   result=list(reversed(result));compact=[result[0]]
   for p in result[1:]:
    if math.dist(p,compact[-1])>1e-7:compact.append(p)
   return compact
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   nxt=(n[0]+dx,n[1]+dy);e=point(nxt);new=travelled+step*math.hypot(dx,dy)
   if new+math.dist(e,end)>max_length or new>=cost.get(nxt,float('inf')):continue
   key=tuple(sorted((n,nxt)))
   if key not in edges:edges[key]=legal(s,e)
   if not edges[key]:continue
   cost[nxt]=new;prev[nxt]=n;heapq.heappush(queue,(new+math.dist(e,end),new,nxt))
 return None
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('board','owners','source','out','placement_candidates'):ap.add_argument('--'+k.replace('_','-'),dest=k,type=Path,required=True)
 ap.add_argument('--baseline-disposition',type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 model=json.loads((a.source/'design.json').read_text());parts=model['components'];rows=json.loads(a.owners.read_text())['capacitors'];owner=next(r for r in rows if r['ref']=='C14012')
 if (owner['owner'],owner['actual_owner_MPN'],owner['category'],owner['power_nodes'],owner['return_nodes'])!=('U14014','SN74LVC14APWR','contact_filter',[{'ref':'U14014','pin':'11','net':'MPG_ENABLE_CONDITIONED'}],[{'ref':'U14014','pin':'7','net':'LOGIC_GND'}]):raise ValueError('Exact actual contact filter source required')
 if parts['C14012']['mpn']!='GRM1885C2A103JA01D'or parts['C14012']['pins']!={'1':'MPG_ENABLE_CONDITIONED','2':'LOGIC_GND'}:raise ValueError('Exact original filter component required')
 frozen={str(p.resolve()):sha(p)for p in(a.board,a.owners,a.source/'design.json',a.source/'netlist.xml',a.placement_candidates,Path(__file__))}
 baseline_path=a.board.parent/'drc.json'
 frozen.update({str(p.resolve()):sha(p) for p in (baseline_path,a.baseline_disposition)})
 known=reviewed_wip_warnings(json.loads(baseline_path.read_text()),json.loads(a.baseline_disposition.read_text()),sha(a.board))
 b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};cap=fps['C14012'];oldpose=(tuple(cap.GetPosition()),cap.GetOrientationDegrees(),cap.GetLayer());oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in b.GetPads()}
 clusters=source_clusters(b);capuids={p.m_Uuid.AsString()for p in cap.Pads()};clusters=[v-capuids for v in clusters if v-capuids]
 pin=lambda r,n:next(p for p in fps[r].Pads()if p.GetNumber()==n)
 cp,cr,op,og=pin('C14012','1'),pin('C14012','2'),pin('U14014','11'),pin('U14014','7')
 if cap.GetLayer()!=pcbnew.F_Cu or fps['U14014'].GetLayer()!=pcbnew.F_Cu:raise ValueError('Actual same-F manufacturer lands required')
 touched={t.m_Uuid.AsString():t for t in b.GetTracks()if any(t.GetNetname()==p.GetNetname()and(t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd()))for p in cap.Pads())}
 if set(touched)!={LEAF}or touched[LEAF].GetNetname()!=op.GetNetname()or isinstance(touched[LEAF],pcbnew.PCB_VIA):raise ValueError('Exact private old pad leaf differs')
 old_objects={t.m_Uuid.AsString():t for t in b.GetTracks()}
 stale=old_objects[STALE_VIA]
 if not isinstance(stale,pcbnew.PCB_VIA)or stale.GetNetname()!=op.GetNetname():raise ValueError('Exact old filter transition differs')
 incident={t.m_Uuid.AsString() for t in b.GetTracks()if not isinstance(t,pcbnew.PCB_VIA)and t.IsOnLayer(pcbnew.F_Cu)and t.GetNetname()==op.GetNetname()and t.HitTest(stale.GetPosition())}
 if incident!={LEAF}:raise ValueError('Old transition has another real F branch')
 if any(p.IsOnLayer(pcbnew.F_Cu)and p.HitTest(stale.GetPosition())for p in b.GetPads()):raise ValueError('Old transition touches a real F source pad')
 if not any(t.IsOnLayer(pcbnew.B_Cu)and t.GetNetname()==op.GetNetname()and t.HitTest(stale.GetPosition())for t in b.GetTracks()if not isinstance(t,pcbnew.PCB_VIA)):raise ValueError('Actual retained B trunk missing')
 stub=old_objects[OLD_B_STUB];origin=old_objects[ORIGIN_VIA]
 if isinstance(stub,pcbnew.PCB_VIA)or stub.GetLayer()!=pcbnew.B_Cu or stub.GetNetname()!=op.GetNetname()or not stub.HitTest(stale.GetPosition())or not stub.HitTest(origin.GetPosition()):raise ValueError('Exact old private B filter branch differs')
 if any(p.IsOnLayer(pcbnew.B_Cu)and p.HitTest(stub.GetStart())for p in b.GetPads()):raise ValueError('Private B branch origin touches an unrelated source land')
 for ident in RETIRED:b.Remove(old_objects[ident])
 b.BuildConnectivity()
 # Explicit native source-cluster retention is required before moving the pad.
 byu={p.m_Uuid.AsString():p for p in b.GetPads()}
 for ids in clusters:
  actual={p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(byu[next(iter(ids))])if isinstance(p,pcbnew.PAD)}|{next(iter(ids))}
  if not ids<=actual:raise ValueError('Private-leaf retirement fragments another source cluster')
 occupancy=MutableOccupancy()
 for r,f in fps.items():occupancy.update(r,f.GetLayer(),side_box(f))
 occupancy.hard.extend([((331,278,371,333),pcbnew.F_Cu),((421.87,277.3,447.27,346.45),pcbnew.F_Cu)])
 geometry=Geometry(b)
 choices=[];signal_candidates=[];origin=mm(op.GetPosition());counts=collections.Counter()
 fills=collect_native_reference_fills(b,{cr.GetNetname()},[pcbnew.In1_Cu])
 own_reference=fills.get((cr.GetNetname(),pcbnew.In1_Cu))
 if own_reference is None or not own_reference.Area():raise ValueError('Actual own In1 return plane absent')
 candidates=json.loads(a.placement_candidates.read_text())['short_signal_candidates']
 # The cap is excluded only from the immutable old-position obstacle index;
 # both new pads are independently checked against all other metal below.
 for candidate in candidates:
    angle=candidate['angle'];cap.SetPosition(pcbnew.VECTOR2I(*candidate['position_nm']));cap.SetOrientationDegrees(angle);box=side_box(cap)
    if min(box)<.5 or box[2]>459.5 or box[3]>339.5 or occupancy.collision('C14012',pcbnew.F_Cu,box,.25):continue
    counts['clear_body']+=1
    if any(intersects(tuple(pcbnew.ToMM(v)for v in(p.GetBoundingBox().GetX(),p.GetBoundingBox().GetY(),p.GetBoundingBox().GetRight(),p.GetBoundingBox().GetBottom())),tuple(pcbnew.ToMM(v)for v in(other.GetBoundingBox().GetX(),other.GetBoundingBox().GetY(),other.GetBoundingBox().GetRight(),other.GetBoundingBox().GetBottom())),.15)for p in cap.Pads()for other in b.GetPads()if other.GetParentFootprint().GetReference()!='C14012'and other.IsOnLayer(pcbnew.F_Cu)and p.GetNetname()!=other.GetNetname()):continue
    signal=grid_path(geometry,mm(op.GetPosition()),mm(cp.GetPosition()),cp.GetNetname(),8,extra_pad=cr)
    if signal is None:continue
    counts['legal_signal']+=1
    signal_candidates.append(dict(position_nm=list(cap.GetPosition()),angle=angle,signal_path_mm=signal,signal_length_mm=path_length(signal),ground_pad_mm=mm(cr.GetPosition())))
    # This direct ground transition uses the physically adjacent reference.
    # No long F return detour or unrelated named island is credited.
    for d in (.7,.85,1.,1.25,1.5,1.75,2.):
     for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)):
      pt=(round(mm(cr.GetPosition())[0]+d*dx,6),round(mm(cr.GetPosition())[1]+d*dy,6))
      if not geometry.via(pt,cr.GetNetname()) or not covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),own_reference):continue
      if any(distance(pt,s,e)<.455 for s,e in zip(signal,signal[1:])):continue
      ret=grid_path(geometry,mm(cr.GetPosition()),pt,cr.GetNetname(),2.,other_routes=[signal],extra_pad=cp)
      if ret is not None:choices.append((path_length(signal)+path_length(ret),tuple(cap.GetPosition()),angle,signal,ret,pt))
 if not choices:
  a.out.mkdir(parents=True);write(a.out/'unadopted-search.json',dict(passed=False,input_sha256=frozen,original_PCB_and_source_unchanged=True,search_counts=dict(counts),short_signal_candidates=signal_candidates,required_remaining='Same-side source-owned local return must route through a physically joined adjacent own reference; no F-only ground pair fits the declared20mm screen.',manufacturing_ready=False))
  raise ValueError('No true same-side contact-filter cell fits; explicit further routing required '+str(counts))
 # Shortest actual legal pair; no invented 0603 land rotation or circuit delta.
 _,position,angle,signal,ret,ground_via=min(choices,key=lambda v:v[0]);cap.SetPosition(pcbnew.VECTOR2I(*position));cap.SetOrientationDegrees(angle)
 added=[]
 def add_path(points,net,layer):
  for s,e in zip(points,points[1:]):
   if math.dist(s,e)<1e-7:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);added.append(t)
 def add_via(point,net):
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(point));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);v.SetIsFree(True);b.Add(v);added.append(v);return v
 for points,net in((signal,cp.GetNetname()),(ret,cr.GetNetname())):
  for s,e in zip(points,points[1:]):
   if math.dist(s,e)<1e-7:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);added.append(t)
 v=add_via(ground_via,cr.GetNetname())
 # The exact receiving ground pin has no nearby physical stitch in the
 # baseline. Add its own short source branch, rather than crediting a label.
 geometry=Geometry(b)
 owner_return=None
 for d in (.7,.85,1.,1.25,1.5,1.75,2.):
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)):
   point=(round(mm(og.GetPosition())[0]+d*dx,6),round(mm(og.GetPosition())[1]+d*dy,6))
   if not geometry.via(point,cr.GetNetname())or not covered(circle(tuple(xy(point)),pcbnew.FromMM(.24)),own_reference):continue
   path=grid_path(geometry,mm(og.GetPosition()),point,cr.GetNetname(),2.,other_routes=[signal,ret])
   if path is not None:owner_return=path,point;break
  if owner_return:break
 if owner_return is None:raise ValueError('Actual receiving U14014.7 needs a legal source-ground stitch')
 add_path(owner_return[0],cr.GetNetname(),pcbnew.F_Cu);owner_ground_via=add_via(owner_return[1],cr.GetNetname())
 geometry=Geometry(b)
 # The original transfer's B reference is obstructed by the actual foreign
 # C14047 field lands. Preserve the clamp and reroute its private transfer
 # above that field projection, keeping the short actual source-ground path.
 # Replace only the private obsolete branch with a source-to-input feed, keeping
 # the capacitor/input connection short and on F.
 own_b=collect_native_reference_fills(b,{cr.GetNetname()},[pcbnew.In4_Cu])[(cr.GetNetname(),pcbnew.In4_Cu)]
 clamp_output,clamp_ground=pin('U14012','3'),pin('U14012','1')
 source_escape=None
 # This declared 3.5 mm slow-contact escape is a layout screen, not a
 # manufacturer's numeric limit or an RF qualification claim.
 for d in (1.,1.25,1.5,1.75,2.,2.25,2.5,2.75,3.,3.25,3.5):
  for dx,dy in ((0,-1),(-.707107,-.707107),(.707107,-.707107),(-1,0),(1,0)):
   point=(round(mm(clamp_output.GetPosition())[0]+d*dx,6),round(mm(clamp_output.GetPosition())[1]+d*dy,6))
   if not geometry.via(point,cp.GetNetname())or not geometry.clear([mm(clamp_output.GetPosition()),point],cp.GetNetname(),pcbnew.F_Cu):continue
   # Actual full own-return rings must remain outside both foreign copper
   # and native signal-via holes. The final strict checker repeats this after
   # refill and permits only the resulting endpoint's own antipad.
   ring=circle(tuple(xy(point)),pcbnew.FromMM(1.07));ring.BooleanSubtract(circle(tuple(xy(point)),pcbnew.FromMM(.87)))
   if not covered(ring,own_reference)or not covered(ring,own_b):continue
   ground_choice=None
   for spacing in(.7,.85,1.):
    for gx,gy in ((-1,0),(1,0),(0,-1),(0,1)):
     q=(round(point[0]+spacing*gx,6),round(point[1]+spacing*gy,6))
     if not geometry.via(q,cr.GetNetname())or not covered(circle(tuple(xy(q)),pcbnew.FromMM(.24)),own_reference)or not covered(circle(tuple(xy(q)),pcbnew.FromMM(.24)),own_b):continue
     ground_path=grid_path(geometry,mm(clamp_ground.GetPosition()),q,cr.GetNetname(),2.,other_routes=[[mm(clamp_output.GetPosition()),point]])
     if ground_path is not None:ground_choice=q,ground_path;break
    if ground_choice:break
   if ground_choice:source_escape=point,ground_choice;break
  if source_escape:break
 if source_escape is None:raise ValueError('Actual clamp transfer needs a bounded own-domain escape above the retained foreign field pads')
 source_point,(source_stitch,source_return_path)=source_escape
 add_path([mm(clamp_output.GetPosition()),source_point],cp.GetNetname(),pcbnew.F_Cu)
 source_signal_via=add_via(source_point,cp.GetNetname())
 add_path(source_return_path,cr.GetNetname(),pcbnew.F_Cu);source_return_via=add_via(source_stitch,cr.GetNetname())
 geometry=Geometry(b)
 chosen_feed=None
 for d in (.7,.85,1.,1.25,1.5,1.75,2.):
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)):
   point=(round(mm(op.GetPosition())[0]+d*dx,6),round(mm(op.GetPosition())[1]+d*dy,6))
   if not geometry.via(point,cp.GetNetname())or not geometry.clear([mm(op.GetPosition()),point],cp.GetNetname(),pcbnew.F_Cu):continue
   path=next((ps for ps in paths(source_point,point)if path_length(ps)<=35. and geometry.clear(ps,cp.GetNetname(),pcbnew.B_Cu)and all(covered(corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.2)),own_b)for s,e in zip(ps,ps[1:]))),None)
   if path is None:continue
   stitch=next((q for spacing in(.7,.85,1.)for sx,sy in((1,0),(-1,0),(0,1),(0,-1))for q in[(round(point[0]+spacing*sx,6),round(point[1]+spacing*sy,6))]if geometry.via(q,cr.GetNetname())and math.dist(q,point)>=.65 and covered(circle(tuple(xy(q)),pcbnew.FromMM(.24)),own_reference)and covered(circle(tuple(xy(q)),pcbnew.FromMM(.24)),own_b)),None)
   if stitch:chosen_feed=point,path,stitch;break
  if chosen_feed:break
 if chosen_feed is None:raise ValueError('Actual conditioned source requires a B feed with continuous own return and local transition stitch')
 feed_point,feed_path,feed_stitch=chosen_feed
 add_path(feed_path,cp.GetNetname(),pcbnew.B_Cu);add_path([mm(op.GetPosition()),feed_point],cp.GetNetname(),pcbnew.F_Cu)
 feed_via=add_via(feed_point,cp.GetNetname());feed_return_via=add_via(feed_stitch,cr.GetNetname())
 geometry=Geometry(b)
 series_node=pin('R14021','2')
 pull_path=grid_path(geometry,mm(series_node.GetPosition()),mm(cp.GetPosition()),cp.GetNetname(),12.,extra_pad=cr)
 if pull_path is None:raise ValueError('Exact R14021.2 series-input node still needs physical copper')
 add_path(pull_path,cp.GetNetname(),pcbnew.F_Cu)
 expected={t.m_Uuid.AsString():identity(t)for t in added};b.BuildConnectivity()
 if not all(connected(b,cp,p)for p in (op,pin('U14012','3'),series_node))or not connected(b,cr,og):raise ValueError('Actual whole conditioned net or receiving source-ground pair did not close')
 a.out.mkdir(parents=True);dest=a.out/'motherboard-contact-filter-cell-candidate.kicad_pcb'
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
 for p in a.board.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
  elif p.name=='fp-lib-table':shutil.copyfile(p,a.out/p.name)
 pcbnew.SaveBoard(str(dest),b)
 run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);(a.out/'drc.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Actual native DRC failed to execute')
 report=json.loads((a.out/'drc.json').read_text())
 if report.get('ignored_checks')or any(v['severity']=='error'for v in report['violations']):raise ValueError('Native contact-filter cell has errors/ignored checks')
 if new_route_defects(report,known):raise ValueError('New actual native defect requires reroute; no warning suppression')
 if any(i['uuid']in expected or i['uuid']==cap.m_Uuid.AsString()for v in report['violations']for i in v['items']):raise ValueError('New native cell warning requires actual reroute')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();nf={f.GetReference():f for f in fresh.GetFootprints()};cu={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()};pads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in fresh.GetPads()}
 if set(cu)!=set(oldcu)-RETIRED|set(expected)or any(cu[u]!=v for u,v in oldcu.items()if u not in RETIRED)or any(cu[u]!=v for u,v in expected.items()):raise ValueError('Retained or exact new copper/net changed')
 if set(pads)!=set(oldpads)or any(pads[u]!=v for u,v in oldpads.items()if v[0]!='C14012')or any(pads[u][:3]!=oldpads[u][:3]for u in capuids):raise ValueError('Other actual lands/poses/source pins changed')
 byu={p.m_Uuid.AsString():p for p in fresh.GetPads()}
 for ids in clusters:
  actual={p.m_Uuid.AsString()for p in fresh.GetConnectivity().GetConnectedItems(byu[next(iter(ids))])if isinstance(p,pcbnew.PAD)}|{next(iter(ids))}
  if not ids<=actual:raise ValueError('Prior unmoved source cluster fragmented')
 npin=lambda r,n:next(p for p in nf[r].Pads()if p.GetNumber()==n)
 if not all(connected(fresh,npin('C14012','1'),npin(*pair))for pair in(('U14014','11'),('U14012','3'),('R14021','2')))or not connected(fresh,npin('C14012','2'),npin('U14014','7')):raise ValueError('Native final actual whole conditioned net/own-filter pairs opened')
 final_via=next(t for t in fresh.GetTracks()if t.m_Uuid.AsString()==v.m_Uuid.AsString())
 final_ref=collect_native_reference_fills(fresh,{cr.GetNetname()},[pcbnew.In1_Cu])[(cr.GetNetname(),pcbnew.In1_Cu)]
 if not final_via.FlashLayer(pcbnew.In1_Cu)or not fresh.GetConnectivity().IsConnectedOnLayer(final_via,pcbnew.In1_Cu)or not covered(circle(tuple(final_via.GetPosition()),pcbnew.FromMM(.24)),final_ref):raise ValueError('Final ground via lacks actual own-reference annulus')
 for s,e in zip(signal,signal[1:]):
  if not covered(corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.2)),final_ref):raise ValueError('Filter signal lacks continuous adjacent own return')
 first=parse(without_generated_fills(a.board.read_text()));last=parse(without_generated_fills(dest.read_text()));oldraw={ref(f):dump(f)for f in children(first,'footprint')};newraw={ref(f):dump(f)for f in children(last,'footprint')}
 if any(newraw[r]!=v for r,v in oldraw.items()if r!='C14012'):raise ValueError('Unrelated raw footprint changed')
 defs=lambda tree:{value(child(z,'uuid')[1]):zone_definition(z)for z in children(tree,'zone')}
 if defs(first)!=defs(last):raise ValueError('Zone definition changed')
 if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen input changed')
 scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact C14012 actual U14014.11 contact-filter cell: proven old private pad-only leaf and redundant transition retired; all retained B source trunks/clock copper and prior unmoved native source clusters preserved; sameF signal with actual adjacent own In1 source-ground return.',reviewed_footprint_references=['C14012'],reviewed_copper_delta_UUIDs=sorted(set(expected)|RETIRED),reviewed_added_zone_UUIDs=[])
 write(a.out/'bounded-scope.json',scope)
 result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_retired_private_filter_copper=[dict(uuid=u,before=oldcu[u])for u in sorted(RETIRED)],all_existing_clock_copper_preserved=True,new_copper_UUIDs=sorted(expected),added_vias=4,actual_ground_via_position_mm=ground_via,actual_receiver_ground_via_position_mm=owner_return[1],actual_conditioned_source_feed_path_mm=path_length(feed_path),actual_own_In1_flashed_native_connected_annulus=True,actual_source_ground_endpoint='U14014.7',whole_actual_four_source_pin_conditioned_net_connected=True,exact_capacitor_pose_before=[list(oldpose[0]),oldpose[1],oldpose[2]],exact_capacitor_pose_after=[list(position),angle,pcbnew.F_Cu],actual_signal_path_mm=path_length(signal),actual_return_path_mm=path_length(ret),actual_sameF_signal_and_own_reference_return_native_connected=True,all_other_copper_pads_poses_and_zone_rules_preserved=True,all_unmoved_source_clusters_preserved=True,native_DRC_types=dict(collections.Counter(v['type']for v in report['violations'])),native_errors=0,ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,measured_filter_or_EMC_qualified=False)
 write(a.out/'receipt.json',result);print({k:result[k]for k in('passed','actual_signal_path_mm','actual_return_path_mm','native_DRC_types','uncapped_missing_joins','board_sha256')})
if __name__=='__main__':main()
