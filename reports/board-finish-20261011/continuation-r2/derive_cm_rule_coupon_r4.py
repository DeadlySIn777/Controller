"""Separate the other-net control so native connectivity cannot merge its net."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'check_cm_terminal_native_rules_r3.py';target=H/'check_cm_terminal_native_rules_r4.py'
if target.exists():raise ValueError('Fresh isolated negative control required')
text=source.read_text(encoding='utf-8')
edits={
"OUT=HERE/'cm-terminal-native-rule-coupons-r3'":"OUT=HERE/'cm-terminal-native-rule-coupons-r4'",
"base=OUT/'original-profile';test=OUT/'proposed-profile'":"base=OUT/'original-profile';test=OUT/'proposed-profile';other=OUT/'other-literal-alone'",
"    base.mkdir();test.mkdir()":"    base.mkdir();test.mkdir();other.mkdir()",
"b''.join(r['chunk'] for r in controls.values())+inv[2],rules)":"b''.join(r['chunk'] for name,r in controls.items() if name!='controlled-other-literal-net')+inv[2],rules),(other,prefix+controls['controlled-other-literal-net']['chunk']+inv[2],rules)",
"for root in [base,test]":"for root in [base,test,other]",
"[('original',base),('proposed',test)]":"[('original',base),('proposed',test),('other',other)]",
"        if has('proposed',r['uuid'],'track_width')!=r['expected_width_error']":"        role='other' if name=='controlled-other-literal-net' else 'proposed'\n        if has(role,r['uuid'],'track_width')!=r['expected_width_error']",
"        if has('proposed',r['uuid'],'track_segment_length')!=r['expected_length_error']":"        if has(role,r['uuid'],'track_segment_length')!=r['expected_length_error']"}
for old,new in edits.items():
    if text.count(old)!=1:raise ValueError('Exact isolated coupon edit anchor differs:'+old)
    text=text.replace(old,new)
target.write_text(text,encoding='utf-8')
(H/'cm-terminal-native-rule-coupons-r3/net-control-correction-r4.json').write_text(json.dumps({'source_sha256':sha(source),'derived_sha256':sha(target),'native_diagnostic':str((H/'cm-terminal-native-rule-coupons-r3/net-diagnostic-r5/native-nets.json').resolve()),'native_diagnostic_sha256':sha(H/'cm-terminal-native-rule-coupons-r3/net-diagnostic-r5/native-nets.json'),'cause':'An overlapping padless foreign-net negative-control track was assigned the contacted CM clock net during native LoadBoard. Separate other-literal coupon prevents a physical short; exact rules/project/area/real neck are unchanged.','real_board_modified':False},indent=1)+'\n',encoding='utf-8')
runpy.run_path(str(target),run_name='__main__')
