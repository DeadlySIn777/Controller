"""Actual conductor identity, unchanged zones and physical-cut validation."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity
from hardware_build_assembly import parse,children,child,value,dump
P=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r69-r01'
board=P/'local-CMOS-ground-ties-candidate.kicad_pcb'
old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb'
r=json.loads((P/'receipt.json').read_text());assert r['passed']and r['board_sha256']==sha(board)
frozen={str(p):sha(p)for p in(board,old,P/'receipt.json',Path(__file__))}
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();co=b.GetConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
before=pcbnew.LoadBoard(str(old));before.BuildConnectivity();oc={t.m_Uuid.AsString():t for t in before.GetTracks()}
groups=[g for g in r['groups']if g['retained']];new={u for g in groups for u in g['new_UUIDs']}
assert set(cu)-set(oc)==new and set(oc)<=set(cu)
assert all(identity(cu[u])==identity(t)for u,t in oc.items())
assert all(not isinstance(cu[u],pcbnew.PCB_VIA)and cu[u].GetNetname()=='/LOGIC_GND'and cu[u].GetWidth()==pcbnew.FromMM(.20)and cu[u].GetLayer()in(pcbnew.F_Cu,pcbnew.B_Cu)for u in new)
def zones(p):return {value(child(z,'uuid')[1]):dump([v for v in z if not(isinstance(v,list)and v[0]in('filled_polygon','fill_segments'))])for z in children(parse(p.read_text()),'zone')}
assert zones(board)==zones(old)
for ext in('.kicad_dru','.kicad_pro'):assert board.with_suffix(ext).read_bytes()==old.with_suffix(ext).read_bytes()
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()}
positive=[]
for g in groups:
 p,q=ps[g['reference'],g['input_pin']],ps[g['reference'],g['target_ground_pin']]
 assert q.m_Uuid.AsString()in{i.m_Uuid.AsString()for i in co.GetConnectedItems(p)}
 positive.append(dict(reference=g['reference'],input_pin=g['input_pin'],actual_GND_pin=g['target_ground_pin'],native_physically_connected=True))
# One independent actual cut removes exactly this transaction. Net names,
# real SOURCE pads, old copper and filled zone geometry are retained.
n=pcbnew.LoadBoard(str(board));nc={t.m_Uuid.AsString():t for t in n.GetTracks()};alive=list(nc.values())
for uid in new:n.Remove(nc[uid])
n.BuildConnectivity();negative_co=n.GetConnectivity();ns={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in n.GetPads()if p.GetNumber()};negative=[]
for g in groups:
 p,q=ns[g['reference'],g['input_pin']],ns[g['reference'],g['target_ground_pin']]
 assert p.GetNetname()==q.GetNetname()=='/LOGIC_GND'
 assert q.m_Uuid.AsString()not in{i.m_Uuid.AsString()for i in negative_co.GetConnectedItems(p)}
 negative.append(dict(reference=g['reference'],input_pin=g['input_pin'],actual_GND_pin=g['target_ground_pin'],same_labels_but_actual_copper_cut_rejected=True))
assert all(sha(Path(p))==h for p,h in frozen.items())
write(P/'independent-native-cut-proof.json',dict(passed=True,board_sha256=sha(board),input_sha256=frozen,exact_new_same_side_020_ground_segments=len(new),new_vias=0,all_old_physical_copper_and_zone_definitions_unchanged=True,actual_SOURCE_input_to_GND_positives=positive,actual_new_transaction_removed_negative_controls=negative,cut_board_never_saved=True,global_return_or_current_capacity_qualified=False,manufacturing_ready=False))
print(dict(passed=True,new_Cu=len(new),actual_positives=len(positive),physical_cut_negatives=len(negative)))
