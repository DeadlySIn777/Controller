"""Create a separate frozen known-failure derivative; leave PASS emitter intact."""
from pathlib import Path
import hashlib,py_compile
H=Path(__file__).resolve().parent
src=H/'emit_current_owned_native_recipe_r286.py';dst=H/'emit_known_failed_reference_native_recipe_r298.py'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='d18aa3673822b921ea8833dd8cebdc3a5b4cec4d16c43ea15722be47477e18b5'
assert not dst.exists()
s=src.read_text()
s=s.replace('import native_owned_root_pose_contract_r3 as FP','import native_owned_root_pose_contract_r3 as FP\nimport failure_bound_native_emit_gate_r298 as FAIL_GATE')
s=s.replace("m['schema']=='current-owned-native-emitter-manifest-r286'","m['schema']=='known-failed-reference-current-native-diagnostic-manifest-r298'")
start=s.index(' gate=read(audit);bound_gate=gate');end=s.index(' g,h,b,q,current=',start)
s=s[:start]+" diagnostic_gate=FAIL_GATE.validate(m,model,audit,failure)\n"+s[end:]
s=s.replace("'verdict':'EXACT_CURRENT_OWNED_NATIVE_RECIPE_DIAGNOSTIC_INCREMENTAL_GATES_BOUND_FULL_PRODUCTION_FAIL_OPEN'","'verdict':'EXACT_CURRENT_KNOWN_REFERENCE_FAILURE_NATIVE_DIAGNOSTIC_CONTACT_SOURCE_NATIVE_CU_PASS_REFERENCES_FAIL_PRODUCTION_FAIL_OPEN'")
s=s.replace("'production_failure_ledger_file':str(failure)","'known_failed_reference_diagnostic_gate':diagnostic_gate,'known_failed_reference_gate_helper_sha256':sha(FAIL_GATE.__file__),'strict_old_reference_gate_pass':False,'full_new_reference_gate_pass':False,'production_failure_ledger_file':str(failure)")
assert 'fresh_actual_incremental_contact_source_strict_old_reference_native_effective_Cu_gate_pass'not in s
dst.write_text(s,encoding='utf-8',newline='\n');py_compile.compile(str(dst),doraise=True)
print(hashlib.sha256(dst.read_bytes()).hexdigest())
