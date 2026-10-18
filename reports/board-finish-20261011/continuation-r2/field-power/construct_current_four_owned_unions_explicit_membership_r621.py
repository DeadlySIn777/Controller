"""Use exact owned-member identity rather than an omitted diagnostic flag."""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'construct_R543_only_four_inward_same_settings_unions_r619.py'
s=p.read_text(encoding='utf-8')
s=s.replace('R543-only-four-current-inward-same-nine-settings-unions-r619','R543-four-current-inward-unions-explicit-owned-membership-r621')
old="assert z.get('prospective_not_native')and set(z['fills'])=={layer}"
new="assert member['uuid']not in {x['uuid']for x in h['zones']}and z['net']==member['net']and set(z['fills'])=={layer},('exact_declared_owned_member_identity',member['uuid']);assert all(z[k]==v for k,v in profile.items()if k in z)"
assert old in s;s=s.replace(old,new)
s=s.replace("print('R619'","print('R621'")
exec(compile(s,str(Path(__file__)),'exec'))
