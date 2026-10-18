"""Close only the C14012 pendant-enable filter at its actual U14014 input.

Exactly one old private pad-only leaf is retired. All existing clock copper,
source endpoints and all prior unmoved source clusters remain invariant.
No source pin, land, value or unrelated pose changes; no new vias.
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

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
LEAF='82cde8bc-14e0-4619-8f22-f833a5d6578b'
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
 for k in ('board','owners','source','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 model=json.loads((a.source/'design.json').read_text());parts=model['components'];rows=json.loads(a.owners.read_text())['capacitors'];owner=next(r for r in rows if r['ref']=='C14012')
 if (owner['owner'],owner['actual_owner_MPN'],owner['category'],owner['power_nodes'],owner['return_nodes'])!=('U14014','SN74LVC14APWR','contact_filter',[{'ref':'U14014','pin':'11','net':'MPG_ENABLE_CONDITIONED'}],[{'ref':'U14014','pin':'7','net':'LOGIC_GND'}]):raise ValueError('Exact actual contact filter source required')
 if parts['C14012']['mpn']!='GRM1885C2A103JA01D'or parts['C14012']['pins']!={'1':'MPG_ENABLE_CONDITIONED','2':'LOGIC_GND'}:raise ValueError('Exact original filter component required')
 frozen={str(p.resolve()):sha(p)for p in(a.board,a.owners,a.source/'design.json',a.source/'netlist.xml',Path(__file__))}
 b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};cap=fps['C14012'];oldpose=(tuple(cap.GetPosition()),cap.GetOrientationDegrees(),cap.GetLayer());oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in b.GetPads()}
 clusters=source_clusters(b);capuids={p.m_Uuid.AsString()for p in cap.Pads()};clusters=[v-capuids for v in clusters if v-capuids]
 pin=lambda r,n:next(p for p in fps[r].Pads()if p.GetNumber()==n)
 cp,cr,op,og=pin('C14012','1'),pin('C14012','2'),pin('U14014','11'),pin('U14014','7')
 if cap.GetLayer()!=pcbnew.F_Cu or fps['U14014'].GetLayer()!=pcbnew.F_Cu:raise ValueError('Actual same-F manufacturer lands required')
 touched={t.m_Uuid.AsString():t for t in b.GetTracks()if any(t.GetNetname()==p.GetNetname()and(t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd()))for p in cap.Pads())}
 if set(touched)!={LEAF}or touched[LEAF].GetNetname()!=op.GetNetname()or isinstance(touched[LEAF],pcbnew.PCB_VIA):raise ValueError('Exact private old pad leaf differs')
 b.Remove(touched[LEAF]);b.BuildConnectivity()
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
 # The cap is excluded only from the immutable old-position obstacle index;
 # both new pads are independently checked against all other metal below.
 for angle in (0,90,180,270):
  cap.SetPosition(xy((0,0)));cap.SetOrientationDegrees(angle);delta=mm(cp.GetPosition())
  for ox in [v/4 for v in range(-28,29)]:
   for oy in [v/4 for v in range(-28,29)]:
    if math.hypot(ox,oy)>7 or math.hypot(ox,oy)<1.5:continue
    cap.SetPosition(xy((origin[0]-delta[0]+ox,origin[1]-delta[1]+oy)));box=side_box(cap)
    if min(box)<.5 or box[2]>459.5 or box[3]>339.5 or occupancy.collision('C14012',pcbnew.F_Cu,box,.25):continue
    counts['clear_body']+=1
    if any(intersects(tuple(pcbnew.ToMM(v)for v in(p.GetBoundingBox().GetX(),p.GetBoundingBox().GetY(),p.GetBoundingBox().GetRight(),p.GetBoundingBox().GetBottom())),tuple(pcbnew.ToMM(v)for v in(other.GetBoundingBox().GetX(),other.GetBoundingBox().GetY(),other.GetBoundingBox().GetRight(),other.GetBoundingBox().GetBottom())),.15)for p in cap.Pads()for other in b.GetPads()if other.GetParentFootprint().GetReference()!='C14012'and other.IsOnLayer(pcbnew.F_Cu)and p.GetNetname()!=other.GetNetname()):continue
    signal=grid_path(geometry,mm(op.GetPosition()),mm(cp.GetPosition()),cp.GetNetname(),8,extra_pad=cr)
    if signal is None:continue
    counts['legal_signal']+=1
    signal_candidates.append(dict(position_nm=list(cap.GetPosition()),angle=angle,signal_path_mm=signal,signal_length_mm=path_length(signal),ground_pad_mm=mm(cr.GetPosition())))
    ret=grid_path(geometry,mm(og.GetPosition()),mm(cr.GetPosition()),cr.GetNetname(),20,other_routes=[signal],extra_pad=cp)
    if ret is not None:choices.append((path_length(signal)+path_length(ret),tuple(cap.GetPosition()),angle,signal,ret))
 if not choices:
  a.out.mkdir(parents=True);write(a.out/'unadopted-search.json',dict(passed=False,input_sha256=frozen,original_PCB_and_source_unchanged=True,search_counts=dict(counts),short_signal_candidates=signal_candidates,required_remaining='Same-side source-owned local return must route through a physically joined adjacent own reference; no F-only ground pair fits the declared20mm screen.',manufacturing_ready=False))
  raise ValueError('No true same-side contact-filter cell fits; explicit further routing required '+str(counts))
 # Shortest actual legal pair; no invented 0603 land rotation or circuit delta.
 _,position,angle,signal,ret=min(choices,key=lambda v:v[0]);cap.SetPosition(pcbnew.VECTOR2I(*position));cap.SetOrientationDegrees(angle)
 added=[]
 for points,net in((signal,cp.GetNetname()),(ret,cr.GetNetname())):
  for s,e in zip(points,points[1:]):
   if math.dist(s,e)<1e-7:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);added.append(t)
 expected={t.m_Uuid.AsString():identity(t)for t in added};b.BuildConnectivity()
 if not connected(b,cp,op)or not connected(b,cr,og):raise ValueError('Actual local capacitor/input/return pairs did not close')
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
 if any(i['uuid']in expected or i['uuid']==cap.m_Uuid.AsString()for v in report['violations']for i in v['items']):raise ValueError('New native cell warning requires actual reroute')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();nf={f.GetReference():f for f in fresh.GetFootprints()};cu={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()};pads={p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in fresh.GetPads()}
 if set(cu)!=set(oldcu)-{LEAF}|set(expected)or any(cu[u]!=v for u,v in oldcu.items()if u!=LEAF)or any(cu[u]!=v for u,v in expected.items()):raise ValueError('Retained or exact new copper/net changed')
 if set(pads)!=set(oldpads)or any(pads[u]!=v for u,v in oldpads.items()if v[0]!='C14012')or any(pads[u][:3]!=oldpads[u][:3]for u in capuids):raise ValueError('Other actual lands/poses/source pins changed')
 byu={p.m_Uuid.AsString():p for p in fresh.GetPads()}
 for ids in clusters:
  actual={p.m_Uuid.AsString()for p in fresh.GetConnectivity().GetConnectedItems(byu[next(iter(ids))])if isinstance(p,pcbnew.PAD)}|{next(iter(ids))}
  if not ids<=actual:raise ValueError('Prior unmoved source cluster fragmented')
 npin=lambda r,n:next(p for p in nf[r].Pads()if p.GetNumber()==n)
 if not connected(fresh,npin('C14012','1'),npin('U14014','11'))or not connected(fresh,npin('C14012','2'),npin('U14014','7')):raise ValueError('Native final actual own-filter pairs opened')
 first=parse(without_generated_fills(a.board.read_text()));last=parse(without_generated_fills(dest.read_text()));oldraw={ref(f):dump(f)for f in children(first,'footprint')};newraw={ref(f):dump(f)for f in children(last,'footprint')}
 if any(newraw[r]!=v for r,v in oldraw.items()if r!='C14012'):raise ValueError('Unrelated raw footprint changed')
 defs=lambda tree:{value(child(z,'uuid')[1]):zone_definition(z)for z in children(tree,'zone')}
 if defs(first)!=defs(last):raise ValueError('Zone definition changed')
 if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen input changed')
 scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact C14012 actual U14014.11 contact-filter cell: one proven old private pad-only leaf retired; sameF owner-signal and owner-ground branches closed around all actual retained copper; all prior unmoved native source clusters retained.',reviewed_footprint_references=['C14012'],reviewed_copper_delta_UUIDs=sorted(set(expected)|{LEAF}),reviewed_added_zone_UUIDs=[])
 write(a.out/'bounded-scope.json',scope)
 result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_retired_private_leaf=dict(uuid=LEAF,before=oldcu[LEAF]),all_existing_clock_copper_preserved=True,new_F_copper_UUIDs=sorted(expected),added_vias=0,exact_capacitor_pose_before=[list(oldpose[0]),oldpose[1],oldpose[2]],exact_capacitor_pose_after=[list(position),angle,pcbnew.F_Cu],actual_signal_path_mm=path_length(signal),actual_return_path_mm=path_length(ret),actual_sameF_signal_and_return_native_connected=True,all_other_copper_pads_poses_and_zone_rules_preserved=True,all_unmoved_source_clusters_preserved=True,native_DRC_types=dict(collections.Counter(v['type']for v in report['violations'])),native_errors=0,ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,measured_filter_or_EMC_qualified=False)
 write(a.out/'receipt.json',result);print({k:result[k]for k in('passed','actual_signal_path_mm','actual_return_path_mm','native_DRC_types','uncapped_missing_joins','board_sha256')})
if __name__=='__main__':main()
