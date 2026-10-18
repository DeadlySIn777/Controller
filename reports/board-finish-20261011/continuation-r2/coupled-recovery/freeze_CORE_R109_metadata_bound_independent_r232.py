"""Preserve R230 failure; distinguish two exactly bound provenance keys."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
src=H/'audit_CORE_R109_actual_R214_independent_r230.py'
dst=H/'audit_CORE_R109_actual_R214_independent_r232.py'
out=H/'CORE-R109-vs-actual-R214-independent-r230'
assert not dst.exists() and out.is_dir() and not (out/'failure.json').exists()
pin=hashlib.sha256(src.read_bytes()).hexdigest()
assert pin=='272858df439429dcea1d51aa569c7fe490f959f31768574d3173c9f6ade39f50'
(out/'failure.json').write_text(json.dumps({'verdict':'INDEPENDENT_AUDITOR_METADATA_IDENTITY_ASSERTION_FAILED_BEFORE_GEOMETRY','script_sha256':pin,'exit_code':1,'exact_failure':'assert g100==g and h100==h and b100==b','retained_evidence':True,'no_candidate_change':True,'no_native_job':True,'geometric_or_reference_acceptance_claimed':False,'next_revision':'Bind each exact CORE_R100/CORE_R109 provenance row separately; compare all remaining metadata, all native/discrete definitions and all role WKB bytes exactly.'},indent=1)+'\n')
t=src.read_text().replace('CORE-R109-vs-actual-R214-independent-r230','CORE-R109-vs-actual-R214-independent-r232').replace('R230_','R232_')
a='assert g100==g and h100==h and b100==b;qm100='
assert t.count(a)==1
replace="""assert g100==g and h100==h;assert b100['CORE_R100_only_added_ordinary_native_actual_fill_projection']==b['CORE_R109_only_added_ordinary_native_actual_fill_projection'];assert {k:v for k,v in b100.items()if k!='CORE_R100_only_added_ordinary_native_actual_fill_projection'}=={k:v for k,v in b.items()if k!='CORE_R109_only_added_ordinary_native_actual_fill_projection'};put(O/'exact-provenance-row-key-difference-only.json',{'old_key':'CORE_R100_only_added_ordinary_native_actual_fill_projection','new_key':'CORE_R109_only_added_ordinary_native_actual_fill_projection','exact_same_row_values':b['CORE_R109_only_added_ordinary_native_actual_fill_projection'],'every_other_metadata_value_exact':True});qm100="""
t=t.replace(a,replace)
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
