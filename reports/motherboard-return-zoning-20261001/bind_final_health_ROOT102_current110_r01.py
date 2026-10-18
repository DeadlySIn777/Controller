"""Read-only final ROOT102 health composition binding and prior SOURCE proof."""
from pathlib import Path
import argparse, json, sys
sys.path.insert(0, str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha, write
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_build_assembly import parse, dump, children
from hardware_merge_bounded_pcb_delta import without_generated_fills, objects, reference

ap=argparse.ArgumentParser()
ap.add_argument('--board', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a=ap.parse_args()
assert not a.out.exists()
a.out.mkdir(parents=True)
R=Path('reports/motherboard-return-zoning-20261001')
B=R/'ROOT101-two-same-side-bypass-restored-r06/motherboard-two-same-side-bypass-candidate.kicad_pcb'
M=R/'ROOT101-health-complete-delta-r30/current110-unbound-composition-manifest.json'
S=B.parent/'bounded-scope.json'
P=a.board.parent/'receipt.json'
inputs={str(q):sha(q)for q in(B,M,S,P,a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
assert sha(B)=='769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5'
assert inputs['hardware/motherboard/design.json']=='6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
assert inputs['hardware/motherboard/netlist.xml']=='9f2c3c7b1e1b8f8cf108d0460dd0f709033f6ebdbf7f7a1b596abf1190eec633'
merge=json.loads(P.read_text());assert merge['board_sha256']==sha(a.board)
assert merge['native_DRC_regular']==0 and merge['ignored_checks']==[]
oldtree=parse(without_generated_fills(B.read_text()))
newtree=parse(without_generated_fills(a.board.read_text()))
oldfps={reference(f):f for f in children(oldtree,'footprint')}
newfps={reference(f):f for f in children(newtree,'footprint')}
assert all(dump(oldfps[r])==dump(newfps[r])for r in('C13006','C13007'))
two_scope=json.loads(S.read_text())
two_ids=two_scope['reviewed_copper_delta_UUIDs'];assert len(two_ids)==6
two_cu={}
for kind in('segment','via','arc'):
 old,new=objects(oldtree,kind),objects(newtree,kind)
 for uid in two_ids:
  if uid in old:
   assert uid in new and dump(old[uid])==dump(new[uid])
   two_cu[uid]=dict(kind=kind,definition=dump(old[uid]))
assert set(two_cu)==set(two_ids)
before=pcbnew.LoadBoard(str(B));after=pcbnew.LoadBoard(str(a.board))
nets={q.GetNetname()for q in before.GetPads()if q.GetNumber()}
prior=native_pad_clusters(before,nets);now=native_pad_clusters(after,nets)
assert clusters_survive(prior,now)
write(a.out/'all-ROOT102-prior-native-Source-clusters.json',dict(passed=True,board_sha256=sha(a.board),input_sha256=inputs,before=prior,after=now,all_prior_native_Source_pad_clusters_survive=True))
manifest=json.loads(M.read_text());groups=[g for g in manifest['owned_loops']if g['retained']]
assert len(groups)==110 and len({g['ref']for g in groups})==110
assert {'C13006','C13007','C11078','C11079','C11080','C11081'}<={g['ref']for g in groups}
manifest.update(board_sha256=sha(a.board),current_native_proof_required=True,ROOT102_composition_input_sha256=inputs,scope='Exact current ROOT102 plus bounded health correction:110 actual owned-loop groups. All prior ROOT102 Source clusters and its two-cap poses/six conductors survive. Final strict loops/control/resource/registration/unchanged r07 and persisted cuts are separately required before adoption. No Source27, loaded timing/current/thermal or manufacturing qualification.')
write(a.out/'current110-bypass-manifest.json',manifest)
assert all(sha(Path(q))==h for q,h in inputs.items())
write(a.out/'binding.json',dict(passed=True,board_sha256=sha(a.board),input_sha256=inputs,all_ROOT102_Source_clusters_preserved=True,ROOT102_C13006_C13007_exact_poses_and_six_conductors_preserved=True,two_cap_conductors=two_cu,owned_loop_groups_bound=110,final_native_scope_proofs_pending=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(a.board),prior_Source_clusters=len(prior),loops=110)),flush=True)
