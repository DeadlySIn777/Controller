"""Physically anchor the literal OUT9 FieldB In4 piece by a real Ground contact."""
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
from hardware_route_selected_additive import corridor_polygon

base=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
mp=Path('reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json')
proposal=Path('reports/motherboard-return-zoning-20261001/source26-r74-OUT9-external-ground-transfer-proposal-r01.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-r74-OUT9-external-ground-transfer-r01')
if out.exists():raise ValueError('Fresh immutable output required')
out.mkdir();(out/'inputs').mkdir()
frozen={str(p):sha(p)for p in(base,mp,proposal,Path(__file__))}
for p in(base,mp,proposal,Path(__file__)):shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();mapping=json.loads(mp.read_text())
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base)
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
row=json.loads(proposal.read_text())['proposal'][0];net='/motherboard_do/FIELD_B_0V';g=Geometry(b);q=row['new_ground_transfer_via_mm'];new=[]
paths=[(pcbnew.In4_Cu,row['literal_In4_piece_contact_path_mm']),(pcbnew.In3_Cu,row['source_backed_In3_ground_power_path_mm'])]
if not g.via(q,net)or any(not g.clear(p,net,l,.2)for l,p in paths):raise ValueError('Actual bounded Ground paths no longer fit')
crossings=[]
for layer,path in paths:
    for a,c in zip(path,path[1:]):
        shape=corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(.1))
        for old in b.GetTracks():
            if old.Type()!=pcbnew.PCB_TRACE_T or old.GetLayer()not in(pcbnew.F_Cu,pcbnew.B_Cu)or old.GetNetname()==net:continue
            other=corridor_polygon(tuple(old.GetStart()),tuple(old.GetEnd()),old.GetWidth()/2)
            if shape.Collide(other):crossings.append(dict(ground_layer=b.GetLayerName(layer),opposite_native_trace_UUID=old.m_Uuid.AsString(),opposite_trace_layer=old.GetLayerName(),opposite_trace_net=old.GetNetname(),bounded_SELV_ground_power_only=True,no_signal_reference_exception=True))
        t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(xy(a));t.SetEnd(xy(c));b.Add(t);new.append(t.m_Uuid.AsString())
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(q));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);new.append(v.m_Uuid.AsString());vid=v.m_Uuid.AsString()
dest=out/'motherboard-OUT9-external-ground-transfer-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(ext),dest.with_suffix(ext))
for f in base.parent.iterdir():
    if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
    elif f.name=='fp-lib-table':shutil.copy2(f,out/f.name)
write(out/'generation.json',dict(input_sha256=frozen,new_ground_Cu_UUIDs=new,proposal=row,opposite_layer_ground_power_crossings=crossings,no_Source_or_zone_or_old_Cu_changes=True))
print('OUT9 true external Ground contact native refill starts',flush=True)
native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();actual={t.m_Uuid.AsString():t for t in b.GetTracks()}
if set(actual)!=set(oldcu)|set(new)or any(identity(actual[u])!=i for u,i in oldcu.items())or oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or definitions(dest)!=oldzones:raise ValueError('Old SOURCE geometry changed')
after=native_pad_clusters(b,nets);preserved=clusters_survive(oldclusters,after);write(out/'all-native-SOURCE-cluster-proof.json',dict(passed=preserved,before=oldclusters,after=after))
if not preserved:raise ValueError('Actual old SOURCE cluster split')
if any(r['severity']=='error'for r in native['violations'])or native['ignored_checks']:raise ValueError('Actual native errors remain')
Sourceproof=review(b,[dict(net=net,new_copper_UUIDs=new)],mapping['pads']);write(out/'every-new-ground-Cu-SOURCE-witness.json',Sourceproof)
conn=b.GetConnectivity();via=actual[vid]
for layer in(pcbnew.In3_Cu,pcbnew.In4_Cu):
    if not physical_reference_contact(via,layer,conn):raise ValueError('Actual Ground transfer missing flashed connected annulus')
full=validate(b,mapping);full.update(board_sha256=sha(dest),source_map_sha256=sha(mp));write(out/'full-native-resource-review.json',full)
remaining=[r for r in full['unanchored_components']if r['literal_native_positive_metal_provenance']['zone_uuid']=='70779225-3f58-41c9-9ef5-f15169383fc2']
if remaining:raise ValueError('Literal OUT9 SOURCE-bearing piece still unanchored')
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];delta=[]
for kind in('segment','via','arc'):
    old,nw=[objects(t,kind)for t in trees];delta.extend(u for u in set(old)|set(nw)if u not in old or u not in nw or dump(old[u])!=dump(nw[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='One genuine conventional Ground-power In3/In4 transfer just outside the too-narrow OUT9 FIELD_B In4 piece plus actual short In4 contact and own In3 SOURCE connection. Every existing SOURCE pad/Cu/pose/zone remains exact. No signal-transfer or borrowed-reference exception; no current-capacity claim.'))
run=subprocess.run([sys.executable,'tools/motion_card_routing_inventory.py','--board',str(dest),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(out/'independent-connectivity')],capture_output=True,text=True);(out/'independent-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError('Independent SOURCE connectivity failed')
ind=json.loads((out/'independent-connectivity/review.json').read_text())
for path,h in frozen.items():
    if sha(Path(path))!=h:raise ValueError('Frozen input changed')
write(out/'receipt.json',dict(passed=True,before_board_sha256=sha(base),board_sha256=sha(dest),new_ground_Cu=len(new),actual_ground_transfer_flashed_connected_layers=['In3.Cu','In4.Cu'],allnewCu_numbered_SOURCE_anchored=True,alloldSourceclusters_preserved=True,native_errors=0,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),ignored_checks=[],remaining_unanchored_resources=len(full['unanchored_components']),uncapped_native=ind['uncapped_unconnected_ratsnest_edges'],independent_Source_missing=ind['independent_physical_cluster_missing_joins'],orphan_copper=ind['orphan_copper_items'],manufacturing_ready=False))
print('Actual OUT9 Ground transfer candidate native/SOURCE checks passed',flush=True)
