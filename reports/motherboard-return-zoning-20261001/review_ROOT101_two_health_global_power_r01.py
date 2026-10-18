"""Actual current health prototype against the exact qualified IO3 baseline."""
from pathlib import Path
import argparse,sys,importlib.util,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
P=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py')
BASE=Path('reports/motherboard-pcb-integration-20261001/IO3-BankA-complete-antipad-cleanup-baseline-r99a-r02/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb')
assert sha(P)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
assert sha(BASE)=='3990f4918ff9b3c672e28eaeb098806093ac9b6dae2f2fe84dfefd972ea5731b'
spec=importlib.util.spec_from_file_location('frozen_power_r07',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
inputs={str(q):sha(q)for q in[P,BASE,a.board,Path(__file__)]}
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(a.board))
try:r=m.review(before,after)
except Exception as e:
 write(a.out,dict(passed=False,input_sha256=inputs,board_sha256=sha(a.board),error=str(e),guard_unchanged=True,Source_or_pcb_mutated=False));raise
assert all(sha(q)==h for q,h in inputs.items());r.update(input_sha256=inputs,board_sha256=sha(a.board),baseline_sha256=sha(BASE),frozen_guard_unchanged=True,Source_or_pcb_mutated=False);write(a.out,r);print(json.dumps(dict(passed=r['passed'],board_sha256=r['board_sha256'])),flush=True)
