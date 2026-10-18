"""Derive only explicit connector-surface classification metadata; no geometry."""
import hashlib, json, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
original = H / 'audit_combined_R753_actual_full_state_r759.py'
text = original.read_text(encoding='utf-8')
old = "assert bool(old['smd']) == (p['attr'] == 'smd')"
assert text.count(old) == 1
text = text.replace(old, "assert bool(old['smd']) == (p['attr'] in ('smd', 'conn'))\n            if p['attr'] == 'conn': assert old['hole'] is None and p['drill'] == 0")
name = 'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r759'
assert text.count(name) == 1
text = text.replace(name, 'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763')
oldledger = "'at_mm': p['at'], 'layers': p['layers'], 'polygon':"
assert text.count(oldledger) == 1
text = text.replace(oldledger, "'at_mm': p['at'], 'layers': p['layers'], 'native_attribute': p['attr'], 'polygon':")
target = H / 'audit_combined_R753_actual_full_state_conn_scope_r763.generated.py'
assert not target.exists(); target.write_text(text, encoding='utf-8')
out = H / 'actual-native-conn-surface-pad-scope-derivation-r763'
assert not out.exists(); out.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
(out / 'receipt.json').write_text(json.dumps({'status':'EXPLICIT_SOURCE_CONNECTOR_SURFACE_CLASSIFICATION_ONLY',
    'original_script_SHA256':sha(original), 'generated_script_file':str(target), 'generated_script_SHA256':sha(target),
    'host_smd_flag_scope':['actual native smd', 'actual native conn surface land with no hole and zero drill'],
    'native_attribute_preserved_in_ledger':True, 'native_or_pad_geometry_or_masks_changed':False,
    'R759_failed_assertion_preserved':True, 'native_jobs':0},indent=1)+'\n',encoding='utf-8')
print(json.dumps({'generated_script':str(target),'SHA256':sha(target)}))
