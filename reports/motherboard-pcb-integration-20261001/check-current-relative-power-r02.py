"""Apply frozen native power guard after the separately reviewed unused-pour disposition.

This is relative geometric preservation, not complete rail/thermal qualification.
The immutable r95a disposition and its independent review remain prerequisites.
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
before=root/'IO3-BankA-unused-pour-cleanup-baseline-r95a/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb'
review=Path('reports/motherboard-return-zoning-20261001/BankA-IO3-width-cleanup-independent-r01/receipt.json')
assert sha(before)=='fda233cbe5e176b4b134b01756a0463ccfa1fdf07663806b669608cdc1269146'
assert sha(review)=='616279d843f4c556a093c26e14f56c04eda405baa8dbc31a98e68a22ae6403b5'
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
print(json.dumps(dict(passed=True,board_sha256=sha(a.board),scope='Exact r95a cleanup baseline to actual current IO3/CORE relative geometry')))
