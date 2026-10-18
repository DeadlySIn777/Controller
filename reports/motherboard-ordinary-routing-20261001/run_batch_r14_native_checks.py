"""Fresh native refill and independent checks; immutable failures remain reports."""
from pathlib import Path
import subprocess,sys,json,concurrent.futures
p=Path(__file__).parent;out=p/'actual-source26-root83-In2-batch-r14';board=out/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
py='C:/Program Files/KiCad/10.0/bin/python.exe';cli='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
assert board.is_file()
def run(name,args):
 with(out/(name+'-command.txt')).open('w')as log:result=subprocess.run([str(v)for v in args],stdout=log,stderr=subprocess.STDOUT)
 return dict(name=name,exit_code=result.returncode)
rows=[run('native',[cli,'pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',out/'native.json',board])]
drc=json.loads((out/'native.json').read_text());assert not drc['violations']and not drc['ignored_checks'],drc['violations']
rows.append(run('fresh-map',[py,'tools/hardware_map_motherboard_domains.py','--board',board,'--source','hardware/motherboard','--out',out/'fresh-domain-map']))
assert rows[-1]['exit_code']==0
validator=p/'verify_root83_In2_batch_r14.py';assert validator.exists()
jobs=[('actual-source-return-power-proof',[py,validator]),
 ('independent-inventory',[py,'tools/motion_card_routing_inventory.py','--board',board,'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',out/'independent-connectivity']),
 ('old101-native-bypass',[py,'tools/hardware_verify_owned_bypass_batch.py','--board',board,'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt','reports/motherboard-owned-bypass-routing-20261001/source26-r76-strict-same-side-r01/combined101-bypass-manifest.json','--out',out/'old101-native-bypass-proof.json'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows.extend(pool.map(lambda j:run(*j),jobs))
(out/'native-check-command-results.json').write_text(json.dumps(dict(commands=rows,passed=all(r['exit_code']==0 for r in rows)),indent=2))
print(json.dumps(rows));sys.exit(0 if all(r['exit_code']==0 for r in rows)else 1)
