"""Repair exact new reference copper against the real source26 entry geometry."""
import collections,json,math,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write,SEEDS
from hardware_route_logic_return import identity,pad_identity,xy,mm
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_stitch_owned_return_planes import definitions
from hardware_merge_bounded_pcb_delta import objects,parse,without_generated_fills,dump
from hardware_route_local_signals import paths

base=Path('reports/motherboard-pcb-integration-20261001/source26-return-plane-r51/motherboard-bounded-merged-candidate.kicad_pcb')
protected=Path('reports/motherboard-pcb-integration-20261001/source26-ao-display-r50/motherboard-ao-display-reconciled-candidate.kicad_pcb')
source_ledger=Path('reports/motherboard-source-return-anchors-20261001/reviewed-stitches-r05/receipt.json')
transfer_ledger=Path('reports/motherboard-return-zoning-20261001/source25-r46-reference-transfer-r03/receipt.json')
out=Path('reports/motherboard-return-zoning-20261001/source26-root51-reference-conflicts-r02')
retire={'22bb7970-7f8a-48b1-a00d-ced6aec2c839','556fca79-c649-4f73-b8d5-cb47da61a1db','d55efe31-b2c5-4c4e-9a3e-8afa1e4a95f2','6d6b64a9-595a-4566-a9f8-a9cba473219f'}
move={'956e359a-ed6a-4261-b34e-9449202ed37e','c121b849-bbbb-49ec-8623-73c6b091087b','c88fe8b0-f677-41c9-8cba-56038794faa4','d676ca83-09ea-4811-bd56-557376fe2b7d'}
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir();(out/'inputs').mkdir()
inputs=[base,protected,source_ledger,transfer_ledger,Path(__file__)];frozen={str(p.resolve()):sha(p)for p in inputs}
for p in inputs:shutil.copy2(p,out/'inputs'/p.name)
b=pcbnew.LoadBoard(str(base));cu={t.m_Uuid.AsString():t for t in b.GetTracks()};oldcu={u:identity(t)for u,t in cu.items()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones=definitions(base)
before_root=pcbnew.LoadBoard(str(protected));rootcu={t.m_Uuid.AsString():identity(t)for t in before_root.GetTracks()};nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};rootclusters=native_pad_clusters(before_root,nets)
transfers={r['uuid']:r for r in json.loads(transfer_ledger.read_text())['new_own_return_transfer_vias']};groups={r['via_uuid']:r for r in json.loads(source_ledger.read_text())['actual_owned_return_groups']};fps={f.GetReference():f for f in b.GetFootprints()};pads={p.m_Uuid.AsString():p for p in b.GetPads()};records=[]
if (retire|move)&set(rootcu):raise ValueError('An original/root50 copper object is in the new-reference repair scope')
for uid in retire:
 t=cu[uid];row=transfers[uid]
 if not isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()!=row['net']or mm(t.GetPosition())!=tuple(row['position_mm']):raise ValueError('Exact new standalone transfer differs')
 records.append(dict(action='retire_new_conflicting_transfer',uuid=uid,net=t.GetNetname(),position_mm=list(mm(t.GetPosition())),reason='A new standalone reference-transfer drill intersects subsequently reviewed real entry/current-return copper. It is removed; this is not a source terminal or required receiving IO3 via. Same-layer own-return bridging closes the reference separately, and all root50 SOURCE-pad clusters must remain.'))
 b.Remove(t)
held=[];allowed=set(retire)
for uid in move:
 row=groups[uid];v=cu[uid];p=pads[row['source_pad_uuid']];trackids=[u for u in row['new_copper_UUIDs']if u!=uid]
 if len(trackids)!=1 or v.GetNetname()!=row['return_net']or p.GetNetname()!=row['return_net']:raise ValueError('Exact reviewed CMOS source return group differs')
 t=cu[trackids[0]]
 if t.GetNetname()!=p.GetNetname()or t.GetStart()!=p.GetPosition()or t.GetEnd()!=v.GetPosition():raise ValueError('Reviewed source branch endpoints differ')
 held.append((row,p,t,v));allowed.update(row['new_copper_UUIDs']);b.Remove(t);b.Remove(v)
g=Geometry(b);fills=collect_native_reference_fills(b,set(SEEDS.values())-{'/CHASSIS'},[pcbnew.In1_Cu,pcbnew.In4_Cu])
for row,p,t,v in held:
 start=mm(p.GetPosition());layer=p.GetParentFootprint().GetLayer();adjacent=pcbnew.In1_Cu if layer==pcbnew.F_Cu else pcbnew.In4_Cu;net=p.GetNetname();chosen=None
 for distance in(.65,.8,1.,1.2,1.5,1.8,2.,2.5,3.):
  for angle in range(32):
   q=tuple(round(x,6)for x in(start[0]+distance*math.cos(angle*math.pi/16),start[1]+distance*math.sin(angle*math.pi/16)))
   if g.via(q,net)and g.clear([start,q],net,layer,.2)and covered(circle(tuple(xy(q)),pcbnew.FromMM(.26)),fills[net,adjacent]):chosen=q;break
  if chosen:break
 if chosen is None:
  owner=fps[row['owner']];ground=[q for q in owner.Pads()if q.GetNumber()and q.GetNetname()==net and q.IsOnLayer(layer)]
  target=next((q for q in sorted(ground,key=lambda q:math.dist(start,mm(q.GetPosition())))if math.dist(start,mm(q.GetPosition()))<=8. and g.clear([start,mm(q.GetPosition())],net,layer,.2)),None)
  if target is None:raise ValueError('No legal actual-source short own-return escape/actual owner-ground branch on current51 '+row['reference']+'.'+row['pin'])
  t.SetEnd(target.GetPosition());b.Add(t);g.add(t);retire.add(v.m_Uuid.AsString())
  records.append(dict(action='connect_cap_to_actual_owner_ground_retire_new_via',reference=row['reference'],pin=row['pin'],source_pad_uuid=p.m_Uuid.AsString(),owner_reference=owner.GetReference(),owner_pin=target.GetNumber(),owner_pad_uuid=target.m_Uuid.AsString(),net=net,track_uuid=t.m_Uuid.AsString(),retired_via_uuid=v.m_Uuid.AsString(),actual_same_side_branch_length_mm=math.dist(start,mm(target.GetPosition())),reason='The actual later field-current return blocks all short through drills. The capacitor instead connects directly to its actual same-side IC ground pin; only the newly added now-redundant drill is retired.'))
  continue
 oldpos=mm(v.GetPosition());v.SetPosition(xy(chosen));t.SetEnd(xy(chosen));b.Add(t);b.Add(v);g.add(t);g.add(v)
 records.append(dict(action='move_exact_new_source_escape',via_uuid=v.m_Uuid.AsString(),track_uuid=t.m_Uuid.AsString(),reference=row['reference'],pin=row['pin'],source_pad_uuid=p.m_Uuid.AsString(),net=net,old_via_mm=list(oldpos),new_via_mm=list(chosen),adjacent_layer=b.GetLayerName(adjacent),actual_branch_length_mm=math.dist(start,chosen)))
dest=out/'motherboard-new-reference-conflicts-repaired-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),dest.with_suffix(suffix))
for p in base.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
write(out/'generation.json',dict(input_sha256=frozen,exact_repairs=records))
native=drc(dest,out,'native');fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();current={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
if any(current.get(u)!=v for u,v in rootcu.items()):raise ValueError('Root50 protected current/source copper changed')
if set(current)!=set(oldcu)-retire or any(current.get(u)!=v for u,v in oldcu.items()if u not in allowed):raise ValueError('Unreviewed original/current51 native copper changed')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in fresh.GetPads()}or oldzones!=definitions(dest):raise ValueError('Source pads/poses/zone definitions changed')
after=native_pad_clusters(fresh,nets);survived=clusters_survive(rootclusters,after);write(out/'all-root50-source-cluster-proof.json',dict(before=rootclusters,after=after,passed=survived))
if not survived:raise ValueError('A real root50 SOURCE-pad cluster was lost')
freshcu={t.m_Uuid.AsString():t for t in fresh.GetTracks()};freshpads={p.m_Uuid.AsString():p for p in fresh.GetPads()};fills=collect_native_reference_fills(fresh,set(SEEDS.values())-{'/CHASSIS'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);proof=[]
for row in records:
 if row['action']=='connect_cap_to_actual_owner_ground_retire_new_via':
  p=freshpads[row['source_pad_uuid']];q=freshpads[row['owner_pad_uuid']]
  if q.m_Uuid.AsString()not in{x.m_Uuid.AsString()for x in fresh.GetConnectivity().GetConnectedItems(p)}:raise ValueError('Actual capacitor-to-owner ground branch is open')
  proof.append(dict(source_pad_uuid=row['source_pad_uuid'],actual_owner_ground_pad_uuid=row['owner_pad_uuid'],actual_same_side_owner_ground_connected=True));continue
 if row['action']!='move_exact_new_source_escape':continue
 p=freshpads[row['source_pad_uuid']];v=freshcu[row['via_uuid']];layer=fresh.GetLayerID(row['adjacent_layer']);peers={x.m_Uuid.AsString()for x in fresh.GetConnectivity().GetConnectedItems(v)}
 if p.m_Uuid.AsString()not in peers or not physical_reference_contact(v,layer,fresh.GetConnectivity())or not covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),fills[row['net'],layer]):raise ValueError('Relocated branch lacks exact actual SOURCE/native-annulus contact')
 proof.append(dict(via_uuid=row['via_uuid'],source_pad_uuid=row['source_pad_uuid'],actual_own_source_connected=True,actual_annulus_flashed_native_connected_on_adjacent_layer=True,full_own_filled_annulus=True))
if any(sha(Path(p))!=v for p,v in frozen.items()):raise ValueError('Frozen input changed')
# Include literal derived annulus metadata updates in the reviewed scope;
# native refill may change those fields without changing track/via geometry.
trees=[parse(without_generated_fills(p.read_text()))for p in(base,dest)];delta=[]
for kind in('segment','via','arc'):
 old,new=[objects(tree,kind)for tree in trees]
 delta.extend(u for u in set(old)|set(new)if u not in old or u not in new or dump(old[u])!=dump(new[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Correct eight exact newly added reference vias/ground branches that conflict with later actual entry distribution: retire four standalone new transfer drills and relocate four real source-owned CMOS ground escapes. Every root50 Cu/source cluster/land/pose and all zone definitions remain exact.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[]))
receipt=dict(input_sha256=frozen,board_sha256=sha(dest),exact_repairs=records,actual_source_annulus_proofs=proof,root50_all_native_Cu_and_SOURCE_clusters_preserved=True,current51_all_other_Cu_pads_poses_zone_definitions_preserved=True,native_errors=sum(x['severity']=='error'for x in native['violations']),native_DRC_types=dict(collections.Counter(x['type']for x in native['violations'])),ignored_checks=native['ignored_checks'],uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False)
write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in('input_sha256','exact_repairs','actual_source_annulus_proofs')},indent=2))
