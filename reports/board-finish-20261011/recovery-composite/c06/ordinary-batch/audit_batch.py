"""Independent exact-distance audit of the new zero-via ordinary batch path.

Does not route, modify, save, or refill a board. The prior two frozen paths
are explicit copper obstacles. All native/electrical qualification stays open.
"""
import hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'alternate-r07'))
import screen_r07 as R
import screen_c06 as S
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

SELECT = {'/BANK_B_BUFFER_ENABLE_QUALIFIED'}


def main():
    report = json.loads(S.read(HERE / 'feasibility.json'))
    for path, expected in report['source_files_sha256'].items():
        if hashlib.sha256(S.read(path)).hexdigest() != expected:
            raise ValueError('Frozen screen input changed: ' + path)
    S.read(Path(__file__))
    g, _, overlay = R.overlay_and_targets()
    parts = json.loads(S.read(R.R07_PART))
    two = json.loads(S.read(HERE.parent / 'two-zero-via/audit.json'))
    if two['verdict'] != 'HOST_PASS_NATIVE_OPEN':
        raise ValueError('Prior two-path audit is not passed')
    prior = []
    for row in two['rows']:
        for route in row['segments']:
            for i, (a, b) in enumerate(zip(route['points_mm'], route['points_mm'][1:])):
                uid = 'FROZEN_TWO_' + S.norm(row['net']) + '_' + str(i)
                g['tracks'].append({'uuid': uid, 'net': row['net'], 'a': a, 'b': b,
                                    'w': .2, 'layer': route['layer']})
                prior.append(uid)
    reserved = json.loads(S.read(HERE.parent / 'alternate-r07/reserved-r07.json'))
    dru = S.read(HERE.parent / 'alternate-r07/reserve/board.kicad_dru').decode()
    exemptions = {}
    for line in dru.splitlines():
        m = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if m:
            exemptions[m.group(1)] = {S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'", m.group(2))}
    print('BATCH_DIRECT_MODEL_START', flush=True)
    model = S.Model(g, reserved, exemptions)
    print('BATCH_DIRECT_MODEL_READY', flush=True)
    old = R.composition.inventory(S.read(S.overlay_tool.base.BASE))
    current = R.composition.inventory(S.read(R.R07))
    changed = set(current[4]) - {uid for uid, ch in old[4].items() if current[4].get(uid) == ch}
    changed_plane = [uid for uid in changed
                     if R.composition.pcbtext.chunk_kind(current[4][uid]) in ('segment', 'arc')
                     and R.composition.pcbtext.chunk_layer(current[4][uid]) in ('In1.Cu', 'In4.Cu')]
    if changed_plane:
        raise ValueError('Changed reference-plane track/arc requires a distinct conservative fill audit')
    foreign = [v for v in g['vias'] if v['uuid'] in changed and S.norm(v['net']) != '/LOGIC_GND']
    cuts = unary_union([Point(v['x'], v['y']).buffer(v['d'] / 2 +
             (.15 if g['domains_normalized'].get(S.norm(v['net'])) == 'DOM_LOGIC' else .6) + .025)
             for v in foreign])
    refs, witnesses = {}, {}
    for layer in ('In1.Cu', 'In4.Cu'):
        fills = unary_union([r['shape'] for r in model.records[layer]
                             if r['kind'] == 'fill' and r['net'] == '/LOGIC_GND'])
        safe = fills.difference(cuts)
        own = [r['shape'] for r in model.records[layer]
               if r.get('net') == '/LOGIC_GND' and r['kind'] in ('pad', 'via', 'track')]
        conductive = unary_union([safe] + own)
        anchor = model.pads['J11001.2#0']
        anchor_poly = unary_union(S.poly(anchor['layers'][layer]))
        components = [conductive] if conductive.geom_type == 'Polygon' else list(conductive.geoms)
        source_parts = [component for component in components if component.intersects(anchor_poly)]
        refs[layer] = safe.intersection(unary_union(source_parts))
        witnesses[layer] = {'source_anchor_pad_id': 'J11001.2#0', 'source_anchor_uuid': anchor['uuid'],
                           'source_anchor_xy_mm': [anchor['x'], anchor['y']],
                           'source_component_count': len(source_parts), 'foreign_via_cutters': len(foreign)}
    controlled = {S.norm(n): value for n, value in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    power = {S.norm(n) for n in json.loads(S.read(S.EXT / 'tools/power_widths.json'))}
    barriers = {row['refdes'] for row in json.loads(S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
    rows = []
    for record in report['results']:
        if record['verdict'] != 'HOST_PATH_NATIVE_OPEN':
            continue
        net = S.norm(record['net'])
        if net not in SELECT or len(record['paths']) != 1:
            raise ValueError('Unexpected selected net/path count')
        route = record['paths'][0]
        if route['layer'] != 'F.Cu' or route['width_mm'] != .2 or route['new_vias']:
            raise ValueError('Unexpected zero-via geometry')
        spec = controlled.get(net)
        if not spec or spec.get('class') != 'NONE' or net in power or g['domains_normalized'].get(net) != 'DOM_LOGIC':
            raise ValueError('Controlled, power, or domain policy mismatch')
        target = {'net': record['net'], 'domain': 'DOM_LOGIC', 'c05_groups': parts['nets'][record['net']],
                  'lost_relationships': [{'r07_connected_pad_ids': sum(record['native_before_groups'], [])}]}
        groups = model.contact_groups(target)
        points = route['points_mm']
        line = LineString(points)
        failures, minimum, endpoints = [], {}, []
        for point, group, uid in [(points[0], groups[0], route['source_uuid']),
                                   (points[-1], groups[1], route['target_uuid'])]:
            owner = [r for r in group['records'] if r['uuid'] == uid and r['layer'] == 'F.Cu']
            if not owner or not any(r['shape'].covers(Point(point)) for r in owner):
                failures.append('Exact conductive endpoint/UUID mismatch')
            endpoints.append({'xy_mm': point, 'owner_uuid': uid, 'native_group_pad_ids': group['pad_ids']})
        for obstacle in model.records['F.Cu']:
            if obstacle['net'] == net:
                continue
            gap = .25 if obstacle['kind'] == 'hole' else .15 if obstacle.get('domain') == 'DOM_LOGIC' else .6
            distance = line.distance(obstacle['shape']) - .1
            minimum[obstacle['kind']] = min(minimum.get(obstacle['kind'], 999), distance)
            if distance < gap + .025 - .000001:
                failures.append({'kind': obstacle['kind'], 'uuid': obstacle.get('uuid'), 'net': obstacle['net'],
                                 'copper_gap_mm': distance, 'required_mm': gap + .025})
        for obstacle in model.hard['F.Cu']:
            if net not in obstacle['exempt'] and line.buffer(.125).intersects(obstacle['shape']):
                failures.append({'kind': obstacle['kind'], 'name': obstacle['name']})
        for footprint in g['footprints']:
            if footprint['ref'] in barriers:
                for polys in footprint['courtyard'].values():
                    for shape in S.poly(polys):
                        if line.buffer(.125).intersects(shape.buffer(.6)):
                            failures.append({'kind': 'barrier_courtyard', 'ref': footprint['ref']})
        references = {layer: ref.covers(line) for layer, ref in refs.items()}
        if not all(references.values()):
            failures.append({'kind': 'physical_source_reference', 'layers': references})
        rows.append({'net': record['net'], 'route': route, 'endpoints': endpoints,
                     'physical_native_groups': [group['pad_ids'] for group in groups],
                     'digital_source_policy': spec, 'source_anchor_both_planes': references,
                     'length_mm': line.length, 'minimum_gap_by_kind_mm': minimum,
                     'failures': failures, 'verdict': 'HOST_PASS_NATIVE_OPEN' if not failures else 'FAIL'})
    if len(rows) != 1:
        raise ValueError('Expected one ordinary batch candidate')
    for path, expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Audit input changed: ' + path)
    output = {'schema': 'r07-ordinary-batch-direct-audit-v1',
              'verdict': 'HOST_PASS_NATIVE_OPEN' if all(row['verdict'] == 'HOST_PASS_NATIVE_OPEN' for row in rows) else 'FAIL',
              'source_board_sha256': R.R07_SHA, 'rows': rows, 'reference_witnesses': witnesses,
              'changed_plane_tracks_or_arcs': changed_plane, 'prior_two_added_segments_as_obstacles': prior,
              'overlay': overlay, 'source_files_sha256': S.READS,
              'native_jobs': 0, 'gpu_jobs': 0, 'board_emitted': False, 'adopted': False, 'manufacturing_ready': False,
              'limits': ['Independent direct geometry checks, not fresh current refilled native evidence',
                         'Native DRC, r06/live strict partition guards, fresh return and electrical/SI gates remain open',
                         'Qualified enable net semantics are unchanged; this route is not independent safety-function qualification']}
    (HERE / 'audit.json').write_text(json.dumps(output, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'audit': str(HERE / 'audit.json'), 'verdict': output['verdict']}), flush=True)


if __name__ == '__main__':
    main()
