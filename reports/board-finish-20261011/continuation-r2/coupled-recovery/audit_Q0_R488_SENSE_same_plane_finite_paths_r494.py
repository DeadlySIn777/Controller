"""Rebind the finite SAME_PLANE proposal to exact R488/R492 source arrays.

R482 raw failure and R484 proof remain immutable. This successor changes
only the bound current model/source audit, retaining the exact own aperture,
path width and source-constrained search. It does not qualify native/SI.
"""
from pathlib import Path
H = Path(__file__).resolve().parent
base = H / 'audit_Q0_SENSE_actual_same_plane_finite_paths_r482.py'
code = base.read_text()
replacements = {
    'Q0-SENSE-actual-same-plane-finite-paths-r482': 'Q0-R488-SENSE-same-plane-finite-paths-r494',
    'Q0-R478-exact-pose-current-contacts-reference-r480': 'Q0-R488-final-owned-exact-wrapper-r492',
    'fa9629bb0b6bc93b39b0148e9e4236c351aaabd0edba06823f9423c86b3e6279': 'ab9fc241ac29e0b6b56563ff3949e8278a7d28ee4b7d56988e99c96f425aecdc',
    'Q0-exact-R476-ground-contact-pose-r478/model.pkl': 'Q0-owned-roles-literal-negative-canonical-r488/model.pkl',
    'aec47d8600135e340be9e38ca18891e2903e7c283ee0b7095673d383ce079ebd': '1b2c6f54ab37e90c415a2e053862d8d8e35f3767b4e2130555bb307458cf075e',
    'finite=local.buffer(-.105,quad_segs=128)': 'finite=local.difference(own).buffer(-.105,quad_segs=128)',
    'R480_incremental_receipt_sha256': 'R492_incremental_receipt_sha256',
}
for old, new in replacements.items():
    assert old in code, old
    code = code.replace(old, new)
exec(compile(code, str(base), 'exec'))
