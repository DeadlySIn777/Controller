"""Bounded real Source-ground escapes and one native same-domain transfer."""
import sys,json,shutil,collections,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm,identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_validate_return_bridge_sources import review
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_validate_motherboard_return_planes_r06 import validate
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects

base=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
mp=Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-r74-two-actual-ground-contacts-r01')
if out.exists():raise ValueError('Fresh immutable output required')
out.mkdir();(out/'inputs').mkdir()
for p in(base,mp,Path(__file__)):shutil.copy2(p,out/'inputs'/p.name)
frozen={str(p):sha(p)for p in(base,mp,Path(__file__))}
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();mapping=json.load(open(mp));oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base)
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets);new=[];groups=[];rows=[]
pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()}
def line(p,q,layer,net):
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(xy(p));t.SetEnd(xy(q));b.Add(t);new.append(t.m_Uuid.AsString());return t.m_Uuid.AsString()
def via(q,net):
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(q));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new.append(v.m_Uuid.AsString());return v.m_Uuid.AsString()
proposal=json.load(open('reports/motherboard-return-zoning-20261001/source26-r74-three-source-ground-contact-proposals-r01.json'))
for item in proposal['rows']:
 if not item['proposals']:continue
 chosen=item['proposals'][0];net=item['net'];path=chosen['new_own_In4_ground_contact_path_mm'];g=Geometry(b)
 if not g.clear(path,net,pcbnew.In4_Cu,.2):raise ValueError('Actual bounded own inner Ground contact obstructed')
 ids=[line(p,q,pcbnew.In4_Cu,net)for p,q in zip(path,path[1:])];groups.append(dict(net=net,new_copper_UUIDs=ids));rows.append(dict(net=net,path_mm=path,existing_ground_via_UUID=chosen['actual_source_via_uuid'],Source_witness=chosen['Source_witness'],new_copper_UUIDs=ids,no_new_barrel=True,low_current_reference_contact_only=True))
if len(rows)!=2:raise ValueError('Exactly the two frozen Source-return contacts required')
dest=out/'motherboard-two-Source-ground-contacts-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for s in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(s),dest.with_suffix(s))
for f in base.parent.iterdir():
 if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(rows=rows,input_sha256=frozen,new_copper_UUIDs=new,actual_ground_power_only=True,no_source_or_zone_or_pose_changes=True))
print('Actual four Source-ground resource refill/native DRC starts',flush=True)
native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()};now={u:identity(t)for u,t in actual.items()}
if set(now)!=set(oldcu)|set(new)or any(now[u]!=v for u,v in oldcu.items())or oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or oldzones!=definitions(dest):raise ValueError('Old Source lands/Cu/poses/zones changed')
preserved=clusters_survive(oldclusters,native_pad_clusters(b,nets));write(out/'all-native-SOURCE-cluster-proof.json',dict(passed=preserved,before=oldclusters,after=native_pad_clusters(b,nets)))
if not preserved:raise ValueError('Actual preexisting Source cluster lost')
proof=review(b,groups,mapping['pads']);write(out/'every-new-ground-conductor-SOURCE-witness.json',proof)
conn=b.GetConnectivity();contacts=[]
for row in rows:
 v=actual[row['existing_ground_via_UUID']]
 if not physical_reference_contact(v,pcbnew.In4_Cu,conn):raise ValueError('Retained actual Source-connected In4 Ground annulus lost')
 contacts.append(dict(via_uuid=v.m_Uuid.AsString(),actual_flashed_native_connected_layers=['In4.Cu'],actual_Source_witness=True,no_new_via=True))
write(out/'actual-receiving-ground-contacts.json',dict(passed=True,rows=contacts,no_blanket_two_sided_signal_reference_claim=True))
full=validate(b,mapping);full['board_sha256']=sha(dest);full['source_map_sha256']=sha(mp);write(out/'full-native-resource-review.json',full)
if any(r['severity']=='error'for r in native['violations'])or native['ignored_checks']:raise ValueError('Native regular errors or ignored checks remain')
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];delta=[]
for kind in('segment','via','arc'):
 old,after=[objects(tree,kind)for tree in trees];delta.extend(u for u in set(old)|set(after)if u not in old or u not in after or dump(old[u])!=dump(after[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Two actual Source-ground reference resource closures: one 5.218 mm LOGIC In4 contact to a native Source-ground annulus and one .250 mm FIELD_B In4 contact to a real Source-ground annulus. No Source pins/poses/lands/old Cu/zone outlines are changed. Actual Source/native contacts are separately proved; no global current capacity or complete signal corridor claim.'))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True);(out/'independent-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent complete Source inventory fails')
ind=json.load(open(out/'independent-connectivity/review.json'))
for p,h in frozen.items():
 if sha(Path(p))!=h:raise ValueError('Frozen input changed')
r=dict(passed=True,before_board_sha256=sha(base),board_sha256=sha(dest),new_ground_Cu=len(new),native_errors=0,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),ignored_checks=native['ignored_checks'],all_old_Source_clusters_Cu_pads_poses_zones_preserved=True,every_new_Cu_numbered_Source_anchored=True,unanchored_resource_count=len(full['unanchored_components']),uncapped_unconnected=ind['uncapped_unconnected_ratsnest_edges'],independent_Source_missing_joins=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],scope_sha256=sha(out/'bounded-scope.json'),manufacturing_ready=False)
write(out/'receipt.json',r);print(json.dumps(r,indent=2))
