"""Bind omitted old q settings to exact R601 native owner declaration."""
from pathlib import Path
s=Path(__file__).with_name('audit_final_four_direction_union_native_intent_scope_r651.py').read_text(encoding='utf-8')
old="z=pl['new_q'];assert z==next(a for a in q if a['uuid']==z['uuid']);assert all(tuple(z[k]for k in fields)==tuple(a[k]for k in fields)for a in pl['exact_before_q'])"
new="z=pl['new_q'];assert z==next(a for a in q if a['uuid']==z['uuid'])\n  authority=H/'eight-native-overlap-plan-exact-R543-source-head-recensus-r601/four-current-scope-minimal-component-plans.json';assert sha(authority)=='ed603fce61c69311fc9a8c56c6950c28bb719c795c9c365d42e295c4ed59545e';ap=next(a for a in json.loads(authority.read_bytes())if set(a['exact_R543_before_owned_UUIDs'])==set(pl['members_before_UUIDs']));declared={'net':ap['raw_net'],'layer':ap['layer'],**{('clearance_mm'if k=='local_clearance_mm'else k):v for k,v in ap['nine_setting_owner_authority'].items()}}\n  assert set(declared)==set(fields)and all(z[k]==declared[k]for k in fields)\n  assert all(all(k not in a or a[k]==declared[k]for k in fields)for a in pl['exact_before_q'])"
assert old in s;s=s.replace(old,new).replace('final-four-direction-union-native-intent-scope-readonly-r651','final-four-direction-union-native-intent-scope-readonly-r653').replace('R651','R653')
exec(compile(s,str(Path(__file__)),'exec'))
