"""Retain every prior circuit check and add exact sliver/four-loop transaction."""
from pathlib import Path
p=Path(__file__).parent;dest=p/'verify-root78-combined.py';assert not dest.exists()
s=(p/'verify-root76-combined.py').read_text()
s=s.replace('adopting ROOT76','adopting ROOT78')
s=s.replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-four-HF-closures-r78'")
s=s.replace("board=P/'motherboard-literal38-neck-rule-candidate.kicad_pcb'","board=P/'motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace('source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb','source26-FPGA38-rule-r76/motherboard-literal38-neck-rule-candidate.kicad_pcb')
s=s.replace('source26-r76-r01/domain-map.json','source26-r78-r01/domain-map.json')
s=s.replace("rule_proof=P/'review.json'","rule_proof=P/'retained-FPGA38-rule-proof.json'")
s=s.replace("rule_proof,P/'proposal.json'","rule_proof,old.parent/'proposal.json'")
s=s.replace('return bridges 97 bypass loops','return bridges 101 bypass loops')
needle="assert not(P/'adoption.json').exists()"
extra="""
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
"""
s=s.replace(needle,needle+extra)
needle="\nchecks=[]\n"
extra="""
from hardware_route_logic_return import identity
literal_donor=pcbnew.LoadBoard(str(strict4/'owned-bypass-loop-candidate.kicad_pcb'))
donor_Cu={t.m_Uuid.AsString():identity(t)for t in literal_donor.GetTracks()}
new9=read(strict4/'bounded-scope.json')['reviewed_copper_delta_UUIDs'];assert len(new9)==9
assert all(identity(cu[u])==donor_Cu[u]for u in new9)
"""
assert s.count(needle)==1
s=s.replace(needle,extra+'\n'+needle,1)
s=s.replace('full_power_or_reference_qualification=False,','four_unused_literal_slivers_physically_removed=True,four_remaining_real_reference_resources=4,four_new_actual_HF_branches_checked=4,full_power_or_reference_qualification=False,')
dest.write_text(s)
print(dict(prepared=True,all_prior_circuit_checks_retained=True,additional_loops=4,all_required_loops=101))
