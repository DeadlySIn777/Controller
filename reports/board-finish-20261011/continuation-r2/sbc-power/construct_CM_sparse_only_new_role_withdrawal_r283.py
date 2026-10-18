"""Preserve inherited role/fill mismatch; cut only new CM role withdrawals."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_CM_sparse_current_R364_local_negative_r279.py').read_text()
s=s.replace('CM-sparse-exact-current-R364-normal-antipads-local-negative-r279','CM-sparse-exact-current-R364-only-new-role-withdrawal-inherited-fills-FAIL-r283')
s=s.replace("filled=[];out=[];affected={'/LOGIC_GND'}", "inherited_outside=[];filled=[];out=[];affected={'/LOGIC_GND'}")
old="assert prevoutside.is_empty,('inherited_owned_fill_outside_bound_physical',z['uuid'],l,i,prevoutside.area)"
new="""if not prevoutside.is_empty:inherited_outside.append({'generated_UUID':z['uuid'],'raw_net':z['net'],'layer':l,'record':i,'inherited_literal_before_actual_filled_outside_bound_physical_FAIL':save(z['uuid']+'-'+l+'-'+str(i)+'-inherited-literal-outside-before-physical',prevoutside),'not_globally_clipped_or_waived':True})"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("extra=zero(p).difference(newphysical)", "extra=zero(p).intersection(oldphysical.difference(newphysical))")
s=s.replace("put(O/'only-new-CM-generated-role-ordered-operations.json',roles);", "put(O/'inherited-owned-filled-outside-before-physical-FAIL-retained.json',inherited_outside);put(O/'only-new-CM-generated-role-ordered-operations.json',roles);")
s=s.replace("'signed_CM_return_A':3.5593046439628484", "'inherited_owned_fill_outside_physical_FAIL_count':len(inherited_outside),'only_exact_new_role_withdrawal_applied_no_global_old_outside_clip':True,'signed_CM_return_A':3.5593046439628484")
s=s.replace('R279','R283')
exec(compile(s,str(__file__),'exec'))
