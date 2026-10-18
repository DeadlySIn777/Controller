"""Actual DAC GND5 and LDAC4 low-default stitch with bounded own In1 collar."""
import sys,json,shutil,math,collections,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact,validate
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_zone_motherboard_returns import rectangle,duplicate,inflation,split_polygons
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_build_assembly import parse,children,child,value,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition,sha_text
base=Path('reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/motherboard-source26-orphan-free-candidate.kicad_pcb')
mp=Path('reports/motherboard-domains-20261001/source26-r61-orphan-free-r01/domain-map.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r01')
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();(out/'inputs').mkdir();frozen={str(p.resolve()):sha(p)for p in(base,mp,Path(__file__))}
for p in(base,mp,Path(__file__)):shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();mapping=json.loads(mp.read_text());fp=next(f for f in b.GetFootprints()if f.GetReference()=='U14623');p=next(p for p in fp.Pads()if p.GetNumber()=='5');net='/motherboard_analog_output/AO1_COM'
if p.GetNetname()!=net or mm(p.GetPosition())!=(395.4,250.0)or fp.GetLayer()!=pcbnew.F_Cu:raise ValueError('Exact reviewed native pin differs')
source_uid=p.m_Uuid.AsString();oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets)
s=mm(p.GetPosition());q=(394.1,249.75);ext=rectangle([393.7,249.35,394.5,250.15]);g=Geometry(b);guard=ReferenceGuard(b,mapping)
if not g.via(q,net)or not g.clear([s,q],net,pcbnew.F_Cu,.2):raise ValueError('Actual compact source branch/barrel is obstructed')
# The entire extension, not only its centre, must avoid all source-derived
# foreign package/metal, floating islands, barriers and raw-converter areas.
foreign=[]
for other,shape in guard.indices[pcbnew.In1_Cu].candidates((393.7,249.35),(394.5,250.15),.3):
 if other!=net and ext.Collide(shape):foreign.append(other)
if foreign:raise ValueError('Extension intersects foreign source projection '+repr(foreign))
matching=[]
for z in b.Zones():
 if not z.GetIsRuleArea()and z.GetNetname()==net and z.GetLayer()==pcbnew.In1_Cu:
  overlap=duplicate(z.Outline());overlap.BooleanIntersection(ext)
  if overlap.Area()>1e6:matching.append(z)
if len(matching)!=1:raise ValueError('Exactly one existing AO1 outline must own the compact extension')
ao=matching[0];first_area=ao.Outline().Area()/1e12;combined=duplicate(ao.Outline());combined.BooleanAdd(ext)
if combined.OutlineCount()!=1:raise ValueError('Compact same-net extension is not a single continuous outline')
ao.Outline().RemoveAllContours();ao.Outline().Append(combined)
addedzones=[];changed=[dict(uuid=ao.m_Uuid.AsString(),before_area_mm2=first_area,after_combined_area_mm2=combined.Area()/1e12,extra_fragment_UUIDs=[],reason='A compact actual-secondary ground via extends the existing same-net AO1 outline, avoiding invalid intersecting same-priority zones.')];cut=inflation(ext,.25)
for z in list(b.Zones()):
 if z.GetIsRuleArea()or z.GetLayer()!=pcbnew.In1_Cu or z.GetNetname()!='/LOGIC_GND':continue
 overlap=duplicate(z.Outline());overlap.BooleanIntersection(cut)
 if overlap.Area()<1e6:continue
 uid=z.m_Uuid.AsString();first_area=z.Outline().Area()/1e12;remaining=duplicate(z.Outline());remaining.BooleanSubtract(cut);sections=sorted(split_polygons(remaining),key=lambda v:v.Area(),reverse=True)
 if not sections:raise ValueError('Local extension would remove an entire existing logic zone')
 z.Outline().RemoveAllContours();z.Outline().Append(sections[0]);extra=[]
 for section in sections[1:]:
  frag=z.Duplicate();frag.Outline().RemoveAllContours();frag.Outline().Append(section);b.Add(frag);extra.append(frag.m_Uuid.AsString());addedzones.append(frag.m_Uuid.AsString())
 changed.append(dict(uuid=uid,before_area_mm2=first_area,after_combined_area_mm2=sum(v.Area()for v in sections)/1e12,extra_fragment_UUIDs=extra))
t=pcbnew.PCB_TRACK(b);t.SetNet(p.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetStart(p.GetPosition());t.SetEnd(xy(q));t.SetWidth(pcbnew.FromMM(.2));b.Add(t)
p4=next(p for p in fp.Pads()if p.GetNumber()=='4');t4=pcbnew.PCB_TRACK(b);t4.SetNet(p.GetNet());t4.SetLayer(pcbnew.F_Cu);t4.SetStart(p4.GetPosition());t4.SetEnd(xy(q));t4.SetWidth(pcbnew.FromMM(.2));b.Add(t4)
v=pcbnew.PCB_VIA(b);v.SetNet(p.GetNet());v.SetPosition(xy(q));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new=[t.m_Uuid.AsString(),v.m_Uuid.AsString(),t4.m_Uuid.AsString()]
dest=out/'motherboard-AO1-DAC-return-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(actual_source_reference='U14626',actual_ground_pin='5',actual_LDAC_low_default_pin='4',primary_datasheet='https://www.analog.com/media/en/technical-documentation/data-sheets/ad5683r_5682r_5681r_5683.pdf',primary_revision='D Figure10/Table9 page10 SDO-option MSOP',pin4_is_LDAC_not_a_second_ground_pin=True,source_pad_uuid=source_uid,actual_source_position_mm=list(s),new_via_position_mm=list(q),length_mm=math.dist(s,q),new_copper_UUIDs=new,new_zone_UUIDs=addedzones,reviewed_existing_zone_outline_changes=changed,extension_bounds_mm=[393.7,249.35,394.5,250.15],input_sha256=frozen))
print('Native refill / full unsuppressed DRC',flush=True);native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()};now={u:identity(t)for u,t in actual.items()}
if set(now)!=set(oldcu)|set(new)or any(now[u]!=x for u,x in oldcu.items()):raise ValueError('Original actual56 physical copper changed')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}:raise ValueError('Original source pads/poses changed')
defs=definitions(dest);changeduids={r['uuid']for r in changed}
if set(defs)!=set(oldzones)|set(addedzones)or any(defs[u]!=d for u,d in oldzones.items()if u not in changeduids):raise ValueError('Unreviewed zone definition changed')
after=native_pad_clusters(b,nets);survived=clusters_survive(before,after);write(out/'all-native-source-cluster-proof.json',dict(before=before,after=after,passed=survived))
if not survived:raise ValueError('An original source cluster split')
v=actual[new[1]];peers={p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(v)};fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu])[net,pcbnew.In1_Cu]
if source_uid not in peers or p4.m_Uuid.AsString()not in peers or not physical_reference_contact(v,pcbnew.In1_Cu,b.GetConnectivity())or not covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),fill):raise ValueError('Actual DAC GND5 / flashed connected In1 annulus not proven')
if any(r['severity']=='error'for r in native['violations'])or native['ignored_checks']:raise ValueError('Native errors or ignored checks remain')
reviews=[dict(uuid=u,before_definition_sha256=sha_text(oldzones[u]),after_definition_sha256=sha_text(defs[u]),electrical_outline_correction_reason='The real AD5683R-3 GND5 and LDAC4 LOW tie needs a compact conventional plated return stitch. This exact local LOGIC In1 outline subtraction preserves clearance to a same-side AO1 DAC In1 collar; no foreign source metal, source-pad cluster, power plane or package barrier is borrowed.')for u in changeduids]
# Native refill may change derived old-via zone_layer_connections metadata.
# Inventory the exact lexical delta separately; physical identities above
# prove that no old conductor or annulus geometry was moved or replaced.
trees=[parse(without_generated_fills(v.read_text()))for v in(base,dest)];rawdelta=[]
for kind in('segment','via','arc'):
 a,c=[objects(tree,kind)for tree in trees]
 rawdelta.extend(u for u in set(a)|set(c)if u not in a or u not in c or dump(a[u])!=dump(c[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Actual U14626 GND5 and LOW-default LDAC4 are physically joined by two short F branches, conventional retained-annulus via and tightly bounded own In1 reference extension. Exact generated LOGIC In1 outline holes retain all prior source-pad clusters; source/pad/pose/all physical old Cu remain exact. This is low-current reference closure, not global current capacity or completed analog routing.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(rawdelta),reviewed_added_zone_UUIDs=addedzones,reviewed_existing_zone_outline_deltas=reviews))
for p,h in frozen.items():
 if sha(Path(p))!=h:raise ValueError('Frozen input changed')
print('Full actual native resource review',flush=True);full=validate(b,mapping);full['board_sha256']=sha(dest);full['source_map_sha256']=sha(mp);write(out/'full-native-resource-review.json',full)
selected=[r for r in full['filled_components']if r['net']==net]
if not selected or any(not r['passed']for r in selected):raise ValueError('An actual AO1 resource remains unanchored')
r=dict(board_sha256=sha(dest),before_board_sha256=sha(base),source_map_sha256=sha(mp),native_errors=0,native_DRC_types=dict(collections.Counter(x['type']for x in native['violations'])),ignored_checks=native['ignored_checks'],actual_DAC_GND5_and_LDAC4_connected=True,actual_In4_annulus_qualification_claim=False,quiet_precision_or_global_current_capacity_qualification_claim=False,actual_In1_annulus_flashed_and_native_connected=True,actual_full_own_In1_annulus_coverage=True,all_old_Cu_source_pads_poses_and_clusters_preserved=True,actual_ground_branch_length_mm=math.dist(s,q),new_copper_UUIDs=new,new_zone_UUIDs=addedzones,existing_zone_outline_reviews=reviews,ground_pin_function='GND5',pin4_function='LDAC tiedLOW' ,scope_sha256=sha(out/'bounded-scope.json'),AO1_actual_source_anchored_resources=selected,AO1_reference_resources_passed=True,global_reference_passed=full['passed'],manufacturing_ready=False)
write(out/'receipt.json',r);print(json.dumps({k:v for k,v in r.items()if k!='AO1_actual_source_anchored_resources'},indent=2))


