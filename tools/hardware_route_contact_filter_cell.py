"""Close only the C14012 pendant-enable filter at its actual U14014 input.

Exactly one old private pad-only leaf is retired. One existing three-item clock
transition moves locally to free the input fanout; clock copper widths/drill,
source endpoints and all prior source clusters remain. The explicit additional
2mm length screen is an engineering bound; final return review remains required.
No source pin, land, value or unrelated pose changes; no new vias.
The declared 8mm signal and 20mm return search bounds are engineering layout
screens, not manufacturer guarantees or a measured filtering/EMC assertion.
"""
import argparse,collections,copy,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,children,child,value,q,dump
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills,zone_definition
from hardware_route_owned_bypass_loops import Geometry,connected
from hardware_route_local_signals import paths
from hardware_populate_motherboard_pcb import sha,write,pad_template,footprint_name,intersects
from hardware_place_owned_capacitors_native import MutableOccupancy,side_box
from hardware_anchor_owned_cmos_returns import source_clusters
from hardware_route_logic_return import identity,mm,xy,segment_distance,distance

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
LEAF='82cde8bc-14e0-4619-8f22-f833a5d6578b'
CLOCK={'a9ebc455-5dc9-4a45-9f70-5b45351e4560','fdd40b38-090e-4411-9fa4-5328aed881f3','5dfb8bb6-6990-4896-84f1-387ed5c4b5d1'}
def ref(f):return next(value(p[2])for p in children(f,'property')if value(p[1])=='Reference')
def path_length(points):return sum(math.dist(a,b)for a,b in zip(points,points[1:]))
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
 clock_items={t.m_Uuid.AsString():t for t in b.GetTracks()if t.m_Uuid.AsString()in CLOCK}
 if set(clock_items)!=CLOCK or any(t.GetNetname()!='/motherboard_operator/FAST_SR_CLK_BUFFER'for t in clock_items.values()):raise ValueError('Exact old blocking clock junction required')
 if any((125637500,277875000)not in (tuple(t.GetStart()),tuple(t.GetEnd()))for t in clock_items.values()):raise ValueError('Exact blocking clock coordinates differ')
 for t in clock_items.values():b.Remove(t)
 geometry=Geometry(b)
 clock_options=[];escape=(mm(op.GetPosition()),(mm(op.GetPosition())[0]+2,mm(op.GetPosition())[1]));clock_name='/motherboard_operator/FAST_SR_CLK_BUFFER'
 for ix in range(-8,9):
  for iy in range(-8,9):
   pt=(125.6375+ix/4,277.875+iy/4)
   if math.dist(pt,(125.6375,277.875))<.8 or math.dist(pt,(125.6375,277.875))>2:continue
   if not geometry.via(pt,clock_name)or distance(pt,*escape)<.5:continue
   legs=[]
   for t in clock_items.values():
    if isinstance(t,pcbnew.PCB_VIA):continue
    fixed=mm(t.GetEnd())if tuple(t.GetStart())==(125637500,277875000)else mm(t.GetStart())
    if not geometry.clear([fixed,pt],clock_name,t.GetLayer())or t.GetLayer()==pcbnew.F_Cu and segment_distance(fixed,pt,*escape)<.35:break
    legs.append((fixed,pt))
   else:
    total=sum(math.dist(s,e)for s,e in legs)
    if total<=13.7:clock_options.append((math.dist(pt,(125.6375,277.875)),total,pt))
 if not clock_options:raise ValueError('Current clock transition has no legal bounded escape outside the required contact fanout')
 new_junction=min(clock_options)[2]
 for t in clock_items.values():
  if isinstance(t,pcbnew.PCB_VIA):t.SetPosition(xy(new_junction))
  else:
   if tuple(t.GetStart())==(125637500,277875000):t.SetStart(xy(new_junction))
   if tuple(t.GetEnd())==(125637500,277875000):t.SetEnd(xy(new_junction))
   if not geometry.clear([mm(t.GetStart()),mm(t.GetEnd())],t.GetNetname(),t.GetLayer()):raise ValueError('Same-line clock junction move lacks native metal clearance')
  b.Add(t);geometry.add(t)
 clock_after={u:identity(t)for u,t in clock_items.items()}
 clock_length=lambda values:sum(math.dist(v[2],v[3])/1e6 for v in values if v[7]is None)
 if abs(clock_length([oldcu[u]for u in CLOCK])-clock_length(list(clock_after.values())))>2:raise ValueError('Local clock transition exceeds bounded extra length')
 choices=[];origin=mm(op.GetPosition());counts=collections.Counter()
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
    signal=next((v for v in paths(mm(cp.GetPosition()),mm(op.GetPosition()))if path_length(v)<=8 and geometry.clear(v,cp.GetNetname(),pcbnew.F_Cu)),None)
    if signal is None:continue
    counts['legal_signal']+=1
    ret=next((v for v in paths(mm(cr.GetPosition()),mm(og.GetPosition()))if path_length(v)<=20 and geometry.clear(v,cr.GetNetname(),pcbnew.F_Cu)),None)
    if ret is not None:choices.append((path_length(signal)+path_length(ret),tuple(cap.GetPosition()),angle,signal,ret))
 if not choices:raise ValueError('No true same-side contact-filter cell fits; explicit further routing required '+str(counts))
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
 if set(cu)!=set(oldcu)-{LEAF}|set(expected)or any(cu[u]!=v for u,v in oldcu.items()if u not in {LEAF}|CLOCK)or any(cu[u]!=v for u,v in expected.items())or any(cu[u]!=v for u,v in clock_after.items()):raise ValueError('Retained or exact new copper/net changed')
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
 scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact C14012 actual U14014.11 contact-filter cell: one proven old private pad-only leaf retired; blocking three-item clock junction moved locally with unchanged endpoints/width/drill and at most2mm additional clock path; sameF owner-signal and owner-ground branches closed; all prior unmoved native source clusters retained.',reviewed_footprint_references=['C14012'],reviewed_copper_delta_UUIDs=sorted(set(expected)|{LEAF}|CLOCK),reviewed_added_zone_UUIDs=[])
 write(a.out/'bounded-scope.json',scope)
 result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),exact_retired_private_leaf=dict(uuid=LEAF,before=oldcu[LEAF]),exact_local_clock_junction_edits=[dict(uuid=u,before=oldcu[u],after=clock_after[u])for u in sorted(CLOCK)],clock_old_total_path_mm=clock_length([oldcu[u]for u in CLOCK]),clock_new_total_path_mm=clock_length(list(clock_after.values())),clock_return_corridor_after_final_plane_merge_required=True,new_F_copper_UUIDs=sorted(expected),added_vias=0,exact_capacitor_pose_before=[list(oldpose[0]),oldpose[1],oldpose[2]],exact_capacitor_pose_after=[list(position),angle,pcbnew.F_Cu],actual_signal_path_mm=path_length(signal),actual_return_path_mm=path_length(ret),actual_sameF_signal_and_return_native_connected=True,all_other_copper_pads_poses_and_zone_rules_preserved=True,all_unmoved_source_clusters_preserved=True,native_DRC_types=dict(collections.Counter(v['type']for v in report['violations'])),native_errors=0,ignored_checks=[],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,measured_filter_or_EMC_qualified=False)
 write(a.out/'receipt.json',result);print({k:result[k]for k in('passed','actual_signal_path_mm','actual_return_path_mm','native_DRC_types','uncapped_missing_joins','board_sha256')})
if __name__=='__main__':main()
