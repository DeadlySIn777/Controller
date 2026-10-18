"""Read-only physical source-root census after frozen native-bound38 planes."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from inventory import sha
HERE=Path(__file__).resolve().parent;OUT=HERE/'remaining-field-ground-r6';assert not OUT.exists();OUT.mkdir();gp=HERE/'native-bound-field-contact-audit-r5/groups.pkl';r=json.loads((gp.parent/'receipt.json').read_text());assert sha(gp)==r['groups_sha256'];gg=pickle.loads(gp.read_bytes());rows=[]
for bank,net,source in [('FAG','/motherboard_motors/FIELD_GND','J11003'),('FBG','/motherboard_do/FIELD_B_0V','J11005')]:
    groups=gg[net];root=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(source,'2') for q in xs));unrooted=[]
    for i,xs in enumerate(groups):
        pads=sorted({(q['ref'],q['pin'],q['uuid']) for q in xs if q['kind']=='pad' and q['pin']})
        if i!=root and pads:unrooted.append({'group':i,'pads':pads,'layers':sorted({q['layer'] for q in xs}),'physical_items':len({(q['kind'],q['uuid']) for q in xs if q['kind']!='fill'})})
    row={'bank':bank,'net':net,'source':source+'.2','source_group':root,'source_rooted_named_pads':len({(q['ref'],q['pin'],q['uuid']) for q in groups[root] if q['kind']=='pad' and q['pin']}),'remaining_groups':unrooted};rows.append(row);print(json.dumps(row))
receipt={'verdict':'EXACT_NATIVE_BOUND_HOST_CENSUS_REMAINING_GROUND_JOINS_REQUIRED','bound_contact_audit_sha256':sha(gp.parent/'receipt.json'),'rows':rows,'native_jobs':0};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'))
