"""Keep R482 FAIL; constrain path search around the exact own aperture."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'audit_Q0_SENSE_actual_same_plane_finite_paths_r482.py'
code=base.read_text().replace('Q0-SENSE-actual-same-plane-finite-paths-r482','Q0-SENSE-same-plane-exact-own-constrained-paths-r484').replace('finite=local.buffer(-.105,quad_segs=128)','finite=local.difference(own).buffer(-.105,quad_segs=128)')
exec(compile(code,str(base),'exec'))
