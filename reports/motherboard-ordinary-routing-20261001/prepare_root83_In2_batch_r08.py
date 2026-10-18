"""Bounded F/In2 SOURCE pairs; every resulting plane change remains pending."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root81_OUT_PERMIT_pair_r06.py').read_text()
s=s.replace('source26-C19042-local-bypass-r81','source26-reference-closure-and-spurs-r83').replace('source26-r81-r01/domain-map.json','source26-r83-r01/domain-map.json')
s=s.replace("if pair=={'R14401.1','U14402.1'}:\n            assert name=='/mc_permission/OUT_PERMIT'", "if 0<length<=25:")
s=s.replace('if len(groups)>=12:break','if len(groups)>=8:break')
s=s.replace('motherboard-OUT-PERMIT-common-In1-candidate.kicad_pcb','motherboard-ordinary-In2-batch-candidate.kicad_pcb')
(p/'route_root83_In2_batch_r08.py').write_text(s);compile(s,str(p/'route_root83_In2_batch_r08.py'),'exec')
