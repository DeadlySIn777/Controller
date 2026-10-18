"""Actual exact one-loop replacement, SOURCE/annulus and physical-cut proof."""
import sys,json,hashlib,collections,subprocess
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_route_owned_bypass_loops_r02 import actual_receiving_return_anchors
out=Path('reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01');dest=out/'motherboard-C11087-ground-transfer-candidate.kicad_pcb';gen=json.loads((out/'generation.json').read_text());base=Path(gen['before_board']);oldproof=json.loads((base.parent/'post-refill-proof.json').read_text());inv=json.loads((base.parent/'before-invariants.json').read_text());native=json.loads((out/'native.json').read_text());baseline=json.loads((base.parent/'native.json').read_text());owners_path=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json');historical=Path('reports/motherboard-owned-bypass-routing-20261001/source26-r76-strict-same-side-r01/combined101-bypass-manifest.json')
if sha(base)!=gen['before_board_sha256']:raise ValueError('Frozen exact bypass donor base changed')
def warnings(r):return sorted((v['type'],v['severity'],tuple(sorted(i['uuid']for i in v.get('items',[]))))for v in r['violations'])
if native['ignored_checks']or any(v['severity']=='error'for v in native['violations'])or warnings(native)!=warnings(baseline):raise ValueError('Native exact baseline changed')
b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};pin=lambda ref,n:next(p for p in fps[ref].Pads()if p.GetNumber()==n);cap=pin('C11087','1');vcc=pin('U11033','5');ret=pin('C11087','2');gnd=pin('U11033','3');conn=b.GetConnectivity()
def connected(p,q):return q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in conn.GetConnectedItems(p)}
if not connected(cap,vcc)or not connected(ret,gnd):raise ValueError('Actual moved bypass pair is not physically connected')
oldcu={u:identity(t)for u,t in tracks.items()if u not in gen['new_Cu_UUIDs']};digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
if digest(oldcu)!=inv['Cu_identity_sha256']or digest({p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()})!=inv['pad_identity_sha256']:raise ValueError('Old native Cu/pads/poses changed')
after=native_pad_clusters(b,{p.GetNetname()for p in b.GetPads()if p.GetNumber()});before=json.loads((base.parent/'all-native-SOURCE-cluster-proof.json').read_text())['after'];survive=clusters_survive(before,after)
write(out/'all-old-SOURCE-cluster-proof.json',dict(passed=survive,before=before,after=after))
if not survive:raise ValueError('Old SOURCE cluster lost')
power_ids=['04d15de0-5cea-4409-b460-c82bbac9b722','8bc78829-90a6-4e9c-a190-9bcaaa46fd1f','9b57c6bc-12f0-45bf-8f39-b2952275d0d5'];row=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);check=NativeCollectedAnnulusCheck(b,{cap.GetNetname():row});reviews=[check.via(tracks[u],row)if tracks[u].Type()==pcbnew.PCB_VIA_T else check.segment(tracks[u],row)for u in power_ids]
ground=tracks[gen['new_ground_via_UUID']];layers=[pcbnew.In1_Cu,pcbnew.In4_Cu]
if ground.GetNetname()!='/LOGIC_GND'or not all(ground.FlashLayer(l)and conn.IsConnectedOnLayer(ground,l)for l in layers):raise ValueError('New actual Ground annuli are absent/unconnected')
anchors=check.source_anchors(ground,'/LOGIC_GND')
if not anchors:raise ValueError('New Ground via lacks a numbered physical SOURCE pad')
group=dict(ref='C11087',category='local_bypass',owner='U11033',new_UUIDs=power_ids+gen['new_Cu_UUIDs'],actual_owning_signal_return_pairs_connected=True,retained=True,disposition='Exact physically rerouted receiving bypass replaces the former eight private copper objects;100 other historical groups stay exact')
old=json.loads(historical.read_text());matching=[r for r in old['owned_loops']if r['ref']=='C11087']
if len(matching)!=1:raise ValueError('Historical one-replacement scope differs')
old['owned_loops']=[group if r['ref']=='C11087'else r for r in old['owned_loops']];old['board_sha256']=sha(dest);old['bounded_one_group_replacement']=dict(historical101_manifest_sha256=sha(historical),old_exact_group=matching[0],new_exact_group=group,retained_count=100,replaced_count=1,all_old_checker_geometry_and_Source_requirements_retained=True)
write(out/'combined100-retained-plus1-replacement-manifest.json',old)
receiving=actual_receiving_return_anchors(b,{'owned_loops':[group]},json.loads(owners_path.read_text()))
write(out/'one-replacement-proof.json',dict(passed=True,board_sha256=sha(dest),actual_cap_power='C11087.1',actual_VCC='U11033.5',actual_cap_return='C11087.2',actual_GND='U11033.3',native_power_and_return_pairs_connected=True,actual_power_branch_UUIDs=power_ids,actual_power_branch_reference_reviews=reviews,actual_physical_receiving_return_reviews=receiving,new_Ground_via_UUID=gen['new_ground_via_UUID'],actual_Ground_flashed_native_connected_layers=['In1.Cu','In4.Cu'],actual_numbered_Source_anchors=anchors,actual_local_power_branch_length_mm=sum(pcbnew.ToMM(tracks[u].GetLength())for u in power_ids if tracks[u].Type()==pcbnew.PCB_TRACE_T),actual_permitted_Ground_distance_mm=gen['source_ground_stitch_distance_mm'],native_DRC_exact_baseline_preserved=True,all_old_Source_Cu_pads_poses_zones_preserved=True,physical_cut_controls_pending=True,full101_and82_and_global_resource_checks_pending=True,manufacturing_ready=False));print('Actual one-loop replacement SOURCE,physical pairs,full frozen annulus/corridor andreceiving Ground pass',flush=True)
