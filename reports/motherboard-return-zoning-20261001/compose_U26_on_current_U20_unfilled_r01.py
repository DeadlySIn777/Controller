"""Literal bounded native U26 transaction composition, not a qualified board.

Preserve current ROOT101+U20 metadata/rules. Derived fill is discarded only
for the fresh later own-field refill; all physical and source objects retain
exact scoped provenance. No fill/geometric acceptance is claimed here.
"""
from pathlib import Path
import sys,json,copy,shutil
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_build_assembly import parse,dump,children
from hardware_merge_bounded_pcb_delta import objects,reference,unchanged_properties,without_generated_fills,dump_board,sha_text,merge_reviewed_existing_zone_outlines
from hardware_map_motherboard_domains import sha,write
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');D=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r235/motor-health-U26-cell-candidate.kicad_pcb');T=Path('reports/motherboard-return-zoning-20261001/ROOT101-U20-actual-cell-merged-stage-r01/motherboard-bounded-merged-candidate.kicad_pcb');P=Path('reports/motherboard-return-zoning-20261001/ROOT101-health-composition-inputs-r01/U26-scope.json');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U20-U26-actual-unfilled-composition-r01');assert not O.exists();O.mkdir();assert sha(T)=='5781df8adfecede0247e8b7ec346e573ba38a313e6f7a0d06e2c3c49d821eb01';frozen={str(p):sha(p)for p in[B,D,T,P,Path(__file__)]};scope=json.loads(P.read_text());trees={k:parse(without_generated_fills(p.read_text()))for k,p in [('before',B),('donor',D),('target',T)]};assert [dump(n)for n in children(trees['before'],'net')]==[dump(n)for n in children(trees['donor'],'net')]==[dump(n)for n in children(trees['target'],'net')],'Net-code/name tables must match literally before AST composition';fps={k:{reference(v):v for v in children(t,'footprint')}for k,t in trees.items()};assert set(fps['before'])==set(fps['donor'])==set(fps['target']);changed=[]
for ref,old in fps['before'].items():
 new=fps['donor'][ref]
 if dump(old)==dump(new):continue
 assert ref in scope['reviewed_footprint_references']and dump(fps['target'][ref])==dump(old)
 assert unchanged_properties(old)==unchanged_properties(new)
 changed.append(ref);trees['target'][trees['target'].index(fps['target'][ref])]=copy.deepcopy(new)
assert set(changed)==set(scope['reviewed_footprint_references']);delta=[]
for kind in('segment','via','arc'):
 old,new,cur=[objects(trees[k],kind)for k in('before','donor','target')]
 for u in set(old)|set(new):
  first,last=old.get(u),new.get(u)
  if first is not None and last is not None and dump(first)==dump(last):continue
  if first is not None:
   assert u in cur and dump(cur[u])==dump(first),'Concurrent actual copper conflict '+u
   trees['target'].remove(cur[u])
  else:assert u not in cur
  if last is not None:trees['target'].append(copy.deepcopy(last))
  delta.append(dict(kind=kind,uuid=u,before_sha256=sha_text(dump(first))if first is not None else None,after_sha256=sha_text(dump(last))if last is not None else None))
assert {r['uuid']for r in delta}==set(scope['reviewed_copper_delta_UUIDs']);oldz,newz=objects(trees['before'],'zone'),objects(trees['donor'],'zone');assert set(oldz)==set(newz)and all(dump(oldz[u])==dump(newz[u])for u in oldz);assert not scope['reviewed_added_zone_UUIDs'];dest=O/'motherboard-U20-U26-unfilled-candidate.kicad_pcb';dest.write_text(dump_board(trees['target']))
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(T.with_suffix(ext),dest.with_suffix(ext))
for p in T.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copy2(p,O/p.name)
assert all(sha(p)==h for p,h in frozen.items());write(O/'composition.json',dict(literal_bounded_composition_passed=True,passed=False,native_refill_required=True,Source_receiving_return_pending=True,before_board=str(T),before_board_sha256=sha(T),board=str(dest),board_sha256=sha(dest),peer_before=str(B),peer_donor=str(D),frozen_sha256=frozen,exact_two_pose_references=changed,exact_copper_delta=delta,all_existing_target_zones_and_rules_preserved=True,Source27_adopted=False,manufacturing_ready=False));print(json.dumps(dict(board=str(dest),sha256=sha(dest),parts=len(fps['target']),scoped_copper_delta=len(delta),native_refill_pending=True)))
