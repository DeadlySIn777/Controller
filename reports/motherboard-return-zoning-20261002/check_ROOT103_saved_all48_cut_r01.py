"""Fresh reload proof of an actual saved/refilled 48-item copper removal."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_build_assembly import parse,dump
from hardware_merge_bounded_pcb_delta import without_generated_fills,objects,zone_definition
root=Path('reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01')
out=root/'persisted-all48-cut-r01'
base=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb')
cut=out/'actual-saved-all48-cut.kicad_pcb'
candidate=root/'motherboard-bounded-merged-candidate.kicad_pcb'
binding=root/'exact-composition-binding.json'
inputs={str(p):sha(p)for p in(base,cut,candidate,binding,out/'cut-inputs.json',out/'drc.json',Path(__file__))}
b=json.loads(binding.read_text());i=json.loads((out/'cut-inputs.json').read_text())
assert set(b['added_copper_UUIDs'])==set(i['removed_UUIDs']) and len(i['removed_UUIDs'])==48
assert i['input_board_sha256']==sha(candidate)==b['board_sha256']
boards=[pcbnew.LoadBoard(str(p))for p in(base,cut,candidate)]
for board in boards:board.BuildConnectivity()
before,after,positive=boards
cu=lambda board:{t.m_Uuid.AsString():identity(t)for t in board.GetTracks()}
pads=lambda board:{p.m_Uuid.AsString():pad_identity(p)for p in board.GetPads()}
assert cu(before)==cu(after) and pads(before)==pads(after)==pads(positive)
assert not(set(i['removed_UUIDs'])&set(cu(after)))
bt,ct=[parse(without_generated_fills(p.read_text()))for p in(base,cut)]
assert {u:dump(f)for u,f in objects(bt,'footprint').items()}=={u:dump(f)for u,f in objects(ct,'footprint').items()}
assert {u:zone_definition(z)for u,z in objects(bt,'zone').items()}=={u:zone_definition(z)for u,z in objects(ct,'zone').items()}
nets={p.GetNetname()for p in before.GetPads()if p.GetNumber()}
old=native_pad_clusters(before,nets);restored=native_pad_clusters(after,nets)
assert old==restored
counts=[x.GetConnectivity().GetUnconnectedCount(False)for x in boards]
assert counts==[3521,3521,3508],counts
drc=json.loads((out/'drc.json').read_text());assert not drc['violations']
assert all(sha(Path(p))==h for p,h in inputs.items())
result=dict(passed=True,input_sha256=inputs,removed_actual_saved_copper_items=48,
 native_refill_and_fresh_reload=True,exact_baseline_copper_pads_poses_zone_definitions_restored=True,
 exact_baseline_Source_clusters_restored=True,baseline_missing_joins=3521,cut_missing_joins=3521,
 positive_candidate_missing_joins=3508,native_regular_DRC_violations=0,
 scope='Coupled actual removal of all 48 additions; not a claim of 48 independent per-item controls.',manufacturing_ready=False)
write(out/'receipt.json',result)
print(json.dumps({k:v for k,v in result.items()if k!='input_sha256'}),flush=True)
