"""Retain r1 zero-result diagnostic; use explicit domain-bearing geometry in r2."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'inventory_current_logic.py';raw=src.read_bytes();s=raw.decode()
old="HERE/'native-198b-geometry/geometry.json'"
new="Path('Z:/pcb-runs/claude-finish/agent-work/field-pdn/testA3/w/geom.json')"
if s.count(old)!=1:raise ValueError('Exact old-domain source mismatch')
s=s.replace(old,new).replace("'current-logic-source-role-inventory-r1.json'","'current-logic-source-role-inventory-r2.json'")
s=s.replace("rows=[]","if not all(isinstance(v,str) and v.startswith('DOM_') for v in domains.values()):raise ValueError('Not a galvanic domain mapping')\n    rows=[]")
dst=HERE/'inventory_current_logic_r2.py'
if dst.exists():raise ValueError('Fresh revision required')
dst.write_text(s,encoding='utf-8')
(HERE/'current-logic-inventory-derivation-r2.json').write_text(json.dumps({'source':str(src),'source_sha256':hashlib.sha256(raw).hexdigest(),'derived':str(dst),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'r1_no_routing_authority':'r1 incorrectly treated native net-code integers as domains; zero candidate result provides no catalog coverage evidence','r2_domain_source_is_same_exact_original_rules_domain_mapping_used_by_fresh_198b_model':True,'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print(str(dst))
