"""Bind exact additive bypass/controlled PROC composition for fresh native proofs."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
R=Path('reports/motherboard-return-zoning-20261002')
D=R/'ROOT103-bypass-PROC-composed-r01'
B=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb')
C=D/'motherboard-bounded-merged-candidate.kicad_pcb'
M=B.parent/'final-binding-r02/current110-bypass-manifest.json'
L=R/'ROOT103-reviewed-local-bypass-batch-r01/receipt.json'
P=Path('reports/motherboard-ordinary-routing-20261001/ROOT31-PROC-literal-F-tunnel-r35/proposed-groups.json')
inputs={str(p):sha(p)for p in(B,C,M,L,P,D/'receipt.json',Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
assert sha(B)=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
receipt=json.loads((D/'receipt.json').read_text());assert receipt['board_sha256']==sha(C)
assert receipt['native_DRC_regular']==0 and not receipt['ignored_checks']
old=json.loads(M.read_text());new=json.loads(L.read_text())
groups=[g for g in old['owned_loops']if g['retained']]+[g for g in new['owned_loops']if g['retained']]
assert len(groups)==len({g['ref']for g in groups})==120
proc=json.loads(P.read_text())['groups'];assert len(proc)==1
ids={u for g in new['owned_loops']if g['retained']for u in g['new_UUIDs']}|set(proc[0]['new_copper_UUIDs'])
assert len(ids)==48
before=pcbnew.LoadBoard(str(B));after=pcbnew.LoadBoard(str(C));before.BuildConnectivity();after.BuildConnectivity()
oldcu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
assert set(newcu)-set(oldcu)==ids and all(newcu.get(u)==v for u,v in oldcu.items())
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
bt=parse(without_generated_fills(B.read_text()));ct=parse(without_generated_fills(C.read_text()))
assert {u:dump(f)for u,f in objects(bt,'footprint').items()}=={u:dump(f)for u,f in objects(ct,'footprint').items()}
assert {u:zone_definition(z)for u,z in objects(bt,'zone').items()}=={u:zone_definition(z)for u,z in objects(ct,'zone').items()}
nets={p.GetNetname()for p in before.GetPads()if p.GetNumber()}
prior=native_pad_clusters(before,nets);current=native_pad_clusters(after,nets)
assert clusters_survive(prior,current)
manifest=dict(board_sha256=sha(C),owned_loops=groups,actual_filled_supply_branch_return_reviews=[],input_sha256=inputs,manufacturing_ready=False)
assert not(D/'current120-bypass-manifest.json').exists()
write(D/'current120-bypass-manifest.json',manifest)
write(D/'prior-source-clusters.json',dict(passed=True,board_sha256=sha(C),before=prior,after=current,all_prior_native_Source_pad_clusters_preserved=True))
assert all(sha(Path(p))==h for p,h in inputs.items())
write(D/'exact-composition-binding.json',dict(passed=True,board_sha256=sha(C),input_sha256=inputs,added_copper_UUIDs=sorted(ids),added_copper_items=48,actual_owned_loops=120,exact_old_copper_lands_poses_zone_definitions_preserved=True,all_prior_Source_clusters_preserved=True,strict_fresh_proofs_pending=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(C),owned_loops=120,added_copper=48)),flush=True)
