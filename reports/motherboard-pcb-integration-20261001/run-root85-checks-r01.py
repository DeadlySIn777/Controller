"""Fresh independent native combined-board circuit checks with bounded concurrency."""
from pathlib import Path
import concurrent.futures,subprocess,json,hashlib,sys
root=Path(__file__).resolve().parents[2];p=root/'reports/motherboard-pcb-integration-20261001/source26-seven-path-IO3-tip-trial-r85'
board=p/'motherboard-bounded-merged-candidate.kicad_pcb';mp=root/'reports/motherboard-domains-20261001/source26-r85-r01/domain-map.json';drc=p/'drc.json'
py='C:/Program Files/KiCad/10.0/bin/python.exe'
with(p/'map-command.log').open('w')as stream:
 result=subprocess.run([py,'tools/hardware_map_motherboard_domains.py','--board',str(board),'--source','hardware/motherboard','--out',str(mp.parent)],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
assert result.returncode==0
common=['--board',str(board),'--map',str(mp),'--drc',str(drc)]
jobs=[
 ('old101', ['tools/hardware_verify_owned_bypass_batch.py','--board',str(board),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt','reports/motherboard-owned-bypass-routing-20261001/source26-r76-strict-same-side-r01/combined101-bypass-manifest.json','--out',str(p/'combined-bypass-proof.json')]),
 ('ordinary9',['reports/motherboard-ordinary-routing-20261001/verify_ordinary_donor_combined.py',*common,'--out',str(p/'combined-ordinary-proof')]),
 ('critical2',['reports/motherboard-critical-routing-20261001/verify_local_critical_combined.py',*common,'--out',str(p/'combined-critical-proof')]),
 ('AO1',['reports/motherboard-critical-routing-20261001/verify_AO1_SDO_combined.py',*common,'--out',str(p/'combined-AO1-verification')]),
 ('C19042',['reports/motherboard-return-zoning-20261001/check_C19042_combined_native_r01.py',*common,'--out',str(p/'combined-C19042-proof.json')]),
 ('C14804',['reports/motherboard-owned-bypass-routing-20261001/verify-C14804-combined-native-r01.py',*common,'--out',str(p/'combined-C14804-proof.json')]),
 ('resources',['tools/hardware_validate_motherboard_return_planes_r06.py','--board',str(board),'--map',str(mp),'--out',str(p/'literal-reference-resources.json')]),
 ('FPGA38',['reports/motherboard-pcb-integration-20261001/check-retained-FPGA38-rule-r01.py','--board',str(board),'--out',str(p/'retained-FPGA38-rule-proof.json')]),
 ('seven-new-ordinary',['reports/motherboard-ordinary-routing-20261001/verify_seven_pair_combined_r15.py',*common,'--out',str(p/'combined-seven-pair-proof')]),
 ('inventory',['tools/motion_card_routing_inventory.py','--board',str(board),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(p/'independent-connectivity')]),
]
sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
inputs={str(q):sha(q)for q in(board,mp,drc,root/'hardware/motherboard/design.json',root/'hardware/motherboard/netlist.xml',Path(__file__))}
def run(job):
 name,args=job;log=p/(name+'-command.log')
 with log.open('w',encoding='utf8')as stream:r=subprocess.run([py,*args],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 return dict(name=name,command=[py,*args],returncode=r.returncode,log_sha256=sha(log))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
 results=[]
 for result in pool.map(run,jobs):results.append(result);print(json.dumps({k:result[k]for k in('name','returncode')}),flush=True)
assert all(sha(q)==h for q,h in inputs.items())
(p/'native-check-command-results.json').write_text(json.dumps(dict(all_commands_completed=all(r['returncode']==0 for r in results),exact_inputs_unchanged=True,input_sha256=inputs,results=results,individual_report_results_still_require_review=True),indent=2))
sys.exit(0 if all(r['returncode']==0 for r in results)else 1)
