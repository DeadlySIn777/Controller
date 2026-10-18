"""Close actual AO1 ISO7761 secondary ground on current native56."""
import sys,json,shutil,math,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
base=Path('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');mp=Path('reports/motherboard-domains-20261001/source26-r56-r01/domain-map.json');out=Path('reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r01')
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();(out/'inputs').mkdir();frozen={str(p.resolve()):sha(p)for p in(base,mp,Path(__file__))}
for p in(base,mp,Path(__file__)):shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();fp=next(f for f in b.GetFootprints()if f.GetReference()=='U14623');p=next(p for p in fp.Pads()if p.GetNumber()=='9');net='/motherboard_analog_output/AO1_COM'
if p.GetNetname()!=net or mm(p.GetPosition())!=(386.375,249.445)or fp.GetLayer()!=pcbnew.F_Cu:raise ValueError('Exact reviewed native pin differs')
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets);g=Geometry(b);fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu])[net,pcbnew.In1_Cu];s=mm(p.GetPosition());q=None
for d in(.7,.8,1.,1.2,1.5,1.8,2.):
 for k in range(32):
  candidate=(round(s[0]+d*math.cos(k*math.pi/16),6),round(s[1]+d*math.sin(k*math.pi/16),6))
  if g.via(candidate,net)and g.clear([s,candidate],net,pcbnew.F_Cu,.2)and covered(circle(tuple(xy(candidate)),pcbnew.FromMM(.26)),fill):q=candidate;break
 if q:break
if q is None:raise ValueError('No clear compact actual-secondary ground stitch')
t=pcbnew.PCB_TRACK(b);t.SetNet(p.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetStart(p.GetPosition());t.SetEnd(xy(q));t.SetWidth(pcbnew.FromMM(.2));b.Add(t)
v=pcbnew.PCB_VIA(b);v.SetNet(p.GetNet());v.SetPosition(xy(q));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new=[t.m_Uuid.AsString(),v.m_Uuid.AsString()]
dest=out/'motherboard-AO1-secondary-return-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(actual_source_reference='U14623',actual_secondary_ground_pin='9',actual_source_position_mm=list(s),new_via_position_mm=list(q),length_mm=math.dist(s,q),new_copper_UUIDs=new,input_sha256=frozen))
native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()};now={u:identity(t)for u,t in actual.items()}
if set(now)!=set(oldcu)|set(new)or any(now[u]!=x for u,x in oldcu.items()):raise ValueError('Original actual56 copper changed')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or oldzones!=definitions(dest):raise ValueError('Original source pads/poses/zones changed')
after=native_pad_clusters(b,nets);survived=clusters_survive(before,after);write(out/'all-native-source-cluster-proof.json',dict(before=before,after=after,passed=survived))
if not survived:raise ValueError('An original source cluster split')
v=actual[new[1]];peers={p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(v)}
fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu])[net,pcbnew.In1_Cu]
if p.m_Uuid.AsString()not in peers or not physical_reference_contact(v,pcbnew.In1_Cu,b.GetConnectivity())or not covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),fill):raise ValueError('Actual secondary pin/source connected flashed inner annulus not proven')
if any(r['severity']=='error'for r in native['violations']):raise ValueError('Native geometry errors remain')
if any(sha(Path(p))!=v for p,v in frozen.items()):raise ValueError('Frozen input changed')
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Two additive real low-current ground objects join the actual ISO7761 AO1 secondary pin9 to its own In1 filled resource. No source/pad/pose/oldCu/zone changes. Actual source reachability, flashed annulus and native own-layer connection are independently checked; no global current or complete analog loop claim.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=new,reviewed_added_zone_UUIDs=[]))
r=dict(board_sha256=sha(dest),before_board_sha256=sha(base),native_errors=0,native_DRC_types=dict(collections.Counter(x['type']for x in native['violations'])),ignored_checks=native['ignored_checks'],actual_secondary_pin_source_connected=True,actual_In1_annulus_flashed_and_native_connected=True,actual_full_own_In1_annulus_coverage=True,all_old_Cu_source_pads_poses_zones_and_clusters_preserved=True,actual_ground_branch_length_mm=math.dist(s,q),new_copper_UUIDs=new,scope_sha256=sha(out/'bounded-scope.json'),global_reference_passed=False,manufacturing_ready=False);write(out/'receipt.json',r);print(json.dumps(r,indent=2))
