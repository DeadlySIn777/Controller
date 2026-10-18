"""One confined host slot, independent preserved power and reference gates."""
from pathlib import Path
import runpy,sys,traceback,json,hashlib
P=Path(__file__).resolve().parent
M=P/'SAFE-repaired-owned-zone-normalization-r160/model.pkl'
assert hashlib.sha256(M.read_bytes()).hexdigest()=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
rows=[]
for name in ('audit_safe_power_source_contacts_r150.py','audit_safe_source_references_r151.py'):
 script=P/name;sys.argv=[str(script),str(M)]
 try:
  print('SAFE_R167_BEGIN',name,flush=True);runpy.run_path(str(script),run_name='__main__');rows.append({'script':name,'run_finished':True})
 except Exception as error:
  traceback.print_exc();rows.append({'script':name,'run_finished':False,'exception':type(error).__name__,'detail':str(error)})
 (P/'SAFE-r167-sequential-independent-gates.json').write_text(json.dumps({'model_sha256':hashlib.sha256(M.read_bytes()).hexdigest(),'rows':rows,'native_jobs':0,'board_written':False},indent=1)+'\n')
print('SAFE_R167_GATES_FINISHED',rows,flush=True)
