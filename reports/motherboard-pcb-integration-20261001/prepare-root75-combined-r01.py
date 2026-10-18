"""Require actual combined ordinary-route proof before ROOT75 adoption."""
from pathlib import Path
here=Path(__file__).parent;target=here/'verify-root75-combined.py'
assert not target.exists()
s=(here/'verify-root74-combined.py').read_text()
s=s.replace('adopting ROOT74','adopting ROOT75')
s=s.replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75'")
s=s.replace("board=P/'motherboard-source26-WIP.kicad_pcb'","board=P/'motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace('source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb','source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
s=s.replace('source26-r74-r01/domain-map.json','source26-r75-r01/domain-map.json')
needle="assert not(P/'adoption.json').exists()"
extra="""
ordinary_proof=P/'combined-ordinary-proof/review.json'
assert read(ordinary_proof)['passed']and read(ordinary_proof)['board_sha256']==sha(board)
assert read(ordinary_proof)['map_sha256']==sha(mp)
frozen[str(ordinary_proof)]=sha(ordinary_proof)
"""
s=s.replace(needle,needle+extra)
s=s.replace('actual_added_CMOS_ground_contacts_checked=len(new_ground_rows),','actual_added_CMOS_ground_contacts_checked=len(new_ground_rows),combined_ordinary_nine_pair_reference_proof=str(ordinary_proof),')
s=s.replace('and 97 bypass loops rechecked.','97 bypass loops and nine ordinary SOURCE-pair routes rechecked.')
s=s.replace("print(dict(adopted=True,", "write(P/'baseline-disposition.json',dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=native['violations'],ignored_checks=[]))\nprint(dict(adopted=True,")
target.write_text(s)
print(dict(prepared=True,new_pairs=9,complete_prior_circuit_guard_retained=True))
