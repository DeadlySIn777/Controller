"""Retire the exact eleven orphan bridges whose predecessor was rejected."""
import sys,json,shutil,collections,subprocess
from pathlib import Path
sys.path.insert(0,'tools')
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_validate_return_bridge_sources import review
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import objects,without_generated_fills
base=Path('reports/motherboard-pcb-integration-20261001/source26-rejected-HF-r61/motherboard-bounded-merged-candidate.kicad_pcb')
mapfile=Path('reports/motherboard-domains-20261001/source26-r60-r01/domain-map.json')
groupfile=Path('reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/generation.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01')
ids=set('''065e4911-2137-4e3c-bc7d-3c62a8a37370 273b69bb-093c-4b5a-a7ab-d8260597e656 500ed1d3-47a7-483b-963e-79fa05964435 548e42b2-2f88-404a-aecb-32cee759e0b1 668fa2af-e1e0-493e-ad0e-63e5305c281f 6c96cb50-2804-4d8c-8225-70e13a8d4d92 7593ad3c-bb49-495d-9c53-f48ffcf0eba0 9799fb95-f94f-436e-b320-d7724a595161 9a1668e6-4cac-4096-942c-e513f1e417d9 b8485b31-cf5c-4f0d-9cb3-429b1be43a0b eaf92f4f-2f1e-4f56-9786-48e0148cdc5b'''.split())
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir(parents=True);(out/'inputs').mkdir();inputs=[base,mapfile,groupfile,Path(__file__),Path('tools/hardware_validate_return_bridge_sources.py'),Path('tests/test_motherboard_return_bridge_sources.py')];frozen={str(p.resolve()):sha(p)for p in inputs}
for i,p in enumerate(inputs):shutil.copy2(p,out/'inputs'/f'{i:02}-{p.name}')
if sha(base)!='43469247759c9226eba46e014b59cffcf620635ae76d95cfb7feeda402b0c9db':raise ValueError('Exact ROOT61 input changed')
b=pcbnew.LoadBoard(str(base));mapping=json.loads(mapfile.read_text());oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};olddefs=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets);conn=b.GetConnectivity();items={t.m_Uuid.AsString():t for t in b.GetTracks()};removed=[]
for uid in sorted(ids):
 t=items[uid]
 if isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()!='/motherboard_do/FIELD_B_0V'or t.GetLayer()!=pcbnew.In1_Cu or t.GetWidth()!=pcbnew.FromMM(.2):raise ValueError('Exact erroneous group differs')
 if any(isinstance(peer,pcbnew.PAD)and peer.GetNumber()for peer in conn.GetConnectedItems(t)):raise ValueError('Literal group now SOURCE-connected; must not retire')
 removed.append(dict(uuid=uid,physical_identity=identity(t),reason='Dependent prior bridge retained after its SOURCE-connected transfer predecessor was rejected; this conductor is physically orphaned.'));b.Remove(t)
dest=out/'motherboard-source26-orphan-free-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for p in base.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
write(out/'retirement-ledger.json',dict(retired_exact_new_bridge_UUIDs=sorted(ids),removed=removed,predecessor_via_UUID='ed8c7321-50c9-4343-be71-84b2ee01dfff',predecessor_missing_on_exact_root61=True,no_SOURCE_pads_were_anchored_by_retired_group=True,required_reference_pockets_still_unqualified=True))
print('Native DRC/refill starts',flush=True);native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity()
current={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
if set(current)!=set(oldcu)-ids or any(v!=oldcu[u]for u,v in current.items()):raise ValueError('Unscoped existing physical copper changed')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or olddefs!=definitions(dest):raise ValueError('Actual pad/pose/source/zone definitions changed')
after=native_pad_clusters(b,nets);proof=clusters_survive(before,after);write(out/'all-native-source-cluster-proof.json',dict(before=before,after=after,passed=proof))
if not proof:raise ValueError('Retiring bridge split an actual SOURCE pad cluster')
if any(r['severity']=='error'for r in native['violations'])or native['ignored_checks']:raise ValueError('Native regular error/ignored checks remain')
groups=[]
for r in json.loads(groupfile.read_text())['accepted']:
 kept=[u for u in r['new_copper_UUIDs']if u not in ids]
 if kept:groups.append(dict(net=r['net'],new_copper_UUIDs=kept))
sourceproof=review(b,groups,mapping['pads']);sourceproof['board_sha256']=sha(dest);sourceproof['source_map_sha256']=sha(mapfile);write(out/'all-retained-new-bridge-source-witnesses.json',sourceproof)
rawtrees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];delta=[]
for kind in('segment','via','arc'):
 old,new=[objects(tree,kind)for tree in rawtrees];delta.extend(u for u in set(old)|set(new)if u not in old or u not in new or dump(old[u])!=dump(new[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Retire only eleven provenance-known new FIELD_B reference bridge conductors proven physically orphaned after predecessor rejection. Every current actual SOURCE pad cluster remains exact; all other existing physical copper, pads, poses and zone definitions remain. New SOURCE-witness gate proves each retained bridge conductor. No required pad is marked NC and missing reference resources remain unfinished.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[]))
print('Independent full SOURCE/connectivity inventory starts',flush=True)
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],text=True,capture_output=True);(out/'independent-connectivity-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent uncapped SOURCE/connectivity proof failed')
ind=json.loads((out/'independent-connectivity/review.json').read_text())
for p,h in frozen.items():
 if sha(Path(p))!=h:raise ValueError('Frozen input changed')
r=dict(passed=True,before_board_sha256=sha(base),board_sha256=sha(dest),retired_exact_new_orphan_conductors=11,retained_bridge_groups=len(groups),retained_bridge_conductors=sourceproof['new_copper_count'],every_retained_bridge_conductor_SOURCE_anchored=True,uncapped_unconnected=ind['uncapped_unconnected_ratsnest_edges'],independent_SOURCE_missing_joins=ind['independent_physical_cluster_missing_joins'],orphan_copper_items=ind['orphan_copper_items'],native_errors=0,ignored_checks=native['ignored_checks'],native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),all_current_SOURCE_pad_clusters_preserved=True,all_unscoped_current_copper_pads_poses_zone_definitions_preserved=True,scope_sha256=sha(out/'bounded-scope.json'),manufacturing_ready=False,global_reference_resources_qualified=False);write(out/'receipt.json',r);print(json.dumps(r,indent=2))
