"""Fresh actual source/contact/ZERO reference audit of the final fill cuts."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R488-explicit-final-current-r496-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R488-explicit-final-current-r496':'Q0-R504-explicit-final-current-r506',
 'Q0_R496_':'Q0_R506_',
 "candidate=H/'Q0-owned-roles-literal-negative-canonical-r488'":"candidate=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504'",
 "assert sha(crp)=='fd6ab6fc83f796e5455370244089b4e4daf571920b81600a6249767f7a3f6e9c'":"assert sha(crp)=='e110f813c32f8a574940b78bb042321a96ea1c1ff8c5f9831f1694957e95341b'",
 "cm=Path(cr['new_model_file']);assert sha(cm)==cr['new_model_sha256']=='1b2c6f54ab37e90c415a2e053862d8d8e35f3767b4e2130555bb307458cf075e'":"cm=Path(cr['model_file']);assert sha(cm)==cr['model_sha256']=='f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a'",
 'exact-final-R488-current-input-and-four-negative-roles.json':'exact-final-R504-current-input-and-four-negative-roles.json',
 "'prior_misbound_R492_credited_only_for_R478':True":"'prior_misbound_R492_credited_only_for_R478':True,'exact_R488_roles_and_local_filled_only_R504_negative_scopes_bound':True",
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
derived=H/'Q0-R504-explicit-final-current-r506-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
