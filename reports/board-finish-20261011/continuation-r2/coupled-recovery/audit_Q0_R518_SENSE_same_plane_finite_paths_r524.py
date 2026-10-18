"""Direct final shielding-head SAME_PLANE geometric binding; native/SI open."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R504-SENSE-same-plane-finite-paths-r510-derived-auditor.py'
code=base.read_text()
replacements={
 'Q0-R504-SENSE-same-plane-finite-paths-r510':'Q0-R518-SENSE-same-plane-finite-paths-r524',
 'Q0-R504-explicit-final-current-r506':'Q0-R518-full-current-contacts-source-reference-r520',
 '8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a':'2a729246c74cc0e9ab25eba0da73a36455850ce5cc044abc9f8788c49515b87d',
 'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl':'Q0-two-SMD-reference-only-owned-FA-recess-current-r518/model.pkl',
 'f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a':'6a042063ca93b82533b30dcefed2366b5f80efaab6e5e06e1c862314d3193d50',
 'R506_incremental_receipt_sha256':'R520_incremental_receipt_sha256',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
derived=H/'Q0-R518-SENSE-same-plane-finite-paths-r524-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
