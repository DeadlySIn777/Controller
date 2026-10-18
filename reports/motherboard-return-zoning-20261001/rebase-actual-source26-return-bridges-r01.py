"""Revalidate only physically necessary prior return bridges on actual source26."""
import sys,json,collections,shutil,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_stitch_owned_return_planes import definitions,ALLOWED_RETURNS
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_validate_motherboard_return_planes_r02 import validate
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_route_owned_bypass_loops import drc
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import objects,without_generated_fills,dump_board
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--map',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
oldbase=Path('reports/motherboard-return-zoning-20261001/interim-full-plane-delta-r02/motherboard-interim-own-reference-candidate.kicad_pcb');oldfinal=Path('reports/motherboard-return-zoning-20261001/source25-r46-grid-reference-bridges-r07/motherboard-own-return-bridges-candidate.kicad_pcb')
groupfiles=[Path('reports/motherboard-return-zoning-20261001')/name/'generation.json'for name in ['source25-r46-reference-bridges-r02','source25-r46-reference-bridges-r04','source25-r46-compact-reference-bridges-r05','source25-r46-opposite-reference-bridges-r06']]
out=a.out
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir(parents=True);(out/'inputs').mkdir();inputs=[a.board,a.map,oldbase,oldfinal,Path(__file__)]+groupfiles;frozen={str(p.resolve()):sha(p)for p in inputs}
for i,p in enumerate(inputs):shutil.copy2(p,out/'inputs'/f'{i:02}-{p.name}')
boards=[pcbnew.LoadBoard(str(p))for p in(a.board,oldbase,oldfinal)];b=boards[0];mapping=json.loads(a.map.read_text());initial=validate(b,mapping);oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};olddefs=definitions(a.board);nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};before=native_pad_clusters(b,nets)
priorcu=[{t.m_Uuid.AsString():t for t in old.GetTracks()}for old in boards[1:]];addids=set(priorcu[1])-set(priorcu[0]);groups=[r for f in groupfiles for r in json.loads(f.read_text())['groups']if r.get('retained')]
if set(u for r in groups for u in r['new_copper_UUIDs'])!=addids:raise ValueError('All prior added Cu must have exact reviewed group provenance')
fills=collect_native_reference_fills(b,ALLOWED_RETURNS,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pieces={key:list(split_polygons(poly))for key,poly in fills.items()};unanchored={(r['net'],b.GetLayerID(r['reference_layer']),r['filled_piece'])for r in initial['unanchored_components']};guard=ReferenceGuard(b,mapping);accepted=[];rejected=[]
for group in groups:
 key=group['net'],b.GetLayerID(group['reference_layer']);start=xy(group['route_mm'][0]);touches=[i for i,piece in enumerate(pieces.get(key,[]))if piece.Contains(start)]
 if not any((key[0],key[1],i)in unanchored for i in touches):rejected.append(dict(group=group,reason='Actual current source26 filled starting resource is absent or already physically source-anchored'));continue
 reason=None
 for uid in group['new_copper_UUIDs']:
  t=priorcu[1][uid]
  if t.GetNetname()!=group['net']or t.GetNetname()not in ALLOWED_RETURNS:raise ValueError('Prior bridge changed to a forbidden net')
  if isinstance(t,pcbnew.PCB_VIA):
   if not guard.geometry.via(mm(t.GetPosition()),t.GetNetname()):reason='Actual current native pad/track/barrier obstruction at proposed return transfer';break
  elif not guard.clear([mm(t.GetStart()),mm(t.GetEnd())],t.GetNetname(),t.GetLayer(),pcbnew.ToMM(t.GetWidth())):
   reason='Actual current native clearance or source-derived foreign projection blocks prior ground bridge';break
 if reason:rejected.append(dict(group=group,reason=reason));continue
 accepted.append(group)
 for uid in group['new_copper_UUIDs']:guard.geometry.add(priorcu[1][uid])
new=sorted(u for g in accepted for u in g['new_copper_UUIDs']);trees=[parse(without_generated_fills(p.read_text()))for p in(a.board,oldfinal)]
for kind in('segment','via','arc'):
 prior=objects(trees[1],kind)
 for uid in sorted(set(new)&set(prior)):trees[0].append(prior[uid])
dest=out/'motherboard-source26-return-bridges-candidate.kicad_pcb';dest.write_text(dump_board(trees[0]),encoding='utf-8')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(a.board.with_suffix(suffix),dest.with_suffix(suffix))
for p in a.board.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,out/p.name)
write(out/'generation.json',dict(accepted=accepted,rejected=rejected,prior_ground_groups=len(groups),actual_revalidated_groups=len(accepted),actual_added_copper=len(new),input_sha256=frozen));print(dict(actual_groups=len(accepted),rejected=len(rejected),actual_new_Cu=len(new)),flush=True)
native=drc(dest,out,'native');b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity();current={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
if set(current)!=set(oldcu)|set(new)or any(current[u]!=r for u,r in oldcu.items()):raise ValueError('Actual current old copper changed')
if oldpads!={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}or olddefs!=definitions(dest):raise ValueError('Actual source/pad/pose/zone changed')
after=native_pad_clusters(b,nets);passed=clusters_survive(before,after);write(out/'all-native-source-cluster-proof.json',dict(before=before,after=after,passed=passed))
if not passed:raise ValueError('A current actual source cluster split')
if any(r['severity']=='error'for r in native['violations'])or native['ignored_checks']:raise ValueError('Actual current native error/ignored checks remain')
final=validate(b,mapping);final['board_sha256']=sha(dest);final['source_map_sha256']=sha(a.map);write(out/'full-native-resource-review.json',final)
rawtrees=[parse(without_generated_fills(p.read_text()))for p in(a.board,dest)];delta=[]
for kind in('segment','via','arc'):
 old,newraw=[objects(tree,kind)for tree in rawtrees];delta.extend(u for u in set(old)|set(newraw)if u not in old or u not in newraw or dump(old[u])!=dump(newraw[u]))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason='Only prior provenance-reviewed low-current ground bridge groups which remain genuinely unanchored and pass actual source26 native geometry/foreign-domain guards are added. All old current source/pad/pose/Cu/zone definitions and source clusters remain exact. No dummy via, old-source property rollback, capacitor move, supply routing or current-capacity claim.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(delta),reviewed_added_zone_UUIDs=[]))
for p,h in frozen.items():
 if sha(Path(p))!=h:raise ValueError('Frozen input changed')
r=dict(passed=True,board_sha256=sha(dest),before_board_sha256=sha(a.board),source_map_sha256=sha(a.map),actual_source26_rebased=True,new_actual_groups=len(accepted),new_copper_UUIDs=new,native_errors=0,native_DRC_types=dict(collections.Counter(r['type']for r in native['violations'])),ignored_checks=native['ignored_checks'],all_current_source_pad_clusters_old_copper_poses_zone_definitions_preserved=True,remaining_unanchored_resources=len(final['unanchored_components']),scope_sha256=sha(out/'bounded-scope.json'),global_reference_passed=final['passed'],manufacturing_ready=False);write(out/'receipt.json',r);print(json.dumps(r,indent=2))
