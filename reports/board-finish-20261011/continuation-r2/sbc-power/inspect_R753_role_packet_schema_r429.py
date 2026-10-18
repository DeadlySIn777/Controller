"""Inspect the packet schema after R428's pre-context guard failure."""
import sys,json,pickle
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
F=H/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/only-final-shared-owned-roles-and-Q0-positive-NOT_MODEL.pkl'
v=pickle.loads(F.read_bytes())
def schema(x,depth=0):
 if depth>=2:return {'type':type(x).__name__,'keys':list(x)[:12]if isinstance(x,dict)else None}
 if isinstance(x,dict):return {'type':'dict','members':{str(k):schema(y,depth+1)for k,y in list(x.items())[:12]}}
 if isinstance(x,list):return {'type':'list','length':len(x),'first':schema(x[0],depth+1)if x else None}
 return {'type':type(x).__name__}
report={'status':'R428_FAILED_PRE_CONTEXT_ROLE_SCHEMA_ASSUMPTION_NO_EDITS','packet_SHA256':N.sha(F),'schema':schema(v),'native_jobs_or_edits':0}
(P/'R428-pre-context-role-schema-failure-and-R429-schema.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps(report),flush=True)
