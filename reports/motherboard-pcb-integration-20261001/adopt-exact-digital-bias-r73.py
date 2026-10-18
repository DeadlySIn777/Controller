"""Copy an independently checked transaction without reserializing its PCB."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_populate_motherboard_pcb import sha,write
src=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r71-digital-bias-r02';donor=src/'digital-bias-return-candidate.kicad_pcb'
dst=ROOT/'reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73'
assert not dst.exists()
names=['receipt.json','independent-native-cut-proof.json','combined-bypass-proof.json','independent-connectivity/review.json']
evidence={n:json.loads((src/n).read_text())for n in names}
assert all(v['board_sha256']==sha(donor)for v in evidence.values())
assert all(evidence[n]['passed']for n in names[:3])and evidence[names[3]]['source_net_checks_pass']and not evidence[names[3]]['orphan_copper_items']
native_files=sorted(src.glob('native-*.json'),key=lambda p:int(p.stem.split('-')[1]));native=native_files[-1];n=json.loads(native.read_text())
assert not n['ignored_checks']and all(v['severity']=='warning'for v in n['violations'])and n['violations']==evidence['receipt.json']['remaining_native_warnings']
dst.mkdir();target=dst/'motherboard-source26-WIP.kicad_pcb';shutil.copyfile(donor,target)
for ext in('.kicad_pro','.kicad_dru'):shutil.copyfile(donor.with_suffix(ext),target.with_suffix(ext))
for p in src.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,dst/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,dst/p.name)
for name in names:
 path=dst/name;path.parent.mkdir(exist_ok=True);shutil.copyfile(src/name,path)
shutil.copyfile(native,dst/'drc.json')
assert sha(target)==sha(donor)
write(dst/'baseline-disposition.json',dict(board_sha256=sha(target),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=n['violations'],ignored_checks=[]))
write(dst/'candidate-copy-receipt.json',dict(passed=True,identical_native_PCB_bytes=True,board_sha256=sha(target),donor_board=str(donor),evidence_sha256={str(src/name):sha(src/name)for name in names},native_DRC_sha256=sha(native),pending_combined_circuit_proof=True,manufacturing_ready=False))
print(dict(copied=True,board_sha256=sha(target),missing_joins=evidence[names[3]]['independent_physical_cluster_missing_joins']))
