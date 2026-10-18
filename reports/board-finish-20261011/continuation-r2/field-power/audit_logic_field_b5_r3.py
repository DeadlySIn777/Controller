"""Independent full prospective contact audit, now including the exact B5 supply repair."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
HERE=Path(__file__).resolve().parent;path=HERE/'audit_logic_field_repairs_r2.py';text=path.read_text()
text=text.replace("OUT=HERE/'logic-field-mutual-contact-audit-r2'","OUT=HERE/'logic-field-b5-mutual-contact-audit-r3'")
text=text.replace("adds+=fieldadd", "adds+=fieldadd;sp=HERE/'b5-contact-repair-r3-frozen';sr=json.loads((sp/'receipt.json').read_text());assert sha(sp/'proposed-zones.pkl')==sr['proposal_sha256'];adds+=pickle.loads((sp/'proposed-zones.pkl').read_bytes())")
text=text.replace("'field_repair_receipt_sha256':sha(fp/'receipt.json'),", "'field_repair_receipt_sha256':sha(fp/'receipt.json'),'b5_repair_receipt_sha256':sha(sp/'receipt.json'),")
exec(compile(text,str(path),'exec'))
