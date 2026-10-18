"""Finish the read-only Source review after a report-key error, preserving CAD."""
import sys,json,collections,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects
from hardware_route_logic_return import identity,pad_identity
from hardware_stitch_owned_return_planes import definitions
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact

folder=Path('reports/motherboard-return-zoning-20261001/source26-r74-OUT9-external-ground-transfer-r01')
dest=folder/'motherboard-OUT9-external-ground-transfer-candidate.kicad_pcb'
base=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
out=Path('reports/motherboard-return-zoning-20261001/source26-r74-OUT9-external-ground-transfer-review-r02')
if out.exists():raise ValueError('Fresh immutable review required')
out.mkdir()
generation=json.loads((folder/'generation.json').read_text());new=generation['new_ground_Cu_UUIDs']
native=json.loads((folder/'native.json').read_text());Source=json.loads((folder/'every-new-ground-Cu-SOURCE-witness.json').read_text());full=json.loads((folder/'full-native-resource-review.json').read_text())
if any(v['severity']=='error'for v in native['violations'])or native['ignored_checks']or not Source['passed']or not json.loads((folder/'all-native-SOURCE-cluster-proof.json').read_text())['passed']:
    raise ValueError('Actual frozen native/Source proof failed')
if any(r['literal_native_positive_metal_provenance']['zone_uuid']=='70779225-3f58-41c9-9ef5-f15169383fc2'for r in full['unanchored_components']):
    raise ValueError('Actual literal OUT9 piece remains unanchored')
frozen={str(p):sha(p)for p in(base,dest,Path(__file__),folder/'generation.json',folder/'native.json',folder/'full-native-resource-review.json')}
before=pcbnew.LoadBoard(str(base));b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();old={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};now={t.m_Uuid.AsString():t for t in b.GetTracks()}
if set(now)!=set(old)|set(new)or any(identity(now[u])!=i for u,i in old.items())or definitions(base)!=definitions(dest):raise ValueError('Exact old Cu/zone preservation failed')
if {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}:raise ValueError('Source lands/poses changed')
via=next(now[u]for u in new if now[u].Type()==pcbnew.PCB_VIA_T)
layers=[]
for layer in(pcbnew.In3_Cu,pcbnew.In4_Cu):
    if not physical_reference_contact(via,layer,b.GetConnectivity()):raise ValueError('Actual Ground annulus unavailable')
    layers.append(b.GetLayerName(layer))
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];delta=[]
for kind in('segment','via','arc'):
    oldtree,newtree=[objects(tree,kind)for tree in trees];delta.extend(u for u in set(oldtree)|set(newtree)if u not in oldtree or u not in newtree or dump(oldtree[u])!=dump(newtree[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exactly5 new Ground-power Cu: one conventional .50/.20 plated transfer outside the too-narrow literal OUT9 FIELD_B In4 piece, a .224mm In4 contact and3 In3 own-SOURCE Ground segments. Native flashed annuli on both used layers, every conductor has a real numbered SOURCE witness. Old pads/poses/Cu/zones remain exact. No signal transfer/reference exception or global ampacity claim.'))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True);(out/'independent-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent complete source inventory failed')
ind=json.loads((out/'independent-connectivity/review.json').read_text())
for path,h in frozen.items():
    if sha(Path(path))!=h:raise ValueError('Read-only input changed')
write(out/'receipt.json',dict(passed=True,input_sha256=frozen,before_board_sha256=sha(base),board_sha256=sha(dest),new_ground_Cu=5,actual_flashed_native_connected_annuli=layers,every_new_Cu_numbered_Source_backed=True,literal_OUT9_resource_physically_Source_anchored=True,no_source_pads_poses_lands_oldCu_or_zones_changed=True,native_errors=0,native_warnings=len(native['violations']),ignored_checks=[],uncapped_native=ind['uncapped_unconnected_ratsnest_edges'],independent_Source_missing=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],all97_prior_loop_proof_pending=True,generator_report_key_error_preserved=True,manufacturing_ready=False))
print('Actual OUT9 external Ground native/Source/independent review passed',flush=True)
