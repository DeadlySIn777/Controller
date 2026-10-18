"""Apply frozen native power guard after the separately reviewed unused-pour disposition.

This is relative geometric preservation, not complete rail/thermal qualification.
The immutable r99a disposition and its native review remain prerequisites; independent peer review is separately required for adoption.
"""
from pathlib import Path
import sys,json,argparse
sys.path[:0]=[str(Path('tools').resolve()),str(Path('reports/motherboard-ordinary-routing-20261001').resolve())]
import pcbnew
import check_io3_backbone_preservation_r07 as power
from hardware_populate_motherboard_pcb import sha,write
ap=argparse.ArgumentParser()
for k in ('board','out'):ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args()
assert not a.out.exists()
root=Path('reports/motherboard-pcb-integration-20261001')
before=root/'IO3-BankA-complete-antipad-cleanup-baseline-r99a-r02/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb'
review=Path('reports/motherboard-pcb-integration-20261001/IO3-BankA-complete-antipad-cleanup-review-r99c/receipt.json')
assert sha(before)=='3990f4918ff9b3c672e28eaeb098806093ac9b6dae2f2fe84dfefd972ea5731b'
assert sha(review)=='335ddd1cce07f09d832cd19ae31f70ffd223abf3c614b532f4d2a6cdeccbafdc'
assert json.loads(review.read_text())['passed']
assert sha(power.__file__)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
files=[before,a.board,review,Path(power.__file__),Path(__file__),Path('hardware/motherboard/design.json')]
frozen={str(p.resolve()):sha(p)for p in files}
b=pcbnew.LoadBoard(str(before));current=pcbnew.LoadBoard(str(a.board))
b.BuildConnectivity();current.BuildConnectivity()
result=power.review(b,current)
assert result['passed']
assert all(sha(p)==h for p,h in frozen.items())
result.update(input_sha256=frozen,board_sha256=sha(a.board),relative_full_cleanup_baseline_to_current_geometry_only=True,global_rail_ampacity_or_thermal_qualification=False,manufacturing_ready=False)
write(a.out,result)
print(json.dumps(dict(passed=True,board_sha256=sha(a.board),scope='Exact r99a cleanup baseline to actual current IO3/CORE relative geometry')))
