"""Preserve R695 failure; explicitly omit ill-conditioned numerical slivers.

No actual copper/port/native input or equation-residual threshold is changed.
The smaller numerical network must still map every literal current choice.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
process = psutil.Process()
process.cpu_affinity(list(range(16, 28)))
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json, hashlib
from pathlib import Path
H = Path(__file__).resolve().parent
source = H / 'solve_R157_actual_FBG_complete_signed_simplex_3D_r695.py'
failed = H / 'R157-actual-FBG-complete-signed-simplex-3D-current-r695'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

assert (failed / 'normalized-sheet-matrix.npz').exists()
assert (failed / 'normalized-real-barrel-matrix.npz').exists()
failure = {'status': 'FAIL_STRICT_UNIT_CURRENT_KCL_BEFORE_ANY_CURRENT_RESULT',
           'first_unit_equation_residual_A': .00390625, 'required_max_unit_residual_A': 1e-6,
           'script_SHA256': sha(source), 'input_receipt_SHA256': sha(H / 'R157-actual-FBG-complete-signed-real-barrel-mesh-input-r693/receipt.json'),
           'sheet_matrix_SHA256': sha(failed / 'normalized-sheet-matrix.npz'),
           'barrel_matrix_SHA256': sha(failed / 'normalized-real-barrel-matrix.npz'),
           'physical_input_not_changed': True, 'no_current_or_voltage_acceptance': True}
failurefile = failed / 'failure.json'
if failurefile.exists():
    assert json.loads(failurefile.read_bytes()) == failure
else:
    failurefile.write_text(json.dumps(failure, indent=1) + '\n', encoding='utf-8')
s = source.read_text(encoding='utf-8')
s = s.replace("OUT = H / 'R157-actual-FBG-complete-signed-simplex-3D-current-r695'", "OUT = H / 'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697'")
s = s.replace("np.cross(T0[:, 1] - T0[:, 0], T0[:, 2] - T0[:, 0])", "(T0[:, 1, 0]-T0[:, 0, 0])*(T0[:, 2, 1]-T0[:, 0, 1])-(T0[:, 1, 1]-T0[:, 0, 1])*(T0[:, 2, 0]-T0[:, 0, 0])")
s = s.replace("np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])", "(T[:, 1, 0]-T[:, 0, 0])*(T[:, 2, 1]-T[:, 0, 1])-(T[:, 1, 1]-T[:, 0, 1])*(T[:, 2, 0]-T[:, 0, 0])")
old = 'omit = area0 < 1e-12'
new = """max_edge_squared = np.max(np.stack([np.sum((T0[:, 1]-T0[:, 0])**2, axis=1), np.sum((T0[:, 2]-T0[:, 1])**2, axis=1), np.sum((T0[:, 0]-T0[:, 2])**2, axis=1)], axis=1), axis=1)
        relative_area = np.divide(area0, max_edge_squared, out=np.zeros_like(area0), where=max_edge_squared>0)
        omit = (area0 < 1e-12) | (relative_area < 1e-8)
        np.save(OUT / (layer.replace('.', '-') + '-original-all-triangle-quality.npy'), np.c_[area0, max_edge_squared, relative_area])"""
assert old in s
s = s.replace(old, new)
s = s.replace("'explicit_numerical_omitted_area_mm2': float(area0[omit].sum())", "'explicit_numerical_omitted_area_mm2': float(area0[omit].sum()), 'minimum_numeric_relative_area_over_longest_edge_squared': 1e-8, 'all_omitted_triangle_coordinates_and_quality_frozen': True")
s = s.replace("'assembly': summaries", "'prior_R695_KCL_failure_receipt_SHA256': sha(H/'R157-actual-FBG-complete-signed-simplex-3D-current-r695/failure.json'), 'explicit_smaller_contained_numerical_subset_no_physical_trim': True, 'assembly': summaries")
exec(compile(s, str(source), 'exec'))
