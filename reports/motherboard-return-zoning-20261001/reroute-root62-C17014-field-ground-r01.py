import sys,json,shutil,collections,subprocess,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_validate_return_bridge_sources import review
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact,validate
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import rectangle,return_net
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects
base=Path('reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/motherboard-source26-orphan-free-candidate.kicad_pcb');mp=Path('reports/motherboard-domains-20261001/source26-r61-orphan-free-r01/domain-map.json');out=Path('reports/motherboard-return-zoning-20261001/source26-r62-C17014-field-return-reroute-r01');uid='ae0081c1-906b-4100-9f7b-a6c130bc13f2';net='/motherboard_motors/FIELD_GND'
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();(out/'inputs').mkdir();inputs=[base,mp,Path(__file__)];frozen={str(p.resolve()):sha(p)for p in inputs}
for p in inputs:shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();mapping=json.load(open(mp));oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets);t=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==uid)
s=mm(t.GetStart());e=mm(t.GetEnd());q=(373.264622,144.667798)
if t.GetNetname()!=net or t.GetLayer()!=pcbnew.In1_Cu or s!=(373.264622,155.19526)or e!=(373.264622,143.967798)or t.GetWidth()!=pcbnew.FromMM(.5):raise ValueError('Exact reviewed obstructive ground-power conductor differs')
g=Geometry(b)
if not g.via(s,net)or not g.via(q,net)or not g.clear([s,q],net,pcbnew.In3_Cu,.5)or not g.clear([e,q],net,pcbnew.In1_Cu,.5):raise ValueError('Real same-width power-return transfer geometry obstructed')
shape=corridor_polygon(tuple(xy(s)),tuple(xy(q)),pcbnew.FromMM(.25));crossings=[]
for row in mapping['pads']:
 if row['domain'].startswith(('SUB:','CONTACT:'))or row['domain']=='CHASSIS':
  if shape.Collide(rectangle(row['copper_aabb_mm'],.3)):raise ValueError('Power return crosses prohibited all-layer floating/contact/chassis metal')
 surface=[l for l in row['copper_layers']if l in('F.Cu','B.Cu')]
 if surface and return_net(row)!=net and shape.Collide(rectangle(row['copper_aabb_mm'])):crossings.append(dict(reference=row['reference'],pin=row['pin'],native_net=row['net'],actual_opposite_copper_layers=surface,domain=row['domain'],power_return_layer='In3.Cu',power_return_net=net,signal_reference_credit=False))
# Original UUID is preserved in a literal two-key physical revision: layer and
# northern endpoint. An In1 tail keeps the exact original source-bearing end.
t.SetLayer(pcbnew.In3_Cu);t.SetEnd(xy(q));tail=pcbnew.PCB_TRACK(b);tail.SetNet(t.GetNet());tail.SetLayer(pcbnew.In1_Cu);tail.SetStart(xy(e));tail.SetEnd(xy(q));tail.SetWidth(pcbnew.FromMM(.5));b.Add(tail);new=[tail.m_Uuid.AsString()];viaids=[]
for p in(s,q):
 v=pcbnew.PCB_VIA(b);v.SetNet(t.GetNet());v.SetPosition(xy(p));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new.append(v.m_Uuid.AsString());viaids.append(v.m_Uuid.AsString())
dest=out/'motherboard-C17014-field-ground-rerouted-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(changed_exact_ground_UUID=uid,before_physical_identity=oldcu[uid],after_physical_identity=identity(t),width_preserved_mm=.5,real_ground_via_positions_mm=[list(s),list(q)],In1_northern_tail_mm=[list(e),list(q)],new_copper_UUIDs=new,prohibited_sub_contact_chassis_package_RAW_barriers_preserved=True,recorded_power_only_SELV_dielectric_crossings=crossings,no_signal_reference_rule_relaxation=True,no_global_current_thermal_capacity_claim=True,input_sha256=frozen))
print('Native exact C17014 ground-power reroute DRC/refill starts',flush=True);native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()};now={u:identity(t)for u,t in actual.items()}
if set(now)!=set(oldcu)|set(new)or any(now[u]!=v for u,v in oldcu.items()if u!=uid):raise ValueError('Unscoped old physical copper changed')
expected=(uid,net,tuple(xy(s)),tuple(xy(q)),pcbnew.In3_Cu,pcbnew.FromMM(.5),None)
if now[uid]!=expected:raise ValueError('Bounded two-key ground-track correction differs')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or oldzones!=definitions(dest):raise ValueError('Existing source pads/poses/zone outlines changed')
after=native_pad_clusters(b,nets);preserved=clusters_survive(before,after);write(out/'all-native-SOURCE-cluster-proof.json',dict(before=before,after=after,passed=preserved))
if not preserved:raise ValueError('Ground reroute split an original SOURCE cluster')
proof=review(b,[dict(net=net,new_copper_UUIDs=new+[uid])],mapping['pads']);write(out/'all-rerouted-new-ground-conductor-SOURCE-witnesses.json',proof)
conn=b.GetConnectivity();annuli=[]
for vid in viaids:
 v=actual[vid];row=dict(via_uuid=vid,position_mm=list(mm(v.GetPosition())),actual_Source_witness=True,actual_flashed_native_connected_layers=[])
 for layer in(pcbnew.In1_Cu,pcbnew.In3_Cu):
  if not physical_reference_contact(v,layer,conn):raise ValueError('Actual ground transfer annulus missing on literal layer')
  row['actual_flashed_native_connected_layers'].append(b.GetLayerName(layer))
 annuli.append(row)
write(out/'actual-ground-power-transfer-annuli.json',dict(passed=True,rows=annuli,filled_signal_reference_qualification_claim=False,current_thermal_prototype_qualification=False))
if any(r['severity']=='error'for r in native['violations'])or native['ignored_checks']:raise ValueError('Native regular errors/ignored checks remain')
full=validate(b,mapping);full['board_sha256']=sha(dest);full['source_map_sha256']=sha(mp);write(out/'full-native-resource-review.json',full)
oldreport=json.load(open('reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/full-native-resource-review.json'))
oldfield=[r for r in oldreport['filled_components']if r['net']==net];newfield=[r for r in full['filled_components']if r['net']==net]
if not oldfield or any(not r['passed']for r in newfield):raise ValueError('A FIELD_GND reference resource lost real Source anchoring')
# The exact blocked C17014 power loop is checked at the unchanged strict .40
# margin after physical reroute, without adding signal Cu or using another net.
pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()};cap=pads['C17014','1'];owner=pads['U17014','14'];power=cap.GetNetname();ret='/LOGIC_GND'
if power!=owner.GetNetname():raise ValueError('Exact C17014 owning VCC differs')
fill=collect_native_reference_fills(b,{ret},[pcbnew.In1_Cu])[ret,pcbnew.In1_Cu];corr=corridor_polygon(tuple(cap.GetPosition()),tuple(owner.GetPosition()),pcbnew.FromMM(.1+.4));covered_now=covered(corr,fill)
write(out/'actual-C17014-strict-reference-corridor.json',dict(board_sha256=sha(dest),C17014_power_pin='1',actual_receiver='U17014.14',signal_or_power_net=power,return_net=ret,own_reference_layer='In1.Cu',points_mm=[list(mm(cap.GetPosition())),list(mm(owner.GetPosition()))],width_mm=.2,reference_margin_mm=.4,actual_continuous_own_reference_after_ground_power_reroute=covered_now,no_HF_objects_added=True,no_relaxed_guard=True))
if not covered_now:raise ValueError('Exact strict C17014 corridor is still blocked')
# Each retained reference bridge remains attached to real SOURCE pads.
groups=[]
for r in json.load(open('reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/generation.json'))['accepted']:
 kept=[u for u in r['new_copper_UUIDs']if u in actual]
 if kept:groups.append(dict(net=r['net'],new_copper_UUIDs=kept))
write(out/'all-43-retained-bridge-source-witnesses.json',review(b,groups,mapping['pads']))
trees=[parse(without_generated_fills(f.read_text()))for f in(base,dest)];delta=[]
for kind in('segment','via','arc'):
 old,newraw=[objects(tree,kind)for tree in trees];delta.extend(u for u in set(old)|set(newraw)if u not in old or u not in newraw or dump(old[u])!=dump(newraw[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Electrically required exact .50mm FIELD_GND power-return track moves from In1 to In3 so it stops cutting the real LOGIC C17014-to-U17014VCC14 reference corridor. Same net/width/original UUID and southern endpoint preserved; northern endpoint gets an exact .70mm same-width In1 tail and two real conventional flashed/native-connected through transfers. All actual SOURCE clusters and 43 retained bridges remain; every new or changed ground conductor has numbered Source witnesses. No signal borrows foreign reference, all-layer package/raw/substrate/contact barrier changes, or power-current/fabrication qualification claims.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[]))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True);(out/'independent-connectivity-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent full Source inventory failed')
for f,h in frozen.items():
 if sha(Path(f))!=h:raise ValueError('Frozen input changed')
ind=json.load(open(out/'independent-connectivity/review.json'));r=dict(passed=True,before_board_sha256=sha(base),board_sha256=sha(dest),changed_exact_ground_UUID=uid,new_copper_UUIDs=new,native_errors=0,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),ignored_checks=native['ignored_checks'],actual_own_LOGIC_C17014_corridor_passed_unmodified_point40_margin=True,all_old_SOURCE_pad_clusters_pads_poses_other_Cu_zone_definitions_preserved=True,all43_retained_bridges_SOURCE_anchored=True,every_new_changed_ground_Cu_SOURCE_anchored=True,all_FIELD_GND_filled_resources_SOURCE_anchored=True,actual_ground_transfer_annuli=annuli,uncapped_unconnected=ind['uncapped_unconnected_ratsnest_edges'],independent_SOURCE_missing_joins=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],scope_sha256=sha(out/'bounded-scope.json'),manufacturing_ready=False,current_thermal_or_global_ground_capacity_qualified=False);write(out/'receipt.json',r);print(json.dumps(r,indent=2))
