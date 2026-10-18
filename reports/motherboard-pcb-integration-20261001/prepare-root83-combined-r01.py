"""Preserve ROOT82 checks and prove OUT9, C14804, and obsolete-stub closure."""
from pathlib import Path
p=Path(__file__).parent
s=(p.parent/'motherboard-critical-routing-20261001/verify-root82-combined.py').read_text()
s=s.replace('ROOT82','ROOT83')
s=s.replace("P=ROOT/'reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root81-composed-r01'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83'")
s=s.replace("old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb'","old=ROOT/'reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root81-composed-r01/motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace('source26-AO1-SDO-root81-composed-r01/domain-map.json','source26-r83-r01/domain-map.json')
s=s.replace("P/'retained-C19042-proof.json'","P/'combined-C19042-proof.json'")
s=s.replace("assert len(resources['unanchored_components'])==1","assert len(resources['unanchored_components'])==0 and resources['passed']")
s=s.replace('remaining_real_reference_resources=1','remaining_real_reference_resources=0')
s=s.replace("merger=read(P/'receipt.json');retired=merger['exact_literal_same_net_AO1_retirement']","merger=read(old.parent/'receipt.json');frozen[str(old.parent/'receipt.json')]=sha(old.parent/'receipt.json');retired=merger['exact_literal_same_net_AO1_retirement']")
anchor='\nchecks=[]\n';assert s.count(anchor)==1
s=s.replace(anchor,"""
adjacent_proof=P/'combined-C14804-proof.json';adjacent=read(adjacent_proof)
assert adjacent['passed'] and adjacent['board_sha256']==sha(board) and adjacent['map_sha256']==sha(mp)
assert adjacent['negative_actual_supply_copper_cut_rejected']
frozen[str(adjacent_proof)]=sha(adjacent_proof)
stub=R/'source26-r81-two-redundant-ground-spurs-r01'
assert read(stub/'receipt.json')['passed'] and read(stub/'old101-native-bypass-proof.json')['passed']
assert not set(read(stub/'receipt.json')['removed_exact_obsolete_Cu'])&set(cu)
for row in read(stub/'receipt.json')['retained_actual_ground_routes']:
 pad=ps[row['ref'],row['pin']];via=cu[row['actual_retained_via']]
 assert pad.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(via)}
 for layer in row['actual_flashed_native_reference_contacts']:assert physical_reference_contact(via,b.GetLayerID(layer),co)
for item in(stub/'receipt.json',stub/'old101-native-bypass-proof.json',stub/'bounded-scope.json'):
 frozen[str(item)]=sha(item)
assert not native['violations'] and not native['ignored_checks']
"""+anchor)
anchor='witnesses=review(b,groups,mapping[\'pads\'])';assert s.count(anchor)==1
s=s.replace(anchor,"""out9=R/'source26-r74-OUT9-external-ground-transfer-review-r02'
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
 evidence=P.parent/folder/'receipt.json';frozen[str(evidence)]=sha(evidence)
"""+anchor)
s=s.replace('full_power_or_reference_qualification=False,manufacturing_ready=False)','all187_reference_resources_actually_SOURCE_anchored=True,separate_C14804_adjacent_only_proof=str(adjacent_proof),two_obsolete_ground_stubs_retired_without_SOURCE_disconnect=True,full_power_or_reference_qualification=False,manufacturing_ready=False)')
s=s.replace('retained_bypass_loops=hf[\'retained_local_loops_checked\'],','retained_bypass_loops=hf[\'retained_local_loops_checked\'],additional_adjacent_only_C14804_bypass_proof=str(adjacent_proof),all187_reference_resources_actually_SOURCE_anchored=True,')
(p/'verify-root83-combined.py').write_text(s);compile(s,str(p/'verify-root83-combined.py'),'exec')
