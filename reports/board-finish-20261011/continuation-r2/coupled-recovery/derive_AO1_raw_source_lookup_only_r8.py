"""Normalize escaped slashes only for lookup; preserve raw source net names."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'bind_AO1_fresh_sexpr_source_contract_r7.py';text=old.read_text();out=H/'AO1-current-F-cage-fresh-source-contract-r7'
assert out.exists()and not(out/'receipt.json').exists()
(out/'reader-failure.json').write_text(json.dumps({'reason':'AO1 COM native raw name contains {slash}; prior lookup omitted normalization','raw_source_net_names_unchanged':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
text=text.replace('AO1-current-F-cage-fresh-source-contract-r7','AO1-current-F-cage-fresh-source-contract-r8')
text=text.replace(" if atom(n,'name')in names:"," if atom(n,'name').replace('{slash}','/')in names:")
text=text.replace("assert {n['raw_name']for n in nets}==names","assert {n['raw_name'].replace('{slash}','/')for n in nets}==names")
text=text.replace("(old/'reader-failure.json').write_text", "assert(old/'reader-failure.json').exists();(OUT/'prior-r6-reader-failure-copy.json').write_text")
dest=H/'bind_AO1_source_raw_lookup_r8.generated.py';assert not dest.exists();dest.write_text(text)
(H/'AO1-source-r8-derivation.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'net_name_changes':0,'lookup_only_escaped_slash_normalization':True},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
