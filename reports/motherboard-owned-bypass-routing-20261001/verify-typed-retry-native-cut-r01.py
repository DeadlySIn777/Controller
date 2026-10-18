"""Prove new local loops, then remove their actual new copper in memory."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
p=Path(__file__).parent/'source26-r73-typed-retry-r01'
board=p/'owned-bypass-loop-candidate.kicad_pcb';receipt=p/'receipt.json'
owners=ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
frozen={str(x):sha(x)for x in(board,receipt,owners,Path(__file__))}
r=json.loads(receipt.read_text());manifest=json.loads(owners.read_text())
assert r['board_sha256']==sha(board) and not r['new_route_DRC_defects']
groups=[g for g in r['owned_loops']if g['retained']]
assert len(groups)==3
byref={g['ref']:g for g in manifest['capacitors']}
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity()
def endpoints(b,row):
 ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()}
 return ps[row['ref'],row['cap_power']],ps[row['ref'],row['cap_return']], [ps[n['ref'],n['pin']]for n in row['power_nodes']], [ps[n['ref'],n['pin']]for n in row['return_nodes']]
def closed(b,row):
 cp,cr,ops,ors=endpoints(b,row);co=b.GetConnectivity()
 connected=lambda p,qs: any(q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(p)}for q in qs)
 assert all(p.GetNetname()==cp.GetNetname()for p in ops)and all(p.GetNetname()==cr.GetNetname()for p in ors)
 return connected(cp,ops)and connected(cr,ors)
positive=[dict(ref=g['ref'],actual_owning_pin_loop=closed(b,byref[g['ref']]))for g in groups]
assert all(x['actual_owning_pin_loop']for x in positive)
cut=pcbnew.LoadBoard(str(board));cu={t.m_Uuid.AsString():t for t in cut.GetTracks()};alive=list(cu.values())
added={u for g in groups for u in g['new_UUIDs']}
for u in added:cut.Remove(cu[u])
cut.BuildConnectivity()
negative=[dict(ref=g['ref'],actual_owning_loop_open_after_Cu_cut=not closed(cut,byref[g['ref']]))for g in groups]
assert all(x['actual_owning_loop_open_after_Cu_cut']for x in negative)
assert all(sha(Path(x))==h for x,h in frozen.items())
write(p/'independent-native-cut-proof.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(board),positive_actual_owner_loops=positive,negative_real_Cu_cut_controls=negative,actual_removed_new_Cu=len(added),cut_board_saved=False,manufacturing_ready=False))
print(dict(passed=True,loops=len(groups),actual_cut_Cu=len(added)))
