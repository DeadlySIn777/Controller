import sys,json,shutil,collections,math,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact,validate
from hardware_validate_return_bridge_sources import review
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_zone_motherboard_returns import rectangle,duplicate,inflation,split_polygons,return_net
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition,sha_text
base=Path('reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/motherboard-source26-orphan-free-candidate.kicad_pcb');mp=Path('reports/motherboard-domains-20261001/source26-r61-orphan-free-r01/domain-map.json');oldbridge=Path('reports/motherboard-pcb-integration-20261001/source26-rejected-HF-r61/motherboard-bounded-merged-candidate.kicad_pcb');retirement=Path('reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/retirement-ledger.json');out=Path('reports/motherboard-return-zoning-20261001/source26-r62-field-status-ground-delivery-r01')
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();(out/'inputs').mkdir();inputs=[base,mp,oldbridge,retirement,Path(__file__)];frozen={str(p.resolve()):sha(p)for p in inputs}
for i,p in enumerate(inputs):shutil.copy2(p,out/'inputs'/f'{i:02}-{p.name}')
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();mapping=json.load(open(mp));fp=next(f for f in b.GetFootprints()if f.GetReference()=='D17067');p=next(p for p in fp.Pads()if p.GetNumber()=='1');net='/motherboard_do/FIELD_B_0V'
if p.GetNetname()!=net or mm(p.GetPosition())!=(301.175,143)or fp.GetLayer()!=pcbnew.F_Cu:raise ValueError('Exact genuine status ground SOURCE differs')
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets)
start=(302.025,143);end=(303.5,169);route=[start,(299.025,143),(299.025,169),end];ext=rectangle([301.675,142.65,302.375,143.35]);g=Geometry(b);guard=ReferenceGuard(b,mapping)
if not g.via(start,net)or not g.via(end,net)or not g.clear([mm(p.GetPosition()),start],net,pcbnew.F_Cu,.2)or not g.clear(route,net,pcbnew.In3_Cu,.2):raise ValueError('Literal real ground-delivery geometry obstructed')
for other,shape in guard.indices[pcbnew.In1_Cu].candidates((301.675,142.65),(302.375,143.35),.3):
 if other!=net and ext.Collide(shape):raise ValueError('Status SOURCE-ground collar overlaps a real foreign projection')
fills=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu]);
if not covered(circle(xy(end),pcbnew.FromMM(.26)),fills[net,pcbnew.In1_Cu]):raise ValueError('Receiving ground transfer lacks literal complete own In1 fill')
ao=next(z for z in b.Zones()if z.m_Uuid.AsString()=='7f148859-5241-41ab-8451-53a391f60591')
if ao.GetNetname()!=net or ao.GetLayer()!=pcbnew.In1_Cu:raise ValueError('Exact SOURCE-own zone differs')
combined=duplicate(ao.Outline());combined.BooleanAdd(ext)
if combined.OutlineCount()!=1:raise ValueError('SOURCE collar loses outline continuity')
ao.Outline().RemoveAllContours();ao.Outline().Append(combined);changed=[ao.m_Uuid.AsString()];new=[]
def track(a,c,layer,uid=None):
 t=pcbnew.PCB_TRACK(b);t.SetNet(p.GetNet());t.SetLayer(layer);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);new.append(t.m_Uuid.AsString());return t
track(mm(p.GetPosition()),start,pcbnew.F_Cu)
for a,c in zip(route,route[1:]):track(a,c,pcbnew.In3_Cu)
viaids=[]
for q in(start,end):
 v=pcbnew.PCB_VIA(b);v.SetNet(p.GetNet());v.SetPosition(xy(q));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new.append(v.m_Uuid.AsString());viaids.append(v.m_Uuid.AsString())
# Restore the exact prior eleven-track bridge only with the omitted predecessor
# replaced by this real source-backed power-return path. Its previous orphan
# rejection remains immutable. Every restored conductor must now reach D17067.1.
restored=json.loads(retirement.read_text())['retired_exact_new_bridge_UUIDs'];oldtree=parse(without_generated_fills(oldbridge.read_text()));oldsegments=objects(oldtree,'segment');oldnative=pcbnew.LoadBoard(str(oldbridge));olditems={t.m_Uuid.AsString():t for t in oldnative.GetTracks()}
for uid in restored:
 t=olditems[uid]
 if not guard.clear([mm(t.GetStart()),mm(t.GetEnd())],net,t.GetLayer(),.2):raise ValueError('Restored bounded inner-ground path obstructed')
 native=pcbnew.Cast_to_PCB_TRACK(t.Duplicate());native.m_Uuid=pcbnew.KIID(uid);native.SetNet(p.GetNet());b.Add(native);new.append(uid)
# Power-return-only insulated crossings are recorded; these footprints do not
# become references for any signal. Actual all-layer native barriers remain.
crossings=[]
for a,c in zip(route,route[1:]):
 from hardware_route_selected_additive import corridor_polygon
 shape=corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(.1))
 for row in mapping['pads']:
  if row['side'] not in('F.Cu','B.Cu')or return_net(row)==net:continue
  if shape.Collide(rectangle(row['copper_aabb_mm'])):crossings.append(dict(reference=row['reference'],pin=row['pin'],net=row['net'],domain=row['domain'],actual_opposite_layer=row['side'],power_return_layer='In3.Cu',power_return_net=net,trace_start_mm=list(a),trace_end_mm=list(c),no_signal_reference_credit=True))
dest=out/'motherboard-field-status-source-return-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(actual_ground_source='D17067.1',actual_source_position_mm=list(mm(p.GetPosition())),source_ground_via_mm=list(start),receiving_ground_via_mm=list(end),power_return_route_mm=route,width_mm=.2,restored_exact_source_guarded_bridge_UUIDs=restored,new_copper_UUIDs=new,own_SOURCE_collar_bounds_mm=[301.675,142.65,302.375,143.35],recorded_power_only_dielectric_crossings=crossings,no_signal_reference_borrowing=True,no_high_current_return_qualification=True,all_layer_package_RAW_SUB_barriers_retained=True,input_sha256=frozen))
print('Native FIELD_B SOURCE-return refill/DRC starts',flush=True);native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()};now={u:identity(t)for u,t in actual.items()}
if set(now)!=set(oldcu)|set(new)or any(now[u]!=v for u,v in oldcu.items()):raise ValueError('Existing physical Cu changed')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}:raise ValueError('Existing exact SOURCE pads/poses changed')
defs=definitions(dest)
if set(defs)!=set(oldzones)or any(defs[u]!=d for u,d in oldzones.items()if u not in changed):raise ValueError('Unscoped zone definition changed')
after=native_pad_clusters(b,nets);preserved=clusters_survive(before,after);write(out/'all-native-SOURCE-cluster-proof.json',dict(before=before,after=after,passed=preserved))
if not preserved:raise ValueError('Old actual SOURCE pad cluster split')
sourceproof=review(b,[dict(net=net,new_copper_UUIDs=new)],mapping['pads']);write(out/'every-new-ground-conductor-SOURCE-witness.json',sourceproof)
conn=b.GetConnectivity();source=p.m_Uuid.AsString();fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu])[net,pcbnew.In1_Cu];annuli=[]
for uid,q in zip(viaids,(start,end)):
 v=actual[uid];peers={q.m_Uuid.AsString()for q in conn.GetConnectedItems(v)};passed=source in peers and physical_reference_contact(v,pcbnew.In1_Cu,conn)and covered(circle(xy(q),pcbnew.FromMM(.26)),fill);annuli.append(dict(via_uuid=uid,position_mm=list(q),actual_numbered_SOURCE_pad='D17067.1',SOURCE_physically_connected=source in peers,actual_flashed_and_native_connected_In1_annulus=physical_reference_contact(v,pcbnew.In1_Cu,conn),full_own_In1_annulus=covered(circle(xy(q),pcbnew.FromMM(.26)),fill),passed=passed))
 if not passed:raise ValueError('Physical real SOURCE/receiving In1 anchor failed')
write(out/'actual-source-receiving-ground-annuli.json',dict(passed=True,annuli=annuli,no_In4_or_global_current_capacity_claim=True))
if any(q['severity']=='error'for q in native['violations'])or native['ignored_checks']:raise ValueError('Actual native errors/ignored checks remain')
reviews=[dict(uuid=u,before_definition_sha256=sha_text(oldzones[u]),after_definition_sha256=sha_text(defs[u]),electrical_outline_correction_reason='Actual field status LED Ground requires a conventional source-backed return stitch. This bounded own In1 collar adds only the needed complete annulus outside the previously too-thin generated strip; actual SOURCE metal/isolators/thermal islands and all old SOURCE clusters remain.')for u in changed]
trees=[parse(without_generated_fills(f.read_text()))for f in(base,dest)];delta=[]
for kind in('segment','via','arc'):
 old,newraw=[objects(tree,kind)for tree in trees];delta.extend(u for u in set(old)|set(newraw)if u not in old or u not in newraw or dump(old[u])!=dump(newraw[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Genuine D17067 Ground1 source-backed low-current FIELD_B return delivery on In3 through the SELV stackup dielectric, two real conventional flashed In1 transfers, and restored exact eleven ground bridge conductors only after each now has a real numbered SOURCE witness. No signal borrows a foreign reference, source pad is NCed, isolation/package/raw/SUB barrier is removed, or high-current/thermal/fabrication rating is claimed. Exact prior SOURCE pad clusters/pads/poses/all other Cu remain.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[],reviewed_existing_zone_outline_deltas=reviews))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True);(out/'independent-connectivity-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent full SOURCE inventory failed')
full=validate(b,mapping);full['board_sha256']=sha(dest);full['source_map_sha256']=sha(mp);write(out/'full-native-resource-review.json',full)
for f,h in frozen.items():
 if sha(Path(f))!=h:raise ValueError('Frozen input changed')
ind=json.load(open(out/'independent-connectivity/review.json'));r=dict(passed=True,board_sha256=sha(dest),before_board_sha256=sha(base),every_new_conductor_physically_SOURCE_anchored=True,new_copper_UUIDs=new,restored_ground_bridges=restored,actual_flashed_In1_source_and_receiving_annuli=annuli,all_old_SOURCE_pad_clusters_pads_poses_other_Cu_preserved=True,native_errors=0,native_DRC_types=dict(collections.Counter(q['type']for q in native['violations'])),ignored_checks=native['ignored_checks'],uncapped_unconnected=ind['uncapped_unconnected_ratsnest_edges'],independent_SOURCE_missing_joins=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],remaining_unanchored_resources=len(full['unanchored_components']),power_return_length_mm=sum(math.dist(a,c)for a,c in zip(route,route[1:])),dielectric_crossings_recorded=len(crossings),scope_sha256=sha(out/'bounded-scope.json'),global_reference_qualified=False,physical_current_thermal_measured=False,manufacturing_ready=False);write(out/'receipt.json',r);print(json.dumps(r,indent=2))
