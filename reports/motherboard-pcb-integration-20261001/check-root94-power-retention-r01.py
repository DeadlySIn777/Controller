"""Apply unchanged relative IO3/CORE guard to the complete ROOT87-to94 delta."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path('reports/motherboard-ordinary-routing-20261001').resolve())]
import pcbnew
import check_io3_backbone_preservation_r07 as power
from hardware_populate_motherboard_pcb import sha,write
root=Path('reports/motherboard-pcb-integration-20261001')
before=root/'source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb'
after=root/'source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb'
assert sha(before)=='0a9e4975b2d9cd90f7853884d626427fb089809c45ae5ed749472c68235e2d13'
assert sha(power.__file__)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
files=[before,after,Path(power.__file__),Path(__file__),Path('hardware/motherboard/design.json')]
frozen={str(p):sha(p)for p in files}
b=pcbnew.LoadBoard(str(before));a=pcbnew.LoadBoard(str(after));b.BuildConnectivity();a.BuildConnectivity()
result=power.review(b,a);assert result['passed']
assert all(sha(p)==h for p,h in frozen.items())
write(after.parent/'current-full-delta-power-proof.json',dict(**result,input_sha256=frozen,board_sha256=sha(after),relative_full_ROOT87_to_ROOT94_geometry_only=True,global_rail_ampacity_or_thermal_qualification=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,scope='Full ROOT87-to94 IO3/CORE relative geometry')))
