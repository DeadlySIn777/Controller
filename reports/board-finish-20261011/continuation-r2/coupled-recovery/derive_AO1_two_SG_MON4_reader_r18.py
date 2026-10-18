"""Correct stale unused MON3 cache-key read; no geometry/policy change."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'search_AO1_MON4_two_SG_source_preserving_r17.py';text=old.read_text();out=H/'AO1-MON4-two-SG-F-In3-B-source-preserving-joint-search-r17'
assert out.exists()and not(out/'receipt.json').exists();(out/'reader-failure.json').write_text(json.dumps({'reason':'Unused win reader retained old MON3 key after R16 current scope became MON4','candidate_emitted':False,'geometry_or_policy_changes':0,'native_jobs':0},indent=1)+'\n')
text=text.replace('AO1-MON4-two-SG-F-In3-B-source-preserving-joint-search-r17','AO1-MON4-two-SG-F-In3-B-source-preserving-joint-search-r18').replace('AO1_R17_','AO1_R18_').replace("win=ctx['current_local_minus_MON3']['outline'];",'')
dest=H/'search_AO1_MON4_two_SG_source_preserving_r18.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-r18-two-SG-cache-reader-correction.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'failure_preserved':True,'geometry_or_policy_changes':0},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
