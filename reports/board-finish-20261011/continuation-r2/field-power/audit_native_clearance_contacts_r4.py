"""Repeat complete retained-contact audit with every original zone's explicit clearance."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
HERE=Path(__file__).resolve().parent;path=HERE/'audit_logic_repairs_r1.py';text=path.read_text()
text=text.replace("OUT=HERE/'logic-return-contact-audit-r1'","OUT=HERE/'native-clearance-contact-audit-r4'")
text=text.replace('import complete_geometry_r2 as G','import complete_geometry_r2 as G\nimport native_clearance_projection_r1 as N')
needle="adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());before=m['projected'];"
new="""adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());fp=HERE/'field-contact-repair-r2-raw';fr=json.loads((fp/'receipt.json').read_text());assert sha(fp/'proposed-zones.pkl')==fr['proposal_sha256'];adds+=pickle.loads((fp/'proposed-zones.pkl').read_bytes());sp=HERE/'b5-contact-repair-r3-frozen';sr=json.loads((sp/'receipt.json').read_text());assert sha(sp/'proposed-zones.pkl')==sr['proposal_sha256'];adds+=pickle.loads((sp/'proposed-zones.pkl').read_bytes());minimum_rows=N.minimum_web_screen(m['new_zones']+adds);(OUT/'minimum-web-screen.json').write_text(json.dumps(minimum_rows,indent=1)+'\\n');before=m['projected'];"""
assert needle in text;text=text.replace(needle,new)
text=text.replace("after,retreats=G.projected(","after,retreats=N.projected(")
text=text.replace("'repair_receipt_sha256':sha(rp/'receipt.json'),", "'repair_receipt_sha256':sha(rp/'receipt.json'),'field_repair_receipt_sha256':sha(fp/'receipt.json'),'b5_repair_receipt_sha256':sha(sp/'receipt.json'),'projection_method':'Max(domain clearance, original explicit local zone clearance, new0.15)+0.025mm; no native fill claim','minimum_web_screen_sha256':sha(OUT/'minimum-web-screen.json'),")
exec(compile(text,str(path),'exec'))
