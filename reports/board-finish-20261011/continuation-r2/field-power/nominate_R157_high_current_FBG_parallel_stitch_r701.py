"""Minimal real-source parallel FBG barrel nomination, no board/current claim.

Native foreign fills remain hard in this first bounded nomination. A path is
credited only to actual R157 B copper and actual source-rooted inner Cu.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
process = psutil.Process()
process.cpu_affinity(list(range(16, 28)))
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, json, pickle, hashlib, time, uuid, math, re, collections
from pathlib import Path
import shapely
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H = Path(__file__).resolve().parent
ROOT = H.parent
sys.path.insert(0, str(ROOT))
for directory in ('sbc-power', 'coupled-recovery'):
    sys.path.insert(0, str(ROOT / directory))
import contact_layout as L
import fast_contacts as F
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import R157_native_selected_actual_conversion_r673 as N
OUT = H / 'R157-high-current-FBG-actual-source-parallel-stitch-nomination-r701'
ACTUAL = ROOT / 'R155-known-reference-native-diagnostic-r157/measure'
MODEL = ROOT / 'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
LATER = H / 'R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r687/model.pkl'
REJECTED_PEER = ROOT / 'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r359/only-new-IO3-existing-annulus-bypass-tracks-no-hole-no-delete.pkl'
PEER = ROOT / 'sbc-power/CM79-R371-exact-additive-nine-IO3-tracks-one-LG-full-profile-handoff-r379/only-add-nine-IO3-tracks-one-LG-role-full-profile-no-hole.pkl'
PEER_MODEL = ROOT / 'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl'
DIC = ROOT / 'coupled-recovery/DIC-policy-coupled-exact-sparse-host-scope-supplement-r566/minimal-exact-DIC-coupled-host-supplement.json'
NET = '/motherboard_do/FIELD_B_0V'
RAW = '/motherboard_do{slash}FIELD_B_0V'
OLD = '7a9206b1-d64b-4ebf-9424-6c4d6d434176'
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n', encoding='utf-8')

def info(shape):
    return {'EMPTY': shape.is_empty, 'type': shape.geom_type, 'area_mm2': shape.area,
            'bounds_mm': None if shape.is_empty else list(shape.bounds), 'WKB_SHA256': hashlib.sha256(shape.wkb).hexdigest()}

def main():
    assert not OUT.exists()
    OUT.mkdir()
    start = time.monotonic()
    N.assert_R157_actual_before()
    assert sha(MODEL) == 'ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    assert sha(LATER) == '3449baef41f8da4cdd7458cb120e906017e2e0c488c061aee9343e4b09022ee0'
    g, h, binding, q, c = pickle.loads(MODEL.read_bytes())
    lg, lh, lb, lq, lc = pickle.loads(LATER.read_bytes())
    assert sha(PEER) == '984337a7c2b2d3d0876cfa4ffdbf005aceaca52a4be717bad82e4cffa4d8fd94'
    assert sha(PEER_MODEL) == 'ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b'
    assert sha(REJECTED_PEER) == '4344fc05c41ca86ca7857e8580c6dbc498f920cc2a2ea2e72a70f68671fa31a8'
    peer_packet = pickle.loads(PEER.read_bytes())
    pg, ph, pb, pq, pc = pickle.loads(PEER_MODEL.read_bytes())
    rejected_packet = pickle.loads(REJECTED_PEER.read_bytes())
    rejected_UUIDs = {t['uuid'] for t in rejected_packet['tracks']}
    assert len(rejected_UUIDs) == 7 and not rejected_UUIDs & {t['uuid'] for t in ph['tracks']}
    assert len(peer_packet['tracks']) == 9 and not peer_packet['vias'] and not peer_packet['removed_original_UUIDs']
    assert all(t in ph['tracks'] for t in peer_packet['tracks'])
    assert len(peer_packet['positive_owned_roles']) == 1
    for role in peer_packet['positive_owned_roles']:
        bound = next(z for z in pq if z['uuid'] == role['uuid'])
        assert all(bound[key] == role[key] for key in ('net', 'layer', 'priority', 'clearance_mm', 'min_thickness_mm', 'pad_connect_mode', 'island_removal_mode', 'thermal_gap_mm', 'thermal_bridge_width_mm'))
        assert bound['shape'].wkb == role['shape'].wkb and bound['zone_outline_shape'].wkb == role['zone_outline_shape'].wkb
    put(OUT / 'rejected-versus-current-peer-identity.json', {'rejected_R360_seven_UUIDs': sorted(rejected_UUIDs), 'rejected_seven_present_in_current_R371_h': [], 'current_nine_UUIDs': [t['uuid'] for t in peer_packet['tracks']], 'current_positive_LG_UUIDs': [z['uuid'] for z in peer_packet['positive_owned_roles']], 'current_exact_sparse_only_hard_no_model_overlay_or_source_credit': True})
    del pg, ph, pb, pq, pc
    assert sha(DIC) == '1422c2032032dbd19427486795963924c7a1bdfe72d7a9c998ea3322986de04e'
    dic = json.loads(DIC.read_bytes()); dic_rows = []
    search_window = box(45.248, 204, 50.248, 209)
    for row in dic['exact_new_chunks']:
        path = Path(row['file']); assert sha(path) == row['SHA256']
        parsed = K.A.G.parse(row['UUID'], path.read_bytes(), {})
        if parsed['kind'] == 'via':
            body = Point(*parsed['at']).buffer(parsed['d'] / 2, quad_segs=128)
        else:
            assert parsed['kind'] == 'segment'
            body = LineString([parsed['a'], parsed['b']]).buffer(parsed['w'] / 2, quad_segs=128)
        # AABB distance is a conservative lower bound for every true cap.
        lower_bound = body.envelope.distance(search_window)
        assert lower_bound > 1.1
        dic_rows.append({'UUID': row['UUID'], 'exact_chunk_SHA256': sha(path), 'true_body_containing_AABB_distance_to_entire_search_window_mm': lower_bound, 'required_all6_disjoint_guard_mm': 1.1})
    assert len(dic_rows) == 13
    put(OUT / 'current-DIC-R566-exact-chunk-remote-disjointness-certificate.json', {'recipe_SHA256': sha(DIC), 'exact_new_chunk_rows': dic_rows, 'no_whole_model_overlay_or_source_credit': True})
    ng = json.loads((ACTUAL / 'actual-full-refill-geometry.json').read_bytes())
    flashes = json.loads((ACTUAL / 'actual-full-refill-via-flashes.json').read_bytes())['vias']
    # All-pad actual polygons for strong ordinary aperture and true Cu checks.
    index = collections.defaultdict(list)
    for p in h['pads']:
        index[p['ref'], str(p['num']), p['x'], p['y'], p['net']].append(p)
    replacements = {}
    for p in ng['pads']:
        options = index[p['ref'], str(p['num']), *p['at'], p['net']]
        assert len(options) == 1, ('actual pad identity ambiguity', p['ref'], p['num'], p['at'])
        old = options[0]
        replacements[old['uuid']] = {**old, 'layers': {layer: O.polys(p['poly']) for layer in p['layers']}}
    assert set(replacements) == {p['uuid'] for p in h['pads']}
    actual = {**h, 'pads': [replacements[p['uuid']] for p in h['pads']],
              'vias': [{**v, 'flashed': flashes[v['uuid']]} for v in h['vias']],
              'zones': [{**z, 'fills': {layer: O.polys(rs) for layer, rs in z['fills'].items()}} for z in ng['zones']]}
    groups, missing = N.bound_R663_before_groups({NET})
    assert not missing
    root = K.root(groups[NET], 'J11005', '2')
    source = {layer: unary_union([r['shape'] for r in root if r['layer'] == layer]) for layer in LAYERS}
    old = next(v for v in actual['vias'] if v['uuid'] == OLD)
    assert (old['net'], old['x'], old['y'], old['d'], old['drill']) == (RAW, 47.748, 206.5, .5, .2)
    assert ('via', OLD, 'B.Cu') in K.keys(root)
    rec, trees = F.build({**actual, 'zones': []})
    holes, holetree = K.hole_context(actual)
    via_points = [Point(v['x'], v['y']) for v in actual['vias']]
    via_tree = STRtree(via_points)
    hole_owners = [(v['net'], False, v) for v in actual['vias']]
    for pad in actual['pads']:
        hole_owners.extend((pad['net'], pad['npth'], pad) for shape in L.poly(pad.get('hole') or []))
    assert len(hole_owners) == len(holes)
    fills = collections.defaultdict(list)
    for zone in actual['zones']:
        for layer, records in zone['fills'].items():
            fills[layer].extend((zone, shape) for shape in L.poly(records))
    filltrees = {layer: STRtree([shape for zone, shape in rows]) for layer, rows in fills.items()}
    smds = [(p, unary_union(L.poly(p['layers'].get('F.Cu', [])) + L.poly(p['layers'].get('B.Cu', [])))) for p in actual['pads'] if p['smd']]
    smdtree = STRtree([shape for p, shape in smds])
    rules = []
    for name, condition, what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)', (ACTUAL / 'copy/board.kicad_dru').read_text(encoding='utf-8')):
        kinds = set(what.split())
        if not kinds & {'via', 'track', 'zone'}:
            continue
        names = re.findall(r"A.intersectsArea\('([^']+)'\)", condition)
        assert len(names) == 1, (name, 'unhandled native disallow area condition')
        area = next(a for a in h['rule_areas'] if a.get('name') == names[0])
        exempt = re.findall(r"A.NetName != '([^']+)'", condition)
        rules.append((name, kinds, area, exempt))
    rules.extend((a.get('name', a['uuid']), {kind for kind, flag in [('via', 'no_vias'), ('track', 'no_tracks'), ('zone', 'no_zones')] if a.get(flag)}, a, []) for a in h['rule_areas'])
    candidates, accepted = [], []
    # A finite local search; no universal impossibility claim if it fails.
    grid = [(round(old['x'] + dx / 10, 6), round(old['y'] + dy / 10, 6))
            for dx in range(-25, 26) for dy in range(-25, 26)
            if .825 ** 2 <= (dx / 10) ** 2 + (dy / 10) ** 2 <= 2.5 ** 2]
    grid.sort(key=lambda p: ((p[0] - old['x']) ** 2 + (p[1] - old['y']) ** 2, p))
    def gap(raw):
        return .15 if h['domains_normalized'][L.norm(raw)] == h['domains_normalized'][NET] else .6
    for diameter, drill in [(.8, .4), (.6, .3), (.5, .2)]:
        for x, y in grid:
            center = Point(x, y)
            failures = []
            radial = diameter / 2
            radius = drill / 2 + .275 + 1e-9
            near_hole_indices = [int(i) for i in holetree.query(box(x-radius, y-radius, x+radius, y+radius), predicate='intersects')]
            nearby_holes = [holes[i] for i in near_hole_indices]
            if any(center.distance(hole) - drill / 2 < .275 for hole in nearby_holes):
                continue
            # True round drills, not polygonal chord clearances.
            near_vias = [int(i) for i in via_tree.query(box(x-.825, y-.825, x+.825, y+.825), predicate='intersects')]
            if any(center.distance(via_points[i]) < .825 or center.distance(via_points[i]) - (drill + actual['vias'][i]['drill']) / 2 < .275 for i in near_vias):
                continue
            if any(center.distance(smds[int(i)][1]) - drill / 2 < .275 for i in smdtree.query(box(x-radius, y-radius, x+radius, y+radius), predicate='intersects')):
                continue
            disk = center.buffer(radial, quad_segs=128)
            ownhole = center.buffer(drill / 2, quad_segs=128)
            physical_ann = disk.difference(unary_union(nearby_holes + [ownhole]))
            inner = {layer: physical_ann.intersection(source[layer]) for layer in ['In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu']}
            target_layers = [layer for layer, contact in inner.items() if not contact.is_empty and contact.area >= .01]
            if not target_layers:
                continue
            path = LineString([(old['x'], old['y']), (x, y)])
            track_width = .5
            body = path.buffer(track_width / 2, quad_segs=128)
            for layer in LAYERS:
                for i in trees[layer].query(disk.buffer(.65), predicate='intersects'):
                    row = rec[layer][int(i)]
                    if row['net'] == RAW:
                        continue
                    item = row['source']
                    if row['kind'] == 'via':
                        clearance = center.distance(Point(item['x'], item['y'])) - radial - item['d'] / 2
                    elif row['kind'] == 'track' and item.get('m') is None:
                        clearance = center.distance(LineString([item['a'], item['b']])) - radial - item['w'] / 2
                    else:
                        clearance = center.distance(row['shape']) - radial
                    if clearance < gap(row['net']) + .025:
                        failures.append({'kind': 'via_TRUE_Cu', 'layer': layer, 'foreign_UUID': row['uuid'], 'gap_mm': clearance, 'required_mm': gap(row['net']) + .025})
                for i in filltrees.get(layer, STRtree([])).query(disk.buffer(.65), predicate='intersects'):
                    zone, shape = fills[layer][int(i)]
                    if zone['net'] == RAW:
                        continue
                    required = max(gap(zone['net']), zone['clearance_mm']) + .025
                    distance = center.distance(shape) - radial
                    if distance < required:
                        failures.append({'kind': 'via_ACTUAL_foreign_fill_hard', 'layer': layer, 'foreign_UUID': zone['uuid'], 'gap_mm': distance, 'required_mm': required})
            for i in trees['B.Cu'].query(body.buffer(.65), predicate='intersects'):
                row = rec['B.Cu'][int(i)]
                if row['net'] == RAW:
                    continue
                item = row['source']
                if row['kind'] == 'via':
                    clearance = path.distance(Point(item['x'], item['y'])) - track_width / 2 - item['d'] / 2
                elif row['kind'] == 'track' and item.get('m') is None:
                    clearance = path.distance(LineString([item['a'], item['b']])) - track_width / 2 - item['w'] / 2
                else:
                    clearance = path.distance(row['shape']) - track_width / 2
                if clearance < gap(row['net']) + .025:
                    failures.append({'kind': 'B_stub_TRUE_Cu', 'foreign_UUID': row['uuid'], 'gap_mm': clearance, 'required_mm': gap(row['net']) + .025})
            for i in filltrees.get('B.Cu', STRtree([])).query(body.buffer(.65), predicate='intersects'):
                zone, shape = fills['B.Cu'][int(i)]
                if zone['net'] == RAW:
                    continue
                required = max(gap(zone['net']), zone['clearance_mm']) + .025
                distance = path.distance(shape) - track_width / 2
                if distance < required:
                    failures.append({'kind': 'B_stub_ACTUAL_foreign_fill_hard', 'foreign_UUID': zone['uuid'], 'gap_mm': distance, 'required_mm': required})
            # No unrelated drill is hidden merely because its B annulus is
            # unflashed. Same-net plated source holes may be crossed.
            for i in holetree.query(body.envelope.buffer(.275), predicate='intersects'):
                raw, npth, item = hole_owners[int(i)]
                if raw == RAW and not npth:
                    continue
                distance = path.distance(holes[int(i)]) - track_width / 2
                if 'drill' in item:
                    distance = path.distance(Point(item['x'], item['y'])) - track_width / 2 - item['drill'] / 2
                if distance < .275:
                    failures.append({'kind': 'B_stub_foreign_or_NPTH_hole', 'UUID': item['uuid'], 'gap_mm': distance})
            for layer in LAYERS:
                for peer in lq + peer_packet['positive_owned_roles']:
                    if peer['layer'] != layer or peer['net'] == RAW:
                        continue
                    for role in ('shape', 'zone_outline_shape'):
                        distance = center.distance(peer[role]) - radial
                        required = max(gap(peer['net']), peer['clearance_mm']) + .025
                        if distance < required:
                            failures.append({'kind': 'later_owned_' + role, 'layer': layer, 'foreign_UUID': peer['uuid'], 'gap_mm': distance, 'required_mm': required})
                    if layer == 'B.Cu':
                        distance = path.distance(peer['shape']) - track_width / 2
                        if distance < max(gap(peer['net']), peer['clearance_mm']) + .025:
                            failures.append({'kind': 'B_stub_later_owned', 'foreign_UUID': peer['uuid'], 'gap_mm': distance})
            for item in peer_packet['tracks']:
                clearance = center.distance(LineString([item['a'], item['b']])) - radial - item['w'] / 2
                if clearance < gap(item['net']) + .025:
                    failures.append({'kind': 'SBC_R379_current_hard_sparse_track', 'foreign_UUID': item['uuid'], 'layer': item['layer'], 'gap_mm': clearance, 'required_mm': gap(item['net']) + .025})
            for name, kinds, area, exempt in rules:
                if RAW in exempt:
                    continue
                shape = unary_union(L.poly(area['outline']))
                if 'via' in kinds and set(area['layers']) & set(LAYERS) and not disk.intersection(shape).is_empty:
                    failures.append({'kind': 'actual_native_no_via', 'rule': name})
                if 'track' in kinds and 'B.Cu' in area['layers'] and not body.intersection(shape).is_empty:
                    failures.append({'kind': 'actual_native_no_track', 'rule': name})
            row = {'at_mm': [x, y], 'diameter_mm': diameter, 'drill_mm': drill, 'B_stub_width_mm': track_width,
                   'B_stub_length_mm': path.length, 'actual_inner_source_contact_layers': target_layers,
                   'actual_inner_finite_annular_contacts': {layer: info(inner[layer]) for layer in target_layers},
                   'actual_old_B_source_attachment': info(body.intersection(source['B.Cu'])), 'guard_failures': failures}
            candidates.append(row)
            if failures:
                continue
            uid = str(uuid.uuid5(uuid.UUID(OLD), 'R157-source-ground-current-reinforcement-' + repr((x, y, diameter, drill))))
            trackuid = str(uuid.uuid5(uuid.UUID(uid), 'B-stub'))
            via = {'uuid': uid, 'net': RAW, 'x': x, 'y': y, 'd': diameter, 'drill': drill,
                   'flashed': LAYERS, 'required_native_actual_flash_layers': ['B.Cu'] + target_layers,
                   'prospective_all6_ordinary_NOT_native_flash_credit': True}
            track = {'uuid': trackuid, 'net': RAW, 'a': [old['x'], old['y']], 'b': [x, y], 'layer': 'B.Cu', 'w': track_width}
            accepted.append({'via': via, 'tracks': [track], 'row': row})
            put(OUT / 'first-positive-nominee.json', {**row, 'via_UUID': uid, 'track_UUID': trackuid})
            print('R701 nominee', x, y, diameter, drill, target_layers, flush=True)
            break
        if accepted:
            break
    packet = OUT / 'only-one-new-parallel-FBG-barrel-and-B-source-stub-NOMINEE.pkl'
    packet.write_bytes(pickle.dumps(accepted, protocol=5))
    put(OUT / 'finite-local-search-attempts.json', candidates)
    put(OUT / 'receipt.json', {'status': 'ACTUAL_SOURCE_PARALLEL_STITCH_NOMINEE_PENDING_PEER_AND_CURRENT_AND_ALL_CONTACT_PROOF' if accepted else 'FINITE_HARD_ACTUAL_FILL_PARALLEL_STITCH_NO_NOMINEE',
                               'actual_R157_geometry_SHA256': sha(ACTUAL / 'actual-full-refill-geometry.json'), 'actual_R157_masks_SHA256': sha(ACTUAL / 'actual-full-refill-via-flashes.json'),
                               'source_R663_SHA256': sha(N.R663 / 'receipt.json'), 'later_owned_peer_model_SHA256': sha(LATER),
                               'SBC_R379_current_hard_only_sparse_packet_SHA256': sha(PEER),
                               'SBC_R371_current_peer_model_SHA256': sha(PEER_MODEL),
                               'DIC_R566_remote_exact_sparse_manifest_SHA256': sha(DIC),
                               'rejected_R360_exact_seven_UUIDs_absent_from_current_peer_h_NOT_hard_ghost_obstacles': True,
                               'existing_high_current_via_UUID': OLD, 'conditional_signed_simplex_current_R697_A': 3.3570849395488573,
                               'accepted_geometry_nominees': len(accepted), 'packet_SHA256': sha(packet),
                               'no_new_current_barrel_rating_or_equal_sharing_inferred': True,
                               'no_Cu_hole_flag_profile_rule_or_board_mutation': True, 'native_jobs': 0, 'adopted': False,
                               'exact_SBC_R379_nine_IO3_bodies_and_one_positive_LG_role_hard_screened_without_model_overlay_or_source_credit': True,
                               'normal_new_foreign_antipads_ALL_old_source_direct_reference_and_sharing_native_thermal_gates': 'OPEN',
                               'elapsed_seconds': time.monotonic() - start})
    print('R701_COMPLETE', sha(OUT / 'receipt.json'), 'nominees', len(accepted), flush=True)

if __name__ == '__main__':
    main()
