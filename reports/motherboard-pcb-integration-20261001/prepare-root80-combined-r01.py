from pathlib import Path
p=Path(__file__).parent;dest=p/'verify-root80-combined.py';assert not dest.exists()
s=(p/'verify-root79-combined.py').read_text().replace('adopting ROOT79','adopting ROOT80')
s=s.replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-critical7-r79'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-two-ground-contacts-r80'")
s=s.replace("old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-four-HF-closures-r78/motherboard-bounded-merged-candidate.kicad_pcb'","old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-critical7-r79/motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace('source26-r79-r01/domain-map.json','source26-r80-r01/domain-map.json')
s=s.replace("len(resources['unanchored_components'])==4","len(resources['unanchored_components'])==2")
s=s.replace('four_remaining_real_reference_resources=4','remaining_real_reference_resources=2')
needle='witnesses=review(b,groups,mapping[\'pads\'])'
extra="""
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
"""
assert s.count(needle)==1;s=s.replace(needle,extra+'\n'+needle,1)
s=s.replace('four_new_actual_HF_branches_checked=4,','four_new_actual_HF_branches_checked=4,two_actual_inner_ground_contacts_checked=True,')
dest.write_text(s)
print('Prepared complete retained circuits plus two actual inner ground contacts')
