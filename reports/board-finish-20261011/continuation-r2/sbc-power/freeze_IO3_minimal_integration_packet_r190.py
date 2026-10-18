"""Correct R188 contract key to include every declared native setting."""
from pathlib import Path
import hashlib,json,ast
P=Path(__file__).resolve().parent
old=P/'freeze_IO3_minimal_integration_packet_r188.py';s=old.read_text()
s=s.replace('IO3-minimal-validated-integration-packet-r188','IO3-minimal-validated-integration-packet-r190').replace('R188_COMPLETE','R190_COMPLETE')
needle="om={(q['net'],q['layer']):q for q in oz};rows=[];replacements=[];untouched=[]"
repl="def key(q):return (q['net'],q['layer'],q.get('clearance_mm',.15),q.get('min_thickness_mm',.15),q.get('pad_connect_mode','FULL_SOLID'),q.get('priority',124),q.get('island_removal_mode',1),q.get('thermal_gap_mm',.15),q.get('thermal_bridge_width_mm',.3))\n om={key(q):q for q in oz};assert len(om)==len(oz);rows=[];replacements=[];untouched=[]"
assert needle in s;s=s.replace(needle,repl).replace("before=om[q['net'],q['layer']]","before=om[key(q)]")
ast.parse(s)
(P/'IO3-minimal-packet-R188-preserved-failure.json').write_text(json.dumps({'verdict':'EMITTER_CONTRACT_ASSERTION_FAILURE_NO_GEOMETRY_OR_BOARD_CHANGED','original_script_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'cause':'The remove/retain dictionary used only raw net and layer, colliding C10036 In4 FBG local .25 priority125 with the .15 priority124 main FBG group. R183 uses full settings keys and is unchanged.','correction':'Derived R190 includes the exact nine-field native setting key, no threshold or gate changes.','original_failed_output_directory':'IO3-minimal-validated-integration-packet-r188','preserve_original_failure':True},indent=1)+'\n')
exec(compile(s,str(old),'exec'))
