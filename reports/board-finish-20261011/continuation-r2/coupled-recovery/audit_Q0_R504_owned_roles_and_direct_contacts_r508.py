"""Final exact role/native clearance/direct contact/exterior check on R504."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R488-actual-filled-exterior-membership-r500-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R488-actual-filled-exterior-membership-r500':'Q0-R504-owned-roles-and-direct-contacts-r508',
 "mp=H/'Q0-owned-roles-literal-negative-canonical-r488/model.pkl'":"mp=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl'",
 '1b2c6f54ab37e90c415a2e053862d8d8e35f3767b4e2130555bb307458cf075e':'f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a',
 'Q0-R488-explicit-final-current-r496':'Q0-R504-explicit-final-current-r506',
 '3dc5358f58193b8d6cd602a9c465c2e2f7629f4fdf5cdecb8cb7b818af7838ec':'8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a',
 'R496_actual_reference_source_contact_receipt_sha256':'R506_actual_reference_source_contact_receipt_sha256',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
derived=H/'Q0-R504-owned-roles-and-direct-contacts-r508-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
