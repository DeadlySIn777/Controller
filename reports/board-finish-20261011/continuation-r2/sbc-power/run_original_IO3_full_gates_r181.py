"""Sequential independent gates on one confined host slot."""
from pathlib import Path
import sys,runpy,json,hashlib
P=Path(__file__).resolve().parent;mp=P/'original-IO3-full-owned-zone-normalization-r177/model.pkl';assert mp.exists()
results=[]
for file in ('audit_original_IO3_full_true_geometry_r178.py','audit_original_IO3_full_original_contacts_r179.py','audit_original_IO3_all76_incremental_r180.py'):
 f=P/file;print('IO3_FULL_GATE_START',file,flush=True);sys.argv=[str(f),str(mp)];runpy.run_path(str(f),run_name='__main__');results.append({'script':file,'script_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(P/'original-IO3-full-sequential-gate-run-r181.json').write_text(json.dumps({'model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'completed':results,'native_jobs':0,'board_written':False},indent=1)+'\n')
