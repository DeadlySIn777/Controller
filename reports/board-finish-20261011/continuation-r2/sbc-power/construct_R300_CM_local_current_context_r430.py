"""Correct the single-positive-role schema; retain R428 failure and scope."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_R300_CM_local_current_context_r428.py').read_text(encoding='utf-8').replace('CM79-R300-exact-current-local-context-BEFORE-fill-only-r428','CM79-R300-exact-current-local-context-BEFORE-fill-only-r430').replace('R428_COMPLETE','R430_COMPLETE')
old="q=(list(shared.values())if isinstance(shared,dict)else list(shared))+(list(positive.values())if isinstance(positive,dict)else list(positive))"
new="q=(list(shared.values())if isinstance(shared,dict)else list(shared))+([positive]if isinstance(positive,dict)and 'uuid'in positive else list(positive))"
assert old in s;s=s.replace(old,new)
s=s.replace("'current_owned_role_count':len(q)","'current_owned_role_count':len(q),'full_current_raw_profile_inventory_additional_binding_required':True")
E=P/'exact-expanded-current-local-context-r430.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
