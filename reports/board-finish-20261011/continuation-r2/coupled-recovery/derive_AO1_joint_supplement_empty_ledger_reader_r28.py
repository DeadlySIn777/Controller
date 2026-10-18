"""Accept empty held-failure ledgers by schema, never by area threshold."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'freeze_AO1_R22_R656_joint_sparse_supplement_r26.py';text=old.read_text();out=H/'AO1-R22-with-R656-seven-ground-joint-sparse-native-supplement-r26'
assert out.exists()and not(out/'receipt.json').exists();(out/'reader-failure.json').write_text(json.dumps({'reason':'R658 reports empty loss lists, not numeric-zero loss counts; no replay or native job produced','native_jobs':0,'adopted':False},indent=1)+'\n')
text=text.replace('AO1-R22-with-R656-seven-ground-joint-sparse-native-supplement-r26','AO1-R22-with-R656-seven-ground-joint-sparse-native-supplement-r28').replace('all(g[k]==0 for k in','all(not g[k] for k in')
dest=H/'freeze_AO1_R22_R656_joint_sparse_supplement_r28.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-r28-ground-receipt-empty-ledger-schema-correction.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'all_nonempty_error_ledgers_still_fail':True,'geometry_or_scope_changes':0},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
