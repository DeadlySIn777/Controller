"""Recheck the previously controlled PROC route on the composed native board."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
import hardware_route_ordinary_wip_r05 as guard
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity
D=Path('reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01')
C=D/'motherboard-bounded-merged-candidate.kicad_pcb'
P=Path('reports/motherboard-ordinary-routing-20261001/ROOT31-PROC-literal-F-tunnel-r35')
B=P/'motherboard-ordinary-F-PROC-candidate.kicad_pcb'
M=D/'source26-map-r02/domain-map.json'
inputs={str(p):sha(p)for p in(C,B,M,P/'proposed-groups.json',P/'manifest.json',P/'freeze-receipt-r01.json',Path(__file__))}
plan=json.loads((P/'proposed-groups.json').read_text())['groups'];assert len(plan)==1
g=plan[0];assert g['net']=='/mc_permission/PROC_PERMIT' and len(g['new_copper_UUIDs'])==32
board=pcbnew.LoadBoard(str(C));board.BuildConnectivity()
donor=pcbnew.LoadBoard(str(B));wanted={t.m_Uuid.AsString():identity(t)for t in donor.GetTracks()}
exact={t.m_Uuid.AsString():t for t in board.GetTracks()}
assert all(identity(exact[u])==wanted[u]for u in g['new_copper_UUIDs'])
pads={p.m_Uuid.AsString():p for p in board.GetPads()};p,q=[pads[u]for u in g['source_pad_UUIDs']]
assert q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
guard.MAPPING=json.loads(M.read_text())
assert guard.MAPPING['input_sha256'][str(C.resolve())]==sha(C)
manifest=json.loads((P/'manifest.json').read_text())
returns=guard.actual_return_check(board,g['new_copper_UUIDs'],manifest['nets'])
assert returns['passed'] and not returns['actual_signal_via_reference_audits']
assert all(sha(Path(p))==h for p,h in inputs.items())
out=D/'composed-PROC-return-r01.json';assert not out.exists()
write(out,dict(passed=True,board_sha256=sha(C),input_sha256=inputs,controlled_route_not_autorouter_generated=True,actual_source_pair=g['source_pair'],exact32_F_segments_preserved=True,actual_return_reviews=returns,physical_timing_qualified=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,items=32,board_sha256=sha(C))),flush=True)
