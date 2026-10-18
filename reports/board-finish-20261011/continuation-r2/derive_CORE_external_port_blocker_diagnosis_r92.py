"""Fix attribution metadata field names only; preserve R90 geometry exactly."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'diagnose_CORE_external_port_blockers_r91.py';source=p.read_text();changes=[]
for old,new,count in [("UUID=q[\"source\"].get(\"uuid\")","UUID=q['uuid']",1),("pin=pad['pin']","pin=pad['num']",2),("CORE-ordinary-external-fill-port-blocker-diagnosis-r91","CORE-ordinary-external-fill-port-blocker-diagnosis-r92",1),("R91_BLOCKERS","R92_BLOCKERS",1),("R91_EXACT_BLOCKER_ATTRIBUTION_FROZEN","R92_EXACT_BLOCKER_ATTRIBUTION_FROZEN",1)]:
 assert source.count(old)==count,(old,source.count(old));source=source.replace(old,new);changes.append({'old':old,'new':new,'count':count})
compile(source,'diagnose_CORE_external_port_blockers_r92.py','exec');out=H/'diagnose_CORE_external_port_blockers_r92.py';assert not out.exists();out.write_text(source)
(H/'CORE-external-port-blocker-diagnosis-r92-derivation.json').write_text(json.dumps({'base_script_sha256':sha(p),'new_script_sha256':sha(out),'changes':changes,'prior_failure':'R91 metadata expected source for pads; actual record has direct uuid','geometry_predicates_unchanged':True,'exact_R90_final_region_WKB_assertions_retained':True},indent=1)+'\n')
print('R92_ATTRIBUTION_DERIVED',sha(out),flush=True)
