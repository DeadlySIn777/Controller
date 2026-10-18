"""Preserve prepared R206; add strict R210 requirement before sparse packaging."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'package_DIC_exact_owned_ledger_r206.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r206','r212')
needle="assert audit['R198_receipt_sha256']==sha(raw)"
assert needle in s;s=s.replace(needle,needle+"\n strictfile=H/'DIC-zero-unwaived-reference-r210.json';strict=load(strictfile);assert strict['verdict']=='DIC_ZERO_UNWAIVED_REFERENCE_EXACT_R204_BOUND_PASS' and not strict['retained_full_body_reference_losses'];assert strict['R204_receipt_sha256']==sha(independent.read_bytes());assert strict['complete_zero_threshold_reference_delta_audit']['every_nonempty_intersection_reported'] and strict['complete_zero_threshold_reference_delta_audit']['threshold_mm2']==0")
needle2="'independent_audit_sha256':sha(independent.read_bytes())"
assert needle2 in s;s=s.replace(needle2,needle2+",'strict_zero_unwaived_reference_file':str(strictfile),'strict_zero_unwaived_reference_sha256':sha(strictfile.read_bytes()),'strict_zero_unwaived_reference_verdict':strict['verdict'],'inherited_1e_9_mm2_reporting_receipt_retained_separately':True")
dst=H/'package_DIC_exact_zero_reference_owned_ledger_r212.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'freeze-DIC-zero-reference-owned-ledger-r212.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Prepared R206 unrun and preserved. Exact4 delete/25 add sparse packager additionally requires independently bound R210 every-nonempty reference intersection gate PASS, pins its receipt, and distinguishes inherited thresholded R204 result. No board emission or geometry change.'},indent=1)+'\n');print(sha(dst.read_bytes()))
