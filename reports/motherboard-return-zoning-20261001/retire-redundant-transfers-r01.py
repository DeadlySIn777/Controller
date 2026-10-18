"""Retire four exact newly redundant single-layer reference-transfer drills."""
import collections,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_route_owned_bypass_loops import drc
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_stitch_owned_return_planes import definitions
from hardware_validate_motherboard_return_planes_r02 import validate

base=Path('reports/motherboard-return-zoning-20261001/source25-r46-reference-bridges-r02/motherboard-own-return-bridges-candidate.kicad_pcb')
mapping=Path('reports/motherboard-return-zoning-20261001/source25-r46-isolation-domain-map-r01/domain-map.json')
ledger=Path('reports/motherboard-return-zoning-20261001/source25-r46-reference-transfer-r03/receipt.json')
out=Path('reports/motherboard-return-zoning-20261001/source25-r46-redundant-transfer-retirement-r01')
ids={'22bb7970-7f8a-48b1-a00d-ced6aec2c839','6d6b64a9-595a-4566-a9f8-a9cba473219f','d55efe31-b2c5-4c4e-9a3e-8afa1e4a95f2','e8edfcc1-8545-4351-9ce0-ba50977e6e83'}
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();(out/'inputs').mkdir()
for p in(base,mapping,ledger):shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};zone_defs=definitions(base);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldclusters=native_pad_clusters(b,nets)
oldledger={r['uuid']:r for r in json.loads(ledger.read_text())['new_own_return_transfer_vias']};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};review=[]
for uid in sorted(ids):
 t=cu[uid];r=oldledger[uid]
 if not isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()!=r['net']or [pcbnew.ToMM(v)for v in t.GetPosition()]!=r['position_mm']:raise ValueError('Exact transfer via identity differs')
 contacts={b.GetLayerName(layer):dict(flashes=t.FlashLayer(layer),native_connected=b.GetConnectivity().IsConnectedOnLayer(t,layer))for layer in[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]}
 if sum(v['native_connected']for v in contacts.values())!=1:raise ValueError('Actual multi-layer via cannot be retired as redundant')
 review.append(dict(uuid=uid,net=t.GetNetname(),position_mm=r['position_mm'],actual_all_six_layer_contacts=contacts,reason='Newly added standalone transfer no longer connects two actual copper layers after own-return bridge refill. Removing this one-layer-only drill cannot remove a cross-layer electrical path. All actual SOURCE-pad clusters are independently rechecked.'))
 b.Remove(t)
dest=out/'motherboard-reference-transfers-cleaned-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for p in base.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
native=drc(dest,out,'native');fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
if set(now)!=set(old)-ids or any(now.get(u)!=v for u,v in old.items()if u not in ids):raise ValueError('Copper beyond exact four redundant transfer drills changed')
if pads!={p.m_Uuid.AsString():pad_identity(p)for p in fresh.GetPads()}or definitions(dest)!=zone_defs:raise ValueError('Source pads or zone definitions changed')
clusters=native_pad_clusters(fresh,nets);passed=clusters_survive(oldclusters,clusters);write(out/'all-source-pad-cluster-proof.json',dict(before=oldclusters,after=clusters,passed=passed))
if not passed:raise ValueError('A real SOURCE-pad cluster split')
anchors=validate(fresh,json.loads(mapping.read_text()));anchors['board_sha256']=sha(dest);write(out/'physical-reference-anchors.json',anchors)
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Retire only four own newly added transfer vias proven to connect one native copper layer after later ground-reference bridging; preserve every real SOURCE-pad cluster.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(ids),reviewed_added_zone_UUIDs=[]))
receipt=dict(input_sha256={str(p):sha(p)for p in(base,mapping,ledger)},board_sha256=sha(dest),exact_retired_single_layer_vias=review,all_other_Cu_pads_poses_zones_and_SOURCE_clusters_preserved=True,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),native_errors=sum(r['severity']=='error'for r in native['violations']),ignored_checks=native['ignored_checks'],remaining_unanchored_resources=len(anchors['unanchored_components']),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False);write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in('input_sha256','exact_retired_single_layer_vias')},indent=2))
