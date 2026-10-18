"""Independent prospective drill/source/reference gate for one actual-FBG stitch.

Existing masks and fills are actual FULL R157. New ordinary-via masks remain
prospective until fresh native API/refill; no current sharing is assigned.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
p = psutil.Process(); p.cpu_affinity(list(range(16, 28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, json, pickle, hashlib, time, collections, math
from pathlib import Path
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H = Path(__file__).resolve().parent; ROOT = H.parent
for directory in (ROOT, ROOT / 'sbc-power', ROOT / 'coupled-recovery'):
    sys.path.insert(0, str(directory))
import contact_layout as L
import fast_contacts as F
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as T
OUT = H / 'R715-FBG-parallel-stitch-actual-baseline-source-reference-independent-r719'
P = H / 'R157-high-current-FBG-actual-source-parallel-stitch-nomination-r715'
M = ROOT / 'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
ACTUAL = ROOT / 'R155-known-reference-native-diagnostic-r157/measure'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n', encoding='utf-8')

def main():
    assert not OUT.exists(); OUT.mkdir(); started = time.monotonic(); T.OUT = OUT
    assert sha(P / 'receipt.json') == '156f6e97f1628baa9f8d39c67a4e953d7b5c5b1ddf345a1b5f8ee68846c1adf6'
    packet = P / 'only-one-new-parallel-FBG-barrel-and-B-source-stub-NOMINEE.pkl'
    assert sha(packet) == 'de776f9dc5f95bc937d88e90d89039c8337641f9f4be5dac52284fddafe811c0'
    item, = pickle.loads(packet.read_bytes()); via = item['via']; track, = item['tracks']
    assert (via['x'], via['y'], via['d'], via['drill']) == (47.948, 204.2, .8, .4)
    assert via['net'] == track['net'] == '/motherboard_do{slash}FIELD_B_0V'
    assert via['flashed'] == LAYERS and track['layer'] == 'B.Cu' and track['w'] == .5
    assert track['a'] == [47.748, 206.5] and track['b'] == [47.948, 204.2]
    N.assert_R157_actual_before(); assert sha(M) == 'ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    g, h, b, q, c = pickle.loads(M.read_bytes())
    ng = json.loads((ACTUAL / 'actual-full-refill-geometry.json').read_bytes())
    flashes = json.loads((ACTUAL / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    nets = {net for net, ref, pin in K.ROOTS[:3]}
    baseline, missing = N.bound_R663_before_groups(nets); assert not missing
    before, before_context, padledger = N.convert_selected_actual(h, c, ng, flashes, nets, ACTUAL / 'copy/board.kicad_pcb')
    assert via['uuid'] not in {v['uuid'] for v in before['vias']}
    assert track['uuid'] not in {t['uuid'] for t in before['tracks']}
    candidate = {**before, 'vias': before['vias'] + [via], 'tracks': before['tracks'] + [track]}
    context = K.hole_context(candidate)
    root_rows, contacts, directbad, samezone, refs, groups = [], [], [], [], [], {}
    for net, ref, pin in K.ROOTS[:3]:
        _, after = K.physical(candidate, net, context); groups[net] = after
        old = baseline[net]; br = K.root(old, ref, pin); ar = K.root(after, ref, pin)
        losses = sorted(K.keys(br) - K.keys(ar))
        relations, bad = K.contact_losses(old, after)
        contacts.append({'net': net, 'old_relationship_rows': relations, 'losses': bad})
        root_rows.append({'net': net, 'external_source': ref + '.' + pin,
            'actual_before_source_pad_count': T.countpad(br), 'prospective_after_source_pad_count': T.countpad(ar),
            'actual_before_source_key_count': len(K.keys(br)), 'prospective_after_source_key_count': len(K.keys(ar)),
            'prior_source_keys_lost': [list(k) for k in losses]})
        fillby = collections.defaultdict(list)
        for group in after:
            for row in group:
                if row['kind'] == 'fill':
                    fillby[row['layer']].append(row)
        for layer in LAYERS:
            oldfill = [row for group in old for row in group if row['kind'] == 'fill' and row['layer'] == layer]
            oldtree = STRtree([row['shape'] for row in oldfill])
            newfill = fillby[layer]; newtree = STRtree([row['shape'] for row in newfill])
            metals = collections.defaultdict(list)
            for group in old:
                for row in group:
                    if row['kind'] != 'fill' and row['layer'] == layer:
                        metals[row['kind'], row['uuid'], layer].append(row['shape'])
            for key, shapes in metals.items():
                body = unary_union(shapes)
                hits = [oldfill[int(i)] for i in oldtree.query(body.buffer(.000002), predicate='intersects') if body.distance(oldfill[int(i)]['shape']) <= .000002]
                if not hits:
                    continue
                newhits = [newfill[int(i)] for i in newtree.query(body.buffer(.000002), predicate='intersects') if body.distance(newfill[int(i)]['shape']) <= .000002]
                row = {'net': net, 'old_key': list(key), 'old_zone_UUIDs': sorted({r['uuid'] for r in hits}), 'new_zone_UUIDs': sorted({r['uuid'] for r in newhits})}
                if not newhits:
                    directbad.append(row)
                if {r['uuid'] for r in hits} - {r['uuid'] for r in newhits}:
                    samezone.append(row)
        losses, proof = T.exact_reference_delta(before, K.source_refs(br), K.source_refs(ar), net)
        refs.append({'net': net, 'strict_original_routed_reference_losses': losses, 'proof': proof})
        put(OUT / 'source-checkpoint.json', root_rows)
        print('R719', net, 'source', T.countpad(ar), 'oldgroups', len(bad), 'source_loss', len(root_rows[-1]['prior_source_keys_lost']), 'refs', len(losses), flush=True)
    fbroot = K.root(groups['/motherboard_do/FIELD_B_0V'], 'J11005', '2')
    fbkeys = K.keys(fbroot)
    via_contact_rows = []
    axis = Point(via['x'], via['y'])
    ann = axis.buffer(via['d'] / 2, quad_segs=128).difference(axis.buffer(via['drill'] / 2, quad_segs=128))
    for layer in LAYERS:
        fill = unary_union([r['shape'] for r in fbroot if r['kind'] == 'fill' and r['layer'] == layer])
        overlap = ann.intersection(fill)
        via_contact_rows.append({'layer': layer, 'prospective_new_via_key_source_rooted': ('via', via['uuid'], layer) in fbkeys,
            'finite_actual_source_fill_annular_overlap': T.shapeinfo(overlap), 'actual_new_native_mask_or_minimum_feature_NOT_claimed': True})
    center = Point(via['x'], via['y']); drill_radius = via['drill'] / 2
    aperture = []
    for oldvia in before['vias']:
        d = center.distance(Point(oldvia['x'], oldvia['y']))
        if d < 1.5:
            aperture.append({'kind': 'old_via', 'UUID': oldvia['uuid'], 'pitch_mm': d,
                'true_drill_edge_gap_mm': d - drill_radius - oldvia['drill'] / 2,
                'PASS': d >= .825 and d - drill_radius - oldvia['drill'] / 2 >= .275})
    for pad in before['pads']:
        for layer in ('F.Cu', 'B.Cu'):
            if pad['smd']:
                for shape in L.poly(pad['layers'].get(layer, [])):
                    d = center.distance(shape) - drill_radius
                    if d < .75:
                        aperture.append({'kind': 'native_SMD_Cu', 'UUID': pad['uuid'], 'layer': layer, 'true_hole_edge_gap_mm': d, 'PASS': d >= .275})
    failures = bool(any(row['losses'] for row in contacts) or any(row['prior_source_keys_lost'] for row in root_rows)
        or directbad or samezone or any(row['strict_original_routed_reference_losses'] for row in refs)
        or any(not row['PASS'] for row in aperture)
        or any(not row['prospective_new_via_key_source_rooted'] for row in via_contact_rows)
        or any(row['finite_actual_source_fill_annular_overlap']['EMPTY'] for row in via_contact_rows if row['layer'] in ('In1.Cu', 'In2.Cu', 'In4.Cu'))
        or ('track', track['uuid'], 'B.Cu') not in fbkeys)
    gp = OUT / 'prospective-one-stitch-three-ground-all-drilled-groups.pkl'; gp.write_bytes(pickle.dumps(groups, protocol=5))
    put(OUT / 'all-old-three-ground-relationships.json', contacts)
    put(OUT / 'old-ANY-direct-native-fill-contact-losses.json', directbad)
    put(OUT / 'old-same-native-zone-direct-fill-differences.json', samezone)
    put(OUT / 'strict-all-three-old-routed-source-references.json', refs)
    put(OUT / 'new-ordinary-via-finite-source-annuli-and-prospective-mask-scope.json', via_contact_rows)
    put(OUT / 'independent-analytic-local-drill-and-SMD-aperture.json', aperture)
    put(OUT / 'receipt.json', {'status': 'PROSPECTIVE_ONE_FBG_STITCH_OLD_CONTACT_SOURCE_REFERENCE_PASS_NATIVE_CURRENT_OPEN' if not failures else 'PROSPECTIVE_ONE_FBG_STITCH_REPAIR_REQUIRED',
        'R715_nominee_receipt_SHA256': sha(P / 'receipt.json'), 'sparse_packet_SHA256': sha(packet),
        'R717_pre_geometry_three_value_conversion_return_failure_preserved': {'script_SHA256': sha(H / 'audit_R715_actual_FBG_parallel_stitch_source_preservation_r717.py'), 'failure': 'ValueError: too many values to unpack (expected 2, got 3); no geometry proof emitted'},
        'actual_before_geometry_SHA256': sha(ACTUAL / 'actual-full-refill-geometry.json'),
        'actual_before_masks_SHA256': sha(ACTUAL / 'actual-full-refill-via-flashes.json'),
        'all_original_mask_bits_and_native_fill_records_unchanged_new_physical_drill_subtracted': True,
        'new_via_layers_are_PROSPECTIVE_not_observed_native_or_forced_original_flags': True,
        'source_census': root_rows, 'old_relationship_loss_count': sum(len(r['losses']) for r in contacts),
        'old_ANY_direct_fill_loss_count': len(directbad), 'old_same_zone_direct_difference_count': len(samezone),
        'strict_old_routed_reference_loss_count': sum(len(r['strict_original_routed_reference_losses']) for r in refs),
        'independent_local_aperture_error_count': sum(not r['PASS'] for r in aperture),
        'required_actual_native_contact_layers': ['B.Cu', 'In1.Cu', 'In2.Cu', 'In4.Cu'],
        'no_equalsharing_or_barrel_current_rating': True,
        'complete_signed_redistribution_voltage_plating_current_thermal_and_native_api_refill_DRC': 'OPEN',
        'groups_SHA256': sha(gp), 'native_jobs': 0, 'adopted': False, 'elapsed_seconds': time.monotonic() - started})
    print('R719_COMPLETE', sha(OUT / 'receipt.json'), 'FAIL', failures, flush=True)

if __name__ == '__main__':
    main()
