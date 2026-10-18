"""Extend the exact paired-return search to current-source reviewed DI/faults."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'new_via_escape_ground_r5.py';raw=source.read_text(encoding='utf-8')
    old="old = json.loads(F.read(HERE / 'ordinary-routes-r1/result.json'))"
    if raw.count(old)!=1:raise ValueError('One exact input read expected')
    raw=raw.replace(old,"old = json.loads(F.read(HERE / 'current-di-fault-routes-r1/result.json'))\n    policy = json.loads(F.read(HERE / 'current-di-fault-routes-r1/current-source-policy.json'))\n    controlled = json.loads(F.read(F.BASE / 'controlled-geometry/controlled-net-map.json'))\n    selected = {S.norm(r['net']):r for r in policy['rows']}\n    if set(S.norm(r['net']) for r in old['results']) != set(selected):raise ValueError('Exact current-source policy mismatch')\n    if set(selected).intersection(S.norm(n) for n in controlled):raise ValueError('Controlled nets excluded from ordinary search')\n    if any(any(p['pintype'] in ('power_in','power_out') for p in r['current_source_ports']) for r in selected.values()):raise ValueError('Power pins excluded')")
    derived=HERE/'new_via_escape_current_ground_r6.py'
    wrapper_source=HERE/'continue_ordinary_escapes_r5.py';wraw=wrapper_source.read_text(encoding='utf-8')
    if wraw.count('import new_via_escape_ground_r5 as R')!=1:raise ValueError('One derived module binding expected')
    wraw=wraw.replace('import new_via_escape_ground_r5 as R','import new_via_escape_current_ground_r6 as R').replace("R.OUT=HERE/'new-via-escape-r5'","R.OUT=HERE/'current-ground-escape-r6'")
    wrapper=HERE/'route_current_ground_escape_r6.py'
    if derived.exists() or wrapper.exists():raise ValueError('Fresh files required')
    derived.write_text(raw,encoding='utf-8');wrapper.write_text(wraw,encoding='utf-8')
    receipt={'original_search':str(source),'original_sha256':sha(source),'derived_search':str(derived),'derived_sha256':sha(derived),'original_wrapper':str(wrapper_source),'original_wrapper_sha256':sha(wrapper_source),'wrapper':str(wrapper),'wrapper_sha256':sha(wrapper),'changes':['Use exactly the26 current-source reviewed DI/fault/reset ordinary nets','Reject any selected net present in the controlled geometry map or any source power pin','All original paired return/hole/clearance/width/layer/finite search criteria retained'],'native_jobs':0,'board_emitted':False,'adopted':False}
    (HERE/'current-ground-escape-derivation-r6.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
