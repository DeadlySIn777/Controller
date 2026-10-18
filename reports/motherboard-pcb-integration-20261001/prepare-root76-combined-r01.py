"""Recheck all routed circuits with the exactly scoped native FPGA neck rule."""
from pathlib import Path
here=Path(__file__).parent;target=here/'verify-root76-combined.py'
assert not target.exists()
s=(here/'verify-root75-combined.py').read_text()
s=s.replace('adopting ROOT75','adopting ROOT76')
s=s.replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76'")
s=s.replace("board=P/'motherboard-bounded-merged-candidate.kicad_pcb'","board=P/'motherboard-literal38-neck-rule-candidate.kicad_pcb'")
s=s.replace('source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb','source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb')
s=s.replace('source26-r75-r01/domain-map.json','source26-r76-r01/domain-map.json')
needle="assert not(P/'adoption.json').exists()"
extra="""
rule_proof=P/'review.json';rule=read(rule_proof)
assert rule['passed']and rule['board_sha256']==sha(board)
assert rule['exact_literal_signal_nets']==38 and rule['maximum_aggregate_per_net_mm']==1.
assert rule['factory_exact_2oz_process_confirmation_outstanding']
for item in(rule_proof,P/'proposal.json',board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru')):
 frozen[str(item)]=sha(item)
"""
s=s.replace(needle,needle+extra)
s=s.replace('full_power_or_reference_qualification=False,manufacturing_ready=False)','bounded_FPGA38_rule_proof=str(rule_proof),factory_exact_2oz_process_confirmation_outstanding=True,full_power_or_reference_qualification=False,manufacturing_ready=False)')
s=s.replace("global_power_or_reference_qualification=False,manufacturing_ready=False)","bounded_FPGA38_rule_proof=str(rule_proof),factory_exact_2oz_process_confirmation_outstanding=True,global_power_or_reference_qualification=False,manufacturing_ready=False)")
target.write_text(s)
print(dict(prepared=True,all_old_circuit_guards_retained=True,exact_factory_DFM_gate_retained=True))
