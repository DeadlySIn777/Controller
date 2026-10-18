"""Independently recheck exact new bias returns and remove their real copper."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_validate_return_bridge_sources import review
P=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r71-digital-bias-r02'
board=P/'digital-bias-return-candidate.kicad_pcb';receipt=P/'receipt.json'
mapping=ROOT/'reports/motherboard-domains-20261001/source26-r71-r01/domain-map.json'
frozen={str(p):sha(p)for p in(board,receipt,mapping,Path(__file__))};r=json.loads(receipt.read_text());assert r['passed']and r['board_sha256']==sha(board)
assert any(row['reference']=='R10027'for row in r['already_connected']), 'Known actual existing Source return was not recognized'
groups=[g for g in r['actual_return_groups']if g['retained']];added={uid for g in groups for uid in g['new_UUIDs']}
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};ps={p.m_Uuid.AsString():p for p in b.GetPads()};co=b.GetConnectivity()
witness=review(b,[dict(net='/LOGIC_GND',new_copper_UUIDs=sorted(added))],json.loads(mapping.read_text())['pads']);positives=[]
for g in groups:
 p=ps[g['source_pad_uuid']];v=cu[g['via_uuid']];layer=b.GetLayerID(g['adjacent_layer'])
 assert p.GetNetname()==v.GetNetname()=='/LOGIC_GND'and p.m_Uuid.AsString()in{i.m_Uuid.AsString()for i in co.GetConnectedItems(v)}and physical_reference_contact(v,layer,co)
 assert v.GetWidth(pcbnew.F_Cu)==pcbnew.FromMM(.5)and v.GetDrill()==pcbnew.FromMM(.2)
 assert all(not isinstance(cu[u],pcbnew.PCB_VIA)and cu[u].GetWidth()==pcbnew.FromMM(.3)for u in g['new_UUIDs']if u!=g['via_uuid'])
 positives.append(dict(reference=g['reference'],pin=g['pin'],actual_own_filled_layer_contact=True))
n=pcbnew.LoadBoard(str(board));nc={t.m_Uuid.AsString():t for t in n.GetTracks()};alive=list(nc.values())
for uid in added:n.Remove(nc[uid])
n.BuildConnectivity();negative_conn=n.GetConnectivity();np={p.m_Uuid.AsString():p for p in n.GetPads()};negatives=[]
for g in groups:
 p=np[g['source_pad_uuid']];assert p.GetNetname()=='/LOGIC_GND';layer=n.GetLayerID(g['adjacent_layer'])
 connected=[nc[v.m_Uuid.AsString()]for v in negative_conn.GetConnectedItems(p)if v.Type()==pcbnew.PCB_VIA_T and physical_reference_contact(nc[v.m_Uuid.AsString()],layer,negative_conn)]
 assert not connected,('Physical cut still grounded',g['reference'])
 negatives.append(dict(reference=g['reference'],pin=g['pin'],same_net_label_preserved=True,actual_adjacent_reference_contact_lost=True))
# Positive classifier control: the preserved old R10027 return must remain
# visible even though GetConnectedItems wraps its via as PCB_TRACK.
known=next(p for p in n.GetPads()if p.GetParentFootprint().GetReference()=='R10027'and p.GetNumber()=='2')
known_vias=[nc[v.m_Uuid.AsString()]for v in negative_conn.GetConnectedItems(known)if v.Type()==pcbnew.PCB_VIA_T and physical_reference_contact(nc[v.m_Uuid.AsString()],pcbnew.In1_Cu,negative_conn)]
assert known_vias and all(isinstance(v,pcbnew.PCB_VIA)for v in known_vias)
assert all(sha(Path(p))==h for p,h in frozen.items())
write(P/'independent-native-cut-proof.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(board),actual_new_Cu_count=len(added),known_existing_return_positive_control=True,connected_vias_resolved_by_native_Type_and_actual_track_UUID=True,native_SOURCE_witnesses=witness,actual_receiving_contact_positives=positives,actual_removed_transaction_negative_controls=negatives,cut_board_saved=False,global_return_capacity_or_physical_default_voltage_qualified=False,manufacturing_ready=False))
print(dict(passed=True,positive_contacts=len(positives),physical_cut_negatives=len(negatives),actual_new_Cu=len(added)))
