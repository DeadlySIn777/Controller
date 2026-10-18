"""Retained physical pad, trace and barrel group obligations, not pin aliases."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from collections import defaultdict
from pathlib import Path
from inventory import sha
HERE=Path(__file__).resolve().parent;OUT=HERE/'logic-discrete-contact-obligations-r1'
def keys(xs):return {(q['kind'],q['uuid']) for q in xs if q['kind'] in ('pad','track','via')}
def main():
    assert not OUT.exists();OUT.mkdir();base=HERE/'coupled-logic-base-r1';r=json.loads((base/'receipt.json').read_text());assert sha(base/'groups.pkl')==r['groups_sha256'];gg=pickle.loads((base/'groups.pkl').read_bytes());old,new=gg['old_groups'],gg['new_groups'];mapping={k:i for i,xs in enumerate(new) for k in keys(xs)};rows=[];missing=[]
    for i,xs in enumerate(old):
        before=keys(xs);parts=defaultdict(list)
        for k in before:
            if k not in mapping:missing.append({'old_group':i,'physical_item':list(k),'disposition':'REMOVED_OR_RETAGGED_IN_OTHER_OWNED_PROPOSAL_REQUIRES_EXACT_OWNER_LEDGER'})
            else:parts[mapping[k]].append(list(k))
        if len(parts)>1:rows.append({'old_group':i,'retained_discrete_item_count':sum(len(x) for x in parts.values()),'new_partitions':{str(k):sorted(v) for k,v in parts.items()},'partition_physical_named_pads':{str(k):sorted({(q['ref'],q['pin'],q['uuid']) for q in new[k] if q['kind']=='pad' and q['pin']}) for k in parts}})
    result={'verdict':'REPAIR_REQUIRED' if rows else 'PASS','base_receipt_sha256':sha(base/'receipt.json'),'split_retained_discrete_groups':rows,'old_discrete_items_not_retained_in_combined_proposal':missing,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'split_groups':len(rows),'partitions':[{k:len(v) for k,v in q['new_partitions'].items()} for q in rows],'missing_owned_removals':len(missing),'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
