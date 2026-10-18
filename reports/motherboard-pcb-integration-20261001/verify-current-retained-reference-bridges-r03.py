"""Recheck actual combined geometry before adopting ROOT87 as routing WIP."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered,circle
from hardware_route_selected_additive import corridor_polygon
from hardware_validate_return_bridge_sources import review
import argparse
ap=argparse.ArgumentParser()
for k in ('board','map','out'):ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args();board=a.board;P=board.parent
assert not a.out.exists()
R=ROOT/'reports/motherboard-return-zoning-20261001'
mp=a.map
aux=ROOT/'reports/motherboard-power-entry-20261001/aux24-field-cell-r68/receipt.json'
ao=R/'source26-r61-AO1-DAC-return-r04/receipt.json'
status=R/'source26-r62-field-status-ground-delivery-r02/receipt.json'
transfer=R/'source26-r62-C17014-field-return-reroute-r01/receipt.json'
bridges=R/'source26-r61-orphan-bridge-retirement-r01/all-retained-new-bridge-source-witnesses.json'
read=lambda p:json.loads(p.read_text())
frozen={str(p):sha(p)for p in (board,mp,aux,ao,status,transfer,bridges,Path(__file__),ROOT/'hardware/motherboard/design.json')}
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();co=b.GetConnectivity()
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
from hardware_route_logic_return import identity
checks=[]
for row in read(aux)['actual_local_endpoint_checks']:
 p,q=ps[row['from_ref'],row['from_pin']],ps[row['to_ref'],row['to_pin']]
 assert p.GetNetname()==q.GetNetname()and q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)}
 checks.append(row)
mapping=read(mp);groups=read(bridges)['groups'];groups=[dict(net=g['net'],new_copper_UUIDs=g['new_copper_UUIDs'])for g in groups]
groups.append(dict(net='/motherboard_status/FIELD_B_0V',new_copper_UUIDs=read(status)['new_copper_UUIDs']))
# Obtain each exact current conductor net rather than infer a sheet alias.
groups[-1]['net']=cu[groups[-1]['new_copper_UUIDs'][0]].GetNetname()
t=read(transfer);groups.append(dict(net='/motherboard_motors/FIELD_GND',new_copper_UUIDs=t['new_copper_UUIDs']+[t['changed_exact_ground_UUID']]))
groups.append(dict(net='/motherboard_analog_output/AO1_COM',new_copper_UUIDs=read(ao)['new_copper_UUIDs']))
seen={};unique_groups=[]
for group in groups:
 ids=[]
 for uid in group['new_copper_UUIDs']:
  if uid in seen:assert seen[uid]==group['net']
  else:seen[uid]=group['net'];ids.append(uid)
 if ids:unique_groups.append(dict(net=group['net'],new_copper_UUIDs=ids))
groups=unique_groups
extra=R/'source26-r69-four-source-ground-pieces-r01'
extra_scope=read(extra/'bounded-scope.json')
groups.append(dict(net='/LOGIC_GND',new_copper_UUIDs=extra_scope['reviewed_copper_delta_UUIDs']))
local=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r69-r01'
local_rows=[g for g in read(local/'receipt.json')['groups']if g['retained']]
for row in local_rows:
 p,q=ps[row['reference'],row['input_pin']],ps[row['reference'],row['target_ground_pin']]
 assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)}
for row in read(extra/'actual-receiving-ground-contacts.json')['rows']:
 v=cu[row['via_uuid']]
 for name in row['actual_flashed_native_connected_layers']:assert physical_reference_contact(v,b.GetLayerID(name),co)
for ep in (extra/'bounded-scope.json',extra/'actual-receiving-ground-contacts.json',local/'receipt.json',local/'independent-native-cut-proof.json'):
 frozen[str(ep)]=sha(ep)
bias=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r71-digital-bias-r02'
bias_receipt=read(bias/'receipt.json');bias_rows=[g for g in bias_receipt['actual_return_groups']if g['retained']]
for row in bias_rows:
 p=ps[row['reference'],row['pin']];v=cu[row['via_uuid']]
 assert p.m_Uuid.AsString()in{i.m_Uuid.AsString()for i in co.GetConnectedItems(v)}
 assert physical_reference_contact(v,b.GetLayerID(row['adjacent_layer']),co)
groups.append(dict(net='/LOGIC_GND',new_copper_UUIDs=[uid for row in bias_rows for uid in row['new_UUIDs']]))
for ep in(bias/'receipt.json',bias/'independent-native-cut-proof.json'):frozen[str(ep)]=sha(ep)
local_new=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r73-plus3-CMOS-stitches-r01'
new_ground_rows=[g for g in read(local_new/'receipt.json')['actual_return_groups']if g['retained']]
for row in new_ground_rows:
 p=ps[row['reference'],row['pin']];v=cu[row['via_uuid']]
 assert p.m_Uuid.AsString()in{i.m_Uuid.AsString()for i in co.GetConnectedItems(v)}
 assert physical_reference_contact(v,b.GetLayerID(row['adjacent_layer']),co)
groups.append(dict(net='/LOGIC_GND',new_copper_UUIDs=[u for row in new_ground_rows for u in row['new_UUIDs']]))
for ep in(local_new/'receipt.json',local_new/'independent-native-cut-proof.json'):
 frozen[str(ep)]=sha(ep)
assert read(local_new/'independent-native-cut-proof.json')['passed']
typed_retry=ROOT/'reports/motherboard-owned-bypass-routing-20261001/source26-r73-typed-retry-r01'
assert read(typed_retry/'independent-native-cut-proof.json')['passed']
for ep in(typed_retry/'receipt.json',typed_retry/'independent-native-cut-proof.json',typed_retry/'combined97-bypass-manifest.json'):
 frozen[str(ep)]=sha(ep)

contacts=R/'source26-r74-two-actual-ground-contacts-r01'
assert read(contacts/'closure-freeze-r02.json')['passed']
contact_scope=read(contacts/'bounded-scope.json')
assert len(contact_scope['reviewed_copper_delta_UUIDs'])==2
donor_contacts=pcbnew.LoadBoard(str(contacts/'motherboard-two-Source-ground-contacts-candidate.kicad_pcb'))
donor_contact_Cu={t.m_Uuid.AsString():identity(t)for t in donor_contacts.GetTracks()}
for uid in contact_scope['reviewed_copper_delta_UUIDs']:
 assert identity(cu[uid])==donor_contact_Cu[uid]
 groups.append(dict(net=cu[uid].GetNetname(),new_copper_UUIDs=[uid]))
for row in read(contacts/'actual-receiving-ground-contacts.json')['rows']:
 for name in row['actual_flashed_native_connected_layers']:
  assert physical_reference_contact(cu[row['via_uuid']],b.GetLayerID(name),co)
for ep in [contacts/'bounded-scope.json',contacts/'actual-receiving-ground-contacts.json',contacts/'closure-freeze-r02.json']:
 frozen[str(ep)]=sha(ep)

out9=R/'source26-r74-OUT9-external-ground-transfer-review-r02'
assert read(out9/'closure-freeze-r03.json')['passed']
out9ids=read(out9/'bounded-scope.json')['reviewed_copper_delta_UUIDs'];assert len(out9ids)==5
out9donor=pcbnew.LoadBoard(str(R/'source26-r74-OUT9-external-ground-transfer-r01/motherboard-OUT9-external-ground-transfer-candidate.kicad_pcb'))
out9cu={t.m_Uuid.AsString():t for t in out9donor.GetTracks()}
assert all(identity(cu[u])==identity(out9cu[u])for u in out9ids)
newvia=[cu[u]for u in out9ids if cu[u].Type()==pcbnew.PCB_VIA_T];assert len(newvia)==1
for layer in(pcbnew.In3_Cu,pcbnew.In4_Cu):assert physical_reference_contact(newvia[0],layer,co)
groups.append(dict(net='/motherboard_do/FIELD_B_0V',new_copper_UUIDs=out9ids))
for item in(out9/'closure-freeze-r03.json',out9/'bounded-scope.json',out9/'receipt.json'):
 frozen[str(item)]=sha(item)
for folder in('source26-OUT9-ground-intermediate-r83a','source26-OUT9-C14804-intermediate-r83b'):
 evidence=ROOT/'reports/motherboard-pcb-integration-20261001'/folder/'receipt.json';frozen[str(evidence)]=sha(evidence)
# Two literal retired Ground leaves follow their exactly relocated Bank A
# receiver resistors. Recheck the replacement pad/trace/via geometry itself.
import math
from hardware_route_logic_return import mm
bank=R/'motor-bank-A-consolidated-reference-donor-r07'
ledger=read(bank/'literal-delta-ledger.json');bankreceipt=read(bank/'receipt.json')
donor=pcbnew.LoadBoard(bankreceipt['donor_board']);donor_cu={v.m_Uuid.AsString():identity(v)for v in donor.GetTracks()}
assert sha(Path(bankreceipt['donor_board']))==bankreceipt['board_sha256']
frozen[str(bank/'literal-delta-ledger.json')]=sha(bank/'literal-delta-ledger.json')
frozen[str(bank/'receipt.json')]=sha(bank/'receipt.json')
frozen[str(Path(bankreceipt['donor_board']))]=sha(Path(bankreceipt['donor_board']))
replacements=[
 ('R11076','90b5918e-ff89-4949-ba4d-d064e6d3c70d','7a90c563-90a9-42e0-ad3e-bd8da0fcfd29','12fdf234-3b5d-4a31-8d0a-768bfcb423ab'),
 ('R11080','626e9a04-e48d-40da-be67-670da8690ff2','d48ab887-7df7-4955-9883-cb4a2e46e56d','6380ace0-5e5c-4a2e-8152-bedebe61400a')]
missing={u for g in groups for u in g['new_copper_UUIDs'] if u not in cu}
assert missing=={r[1]for r in replacements}
replacement_proofs=[];replacement_cuts=[]
cutdir=a.out.parent/(a.out.stem+'-cuts');cutdir.mkdir(exist_ok=False)
source=ps['C10001','2'];ground_fill=collect_native_reference_fills(b,{'/LOGIC_GND'},[pcbnew.In1_Cu])['/LOGIC_GND',pcbnew.In1_Cu]
for ref,retired,track_uid,via_uid in replacements:
 assert retired in ledger['exact_retired_Cu_UUIDs'] and retired not in cu
 pad=ps[ref,'2'];track,via=cu[track_uid],cu[via_uid]
 assert {track_uid,via_uid}<=set(ledger['exact_added_Cu_UUIDs'])
 assert identity(track)==donor_cu[track_uid] and identity(via)==donor_cu[via_uid]
 assert pad.GetNetname()==track.GetNetname()==via.GetNetname()==source.GetNetname()=='/LOGIC_GND'
 assert track.GetLayer()==pcbnew.F_Cu and tuple(track.GetStart())==tuple(pad.GetPosition()) and tuple(track.GetEnd())==tuple(via.GetPosition())
 assert math.isclose(math.dist(tuple(track.GetStart()),tuple(track.GetEnd()))/1e6,.75,abs_tol=1e-9)
 assert via.Type()==pcbnew.PCB_VIA_T and physical_reference_contact(via,pcbnew.In1_Cu,co)
 assert covered(circle(tuple(via.GetPosition()),via.GetWidth(pcbnew.In1_Cu)//2-pcbnew.FromMM(.01)),ground_fill)
 peers={v.m_Uuid.AsString()for v in co.GetConnectedItems(pad)}
 assert {track_uid,via_uid,source.m_Uuid.AsString()}<=peers
 for group in groups:
  if retired in group['new_copper_UUIDs']:group['new_copper_UUIDs'].remove(retired)
 groups.append(dict(net='/LOGIC_GND',new_copper_UUIDs=[track_uid,via_uid]))
 replacement_proofs.append(dict(source_reference=ref,pin='2',retired_exact_leaf=retired,replacement_trace=track_uid,replacement_via=via_uid,actual_F_length_mm=.75,actual_In1_contact_and_own_annulus=True,actual_source_anchor='C10001.2'))
 negative=pcbnew.LoadBoard(str(board));remove=next(t for t in negative.GetTracks()if t.m_Uuid.AsString()==track_uid);negative.Remove(remove)
 cutpath=cutdir/(ref+'-actual-ground-leaf-cut.kicad_pcb');pcbnew.SaveBoard(str(cutpath),negative)
 fresh=pcbnew.LoadBoard(str(cutpath));fresh.BuildConnectivity();fp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in fresh.GetPads()}
 disconnected=fp['C10001','2'].m_Uuid.AsString() not in {v.m_Uuid.AsString()for v in fresh.GetConnectivity().GetConnectedItems(fp[ref,'2'])}
 assert disconnected
 replacement_cuts.append(dict(path=str(cutpath),sha256=sha(cutpath),source_reference=ref,pin='2',actual_removed_UUID=track_uid,disconnected=True))
 del fresh,negative
assert all(g['new_copper_UUIDs'] for g in groups)
witnesses=review(b,groups,mapping['pads'])
annuli=[]
for row in t['actual_ground_transfer_annuli']:
 v=cu[row['via_uuid']]
 for layer in(pcbnew.In1_Cu,pcbnew.In3_Cu):
  assert physical_reference_contact(v,layer,co)
  annuli.append(dict(uuid=v.m_Uuid.AsString(),layer=b.GetLayerName(layer),actual_flashed_native_contact=True))
fills=collect_native_reference_fills(b,{'/LOGIC_GND','/motherboard_analog_output/AO1_COM'},[pcbnew.In1_Cu])
assert covered(corridor_polygon(tuple(ps['C17014','1'].GetPosition()),tuple(ps['U17014','14'].GetPosition()),pcbnew.FromMM(.5)),fills['/LOGIC_GND',pcbnew.In1_Cu])
g=ps['U14626','5'];ldac=ps['U14626','4'];v=cu[read(ao)['new_copper_UUIDs'][1]];peers={i.m_Uuid.AsString()for i in co.GetConnectedItems(v)}
assert {g.m_Uuid.AsString(),ldac.m_Uuid.AsString()}<=peers
assert physical_reference_contact(v,pcbnew.In1_Cu,co)and covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),fills['/motherboard_analog_output/AO1_COM',pcbnew.In1_Cu])
assert all(sha(Path(p))==h for p,h in frozen.items())
write(a.out,dict(passed=True,board_sha256=sha(board),input_sha256=frozen,actual_AUX24_endpoints=checks,actual_SOURCE_bridge_witnesses=witnesses,exact_relocated_BankA_ground_replacements=replacement_proofs,actual_persisted_replacement_leaf_cuts=replacement_cuts,actual_C17014_transfer_annuli=annuli,actual_grounded_input_endpoint_checks=len(local_rows),actual_digital_bias_return_contacts_checked=len(bias_rows),actual_added_CMOS_ground_contacts_checked=len(new_ground_rows),actual_AO1_GND5_LDAC4_and_In1_annulus_passed=True,manufacturing_ready=False))
print(dict(passed=True,actual_source_bridge_groups=len(groups),actual_AUX24_endpoints=len(checks)))
