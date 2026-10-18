"""Bind finite SAME_PLANE proof to corrected FA-margin current model."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R504-SENSE-same-plane-finite-paths-r510-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R504-SENSE-same-plane-finite-paths-r510':'Q0-R526-SENSE-same-plane-finite-paths-r532',
 'Q0-R504-explicit-final-current-r506':'Q0-R526-full-current-contacts-source-reference-r528',
 '8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a':'0fe1fbdb213915cadf704785bccd755c13d8048745b07bc5f8e60ff4d0b69721',
 'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl':'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl',
 'f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a':'97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14',
 'R506_incremental_receipt_sha256':'R528_incremental_receipt_sha256',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
derived=H/'Q0-R526-SENSE-same-plane-finite-paths-r532-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
