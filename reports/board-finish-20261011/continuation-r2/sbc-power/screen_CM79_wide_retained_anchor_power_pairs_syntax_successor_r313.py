"""Frozen R312 parse failure successor; same read-only widened geometry scope."""
from pathlib import Path
import hashlib,json
p=Path(__file__).with_name('screen_CM79_wide_retained_anchor_power_pairs_r312.py')
s=p.read_text(encoding='utf-8').replace("else120.1", "else 120.1")
s=s.replace("'sbc-power/CM79-widened-retained-original-F-anchor-ordinary-port-pairs-r312'", "'sbc-power/CM79-widened-retained-original-F-anchor-ordinary-port-pairs-r313'")
s=s.replace('R312_GROUND','R313_GROUND').replace('R312_SIDE','R313_SIDE').replace('R312_COMPLETE','R313_COMPLETE')
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir();", "started=time.monotonic();assert not O.exists();O.mkdir();put(O/'exact-successor-syntax-scope.json',{'failed_parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'correction':'else120.1 -> else 120.1','no_geometry_scope_change':True});(O/'exact-expanded-screen.py').write_text(s,encoding='utf-8');")
failed=p.parent/'CM79-widened-original-anchor-R312-frozen-parser-failure'
assert not failed.exists();failed.mkdir();(failed/'receipt.json').write_text(json.dumps({'verdict':'PARSER_FAILURE_BEFORE_ANY_MODEL_OR_OUTPUT_DIRECTORY','failed_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exact_error':'SyntaxError: expected else after if expression, line78 else120.1','model_source_native_changes':0},indent=1)+'\n',encoding='utf-8')
exec(compile(s,str(p),'exec'))
