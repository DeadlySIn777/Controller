"""Frozen relative IO3/CORE proof on the exact additive stationary batch."""
from pathlib import Path
import sys,importlib.util,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
P=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py')
spec=importlib.util.spec_from_file_location('strict_power',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-C11087-health-merged-r93/motherboard-bounded-merged-candidate.kicad_pcb')
A=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-actual-r01/owned-bypass-loop-candidate.kicad_pcb')
O=A.parent/'actual-IO3-relative-power-proof.json'
assert not O.exists()
before=pcbnew.LoadBoard(str(B));after=pcbnew.LoadBoard(str(A))
try:
    r=m.review(before,after)
except (ValueError,AssertionError)as e:
    r=dict(passed=False,error=str(e),frozen_power_guard_unchanged=True,manufacturing_ready=False)
r.update(before_board_sha256=sha(B),board_sha256=sha(A),frozen_checker_sha256=sha(P))
write(O,r);print(json.dumps({k:v for k,v in r.items()if not isinstance(v,(dict,list))}))
if not r['passed']:
    raise SystemExit(1)
