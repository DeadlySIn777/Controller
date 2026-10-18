"""Bind the unchanged relative IO3 guard to the independently reviewed exact unused-pour baseline."""
from pathlib import Path
import argparse,sys,json
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-ordinary-routing-20261001')]
import pcbnew
import check_io3_backbone_preservation_r07 as guard
from hardware_map_motherboard_domains import sha,write
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
R=Path('reports/motherboard-return-zoning-20261001');B=R/'health-IO3-baseline-cleanup-r02/motherboard-health-unused-IO3-candidate.kicad_pcb';P=R/'health-IO3-baseline-cleanup-independent-r01/receipt.json';review=json.loads(P.read_text());assert review['passed']and review['board_sha256']==sha(B)=='1719e13d17336716b59078007447706f692abb9d0a6a9efb9bc9a23454b7e365'
assert sha(guard.__file__)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
inputs={str(q):sha(q)for q in(B,P,a.board,Path(__file__),Path(guard.__file__),guard.SOURCE,guard.FEEDS)}
try:proof=guard.review(pcbnew.LoadBoard(str(B)),pcbnew.LoadBoard(str(a.board)))
except Exception as e:write(a.out,dict(passed=False,error=str(e),board_sha256=sha(a.board),input_sha256=inputs,frozen_guard_unchanged=True,no_automatic_waiver=True));raise
assert all(sha(Path(q))==h for q,h in inputs.items());proof.update(board_sha256=sha(a.board),input_sha256=inputs,baseline_sha256=sha(B),independent_baseline_review_sha256=sha(P),frozen_guard_unchanged=True,all_current_loaded_capacity_or_thermal_qualified=False,manufacturing_ready=False);write(a.out,proof);print(json.dumps(dict(passed=True,board_sha256=sha(a.board))))
