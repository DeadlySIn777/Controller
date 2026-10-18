"""Recheck actual combined geometry before adopting ROOT69 as routing WIP."""
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
P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69'
board=P/'motherboard-bounded-merged-candidate.kicad_pcb'
old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'
R=ROOT/'reports/motherboard-return-zoning-20261001'
mp=ROOT/'reports/motherboard-domains-20261001/source26-r69-r01/domain-map.json'
aux=ROOT/'reports/motherboard-power-entry-20261001/aux24-field-cell-r68/receipt.json'
ao=R/'source26-r61-AO1-DAC-return-r04/receipt.json'
status=R/'source26-r62-field-status-ground-delivery-r02/receipt.json'
transfer=R/'source26-r62-C17014-field-return-reroute-r01/receipt.json'
bridges=R/'source26-r61-orphan-bridge-retirement-r01/all-retained-new-bridge-source-witnesses.json'
paths=[board,old,mp,aux,ao,status,transfer,bridges,P/'combined-bypass-proof.json',P/'independent-connectivity/review.json',P/'drc.json',Path(__file__)]
frozen={str(p):sha(p)for p in paths};read=lambda p:json.loads(p.read_text())
assert not(P/'adoption.json').exists()
for p in (P/'combined-bypass-proof.json',P/'independent-connectivity/review.json'):
 assert read(p)['board_sha256']==sha(board)
assert read(P/'combined-bypass-proof.json')['passed']
assert read(P/'independent-connectivity/review.json')['source_net_checks_pass']
native=read(P/'drc.json');assert not native['ignored_checks'] and all(v['severity']=='warning'for v in native['violations'])
b=pcbnew.LoadBoard(str(board));b.BuildConnectivity();before=pcbnew.LoadBoard(str(old));prior=clusters_preserved(source_clusters(before),b)
co=b.GetConnectivity();ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
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
result=dict(passed=True,input_sha256=frozen,board_sha256=sha(board),prior_SOURCE_clusters=prior,actual_AUX24_endpoints=checks,actual_SOURCE_bridge_witnesses=witnesses,actual_C17014_transfer_annuli=annuli,C17014_actual_reference_margin_mm=.4,actual_AO1_GND5_LDAC4_and_In1_annulus_passed=True,full_power_or_reference_qualification=False,manufacturing_ready=False)
write(P/'combined-final-circuit-proof.json',result)
inv=read(P/'independent-connectivity/review.json');hf=read(P/'combined-bypass-proof.json')
write(P/'adoption.json',dict(passed=True,adopted=True,scope='Routing WIP; actual combined AUX24, DAC reference, SOURCE-backed return bridges and 94 bypass loops rechecked. Remaining incomplete feeds/returns/nets are not qualified.',board_sha256=sha(board),exact_source_design_sha256=sha(ROOT/'hardware/motherboard/design.json'),exact_source_netlist_sha256=sha(ROOT/'hardware/motherboard/netlist.xml'),evidence_sha256={**frozen,str(P/'combined-final-circuit-proof.json'):sha(P/'combined-final-circuit-proof.json')},physical_footprints=len(b.GetFootprints()),track_via_count=len(b.GetTracks()),zone_count=len(b.Zones()),missing_joins=inv['independent_physical_cluster_missing_joins'],native_errors=0,native_warnings=len(native['violations']),ignored_checks=[],orphan_copper_count=len(inv['orphan_copper_items']),retained_bypass_loops=hf['retained_local_loops_checked'],receiving_return_endpoints=len(hf['actual_receiving_return_anchor_reviews']),global_power_or_reference_qualification=False,manufacturing_ready=False))
print(dict(adopted=True,missing_joins=inv['independent_physical_cluster_missing_joins'],actual_AUX_endpoints=len(checks),actual_bridge_groups=len(groups)))
