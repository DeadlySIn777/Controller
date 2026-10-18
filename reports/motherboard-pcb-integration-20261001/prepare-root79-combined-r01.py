from pathlib import Path
p=Path(__file__).parent;dest=p/'verify-root79-combined.py';assert not dest.exists()
s=(p/'verify-root78-combined.py').read_text().replace('adopting ROOT78','adopting ROOT79')
s=s.replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-four-HF-closures-r78'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-critical7-r79'")
s=s.replace("old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/motherboard-literal38-neck-rule-candidate.kicad_pcb'","old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-four-HF-closures-r78/motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace("old.parent/'proposal.json'","ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76/proposal.json'")
s=s.replace('source26-r78-r01/domain-map.json','source26-r79-r01/domain-map.json')
needle="assert not(P/'adoption.json').exists()"
extra="""
critical_proof=P/'combined-critical-proof/review.json'
assert read(critical_proof)['passed']and read(critical_proof)['board_sha256']==sha(board)
assert read(critical_proof)['map_sha256']==sha(mp)
frozen[str(critical_proof)]=sha(critical_proof)
"""
s=s.replace(needle,needle+extra,1)
s=s.replace('and nine ordinary SOURCE-pair routes rechecked.','and nine ordinary plus two critical SOURCE-pair routes rechecked.')
s=s.replace('combined_ordinary_nine_pair_reference_proof=str(ordinary_proof),','combined_ordinary_nine_pair_reference_proof=str(ordinary_proof),combined_critical_two_pair_reference_proof=str(critical_proof),')
dest.write_text(s)
print('Prepared complete retained circuits plus exact two critical SOURCE pairs')
