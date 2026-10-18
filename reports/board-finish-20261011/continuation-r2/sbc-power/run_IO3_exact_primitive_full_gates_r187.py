"""One sequential confined slot for the R183 complete independent gates."""
from pathlib import Path
import sys,runpy,json,hashlib
P=Path(__file__).resolve().parent;mp=P/'IO3-exact-unchanged-primitive-composition-r183/model.pkl';assert mp.exists()
results=[]
for name in ('audit_IO3_exact_primitive_geometry_r184.py','audit_IO3_exact_primitive_original_contacts_r185.py','audit_IO3_exact_primitive_all76_r186.py'):
 f=P/name;print('IO3_EXACT_PRIMITIVE_GATE_START',name,flush=True);sys.argv=[str(f),str(mp)];runpy.run_path(str(f),run_name='__main__');results.append({'script':name,'script_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(P/'IO3-exact-primitive-sequential-gate-run-r187.json').write_text(json.dumps({'model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'completed':results,'native_jobs':0,'board_written':False},indent=1)+'\n')
