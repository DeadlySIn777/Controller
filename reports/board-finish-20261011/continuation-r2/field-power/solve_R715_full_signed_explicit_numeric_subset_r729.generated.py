"""Full signed FBG simplex DC envelope on actual R157 sheet/barrel geometry.

Every conserved term may choose any of its actual eligible physical contacts.
Electrode equipotential, material and thermal assumptions remain explicit.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
process = psutil.Process()
process.cpu_affinity(list(range(16, 28)))
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, json, pickle, hashlib, time, math, gc
from pathlib import Path
import numpy as np
import shapely
from shapely.ops import unary_union
from scipy.sparse import coo_matrix, save_npz
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
H = Path(__file__).resolve().parent
ROOT = H.parent
for directory in ('sbc-power', 'coupled-recovery'):
    sys.path.insert(0, str(ROOT / directory))
import contact_layout as L
IN = H / 'R715-one-prospective-barrel-complete-signed-native-baseline-mesh-input-r725'
OUT = H / 'R715-one-prospective-barrel-full-signed-explicit-numeric-subset-redistribution-r729'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
# Explicit conditional planning corner, not a fabrication specification.
CU = 25.0
PLATING = 20.0
TEMP = 125.0
Z0 = np.array([.0175, .2725, .6375, .8925, 1.2575, 1.5125])
Z = (Z0 - Z0[0]) * 1.6 / (Z0[-1] - Z0[0])
RHO = 1.724e-8 * (1 + .00393 * (TEMP - 20))
RS = RHO / (CU * 1e-6)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=1, allow_nan=False, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) + '\n', encoding='utf-8')

class UF:
    def __init__(self, count):
        self.p = np.arange(count)
    def find(self, index):
        while self.p[index] != index:
            self.p[index] = self.p[self.p[index]]
            index = int(self.p[index])
        return index
    def union(self, ids):
        if not len(ids):
            return
        base = self.find(int(ids[0]))
        for index in ids:
            self.p[self.find(int(index))] = base

def main():
    assert not OUT.exists()
    OUT.mkdir()
    start = time.monotonic()
    assert sha(IN / 'receipt.json') == 'cdb015a3ea113d4cba47242c4a40bda047ec847025aba8504746d0e01a8c4522'
    assert sha(H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727/receipt.json')=='b793ef3a1b887f27fb0fc013954a247c2564fee827679e9fa08a5408b4d564b8'
    assert sha(H/'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697/receipt.json')=='286df7e59b8172661e4d8a4f24b18f6f5abaf340a6c073a32379142eebd1c0af'
    receipt = json.loads((IN / 'receipt.json').read_bytes())
    assert not receipt['unrooted_or_other_raw_net_terms']
    assert abs(receipt['whole_domain_signed_KCL_A']) < 2e-14
    portfile = IN / 'actual-native-source-rooted-contact-ports.pkl'
    assert sha(portfile) == receipt['ports_SHA256']
    ports = pickle.loads(portfile.read_bytes())
    termfile = IN / 'complete-signed-FB-term-to-actual-native-physical-contact-ledger.json'
    assert sha(termfile) == receipt['term_ledger_SHA256']
    terms = json.loads(termfile.read_bytes())
    rows, cols, values = [], [], []
    electrodes, meshes, missing, summaries = {}, {}, [], []
    offset = 0
    for layer in LAYERS:
        T0 = np.load(IN / (layer.replace('.', '-') + '-triangles.npy'))
        det0 = (T0[:,1,0]-T0[:,0,0])*(T0[:,2,1]-T0[:,0,1])-(T0[:,1,1]-T0[:,0,1])*(T0[:,2,0]-T0[:,0,0])
        area0 = np.abs(det0) / 2
        max_edge_squared=np.max(np.stack([np.sum((T0[:,1]-T0[:,0])**2,axis=1),np.sum((T0[:,2]-T0[:,1])**2,axis=1),np.sum((T0[:,0]-T0[:,2])**2,axis=1)],axis=1),axis=1)
        relative_area=np.divide(area0,max_edge_squared,out=np.zeros_like(area0),where=max_edge_squared>0)
        omit=(area0<1e-12)|(relative_area<1e-8)
        np.save(OUT/(layer.replace('.','-')+'-original-all-triangle-quality.npy'),np.c_[area0,max_edge_squared,relative_area])
        np.save(OUT / (layer.replace('.', '-') + '-explicit-numerical-omissions.npy'), T0[omit])
        T = T0[~omit]
        coords, inverse = np.unique(T.reshape(-1, 2), axis=0, return_inverse=True)
        nodes = inverse.reshape(-1, 3)
        uf = UF(len(coords))
        local = {}
        xx, yy = coords[:, 0], coords[:, 1]
        for port in ports:
            shape = port['layer_contact_shapes'].get(layer)
            if shape is None:
                continue
            x0, y0, x1, y1 = shape.bounds
            ids = np.flatnonzero((xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1))
            ids = ids[shapely.intersects_xy(shape, xx[ids], yy[ids])]
            if not len(ids):
                missing.append({'UUID': port['UUID'], 'kind': port['kind'], 'ref': port['ref'], 'pin': port['pin'], 'layer': layer})
                continue
            local[port['UUID']] = ids
            uf.union(ids)
        roots = np.array([uf.find(index) for index in range(len(coords))])
        _, compact = np.unique(roots, return_inverse=True)
        ndof = int(compact.max() + 1)
        dofs = compact[nodes] + offset
        for uid, ids in local.items():
            electrodes[uid, layer] = int(compact[ids[0]] + offset)
        det = (T[:,1,0]-T[:,0,0])*(T[:,2,1]-T[:,0,1])-(T[:,1,1]-T[:,0,1])*(T[:,2,0]-T[:,0,0])
        area = np.abs(det) / 2
        assert np.all(area >= 1e-12)
        grad = np.stack([np.c_[T[:, 1, 1] - T[:, 2, 1], T[:, 2, 0] - T[:, 1, 0]],
                         np.c_[T[:, 2, 1] - T[:, 0, 1], T[:, 0, 0] - T[:, 2, 0]],
                         np.c_[T[:, 0, 1] - T[:, 1, 1], T[:, 1, 0] - T[:, 0, 0]]], axis=1) / det[:, None, None]
        stiffness = area[:, None, None] * np.einsum('tik,tjk->tij', grad, grad)
        allsame = (dofs[:, 0] == dofs[:, 1]) & (dofs[:, 1] == dofs[:, 2])
        stiffness[allsame] = 0
        two = (~allsame) & ((dofs[:, 0] == dofs[:, 1]) | (dofs[:, 0] == dofs[:, 2]) | (dofs[:, 1] == dofs[:, 2]))
        for triangle in np.flatnonzero(two):
            unique = 2 if dofs[triangle, 0] == dofs[triangle, 1] else 1 if dofs[triangle, 0] == dofs[triangle, 2] else 0
            repeated = 0 if unique else 1
            conductance = area[triangle] * float(grad[triangle, unique] @ grad[triangle, unique])
            stiffness[triangle] = 0
            stiffness[triangle, unique, unique] = conductance
            stiffness[triangle, repeated, repeated] = conductance
            stiffness[triangle, unique, repeated] = -conductance
            stiffness[triangle, repeated, unique] = -conductance
        active = ~allsame
        rows.append(np.repeat(dofs[active], 3, axis=1).ravel())
        cols.append(np.tile(dofs[active], (1, 3)).ravel())
        values.append(stiffness[active].ravel())
        meshes[layer] = {'dofs': dofs, 'grad': grad, 'centres': T.mean(axis=1), 'area': area}
        summaries.append({'layer': layer, 'triangles': len(T), 'unique_vertices': len(coords), 'electrode_condensed_dofs': ndof,
                          'literal_contact_electrodes': len(local), 'explicit_numerical_omitted_triangles': int(omit.sum()),
                          'explicit_numerical_omitted_area_mm2': float(area0[omit].sum()), 'minimum_numeric_relative_area_over_longest_edge_squared': 1e-8, 'all_omitted_triangle_coordinates_and_quality_frozen': True})
        offset += ndof
        put(OUT / 'assembly-checkpoint.json', summaries)
        print('R695 assembly', layer, ndof, 'dofs', flush=True)
        del T0, T, coords, inverse, roots, compact, uf, stiffness, nodes
        gc.collect()
    barrel, br, bc, bv = [], [], [], []
    for port in ports:
        if not port['barrel_is_plated']:
            continue
        item = port['exact_physical_inventory_record']
        if port['kind'] == 'pad':
            assert not item['npth'] and not item['smd']
            hole = unary_union(L.poly(item['hole']))
            # Chord perimeter omits outer plating area and thus raises R.
            perimeter_m = hole.length * .001
        else:
            perimeter_m = math.pi * item['drill'] * .001
        cross_section_m2 = perimeter_m * PLATING * 1e-6
        contacts = [(i, electrodes[port['UUID'], layer]) for i, layer in enumerate(LAYERS) if (port['UUID'], layer) in electrodes]
        for (i, a), (j, bb) in zip(contacts, contacts[1:]):
            length_m = (Z[j] - Z[i]) * .001
            resistance = RHO * length_m / cross_section_m2
            conductance = RS / resistance
            br.extend([a, bb, a, bb]); bc.extend([a, bb, bb, a]); bv.extend([conductance, conductance, -conductance, -conductance])
            barrel.append({'UUID': port['UUID'], 'kind': port['kind'], 'ref': port['ref'], 'pin': port['pin'],
                           'a': a, 'b': bb, 'layer_a': LAYERS[i], 'layer_b': LAYERS[j],
                           'conditional_R_ohm': resistance, 'G_normalized': conductance,
                           'conditional_span_mm': length_m * 1000, 'inner_hole_perimeter_mm': perimeter_m * 1000,
                           'no_outer_plating_area_credit': True})
    sheet = coo_matrix((np.concatenate(values), (np.concatenate(rows), np.concatenate(cols))), shape=(offset, offset)).tocsr()
    bars = coo_matrix((bv, (br, bc)), shape=(offset, offset)).tocsr()
    matrix = (sheet + bars).tocsr()
    source = next(p for p in ports if p['ref'] == 'J11005' and p['pin'] == '2')
    ground = electrodes[source['UUID'], 'F.Cu']
    count, components = connected_components(matrix, directed=False)
    keep = np.flatnonzero(components == components[ground])
    keep = keep[keep != ground]
    nodeindex = np.full(offset, -1, dtype=np.int64)
    nodeindex[keep] = np.arange(len(keep))
    unresolved = []
    for term in terms:
        options = []
        for endpoint in term['eligible_actual_physical_choices']:
            for layer in endpoint['actual_source_rooted_layers']:
                node = electrodes.get((endpoint['physical_pad_uuid'], layer))
                if node is None or components[node] != components[ground]:
                    unresolved.append({'term': term['name'], 'ref': endpoint['ref'], 'pin': endpoint['pin'], 'UUID': endpoint['physical_pad_uuid'], 'layer': layer})
                else:
                    options.append({'node': node, 'UUID': endpoint['physical_pad_uuid'], 'ref': endpoint['ref'], 'pin': endpoint['pin'], 'layer': layer})
        term['electrode_options'] = options
    put(OUT / 'missing-numerical-literal-contact-electrodes.json', missing)
    put(OUT / 'unresolved-full-signed-electrode-choices.json', unresolved)
    put(OUT / 'exact-signed-term-electrode-options.json', terms)
    put(OUT / 'actual-layer-barrel-links.json', barrel)
    save_npz(OUT / 'normalized-sheet-matrix.npz', sheet)
    save_npz(OUT / 'normalized-real-barrel-matrix.npz', bars)
    binding = {'electrodes': electrodes, 'ground_F_source_UUID': source['UUID'], 'ground_F_node': ground,
               'kept_nodes': keep, 'component_labels': components, 'meshes': meshes, 'ports': ports}
    (OUT / 'exact-mesh-electrode-node-binding.pkl').write_bytes(pickle.dumps(binding, protocol=5))
    if unresolved:
        put(OUT / 'receipt.json', {'status': 'NUMERICAL_SUBSET_FULL_LITERAL_CHOICES_INCOMPLETE_NO_FULL_CURRENT_ACCEPTANCE',
                                  'input_receipt_SHA256': sha(IN / 'receipt.json'), 'unresolved': unresolved,
                                  'native_jobs': 0, 'board_written': False, 'adopted': False})
        return
    source_nodes = [(layer, electrodes[source['UUID'], layer]) for layer in LAYERS if (source['UUID'], layer) in electrodes]
    endpoint_nodes = sorted({option['node'] for term in terms for option in term['electrode_options']})
    pointorder = sorted(electrodes)
    pointnodes = np.array([electrodes[key] for key in pointorder], dtype=np.int64)
    b_a = np.array([e['a'] for e in barrel], dtype=np.int64)
    b_b = np.array([e['b'] for e in barrel], dtype=np.int64)
    b_g = np.array([e['G_normalized'] for e in barrel])
    Ag = matrix[keep][:, keep].tocsc()
    print('R695 factoring', len(keep), 'unknowns', Ag.nnz, 'nnz', flush=True)
    factor = splu(Ag, permc_spec='MMD_AT_PLUS_A')
    unit_cache = {}
    maxres = 0.0
    for first in range(0, len(endpoint_nodes), 16):
        nodes = endpoint_nodes[first:first + 16]
        rhs = np.zeros((len(keep), len(nodes)))
        for col, node in enumerate(nodes):
            if node != ground:
                rhs[nodeindex[node], col] = 1
        U = factor.solve(rhs)
        residual = float(np.max(np.abs(Ag @ U - rhs)))
        assert residual < 1e-6, ('unit-current KCL residual', residual)
        maxres = max(maxres, residual)
        full = np.zeros((offset, len(nodes))); full[keep] = U
        # Store only actual electrode voltages and real barrel currents.
        for col, node in enumerate(nodes):
            unit_cache[node] = {'V': full[pointnodes, col] * RS,
                                'barrel_A': b_g * (full[b_a, col] - full[b_b, col]),
                                'source_V': {layer: float(full[source_node, col] * RS) for layer, source_node in source_nodes}}
        del U, full, rhs
        gc.collect()
        print('R695 full signed unit contacts', first + len(nodes), '/', len(endpoint_nodes), flush=True)
    scenarios = []
    source_term = next(t for t in terms if t['name'] == 'Actual external source return sink')
    other_terms = [t for t in terms if t is not source_term]
    assert abs(sum(t['signed_current_A'] for t in other_terms) + source_term['signed_current_A']) < 2e-14
    global_bar_lo = np.full(len(barrel), np.inf)
    global_bar_hi = np.full(len(barrel), -np.inf)
    global_v_lo = np.full(len(pointnodes), np.inf)
    global_v_hi = np.full(len(pointnodes), -np.inf)
    for source_layer, source_node in source_nodes:
        src = unit_cache[source_node]
        src_v = src['V'] - src['source_V'][source_layer]
        v_lo = src_v * source_term['signed_current_A']; v_hi = v_lo.copy()
        b_lo = src['barrel_A'] * source_term['signed_current_A']; b_hi = b_lo.copy()
        for term in other_terms:
            options = sorted({e['node'] for e in term['electrode_options']})
            current = term['signed_current_A']
            voltage = np.column_stack([(unit_cache[node]['V'] - unit_cache[node]['source_V'][source_layer]) * current for node in options])
            amps = np.column_stack([unit_cache[node]['barrel_A'] * current for node in options])
            v_lo += voltage.min(axis=1); v_hi += voltage.max(axis=1)
            b_lo += amps.min(axis=1); b_hi += amps.max(axis=1)
        global_bar_lo = np.minimum(global_bar_lo, b_lo); global_bar_hi = np.maximum(global_bar_hi, b_hi)
        global_v_lo = np.minimum(global_v_lo, v_lo); global_v_hi = np.maximum(global_v_hi, v_hi)
        worstpoint = int(np.argmax(np.maximum(np.abs(v_lo), np.abs(v_hi))))
        worstbar = int(np.argmax(np.maximum(np.abs(b_lo), np.abs(b_hi))))
        row = {'external_J11005_2_sink_contact_layer_case': source_layer,
               'all_conserved_terms': len(terms), 'signed_source_return_A': -source_term['signed_current_A'],
               'whole_scenario_signed_KCL_A': sum(t['signed_current_A'] for t in terms),
               'maximum_conditional_absolute_any_electrode_drop_V': float(max(abs(v_lo[worstpoint]), abs(v_hi[worstpoint]))),
               'worst_voltage_electrode_UUID_and_layer': list(pointorder[worstpoint]),
               'worst_voltage_signed_interval_V': [float(v_lo[worstpoint]), float(v_hi[worstpoint])],
               'maximum_conditional_absolute_real_barrel_current_A': float(max(abs(b_lo[worstbar]), abs(b_hi[worstbar]))),
               'worst_barrel_UUID': barrel[worstbar]['UUID'], 'worst_barrel_layers': [barrel[worstbar]['layer_a'], barrel[worstbar]['layer_b']],
               'worst_barrel_signed_interval_A': [float(b_lo[worstbar]), float(b_hi[worstbar])],
               'return_voltage_alone_below_saved_0p48V_COMBINED_positive_plus_return_budget_NOT_loop_PASS': max(np.max(np.abs(v_lo)), np.max(np.abs(v_hi))) <= .48}
        scenarios.append(row)
        put(OUT / 'signed-scenario-checkpoint.json', scenarios)
        print('R695', source_layer, 'maxdropV', row['maximum_conditional_absolute_any_electrode_drop_V'], 'maxbarrelA', row['maximum_conditional_absolute_real_barrel_current_A'], flush=True)
    voltage_rows = [{'UUID': key[0], 'layer': key[1], 'signed_voltage_interval_V': [float(lo), float(hi)]} for key, lo, hi in zip(pointorder, global_v_lo, global_v_hi)]
    barrel_rows = [{**e, 'signed_current_interval_A': [float(lo), float(hi)],
                    'maximum_absolute_A': float(max(abs(lo), abs(hi))),
                    'conditional_segment_Joule_upper_W': max(abs(lo), abs(hi)) ** 2 * e['conditional_R_ohm']} for e, lo, hi in zip(barrel, global_bar_lo, global_bar_hi)]
    put(OUT / 'all-actual-electrode-full-signed-simplex-voltage-bounds.json', voltage_rows)
    put(OUT / 'all-actual-real-barrel-full-signed-simplex-current-bounds.json', barrel_rows)
    put(OUT / 'receipt.json', {'status': 'FULL_SIGNED_ONE_PROSPECTIVE_FBG_BARREL_NUMERICAL_SUBSET_DC_ENVELOPE_SOLVED_NOT_PHYSICAL_CAPACITY_QUALIFIED',
                              'R727_explicit_source_tree_and_byte_binding_receipt_SHA256':sha(H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727/receipt.json'),
                              'baseline_R697_explicit_numeric_subset_receipt_SHA256':sha(H/'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697/receipt.json'),
                              'R695_full_original_matrix_KCL_failure_and_R703_scaling_failure_preserved':True,
                              'one_new_barrel_contacts_PROSPECTIVE_NOT_observed_native':True,
                              'numeric_omission_does_NOT_automatically_upperbound_every_physical_voltage_or_barrel_current':True,
                              'same_numeric_criteria_as_R697_new_mesh_does_NOT_prove_convergence':True,
                              'input_actual_native_mesh_receipt_SHA256': sha(IN / 'receipt.json'),
                              'complete146_signed_ledger_SHA256': receipt['complete146_signed_ledger_SHA256'],
                              'actual_R157_geometry_SHA256': receipt['actual_R157_geometry_SHA256'],
                              'actual_R157_flashes_SHA256': receipt['actual_R157_flashes_SHA256'],
                              'full_FB_terms': len(terms), 'full_exact_physical_endpoint_choices': receipt['exact_native_physical_endpoint_choices'],
                              'full_all_observed_layer_choices_numerically_mapped': True, 'unresolved_endpoints': [],
                              'positive_ground_injection_A': receipt['positive_ground_injection_A'],
                              'negative_converter_ground_injection_A': receipt['converter_negative_ground_injection_A'],
                              'normal_J11005_2_sink_A': receipt['normal_signed_connector_return_A'],
                              'no_equal_endpoint_pad_layer_or_barrel_sharing_assumption': True,
                              'per_term_simplex_extrema_then_Minkowski_sum_is_conservative_linear_enclosure': True,
                              'all_individual_interval_maxima_NOT_simultaneous_independent_loads': True,
                              'conditional_material_inputs': {'Cu_um': CU, 'plating_um': PLATING, 'uniform_Cu_temperature_C': TEMP,
                                                              'rho_ohm_m': RHO, 'max_outer_contact_span_mm': 1.6,
                                                              'serialized_relative_layer_height_ratios_only': Z0.tolist(),
                                                              'barrel_cross_section_inner_perimeter_times_plating_no_outer_area_credit': True},
                              'assembly': summaries, 'matrix_unknowns': len(keep), 'physical_components': int(count),
                              'exact_actual_contact_ports': len(ports), 'electrode_layer_count': len(electrodes),
                              'real_barrel_segment_count': len(barrel), 'unit_contact_response_count': len(unit_cache),
                              'maximum_unit_equation_KCL_residual_A': maxres, 'external_sink_contact_cases': scenarios,
                              'maximum_conditional_absolute_voltage_V': max(s['maximum_conditional_absolute_any_electrode_drop_V'] for s in scenarios),
                              'maximum_conditional_barrel_A': max(s['maximum_conditional_absolute_real_barrel_current_A'] for s in scenarios),
                              'voltage_bounds_SHA256': sha(OUT / 'all-actual-electrode-full-signed-simplex-voltage-bounds.json'),
                              'barrel_current_bounds_SHA256': sha(OUT / 'all-actual-real-barrel-full-signed-simplex-current-bounds.json'),
                              'saved_FA_FB_COMBINED_positive_plus_return_policy_V': .48, 'FIELD5_budget_NOT_inferred': True,
                              'limits': ['This is a numerical solve on an explicitly contained subset of actual R157 Cu, not a board change.',
                                         'Literal pad/annular contact regions are equipotential model electrodes; solder/contact/local pad spreading and plating variation remain unqualified.',
                                         'No equal sharing or cancellation beyond the complete conserved signed ledger is invented.',
                                         'Guaranteed copper/plating/height and temperature, full thermal rise/fault/transient/current density and numerical convergence remain OPEN.',
                                         'The reported voltage is the return only; .48V is the saved COMBINED positive-supply-plus-return budget and no loop acceptance is inferred.',
                                         'R157 required old via-mask failures and other source/reference/current/native DRC failures remain bound; no physical current rating or fabrication acceptance.'],
                              'native_jobs': 0, 'board_written': False, 'adopted': False, 'elapsed_seconds': time.monotonic() - start})
    print('R729_COMPLETE', sha(OUT / 'receipt.json'), flush=True)

if __name__ == '__main__':
    main()
