"""Correct the preserved pre-execution R607 whitespace-only adapter failure."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
prior=H/'audit_R587_fresh_native_all_drill_TMR_source_contact_r607.py'
failed=H/'original-IO3-TMR-R587-fresh-native-all-drill-source-contact-r607'
if not failed.exists():
 failed.mkdir()
 (failed/'failure.json').write_text(json.dumps({'status':'FAILED_BEFORE_ANY_GRAPH_OR_MODEL_OPERATION','helper_SHA256':hashlib.sha256(prior.read_bytes()).hexdigest(),'failure':'SyntaxError: text substitution host[net]for -> prior_groupsfor; no geometry executed or emitted.'},indent=1)+'\n',encoding='utf-8')
s=prior.read_text(encoding='utf-8')
s=s.replace('original-IO3-TMR-R587-fresh-native-all-drill-source-contact-r607','original-IO3-TMR-R587-fresh-native-all-drill-source-contact-r609')
s=s.replace("exec(compile(s,str(Path(__file__)), 'exec'))", "s=s.replace('prior_groupsfor','prior_groups for')\nexec(compile(s,str(Path(__file__)), 'exec'))")
exec(compile(s,str(Path(__file__)),'exec'))
