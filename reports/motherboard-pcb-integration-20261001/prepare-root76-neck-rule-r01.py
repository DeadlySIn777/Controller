"""Prepare an exact rebase of the independently verified FPGA38 rule."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
here=Path(__file__).parent;old=root/'reports/motherboard-critical-routing-20261001'
base='reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb'
out='reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76'
for first,last in [('rebase_fpga_neck_root73.py','rebase-fpga-neck-root76.py'),('validate_rebased_fpga_neck_root73.py','validate-fpga-neck-root76.py')]:
 target=here/last;assert not target.exists()
 s=(old/first).read_text().replace('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb',base).replace('reports/motherboard-critical-routing-20261001/source26-root73-BGA-neck-rule-r07',out)
 s=s.replace('!=3645','!=3612').replace('=3645','=3612')
 s=s.replace("if f.is_dir()and f.suffix=='.pretty':","if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):")
 if first.startswith('rebase_'):
  s=s.replace("OUT=Path(","accepted=e.read(BASE.parent/'adoption.json');assert accepted['passed']and accepted['adopted']and accepted['board_sha256']==e.sha(BASE)\nOUT=Path(",1)
  s=s.replace("newrules=n.proposed_rules(set(proposal['nets']));", "newrules=n.proposed_rules(set(proposal['nets']));assert newrules==e.read('reports/motherboard-critical-routing-20261001/source26-root73-BGA-neck-rule-r07/proposal.json')['appended_DRC_rules'];")
 target.write_text(s)
print(dict(prepared=True,exact_frozen_rule_append_required=True))
