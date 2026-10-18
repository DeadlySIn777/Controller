"""Preserve R189 parser-null assertion; match the exact physical pin roles."""
from pathlib import Path
import hashlib,json,ast
P=Path(__file__).resolve().parent;old=P/'freeze_CORE1V2_power_reference_classification_r189.py';s=old.read_text()
needle="assert {'ref':'L2001','pin':'2','pinfunction':None,'pintype':'passive'} in nodes"
assert needle in s;s=s.replace(needle,"assert any((q['ref'],q['pin'],q['pintype'])==('L2001','2','passive') for q in nodes)")
s=s.replace('CORE1V2-own-rail-shadow-classification-proposal-r189','CORE1V2-own-rail-shadow-classification-proposal-r191').replace('R189_COMPLETE','R191_COMPLETE')
ast.parse(s)
(P/'CORE1V2-classification-R189-preserved-parser-assertion.json').write_text(json.dumps({'verdict':'PARSER_ABSENT_PINFUNCTION_REPRESENTATION_ASSERTION_FAILURE_ONLY','original_script_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'cause':'Frozen atom parser represents absent optional pinfunction as empty text, while R189 required None for L2001.2. Exact ref/pin/pintype remain source-authoritative.','correction':'R191 explicitly matches L2001.2 passive source role and preserves every exported node field.','no_reference_geometry_board_or_source_change':True},indent=1)+'\n')
exec(compile(s,str(old),'exec'))
