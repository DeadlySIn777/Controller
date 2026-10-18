"""Fresh full sparse audit after explicit owned-FA extra-margin correction."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R518-full-current-contacts-source-reference-r520-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R518-full-current-contacts-source-reference-r520':'Q0-R526-full-current-contacts-source-reference-r528',
 'Q0_R520_':'Q0_R528_',
 'Q0-two-SMD-reference-only-owned-FA-recess-current-r518':'Q0-only-new-FA-recess-explicit-100nm-margin-r526',
 '5c8dca541b0774ca8fba7161f34a39277c8d740d379452c6249de2ac8bd7a90f':'db2025ad91530d5a0f0193bc4a08ef672e31127a49b29c9ffedbc298983b391e',
 '6a042063ca93b82533b30dcefed2366b5f80efaab6e5e06e1c862314d3193d50':'97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14',
 'cbe45e63e980bf95da3b3310019c79cbeb2d931262315a440c9f2a7c3dd70069':'1072a12227657bac90d100c243e3ae57085abed0a2123e32332ff40763a9f3f9',
 'exact-R518-input-only-three-old-negative-roles-one-new-ground-zone.json':'exact-R526-input-only-three-old-negative-roles-one-new-ground-zone.json',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
derived=H/'Q0-R526-full-current-contacts-source-reference-r528-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
