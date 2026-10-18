"""Prepare independent combined checks for the copied, verified routing donor."""
from pathlib import Path
here=Path(__file__).parent
copy=here/'adopt-exact-local-CMOS-r74.py'
verify=here/'verify-root74-combined.py'
assert not copy.exists()and not verify.exists()
s=(here/'adopt-exact-digital-bias-r73.py').read_text()
s=s.replace('source26-r71-digital-bias-r02','source26-r73-plus3-CMOS-stitches-r01')
s=s.replace('digital-bias-return-candidate.kicad_pcb','exact-CMOS-ground-candidate.kicad_pcb')
s=s.replace('source26-digital-bias-returns-adopted-r73','source26-local-CMOS-returns-adopted-r74')
copy.write_text(s)
v=(here/'verify-root73-combined.py').read_text()
v=v.replace('Recheck actual combined geometry before adopting ROOT73','Recheck actual combined geometry before adopting ROOT74')
v=v.replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74'")
v=v.replace("source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb","source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb")
v=v.replace('source26-r73-r01/domain-map.json','source26-r74-r01/domain-map.json')
anchor='witnesses=review(b,groups,mapping[\'pads\'])'
assert v.count(anchor)==1
addition="""local_new=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r73-plus3-CMOS-stitches-r01'
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
"""
v=v.replace(anchor,addition+anchor)
v=v.replace('actual_digital_bias_return_contacts_checked=len(bias_rows),','actual_digital_bias_return_contacts_checked=len(bias_rows),actual_added_CMOS_ground_contacts_checked=len(new_ground_rows),')
v=v.replace('and 94 bypass loops rechecked.','and 97 bypass loops rechecked.')
verify.write_text(v)
print(dict(prepared=True,actual_source_and_prior_circuit_checks_retained=True,new_ground_checks=20,bypass_loops=97))
