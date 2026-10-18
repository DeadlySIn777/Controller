"""Recheck literal contact/physical alignment and true plane margin on R526."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R518-new-ground-plane-owned-roles-direct-contacts-r522-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R518-new-ground-plane-owned-roles-direct-contacts-r522':'Q0-R526-plane-roles-and-direct-contacts-r530',
 'Q0-two-SMD-reference-only-owned-FA-recess-current-r518/model.pkl':'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl',
 '6a042063ca93b82533b30dcefed2366b5f80efaab6e5e06e1c862314d3193d50':'97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14',
 'Q0-R518-full-current-contacts-source-reference-r520':'Q0-R526-full-current-contacts-source-reference-r528',
 '2a729246c74cc0e9ab25eba0da73a36455850ce5cc044abc9f8788c49515b87d':'0fe1fbdb213915cadf704785bccd755c13d8048745b07bc5f8e60ff4d0b69721',
 'R520_actual_reference_source_contact_receipt_sha256':'R528_actual_reference_source_contact_receipt_sha256',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
derived=H/'Q0-R526-plane-roles-and-direct-contacts-r530-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
