"""Actual R157 FBG sheets, complete signed ports and observed barrel contacts.

This is a numerical-input artifact. It does not alter any board or native
mask, and it cannot turn unqualified copper/plating/thermal data into ratings.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
process = psutil.Process()
process.cpu_affinity(list(range(16, 28)))
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, json, pickle, hashlib, time, collections, math, gc
from pathlib import Path
import numpy as np
import shapely
from shapely.ops import unary_union
H = Path(__file__).resolve().parent
ROOT = H.parent
for directory in ('sbc-power', 'coupled-recovery'):
    sys.path.insert(0, str(ROOT / directory))
import R157_native_selected_actual_conversion_r673 as N
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K

OUT = H / 'R157-actual-FBG-complete-signed-real-barrel-mesh-input-r693'
NET = '/motherboard_do/FIELD_B_0V'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
MODEL = ROOT / 'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
SIGNED = ROOT / 'field-signed-port-allocation-r4/receipt.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dg(shape):
    return hashlib.sha256(shape.wkb).hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n', encoding='utf-8')

def main():
    assert not OUT.exists()
    OUT.mkdir()
    start = time.monotonic()
    assert sha(MODEL) == 'ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    assert sha(SIGNED) == 'e49fc7f958f264e552843ca43d1271dd84321dbcd52e27e2460155b2e635bb27'
    groups, missing = N.bound_R663_before_groups({NET})
    assert not missing
    root = K.root(groups[NET], 'J11005', '2')
    rootkeys = K.keys(root)
    g, h, b, q, c = pickle.loads(MODEL.read_bytes())
    pads = {p['uuid']: p for p in h['pads']}
    vias = {v['uuid']: v for v in h['vias']}
    observed = json.loads((N.R157 / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    terms = [t for t in json.loads(SIGNED.read_bytes())['terms'] if t['domain'] == 'FB']
    termrows = []
    allchoices = {}
    for term in terms:
        choices = []
        for endpoint in term['eligible_physical_endpoints']:
            uid = endpoint['physical_pad_uuid']
            pad = pads[uid]
            assert (pad['ref'], str(pad['num']), pad['net']) == (endpoint['ref'], endpoint['pin'], endpoint['raw_net'])
            contacts = {layer: unary_union([r['shape'] for r in root if r['kind'] == 'pad' and r['uuid'] == uid and r['layer'] == layer]) for layer in LAYERS}
            contacts = {layer: shape for layer, shape in contacts.items() if not shape.is_empty}
            row = {**endpoint, 'current_at_mm': [pad['x'], pad['y']], 'same_FBG_raw_net': L.norm(pad['net']) == NET,
                   'actual_source_rooted_layers': list(contacts), 'actual_source_rooted': bool(contacts),
                   'native_2nm_graph_key_scope': [('pad', uid, layer) for layer in contacts]}
            choices.append(row)
            allchoices[uid] = row
        termrows.append({'name': term['name'], 'kind': term['kind'], 'signed_current_A': term['signed_current_a'],
                         'eligible_actual_physical_choices': choices,
                         'all_exact_physical_choices_source_rooted': all(e['same_FBG_raw_net'] and e['actual_source_rooted'] for e in choices)})
    put(OUT / 'complete-signed-FB-term-to-actual-native-physical-contact-ledger.json', termrows)
    unrooted = [r for r in termrows if not r['all_exact_physical_choices_source_rooted']]
    nonsource = [r for r in termrows if r['name'] != 'Actual external source return sink']
    positive = sum(max(r['signed_current_A'], 0) for r in nonsource)
    negative = sum(min(r['signed_current_A'], 0) for r in nonsource)
    assert abs(positive + negative - 4.768596828963444) < 2e-14
    print('R693 signed terms', len(termrows), 'choices', len(allchoices), 'unresolved', len(unrooted), 'sourceA', positive + negative, flush=True)
    ports = []
    for kind, inventory in (('pad', pads), ('via', vias)):
        identifiers = sorted({r['uuid'] for r in root if r['kind'] == kind})
        for uid in identifiers:
            item = inventory[uid]
            contacts = {layer: unary_union([r['shape'] for r in root if r['kind'] == kind and r['uuid'] == uid and r['layer'] == layer]) for layer in LAYERS}
            contacts = {layer: shape for layer, shape in contacts.items() if not shape.is_empty}
            assert contacts and L.norm(item['net']) == NET
            if kind == 'via':
                assert set(contacts) <= set(observed[uid])
                hole = item['drill']
            else:
                hole_shape = unary_union(L.poly(item.get('hole') or []))
                hole = 2 * math.sqrt(hole_shape.area / math.pi) if not hole_shape.is_empty else None
            ports.append({'kind': kind, 'UUID': uid, 'ref': item.get('ref'), 'pin': str(item['num']) if kind == 'pad' else None,
                          'raw_net': item['net'], 'at_mm': [item['x'], item['y']], 'plated_hole_mm': hole,
                          'barrel_is_plated': hole is not None, 'layer_contact_shapes': contacts,
                          'observed_native_flash_layers': observed[uid] if kind == 'via' else None,
                          'exact_physical_inventory_record': item,
                          'all_contact_shapes_are_actual_native_all_drill_subtracted_R663_root_group': True})
    portfile = OUT / 'actual-native-source-rooted-contact-ports.pkl'
    portfile.write_bytes(pickle.dumps(ports, protocol=5))
    rows = []
    for layer in LAYERS:
        raw = unary_union([r['shape'] for r in root if r['layer'] == layer])
        exactfile = OUT / (layer.replace('.', '-') + '-exact-all-drilled-source-sheet.wkb')
        exactfile.write_bytes(raw.wkb)
        contained = raw.simplify(.001, preserve_topology=True).buffer(-.0012, join_style=2).intersection(raw)
        # Numerical erosion is explicit; no original board role is replaced.
        outside = contained.difference(raw)
        assert outside.is_empty, (layer, 'numerical domain outside actual source copper', outside.geom_type)
        domainfile = OUT / (layer.replace('.', '-') + '-contained-numerical-sheet.wkb')
        domainfile.write_bytes(contained.wkb)
        patches = [p['layer_contact_shapes'][layer].intersection(contained) for p in ports
                   if p['kind'] == 'pad' and not p['barrel_is_plated'] and layer in p['layer_contact_shapes']]
        patches = [patch for patch in patches if not patch.is_empty]
        patch = unary_union(patches)
        triangles = []
        for domain in (contained.difference(patch), patch):
            if not domain.is_empty:
                triangles.extend(np.asarray(shapely.get_coordinates(t))[:3] for t in shapely.constrained_delaunay_triangles(domain).geoms)
        T = np.asarray(triangles, dtype=np.float64)
        np.save(OUT / (layer.replace('.', '-') + '-triangles.npy'), T)
        row = {'layer': layer, 'exact_physical_WKB_SHA256': dg(raw), 'contained_WKB_SHA256': dg(contained),
               'exact_source_sheet_area_mm2': raw.area, 'contained_area_mm2': contained.area,
               'explicit_numerical_subset_removed_area_mm2': raw.difference(contained).area,
               'outside_actual_Cu_is_EMPTY': outside.is_empty, 'constrained_triangles': len(T),
               'literal_SMD_contact_patches': len(patches), 'simplify_tolerance_mm': .001, 'numeric_inward_mm': .0012}
        rows.append(row)
        put(OUT / 'mesh-input-checkpoint.json', rows)
        print('R693', layer, 'triangles', len(T), 'actual area', raw.area, flush=True)
        del raw, contained, T, triangles
        gc.collect()
    receipt = {'status': 'ACTUAL_R157_FULL_FBG_SIGNED_PORTS_AND_REAL_BARREL_NUMERICAL_INPUT_FROZEN_NOT_CAPACITY_QUALIFIED',
               'actual_R157_geometry_SHA256': sha(N.R157 / 'actual-full-refill-geometry.json'),
               'actual_R157_flashes_SHA256': sha(N.R157 / 'actual-full-refill-via-flashes.json'),
               'R663_actual_source_groups_SHA256': 'a24dcae5ae52ae71e548e7f75f2d1ec746324187cf1dc5ab67e01a4ef6f347b7',
               'source_identity_model_SHA256': sha(MODEL), 'complete146_signed_ledger_SHA256': sha(SIGNED),
               'source': 'J11005.2', 'shutdown_J11006_is_not_a_power_source': True,
               'actual_FBG_source_named_pad_count': len({r['uuid'] for r in root if r['kind'] == 'pad' and str(r['pin'])}),
               'actual_source_discrete_layer_keys': len(rootkeys), 'complete_FB_term_count': len(termrows),
               'exact_native_physical_endpoint_choices': len(allchoices), 'unrooted_or_other_raw_net_terms': unrooted,
               'positive_ground_injection_A': positive, 'converter_negative_ground_injection_A': negative,
               'normal_signed_connector_return_A': positive + negative, 'whole_domain_signed_KCL_A': sum(r['signed_current_A'] for r in termrows),
               'term_ledger_SHA256': sha(OUT / 'complete-signed-FB-term-to-actual-native-physical-contact-ledger.json'),
               'ports_SHA256': sha(portfile), 'actual_rooted_contact_ports': len(ports),
               'actual_rooted_plated_ports': sum(p['barrel_is_plated'] for p in ports), 'layers': rows,
               'serialized_nominal_copper_centres_mm': [.0175, .2725, .6375, .8925, 1.2575, 1.5125],
               'material_and_boundary_scope': 'Serialized35um Cu/.22-.33-.22-.33-.22 dielectric only; guaranteed Cu/plating/layer height, connector solder/contact and temperature/thermal boundaries remain OPEN.',
               'next_gate': 'Conserved full signed simplex electrode voltage/barrel-current envelope on these actual source sheets, not equal pad/layer/barrel sharing.',
               'FA_FB_saved_per_net_drop_policy_V': .48, 'FIELD5_drop_budget_NOT_inferred': True,
               'no_native_flash_substitution_or_phantom_annuli': True, 'all_current_thermal_transient_native_board_acceptance_OPEN': True,
               'native_jobs': 0, 'board_written': False, 'adopted': False, 'elapsed_seconds': time.monotonic() - start}
    put(OUT / 'receipt.json', receipt)
    print('R693_COMPLETE', sha(OUT / 'receipt.json'), 'unresolved', len(unrooted), flush=True)

if __name__ == '__main__':
    main()
