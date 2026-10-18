"""Algebraic conditioning diagnostic on the unchanged failed R695 matrix.

No triangle omission, conductor edit, port change or current-capacity claim.
The original absolute unit-current KCL requirement stays 1e-6 A.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
process = psutil.Process()
process.cpu_affinity(list(range(16, 28)))
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json, pickle, hashlib, time
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz, diags
from scipy.sparse.linalg import splu
H = Path(__file__).resolve().parent
IN = H / 'R157-actual-FBG-complete-signed-simplex-3D-current-r695'
OUT = H / 'R695-unchanged-matrix-diagonal-scaling-unit-KCL-diagnostic-r703'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n', encoding='utf-8')

def main():
    assert not OUT.exists()
    OUT.mkdir()
    started = time.monotonic()
    names = ('normalized-sheet-matrix.npz', 'normalized-real-barrel-matrix.npz',
             'exact-mesh-electrode-node-binding.pkl', 'exact-signed-term-electrode-options.json', 'failure.json')
    before = {name: sha(IN / name) for name in names}
    failure = json.loads((IN / 'failure.json').read_bytes())
    sheet = load_npz(IN / names[0]); bars = load_npz(IN / names[1])
    binding = pickle.loads((IN / names[2]).read_bytes())
    terms = json.loads((IN / names[3]).read_bytes())
    assert not json.loads((IN / 'missing-numerical-literal-contact-electrodes.json').read_bytes())
    assert not json.loads((IN / 'unresolved-full-signed-electrode-choices.json').read_bytes())
    matrix = (sheet + bars).tocsr()
    keep = binding['kept_nodes']; ground = binding['ground_F_node']
    nodeindex = np.full(matrix.shape[0], -1, dtype=np.int64)
    nodeindex[keep] = np.arange(len(keep))
    endpoints = sorted({option['node'] for term in terms for option in term['electrode_options']})
    assert all(node == ground or nodeindex[node] >= 0 for node in endpoints)
    Ag = matrix[keep][:, keep].tocsc()
    diagonal = Ag.diagonal()
    assert np.all(np.isfinite(diagonal)) and np.all(diagonal > 0)
    scale = 1 / np.sqrt(diagonal)
    D = diags(scale, format='csc')
    scaled = (D @ Ag @ D).tocsc()
    asymmetry = Ag - Ag.T
    factor = splu(scaled, permc_spec='MMD_AT_PLUS_A', options={'Equil': False})
    # Extended accumulation is a separate residual observation, never a
    # substitute for the frozen original double-precision absolute check.
    extended = Ag.astype(np.longdouble)
    rows = []
    max_double = max_extended = 0.0
    for first in range(0, len(endpoints), 16):
        nodes = endpoints[first:first + 16]
        rhs = np.zeros((len(keep), len(nodes)))
        for col, node in enumerate(nodes):
            if node != ground:
                rhs[nodeindex[node], col] = 1
        U = scale[:, None] * factor.solve(scale[:, None] * rhs)
        iteration_rows = []
        for iteration in range(5):
            residual = rhs - Ag @ U
            residual_extended = rhs.astype(np.longdouble) - extended @ U.astype(np.longdouble)
            raw = float(np.max(np.abs(residual)))
            ext = float(np.max(np.abs(residual_extended)))
            iteration_rows.append({'iteration': iteration, 'original_double_unit_KCL_residual_A': raw,
                                   'extended_accumulation_unit_KCL_residual_A': ext})
            if raw < 1e-6:
                break
            if iteration < 4:
                correction_rhs = np.asarray(residual_extended, dtype=np.float64)
                U += scale[:, None] * factor.solve(scale[:, None] * correction_rhs)
        final = iteration_rows[-1]
        max_double = max(max_double, final['original_double_unit_KCL_residual_A'])
        max_extended = max(max_extended, final['extended_accumulation_unit_KCL_residual_A'])
        rows.append({'unit_contact_nodes': nodes, 'iterations': iteration_rows,
                     'original_required_absolute_1e_minus6_unit_KCL_PASS': final['original_double_unit_KCL_residual_A'] < 1e-6})
        put(OUT / 'unit-KCL-checkpoint.json', rows)
        print('R703 units', first + len(nodes), '/', len(endpoints), 'original_KCL', final['original_double_unit_KCL_residual_A'], flush=True)
    assert before == {name: sha(IN / name) for name in names}
    np.save(OUT / 'explicit-invertible-diagonal-scale.npy', scale)
    put(OUT / 'receipt.json', {'status': 'UNCHANGED_MATRIX_SCALED_UNIT_KCL_PASS_CURRENT_CONVERGENCE_OPEN' if max_double < 1e-6 else 'UNCHANGED_MATRIX_SCALED_UNIT_KCL_FAIL_NO_CURRENT_PROMOTION',
        'original_R695_failure_exact': failure, 'input_SHA256': before,
        'all_unchanged_matrix_and_node_binding_bytes_after_SHA256': {name: sha(IN / name) for name in names},
        'algebra': 'S = D A D; S y = D b; U = D y; D = diag(1/sqrt(Aii)); no matrix element or physical source changed',
        'original_absolute_unit_KCL_threshold_A': 1e-6, 'unit_response_count': len(endpoints),
        'maximum_original_double_unit_KCL_residual_A': max_double,
        'maximum_extended_accumulation_unit_KCL_residual_A_observation_only': max_extended,
        'unknowns': len(keep), 'nonzeros': int(Ag.nnz),
        'diagonal_min_max': [float(diagonal.min()), float(diagonal.max())],
        'literal_matrix_asymmetry_max': float(np.max(np.abs(asymmetry.data))) if asymmetry.nnz else 0.0,
        'ungauged_literal_row_sum_max': float(np.max(np.abs(np.asarray(matrix.sum(axis=1)).ravel()))),
        'no_additional_triangle_omission_or_physical_Cu_change': True,
        'no_endpoint_or_observed_layer_or_real_barrel_choice_omitted': True,
        'extended_precision_NOT_a_threshold_override_or_physical_convergence_certificate': True,
        'full_signed_voltage_barrel_envelope_numerical_convergence_material_current_thermal_native': 'OPEN',
        'native_jobs': 0, 'board_written': False, 'adopted': False,
        'elapsed_seconds': time.monotonic() - started})
    print('R703_COMPLETE', sha(OUT / 'receipt.json'), 'original_KCL', max_double, flush=True)

if __name__ == '__main__':
    main()
