"""Remove an unsuccessful placement from the bounded two-loop donor."""
from pathlib import Path
import sys,copy,shutil,subprocess,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_merge_bounded_pcb_delta import parse,dump,children,reference,without_generated_fills,dump_board,CLI
from hardware_populate_motherboard_pcb import sha,write
parent=Path('reports/motherboard-return-zoning-20261001')
baseline=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb')
donor=parent/'ROOT101-three-moved-same-side-routing-r05/owned-bypass-loop-candidate.kicad_pcb'
assert sha(baseline)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
assert sha(donor)=='be01db655862d3748c121f0efba63b6108826a13b834ec2e278a0cb43f4bd442'
out=parent/'ROOT101-two-same-side-bypass-restored-r06';out.mkdir(exist_ok=False)
dest=out/'motherboard-two-same-side-bypass-candidate.kicad_pcb'
frozen={str(p):sha(p)for p in(baseline,donor,Path(__file__))}
trees=[parse(without_generated_fills(p.read_text()))for p in(baseline,donor)]
fps=[{reference(f):f for f in children(t,'footprint')}for t in trees]
assert {r for r in fps[0]if dump(fps[0][r])!=dump(fps[1][r])}=={'C13006','C13007','C13011'}
trees[1][trees[1].index(fps[1]['C13011'])]=copy.deepcopy(fps[0]['C13011'])
for p in donor.parent.iterdir():
 if p.is_dir()and p.suffix=='.pretty':shutil.copytree(p,out/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,out/p.name)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(donor.with_suffix(suffix),dest.with_suffix(suffix))
dest.write_text(dump_board(trees[1]))
r=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True)
(out/'drc.txt').write_text(r.stdout+r.stderr)
assert not r.returncode
drc=json.loads((out/'drc.json').read_text());assert not drc['violations']and not drc['ignored_checks']
actual=parse(without_generated_fills(dest.read_text()));now={reference(f):f for f in children(actual,'footprint')}
assert dump(now['C13011'])==dump(fps[0]['C13011'])
assert {r for r in fps[0]if dump(fps[0][r])!=dump(now[r])}=={'C13006','C13007'}
b=pcbnew.LoadBoard(str(dest));b.BuildConnectivity()
write(out/'receipt.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),restored_exact_footprint='C13011',retained_poses=['C13006','C13007'],native_DRC_violations=0,ignored_checks=[],remaining_required_joins=b.GetConnectivity().GetUnconnectedCount(),not_yet_adopted=True,manufacturing_ready=False))
print((out/'receipt.json').read_text(),flush=True)
