"""Recheck actual combined geometry before adopting ROOT79 as routing WIP."""
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
P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-critical7-r79'
board=P/'motherboard-bounded-merged-candidate.kicad_pcb'
old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-four-HF-closures-r78/motherboard-bounded-merged-candidate.kicad_pcb'
R=ROOT/'reports/motherboard-return-zoning-20261001'
mp=ROOT/'reports/motherboard-domains-20261001/source26-r79-r01/domain-map.json'
aux=ROOT/'reports/motherboard-power-entry-20261001/aux24-field-cell-r68/receipt.json'
ao=R/'source26-r61-AO1-DAC-return-r04/receipt.json'
status=R/'source26-r62-field-status-ground-delivery-r02/receipt.json'
transfer=R/'source26-r62-C17014-field-return-reroute-r01/receipt.json'
bridges=R/'source26-r61-orphan-bridge-retirement-r01/all-retained-new-bridge-source-witnesses.json'
paths=[board,old,mp,aux,ao,status,transfer,bridges,P/'combined-bypass-proof.json',P/'independent-connectivity/review.json',P/'drc.json',Path(__file__)]
frozen={str(p):sha(p)for p in paths};read=lambda p:json.loads(p.read_text())
assert not(P/'adoption.json').exists()
critical_proof=P/'combined-critical-proof/review.json'
assert read(critical_proof)['passed']and read(critical_proof)['board_sha256']==sha(board)
assert read(critical_proof)['map_sha256']==sha(mp)
frozen[str(critical_proof)]=sha(critical_proof)

slivers=ROOT/'reports/motherboard-return-zoning-20261001/source26-r74-four-literal-DFM-slivers-r02'
assert read(slivers/'closure-freeze-r03.json')['passed']
resources=read(P/'literal-reference-resources.json')
assert resources['board_sha256']==sha(board)
assert len(resources['unanchored_components'])==4
assert not resources['derived_nonphysical_computation_artifacts']
strict4=ROOT/'reports/motherboard-owned-bypass-routing-20261001/source26-r76-strict-same-side-r01'
assert read(strict4/'independent-native-cut-proof.json')['passed']
assert read(P/'combined-bypass-proof.json')['retained_local_loops_checked']==101
for ep in [slivers/'bounded-scope.json',slivers/'closure-freeze-r03.json',P/'literal-reference-resources.json',strict4/'receipt.json',strict4/'bounded-scope.json',strict4/'independent-native-cut-proof.json',strict4/'combined101-bypass-manifest.json',P/'receipt.json']:
 frozen[str(ep)]=sha(ep)

rule_proof=P/'retained-FPGA38-rule-proof.json';rule=read(rule_proof)
assert rule['passed']and rule['board_sha256']==sha(board)
assert rule['exact_literal_signal_nets']==38 and rule['maximum_aggregate_per_net_mm']==1.
assert rule['factory_exact_2oz_process_confirmation_outstanding']
for item in(rule_proof,ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/proposal.json',board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru')):
 frozen[str(item)]=sha(item)

ordinary_proof=P/'combined-ordinary-proof/review.json'
assert read(ordinary_proof)['passed']and read(ordinary_proof)['board_sha256']==sha(board)
assert read(ordinary_proof)['map_sha256']==sha(mp)
frozen[str(ordinary_proof)]=sha(ordinary_proof)

for p in (P/'combined-bypass-proof.json',P/'independent-connectivity/review.json'):
 assert read(p)['board_sha256']==sha(board)
assert read(P/'combined-bypass-proof.json')['passed']
assert read(P/'independent-connectivity/review.json')['source_net_checks_pass']
native=read(P/'drc.json');assert not native['ignored_checks'] and all(v['severity']=='warning'for v in native['violations'])
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();before=pcbnew.LoadBoard(str(old));prior=clusters_preserved(source_clusters(before),b)
co=b.GetConnectivity();ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
from hardware_route_logic_return import identity
literal_donor=pcbnew.LoadBoard(str(strict4/'owned-bypass-loop-candidate.kicad_pcb'))
donor_Cu={t.m_Uuid.AsString():identity(t)for t in literal_donor.GetTracks()}
new9=read(strict4/'bounded-scope.json')['reviewed_copper_delta_UUIDs'];assert len(new9)==9
assert all(identity(cu[u])==donor_Cu[u]for u in new9)


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
result=dict(passed=True,input_sha256=frozen,board_sha256=sha(board),prior_SOURCE_clusters=prior,actual_AUX24_endpoints=checks,actual_SOURCE_bridge_witnesses=witnesses,actual_C17014_transfer_annuli=annuli,C17014_actual_reference_margin_mm=.4,actual_AO1_GND5_LDAC4_and_In1_annulus_passed=True,actual_grounded_input_endpoint_checks=len(local_rows),four_actual_receiving_ground_contacts_passed=True,actual_digital_bias_return_contacts_checked=len(bias_rows),actual_added_CMOS_ground_contacts_checked=len(new_ground_rows),combined_ordinary_nine_pair_reference_proof=str(ordinary_proof),combined_critical_two_pair_reference_proof=str(critical_proof),bounded_FPGA38_rule_proof=str(rule_proof),factory_exact_2oz_process_confirmation_outstanding=True,four_unused_literal_slivers_physically_removed=True,four_remaining_real_reference_resources=4,four_new_actual_HF_branches_checked=4,full_power_or_reference_qualification=False,manufacturing_ready=False)
write(P/'combined-final-circuit-proof.json',result)
inv=read(P/'independent-connectivity/review.json');hf=read(P/'combined-bypass-proof.json')
write(P/'adoption.json',dict(passed=True,adopted=True,scope='Routing WIP; actual combined AUX24, DAC reference, SOURCE-backed return bridges 101 bypass loops and nine ordinary plus two critical SOURCE-pair routes rechecked. Remaining incomplete feeds/returns/nets are not qualified.',board_sha256=sha(board),exact_source_design_sha256=sha(ROOT/'hardware/motherboard/design.json'),exact_source_netlist_sha256=sha(ROOT/'hardware/motherboard/netlist.xml'),evidence_sha256={**frozen,str(P/'combined-final-circuit-proof.json'):sha(P/'combined-final-circuit-proof.json')},physical_footprints=len(b.GetFootprints()),track_via_count=len(b.GetTracks()),zone_count=len(b.Zones()),missing_joins=inv['independent_physical_cluster_missing_joins'],native_errors=0,native_warnings=len(native['violations']),ignored_checks=[],orphan_copper_count=len(inv['orphan_copper_items']),retained_bypass_loops=hf['retained_local_loops_checked'],receiving_return_endpoints=len(hf['actual_receiving_return_anchor_reviews']),bounded_FPGA38_rule_proof=str(rule_proof),factory_exact_2oz_process_confirmation_outstanding=True,global_power_or_reference_qualification=False,manufacturing_ready=False))
write(P/'baseline-disposition.json',dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=native['violations'],ignored_checks=[]))
print(dict(adopted=True,missing_joins=inv['independent_physical_cluster_missing_joins'],actual_AUX_endpoints=len(checks),actual_bridge_groups=len(groups)))
