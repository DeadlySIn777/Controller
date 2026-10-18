"""Independent actual FULL-before/FULL-after diagnostic, without native jobs.

The only host seed is the exact R155 discrete identity/domain/hole inventory.
All pads, tracks, vias, fills and flash masks used in either graph come from
the respective actual full native export. No proposed or selected fill is used.
"""
import os, psutil
for n in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[n] = '2'
p = psutil.Process(); p.cpu_affinity(list(range(16, 28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import collections, hashlib, json, pickle, sys, time
from decimal import Decimal
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

H = Path(__file__).resolve().parent; ROOT = H.parent
for d in ('field-power', 'sbc-power', 'coupled-recovery'):
    sys.path.insert(0, str(ROOT / d))
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as R
K = N.K; L = N.L; O = N.O; sha = N.sha
OUT = H / 'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r759'
STAGE = H / 'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753'
NF = ROOT / 'combined-R753-one-full-native-fill-cached-DRC-r299/native-full'
BASE = ROOT / 'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
EXPECTED = ROOT / 'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json'
CONTACT = .000002  # 2 nm graph/contact criterion; literal reference threshold is zero.
ROOTS = list(K.ROOTS)

def put(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=1, allow_nan=False) + '\n', encoding='utf-8')

def info(s):
    return {'EMPTY': s.is_empty, 'type': s.geom_type, 'area_mm2': s.area,
            'length_mm': s.length, 'bounds_mm': None if s.is_empty else list(s.bounds),
            'WKB_SHA256': hashlib.sha256(s.wkb).hexdigest()}

def witness(label, s):
    row = info(s)
    if not s.is_empty:
        path = OUT / (label + '.wkb'); path.write_bytes(s.wkb); row['file'] = str(path)
    return row

def iu(x):
    v = Decimal(str(x)) * 1000000; assert v == v.to_integral_value(), x
    return int(v)

def native_header(seed, ng, flashes, pose=None, expected=None):
    """Keep exact physical UUIDs; use actual export geometry for all 9971 pads."""
    assert len(seed['pads']) == len(ng['pads']) == 9971
    byuuid = {p['uuid']: p for p in seed['pads']}; assert len(byuuid) == 9971
    assert pose is None or set(pose['pads']) == set(byuuid)
    fp_ref = {} if pose is None else {u: r[0] for u, r in pose['footprints'].items()}
    assert pose is None or len(fp_ref) == 2723
    at = {}
    for uid, old in byuuid.items():
        if pose is None:
            at[uid] = (old['ref'], str(old['num']), old['x'], old['y'], old['net'])
        else:
            r = pose['pads'][uid]
            assert str(r[0]) == str(old['num']) and r[1] == old['net']
            at[uid] = (old['ref'], str(r[0]), r[2] / 1e6, r[3] / 1e6, r[1])
            assert old['hole'] is None or (r[2] / 1e6, r[3] / 1e6) == (old['x'], old['y'])
    slots = collections.defaultdict(list)
    for uid, key in at.items(): slots[key].append(uid)
    observed = collections.defaultdict(list)
    for p in ng['pads']:
        observed[p['ref'], str(p['num']), *p['at'], p['net']].append(p)
    assert set(slots) == set(observed)
    pads = {}; ledger = []; duplicates = []
    for key, uids in slots.items():
        actual = observed[key]; assert len(actual) == len(uids)
        # The six identical paste pads have no UUID in plane_dump. They may
        # bind by identity only after every exported physical field is equal.
        if len(uids) > 1:
            assert all(p == actual[0] for p in actual)
            duplicates.append({'key': list(key), 'UUIDs': sorted(uids), 'identical_native_rows': True})
        for uid, p in zip(sorted(uids), actual):
            old = byuuid[uid]; layers = {ly: O.polys(p['poly']) for ly in p['layers']}
            assert bool(old['smd']) == (p['attr'] == 'smd')
            assert bool(old['npth']) == (p['attr'] == 'npth')
            if pose is not None:
                assert sorted(p['layers']) == sorted(ly for ly in pose['pads'][uid][4] if ly in K.LAYERS)
            pads[uid] = {**old, 'x': p['at'][0], 'y': p['at'][1], 'layers': layers}
            ledger.append({'UUID': uid, 'ref': p['ref'], 'pin': p['num'], 'raw_net': p['net'],
                           'at_mm': p['at'], 'layers': p['layers'], 'polygon': 'actual native .005 ERROR_INSIDE common shape'})
    tracks = []
    for t in ng['tracks']:
        row = {'uuid': t['uuid'], 'net': t['net'], 'layer': t['layer'], 'a': t['s'], 'b': t['e'], 'w': t['w']}
        if 'm' in t: row['m'] = t['m']
        tracks.append(row)
    vias = [{'uuid': v['uuid'], 'net': v['net'], 'x': v['at'][0], 'y': v['at'][1],
             'd': v['w'], 'drill': v['drill'], 'flashed': flashes[v['uuid']],
             'mask_provenance': 'THIS actual FULL native FlashLayer, no forced layer'} for v in ng['vias']]
    assert set(flashes) == {v['uuid'] for v in vias}
    if expected is not None:
        observed_cu = {t['uuid']: t for t in ng['tracks']} | {v['uuid']: v for v in ng['vias']}
        assert set(observed_cu) == set(expected['copper'])
        for uid, e in expected['copper'].items():
            t = observed_cu[uid]; assert t['net'] == e['raw_net'] and bool(t['locked']) == e['locked_yes']
            if e['kind'] == 'via':
                assert [iu(v) for v in t['at']] == e['at_IU'] and iu(t['drill']) == e['drill_IU']
                assert set(e['diameters_IU'].values()) == {iu(t['w'])}
            else:
                assert [iu(v) for v in t['s']] == e['start_IU'] and [iu(v) for v in t['e']] == e['end_IU']
                assert iu(t['w']) == e['width_IU'] and t['layer'] == e['layer']
    zones = [{**z, 'fills': {ly: O.polys(rs) for ly, rs in z['fills'].items()}} for z in ng['zones']]
    actual = {**seed, 'pads': [pads[p['uuid']] for p in seed['pads']], 'tracks': tracks,
              'vias': vias, 'zones': zones, '_rooted_refs': {}}
    ctx = K.hole_context(actual)
    assert len(ctx[0]) == len(vias) + sum(len(L.poly(p.get('hole') or [])) for p in actual['pads'])
    return actual, ctx, ledger, duplicates

def all_physical(actual, ctx, label):
    """Equivalent to K.physical, batching F.build once for all raw nets."""
    rec, unused = K.F.build(actual); del unused
    buckets = collections.defaultdict(lambda: collections.defaultdict(list))
    for layer, rows in rec.items():
        for row in rows: buckets[L.norm(row['net'])][layer].append(row)
    del rec
    groups = {}; holes, ht = ctx
    for ni, (net, layers) in enumerate(sorted(buckets.items())):
        uf = K.A.S.UF(); rows = []
        for layer, layerrows in layers.items():
            rr = []
            for row in layerrows:
                body = row['shape'].difference(unary_union([holes[int(i)] for i in ht.query(row['shape'], predicate='intersects')]))
                for piece in K.RF.parts(body):
                    key = (row['kind'], row['uuid']) if row['kind'] in ('pad', 'via') else (row['kind'], row['uuid'], layer, K.C.sha(piece.wkb))
                    rr.append({**row, 'key': key, 'shape': piece})
            tree = STRtree([r['shape'] for r in rr])
            for i, row in enumerate(rr):
                uf.find(row['key']); rows.append(row)
                for j in tree.query(row['shape'].buffer(CONTACT), predicate='intersects'):
                    if i < int(j) and row['shape'].distance(rr[int(j)]['shape']) <= CONTACT:
                        uf.join(row['key'], rr[int(j)]['key'])
        out = collections.defaultdict(list)
        for row in rows: out[uf.find(row['key'])].append(row)
        groups[net] = list(out.values())
        if ni % 50 == 0:
            put('status.json', {'phase': label, 'net': net, 'completed_nets': ni, 'net_count': len(buckets)})
            print('R759', label, ni, net, flush=True)
    return groups

def source_fill_index(rows):
    out = {}
    for layer in K.LAYERS:
        pieces = [r for r in rows if r['kind'] == 'fill' and r['layer'] == layer]
        out[layer] = (pieces, STRtree([r['shape'] for r in pieces]))
    return out

def local_hits(index, body, layer):
    rows, tree = index[layer]
    return [rows[int(i)] for i in tree.query(body, predicate='intersects')]

def local_supported(body, index, layer):
    return unary_union([body.intersection(r['shape']) for r in local_hits(index, body, layer)])

def local_reference_loss(body, oldindex, newindex, layer):
    # Both clipped operand sets contain only literal support inside this body.
    # No board-wide source union is repeatedly formed for 94k trace bodies.
    old = local_supported(body, oldindex, layer)
    return old.difference(local_supported(body, newindex, layer))

def prepare():
    assert not OUT.exists(); OUT.mkdir(); started = time.monotonic()
    assert sha(BASE) == 'ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    assert sha(EXPECTED) == '13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3'
    N.assert_R157_actual_before(); _, seed, _, _, _ = pickle.loads(BASE.read_bytes())
    ng = json.loads((N.R157 / 'actual-full-refill-geometry.json').read_bytes())
    fl = json.loads((N.R157 / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    raw = (N.R157 / 'copy/board.kicad_pcb').read_bytes().lower()
    assert b'padstack' not in raw and b'layer_shapes' not in raw and b'custom_pad_primitives' not in raw
    before, ctx, padledger, dup = native_header(seed, ng, fl)
    groups = all_physical(before, ctx, 'PREPARE_ACTUAL_FULL_R157_BEFORE_ALL_NETS')
    known, _ = N.bound_R663_before_groups({r[0] for r in ROOTS[:3]})
    authority = []
    for net, cached in known.items():
        own = groups[net]; rows, bad = K.contact_losses(cached, own)
        back, reverse = K.contact_losses(own, cached)
        authority.append({'net': net, 'R663_to_fresh_full_losses': bad, 'fresh_full_to_R663_losses': reverse})
        assert not bad and not reverse, ('R663 exact baseline authority differs', net)
    (OUT / 'actual-full-R157-before-model.pkl').write_bytes(pickle.dumps(before, protocol=5))
    (OUT / 'actual-full-R157-before-all-net-groups.pkl').write_bytes(pickle.dumps(groups, protocol=5))
    put('before-all-9971-native-pad-binding.json', padledger)
    put('before-indistinguishable-native-paste-pad-bindings.json', dup)
    put('R663-three-ground-authority-equality.json', authority)
    pins = {str(p): sha(p) for p in (BASE, EXPECTED, N.R157 / 'actual-full-refill-geometry.json',
            N.R157 / 'actual-full-refill-via-flashes.json', Path(__file__), Path(N.__file__), Path(K.__file__), Path(K.F.__file__))}
    put('prepare-receipt.json', {'status': 'ACTUAL_FULL_R157_ALL_NET_BASELINE_BOUND_AFTER_NATIVE_PENDING',
        'input_SHA256': pins, 'actual_before_model_SHA256': sha(OUT / 'actual-full-R157-before-model.pkl'),
        'actual_before_groups_SHA256': sha(OUT / 'actual-full-R157-before-all-net-groups.pkl'),
        'pad_UUID_count': len(before['pads']), 'empty_raw_net_pad_count': sum(not p['net'] for p in before['pads']),
        'all_actual_graph_net_count': len(groups), 'actual_hole_count': len(ctx[0]),
        'R663_three_bank_partitions_exact': True, 'physical_contact_distance_mm': CONTACT,
        'literal_reference_and_no_zone_intersection_threshold': 0,
        'host_proposed_or_selected_fill_overlay': False, 'native_jobs': 0, 'elapsed_seconds': time.monotonic() - started})
    print('R759_PREPARED', sha(OUT / 'prepare-receipt.json'), flush=True)

def run_after():
    started = time.monotonic(); pr = json.loads((OUT / 'prepare-receipt.json').read_bytes())
    for p, h in pr['input_SHA256'].items(): assert sha(p) == h
    assert sha(OUT / 'actual-full-R157-before-model.pkl') == pr['actual_before_model_SHA256']
    assert sha(OUT / 'actual-full-R157-before-all-net-groups.pkl') == pr['actual_before_groups_SHA256']
    before = pickle.loads((OUT / 'actual-full-R157-before-model.pkl').read_bytes())
    oldgroups = pickle.loads((OUT / 'actual-full-R157-before-all-net-groups.pkl').read_bytes())
    nr = json.loads((NF / 'receipt.json').read_bytes()); expected = json.loads(EXPECTED.read_bytes())
    assert nr['candidate_SHA256'] == expected['board_sha256'] == '7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
    assert nr['full_native_CPP_Fill_calls'] == 1 and not nr['discrete_Cu_errors']
    assert nr['same_loaded_board_for_all_zones_partitions_Cu_geometry_flash'] and nr['native_saved_reload_Cu_pose_match']
    assert sha(NF / 'actual-full-refill-geometry.json') == nr['actual_full_geometry_SHA256']
    assert sha(NF / 'actual-full-refill-via-flashes.json') == nr['actual_full_flash_SHA256']
    assert sha(NF / 'partitions.json') == nr['partitions_SHA256']
    pose = json.loads((NF / 'before-native-all-FP-pad-pose.json').read_bytes())
    ng = json.loads((NF / 'actual-full-refill-geometry.json').read_bytes())
    flashes = json.loads((NF / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    raw = (STAGE / 'FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb').read_bytes().lower()
    assert b'padstack' not in raw and b'layer_shapes' not in raw and b'custom_pad_primitives' not in raw
    after, ctx, pads, dup = native_header(before, ng, flashes, pose, expected)
    moved = [p['uuid'] for p, n in zip(before['pads'], after['pads']) if (p['x'], p['y']) != (n['x'], n['y'])]
    assert {p['ref'] for p in after['pads'] if p['uuid'] in moved} == {'R10007', 'R10016'} and len(moved) == 4
    groups = all_physical(after, ctx, 'AFTER_ACTUAL_ALL_NET_CPP_FULL_GRAPH')
    oldt = {t['uuid']: t for t in before['tracks']}; newt = {t['uuid']: t for t in after['tracks']}
    removed = set(oldt) - set(newt); added = set(newt) - set(oldt)
    changed = {u for u in set(oldt) & set(newt) if oldt[u] != newt[u]}
    relationships = []; direct = []; roots = {}; source = []; indices = {}
    for ni, (net, old) in enumerate(sorted(oldgroups.items())):
        now = groups.get(net, []); rows, bad = K.contact_losses(old, now, removed)
        relationships.append({'net': net, 'actual_before_groups': len(old), 'actual_after_groups': len(now), 'rows': rows, 'losses': bad})
        for layer in K.LAYERS:
            of = [r for gr in old for r in gr if r['kind'] == 'fill' and r['layer'] == layer]
            nf = [r for gr in now for r in gr if r['kind'] == 'fill' and r['layer'] == layer]
            ot = STRtree([r['shape'] for r in of]); nt = STRtree([r['shape'] for r in nf])
            om = collections.defaultdict(list); nm = collections.defaultdict(list)
            for gr, dest in ((old, om), (now, nm)):
                for rr in gr:
                    if rr['kind'] != 'fill' and rr['layer'] == layer and rr['uuid'] not in removed:
                        dest[rr['kind'], rr['uuid'], layer].append(rr['shape'])
            for key, shapes in om.items():
                body = unary_union(shapes)
                hit = [of[int(i)] for i in ot.query(body.buffer(CONTACT), predicate='intersects') if body.distance(of[int(i)]['shape']) <= CONTACT]
                if not hit: continue
                nb = unary_union(nm.get(key, []))
                nh = [] if nb.is_empty else [nf[int(i)] for i in nt.query(nb.buffer(CONTACT), predicate='intersects') if nb.distance(nf[int(i)]['shape']) <= CONTACT]
                direct.append({'net': net, 'key': list(key), 'ANY_same_raw_actual_fill_touch_retained': bool(nh),
                    'old_touching_zone_UUIDs': sorted({r['uuid'] for r in hit}), 'after_touching_zone_UUIDs': sorted({r['uuid'] for r in nh}),
                    'old_same_zone_touches_not_retained': sorted({r['uuid'] for r in hit} - {r['uuid'] for r in nh})})
        if ni % 50 == 0: put('checkpoint-all-old-contact-counts.json', {'completed': ni, 'relationship_failures': sum(len(r['losses']) for r in relationships), 'direct_losses': sum(not r['ANY_same_raw_actual_fill_touch_retained'] for r in direct)})
    for net, ref, pin in ROOTS:
        old = K.root(oldgroups[net], ref, pin); now = K.root(groups[net], ref, pin); roots[net] = now
        lost = K.keys(old) - K.keys(now) - {('track', u, ly) for u in removed for ly in K.LAYERS}
        source.append({'net': net, 'actual_source': ref + '.' + pin, 'before_named_pads': R.countpad(old), 'after_named_pads': R.countpad(now),
            'before_source_keys': len(K.keys(old)), 'after_source_keys': len(K.keys(now)), 'prior_source_keys_lost': [list(k) for k in sorted(lost)]})
        indices[net] = source_fill_index(old), source_fill_index(now)
    put('all-old-physical-group-relationships.json', relationships)
    put('all-old-direct-native-fill-contacts.json', direct); put('all-nine-actual-source-bank-keys.json', source)
    put('after-all-9971-native-pad-binding.json', pads); put('after-indistinguishable-native-paste-pad-bindings.json', dup)
    oldrefs = []; newrefs = []; positive_before_refs = []
    ground_by_domain = {before['domains_normalized'][net]: net for net, _, _ in ROOTS[:3]}
    for ground, _, _ in ROOTS[:3]:
        oi, ai = indices[ground]; checked = 0; losses = []
        for t in before['tracks']:
            n = L.norm(t['net']); layer = t['layer']
            if t['uuid'] in removed or layer not in K.MAP or n == ground or before['domains_normalized'].get(n) != before['domains_normalized'][ground]: continue
            checked += 1; body = K.A.shape({'kind': 'segment', **t}) if not t.get('m') else L.body(t)
            loss = local_reference_loss(body, oi, ai, K.MAP[layer])
            if not loss.is_empty:
                losses.append({'track_UUID': t['uuid'], 'raw_net': t['net'], 'layer': layer,
                    'literal_actual_before_supported_body_not_supported_after': witness('oldref-' + t['uuid'], loss)})
        oldrefs.append({'ground': ground, 'eligible_retained_track_count': checked, 'losses': losses,
            'formula': 'body intersect local BEFORE source fill, minus local AFTER source fill; ZERO threshold; no own-cap or neighboring aperture waiver'})
        print('R759_OLDREF', ground, checked, len(losses), flush=True)
    # New/changed traces and moved SMDs retain raw full-body deficits separately.
    for uid in sorted(added | changed):
        t = newt[uid]; n = L.norm(t['net']); ground = ground_by_domain.get(after['domains_normalized'].get(n)); layer = t['layer']
        if ground is None or layer not in K.MAP: continue
        body = K.A.shape({'kind': 'segment', **t}) if not t.get('m') else L.body(t)
        holes = unary_union([ctx[0][int(i)] for i in ctx[1].query(body, predicate='intersects')]); physical = body.difference(holes)
        gap = physical.difference(local_supported(physical, indices[ground][1], K.MAP[layer]))
        newrefs.append({'kind': 'track', 'UUID': uid, 'net': t['net'], 'ground': ground, 'layer': layer,
            'actual_all_holes_subtracted_body': info(physical), 'raw_full_body_gap_NO_own_caps_credited': witness('newbody-' + uid, gap),
            'DC_loop_current_and_signal_own_aperture_qualification': 'OPEN_OR_FAIL_SEPARATE; raw gap not automatically mandatory fast-signal failure'})
    for p in after['pads']:
        if p['uuid'] not in moved: continue
        n = L.norm(p['net']); ground = ground_by_domain.get(after['domains_normalized'].get(n))
        for layer, rs in p['layers'].items():
            if ground is None or layer not in K.MAP: continue
            body = unary_union(L.poly(rs)); gap = body.difference(local_supported(body, indices[ground][1], K.MAP[layer]))
            newrefs.append({'kind': 'moved_SMD', 'UUID': p['uuid'], 'ref': p['ref'], 'pin': p['num'], 'ground': ground, 'layer': layer,
                'raw_full_body_gap_NO_neighbor_caps': witness('movedpad-' + p['uuid'], gap)})
    # Preserve actual BEFORE source-supported portions of positive native pours.
    for z in before['zones']:
        n = L.norm(z['net']); ground = ground_by_domain.get(before['domains_normalized'].get(n))
        if ground is None or n == ground: continue
        for layer, rs in z['fills'].items():
            if layer not in K.MAP: continue
            for ci, body in enumerate(L.poly(rs)):
                loss = local_reference_loss(body, indices[ground][0], indices[ground][1], K.MAP[layer])
                if not loss.is_empty: positive_before_refs.append({'zone_UUID': z['uuid'], 'net': z['net'], 'layer': layer, 'contour': ci,
                    'actual_before_supported_native_positive_body_lost': witness('oldpositive-' + z['uuid'] + '-' + layer + '-' + str(ci), loss)})
    put('three-bank-strict-old-routed-body-reference.json', oldrefs)
    put('new-changed-trace-and-moved-SMD-raw-body-references.json', newrefs)
    put('actual-before-supported-positive-native-pour-reference-losses.json', positive_before_refs)
    # Every actual old mask is held; all intended new all6 masks remain observed.
    oldfl = json.loads((N.R157 / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    maskloss = [{'UUID': uid, 'lost_actual_BEFORE_layers': sorted(set(ls) - set(flashes.get(uid, [])))} for uid, ls in oldfl.items() if not set(ls) <= set(flashes.get(uid, []))]
    newmask = [{'UUID': u, 'observed': flashes.get(u, [])} for u in expected['required_NEW_ordinary_all6'] if set(flashes.get(u, [])) != set(K.LAYERS)]
    put('actual-mask-contract-losses.json', {'retained_old': maskloss, 'required_NEW_all6': newmask, 'native_backend_raw_errors': nr['old_actual_or_NEW_ordinary_mask_errors']})
    # Native no-fill areas are hard. This closed-set geometric result is kept
    # separate from CLI rule-provider behavior, including area-zero witnesses.
    nozone = []
    for a in ng['rule_areas']:
        if not a.get('no_fill'): continue
        area = unary_union(L.poly(O.polys(a['outline'])))
        for z in ng['zones']:
            common = set(a['layers']) & set(z['layers'])
            if not common: continue
            outline = unary_union(L.poly(O.polys(z['outline']))); hit = outline.intersection(area)
            if not hit.is_empty: nozone.append({'area_UUID': a['uuid'], 'area_name': a.get('name'), 'zone_UUID': z['uuid'], 'raw_net': z['net'], 'role': 'INTENDED_OUTLINE', 'layers': sorted(common), 'overlap': witness('nozone-outline-' + a['uuid'] + '-' + z['uuid'], hit)})
            for layer in common:
                hit = unary_union(L.poly(O.polys(z['fills'].get(layer, [])))).intersection(area)
                if not hit.is_empty: nozone.append({'area_UUID': a['uuid'], 'zone_UUID': z['uuid'], 'raw_net': z['net'], 'role': 'ACTUAL_CPP_FILL', 'layer': layer, 'overlap': witness('nozone-fill-' + a['uuid'] + '-' + z['uuid'] + '-' + layer, hit)})
    put('actual-native-no-fill-area-closed-set-both-role-intersections.json', nozone)
    # Pin reusable actual graphs/model. No old source arrays or masks substituted.
    mp = OUT / 'actual-combined-full-after-model.pkl'; gp = OUT / 'actual-combined-full-after-all-net-groups.pkl'
    mp.write_bytes(pickle.dumps(after, protocol=5)); gp.write_bytes(pickle.dumps(groups, protocol=5))
    counts = {'old_physical_relationship_losses': sum(len(r['losses']) for r in relationships),
        'old_ANY_same_raw_direct_fill_contact_losses': sum(not r['ANY_same_raw_actual_fill_touch_retained'] for r in direct),
        'nine_source_key_losses': sum(len(r['prior_source_keys_lost']) for r in source),
        'strict_old_routed_reference_losses': sum(len(r['losses']) for r in oldrefs),
        'before_supported_positive_pour_reference_losses': len(positive_before_refs),
        'raw_new_changed_moved_full_body_reference_gaps': sum(not r.get('raw_full_body_gap_NO_own_caps_credited', r.get('raw_full_body_gap_NO_neighbor_caps'))['EMPTY'] for r in newrefs),
        'retained_actual_before_mask_losses': len(maskloss), 'required_NEW_all6_mask_losses': len(newmask),
        'native_no_fill_closed_set_intersections': len(nozone)}
    files = [Path(__file__), EXPECTED, BASE, NF / 'receipt.json', NF / 'actual-full-refill-geometry.json', NF / 'actual-full-refill-via-flashes.json', NF / 'partitions.json', NF / 'before-native-all-FP-pad-pose.json', OUT / 'prepare-receipt.json', STAGE / 'final-stage-manifest.json']
    receipt = {'status': 'ACTUAL_FULL_NATIVE_INCREMENTAL_SOURCE_CONTACT_OLDREFERENCE_PASS_OTHER_GATES_OPEN' if not any(counts.values()) else 'ACTUAL_FULL_NATIVE_DIAGNOSTIC_RAW_FAILURES_REPAIR_REQUIRED',
        'counts': counts, 'all_actual_before_graph_nets': len(oldgroups), 'all_actual_after_graph_nets': len(groups),
        'native_candidate_SHA256': expected['board_sha256'], 'after_actual_model_SHA256': sha(mp), 'after_actual_groups_SHA256': sha(gp),
        'all_9971_physical_pad_UUIDs_343_empty_net_pads_and_duplicate_paste_identities_preserved': True,
        'only_actual_NATIVE_R10007_R10016_moved_pad_poses_used': moved, 'removed_track_UUIDs': sorted(removed),
        'all_nine_source_banks': source, 'same_zone_direct_touch_differences_count': sum(bool(r['old_same_zone_touches_not_retained']) for r in direct),
        'physical_contact_criterion_mm': CONTACT, 'literal_reference_source_and_no_zone_threshold': 0,
        'raw_reference_line_witnesses_preserved': True, 'LOCAL_source_fill_STRtrees_no_repeated_board_wide_union_per_trace': True,
        'actual_source_fill_GAIN_foreign_Cu_native_AND_planner_guard_gate': 'OPEN_SEPARATE_FULL_STATE_CHECK',
        'CPP_pad_partition_comparison_and_signal_own_aperture_ordinary_pairs': 'OPEN_SEPARATE; no raw full-body gap waiver',
        'full_DRC_schematic_parity_source_current_barrel_loop_thermal_SI_fabrication': 'OPEN_OR_FAIL_RETAINED',
        'inherited_CORE_R7_policy_ROOT42_host_reference_and_current_failures': 'PRESERVED_NO_ADOPTION',
        'host_proposed_or_selected_fill_overlay': False, 'manual_native_fill_or_forced_FlashLayer': False,
        'input_SHA256': {str(p): sha(p) for p in files}, 'native_jobs': 0, 'adopted': False, 'manufacturing_ready': False,
        'elapsed_seconds': time.monotonic() - started}
    put('receipt.json', receipt); put('status.json', {'phase': 'COMPLETE', 'counts': counts})
    print('R759_COMPLETE', sha(OUT / 'receipt.json'), counts, flush=True)

if __name__ == '__main__':
    if sys.argv[1:] == ['--prepare']: prepare()
    elif sys.argv[1:] == ['--after']: run_after()
    else: raise SystemExit('Use --prepare or --after; native jobs are never launched here.')
