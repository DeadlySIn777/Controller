"""Read-only direct audit of the two-small-via DI safety-fault proposal.

This is bounded host evidence only; it emits no board or native jobs.
"""
import hashlib, json, math, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'alternate-r07'))
import screen_r07 as R
import screen_c06 as S
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

NET = '/motherboard_io_control/DI_SAFETY_SUPPLY_FAULT'


def main():
    source = json.loads(S.read(HERE / 'feasibility.json'))
    for path, expected in source['source_files_sha256'].items():
        if hashlib.sha256(S.read(path)).hexdigest() != expected:
            raise ValueError('Small-via screen input changed: ' + path)
    S.read(Path(__file__))
    record = next(row for row in source['results'] if S.norm(row['net']) == NET)
    if len(record['paths']) != 1:
        raise ValueError('Expected exactly one candidate path')
    route = record['paths'][0]
    if len(route['segments']) != 3 or len(route['new_signal_vias']) != 2 or route['new_return_vias']:
        raise ValueError('Unexpected dive-return geometry')
    g, targets, overlay = R.overlay_and_targets()
    prior = json.loads(S.read(HERE.parent / 'two-zero-via/audit.json'))
    for row in prior['rows']:
        for segment in row['segments']:
            for i, (a, b) in enumerate(zip(segment['points_mm'], segment['points_mm'][1:])):
                g['tracks'].append({'uuid': 'FROZEN_TWO_' + S.norm(row['net']) + '_' + str(i),
                                    'net': row['net'], 'a': a, 'b': b, 'w': .2, 'layer': segment['layer']})
    reserved = json.loads(S.read(HERE.parent / 'alternate-r07/reserved-r07.json'))
    dru = S.read(HERE.parent / 'alternate-r07/reserve/board.kicad_dru').decode()
    exemptions = {}
    for line in dru.splitlines():
        match = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if match:
            exemptions[match.group(1)] = {S.norm(net) for net in re.findall(r"A\.NetName != '([^']*)'", match.group(2))}
    print('SAFETY_DIRECT_MODEL_START', flush=True)
    model = S.Model(g, reserved, exemptions)
    target = next(target for target in targets if S.norm(target['net']) == NET)
    groups = model.contact_groups(target)
    failures, gaps, endpoints = [], {}, []
    segments = route['segments']
    if [segment['layer'] for segment in segments] != ['F.Cu', 'In3.Cu', 'F.Cu']:
        raise ValueError('Unexpected layer order')
    for segment in segments:
        if segment['width_mm'] != .2:
            raise ValueError('Unexpected width')
        line = LineString(segment['points_mm'])
        layer = segment['layer']
        for obstacle in model.records[layer]:
            if obstacle['net'] == NET:
                continue
            required = .25 if obstacle['kind'] == 'hole' else .15 if obstacle.get('domain') == 'DOM_LOGIC' else .6
            gap = line.distance(obstacle['shape']) - .1
            key = layer + '/' + obstacle['kind']
            gaps[key] = min(gaps.get(key, 999), gap)
            if gap < required + .025 - .000001:
                failures.append({'kind': 'trace_clearance', 'layer': layer, 'uuid': obstacle.get('uuid'),
                                 'net': obstacle['net'], 'gap_mm': gap, 'required_mm': required + .025})
        for obstacle in model.hard[layer]:
            if NET not in obstacle['exempt'] and line.buffer(.125).intersects(obstacle['shape']):
                failures.append({'kind': 'trace_rule_or_reservation', 'layer': layer, 'name': obstacle['name']})
    for point, group, uid in [(segments[0]['points_mm'][0], groups[0], segments[0]['source_uuid']),
                              (segments[-1]['points_mm'][-1], groups[1], segments[-1]['target_uuid'])]:
        owners = [item for item in group['records'] if item['uuid'] == uid and item['layer'] == 'F.Cu']
        if not owners or not any(item['shape'].covers(Point(point)) for item in owners):
            failures.append({'kind': 'endpoint_owner', 'uuid': uid, 'xy_mm': point})
        endpoints.append({'owner_uuid': uid, 'xy_mm': point, 'native_group_pad_ids': group['pad_ids']})
    vias = route['new_signal_vias']
    if segments[0]['points_mm'][-1] != vias[0]['point_mm'] or segments[1]['points_mm'][0] != vias[0]['point_mm'] or segments[1]['points_mm'][-1] != vias[1]['point_mm'] or segments[2]['points_mm'][0] != vias[1]['point_mm']:
        raise ValueError('Exact via/trace endpoint mismatch')
    rule_text = S.read(R.DRU).decode()
    permitted = '(constraint hole_size (min 0.20mm))' in rule_text and '(constraint annular_width (min 0.15mm))' in rule_text
    if not permitted:
        failures.append({'kind': 'small_via_project_permission'})
    controlled = {S.norm(net): spec for net, spec in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    spec = controlled.get(NET)
    if spec and spec.get('class') not in (None, 'NONE'):
        failures.append({'kind': 'controlled_geometry'})
    if NET in {S.norm(net) for net in json.loads(S.read(S.EXT / 'tools/power_widths.json'))}:
        failures.append({'kind': 'power_net'})
    via_rows = []
    for proposed in vias:
        if proposed['size_mm'] != .5 or proposed['drill_mm'] != .2:
            raise ValueError('Unexpected small-via size')
        point = Point(proposed['point_mm'])
        vfail, minimum = [], {}
        for layer in g['copper_layers']:
            for obstacle in model.records[layer]:
                if obstacle['kind'] == 'hole':
                    required = .25
                elif obstacle['net'] == NET:
                    continue
                elif obstacle['kind'] == 'fill' and layer in ('In1.Cu', 'In2.Cu', 'In4.Cu') and obstacle.get('domain') == 'DOM_LOGIC':
                    continue
                else:
                    required = .15 if obstacle.get('domain') == 'DOM_LOGIC' else .6
                # Conservatively compare the NEW COPPER radius to old holes,
                # stronger than drill-to-drill clearance; no via-in-pad waiver.
                gap = point.distance(obstacle['shape']) - .25
                key = layer + '/' + obstacle['kind']
                minimum[key] = min(minimum.get(key, 999), gap)
                if gap < required + .025 - .000001:
                    vfail.append({'kind': 'via_clearance', 'layer': layer, 'uuid': obstacle.get('uuid'),
                                  'net': obstacle['net'], 'gap_mm': gap, 'required_mm': required + .025})
            for obstacle in model.hard[layer]:
                if NET not in obstacle['exempt'] and point.buffer(.275).intersects(obstacle['shape']):
                    vfail.append({'kind': 'via_rule_or_reservation', 'layer': layer, 'name': obstacle['name']})
        nearest = min(math.dist(proposed['point_mm'], [old['x'], old['y']]) for old in g['vias'])
        if nearest < .825 - .000001:
            vfail.append({'kind': 'ordinary_via_spacing', 'distance_mm': nearest, 'required_mm': .825})
        via_rows.append({'proposal': proposed, 'minimum_gap_by_layer_kind_mm': minimum,
                         'nearest_existing_via_mm': nearest, 'failures': vfail})
        failures.extend(vfail)
    if math.dist(vias[0]['point_mm'], vias[1]['point_mm']) < .825:
        failures.append({'kind': 'new_via_spacing'})
    old = R.composition.inventory(S.read(S.overlay_tool.base.BASE))
    current = R.composition.inventory(S.read(R.R07))
    changed = set(current[4]) - {uid for uid, chunk in old[4].items() if current[4].get(uid) == chunk}
    changed_plane = [uid for uid in changed if R.composition.pcbtext.chunk_kind(current[4][uid]) in ('segment', 'arc') and R.composition.pcbtext.chunk_layer(current[4][uid]) in ('In1.Cu', 'In4.Cu')]
    if changed_plane:
        raise ValueError('Changed plane track/arc audit required')
    foreign = [v for v in g['vias'] if v['uuid'] in changed and S.norm(v['net']) != '/LOGIC_GND']
    old_cuts = unary_union([Point(v['x'], v['y']).buffer(v['d'] / 2 + (.15 if g['domains_normalized'].get(S.norm(v['net'])) == 'DOM_LOGIC' else .6) + .025) for v in foreign])
    new_cuts = unary_union([Point(via['point_mm']).buffer(.25 + .15 + .025) for via in vias])
    references, reference_rows = {}, {}
    for layer in ('In1.Cu', 'In4.Cu'):
        fill = unary_union([item['shape'] for item in model.records[layer] if item['kind'] == 'fill' and item['net'] == '/LOGIC_GND'])
        safe = fill.difference(old_cuts).difference(new_cuts)
        own = [item['shape'] for item in model.records[layer] if item['net'] == '/LOGIC_GND' and item['kind'] in ('pad', 'via', 'track')]
        conductive = unary_union([safe] + own)
        anchor = model.pads['J11001.2#0']
        source = unary_union(S.poly(anchor['layers'][layer]))
        components = [conductive] if conductive.geom_type == 'Polygon' else list(conductive.geoms)
        anchored = unary_union([component for component in components if component.intersects(source)])
        references[layer] = safe.intersection(anchored)
        if not references[layer].is_valid:
            raise ValueError('Invalid conservative source-reference polygon')
        return_rows = []
        for via in via_rows:
            ret = via['proposal']['return_via']
            actual = next(old for old in g['vias'] if old['uuid'] == ret['uuid'])
            actual_net = S.norm(actual['net'])
            circle = Point(actual['x'], actual['y']).buffer(actual['d'] / 2)
            distance = math.dist(via['proposal']['point_mm'], [actual['x'], actual['y']])
            joined = actual_net == '/LOGIC_GND' and anchored.intersects(circle) and safe.intersects(circle) and distance <= 1.0 + .000001
            return_rows.append({'uuid': actual['uuid'], 'xy_mm': [actual['x'], actual['y']], 'net': actual_net,
                                'signal_distance_mm': distance, 'source_connected_after_new_antipads_host': joined})
            if not joined:
                failures.append({'kind': 'existing_return_via_not_source_connected', 'layer': layer, 'uuid': actual['uuid']})
        covered, uncovered = [], []
        for segment in segments:
            remainder = LineString(segment['points_mm']).difference(new_cuts)
            missing = remainder.difference(references[layer])
            # GEOS covers() can return false for an exactly clipped antipad
            # boundary even when its set difference is empty. Require empty
            # difference, without widening the reference polygon or allowing
            # any nonzero missing interval.
            covered.append(missing.is_empty)
            uncovered.append({'length_mm': missing.length,
                              'bounds_mm': list(missing.bounds) if not missing.is_empty else [],
                              'wkt': missing.wkt,
                              'raw_covers_predicate': references[layer].covers(remainder),
                              'set_difference_empty': missing.is_empty,
                              'total_missing_length_below_1nm': missing.length <= .000001})
        # Require BOTH source references, stronger than the layer-specific map.
        if not all(covered):
            failures.append({'kind': 'source_reference_gap_after_new_antipads', 'layer': layer, 'segments': covered})
        reference_rows[layer] = {'source_anchor': 'J11001.2#0', 'source_anchor_uuid': anchor['uuid'],
                                 'returns': return_rows, 'all_segments_covered_outside_signal_antipads': covered}
        reference_rows[layer]['uncovered_geometry_diagnostics'] = uncovered
    barriers = {row['refdes'] for row in json.loads(S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
    for footprint in g['footprints']:
        if footprint['ref'] not in barriers:
            continue
        for polygons in footprint['courtyard'].values():
            for polygon in S.poly(polygons):
                if any(LineString(segment['points_mm']).buffer(.125).intersects(polygon.buffer(.6)) for segment in segments) or any(Point(via['point_mm']).buffer(.275).intersects(polygon.buffer(.6)) for via in vias):
                    failures.append({'kind': 'galvanic_barrier', 'ref': footprint['ref']})
    for path, expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Audit input changed: ' + path)
    output = {'schema': 'r07-small-via-safety-fault-direct-audit-v1',
              'verdict': 'HOST_GEOMETRY_PASS_NATIVE_ELECTRICAL_OPEN' if not failures else 'HOST_BLOCKED',
              'net': record['net'], 'source_board_sha256': R.R07_SHA, 'route': route,
              'endpoints': endpoints, 'trace_minimum_gaps_mm': gaps, 'vias': via_rows,
              'reference_audit': reference_rows, 'changed_plane_tracks_or_arcs': changed_plane,
              'failures': failures, 'source_files_sha256': S.READS, 'overlay': overlay,
              'native_jobs': 0, 'gpu_jobs': 0, 'board_emitted': False, 'adopted': False, 'manufacturing_ready': False,
              'limits': ['Conservative old refilled reference geometry, no fresh actual r07 refill',
                         'Reference antipads are a host screen; IO3V3 neck/zone/island loss and return ledgers remain unqualified',
                         'Native DRC, strict no-loss versus both r06 and actual live r07, full critical/safety/current/SI qualification required',
                         'No D4/VIPPO/antipad service exception or new ground stitch claimed']}
    output['reference_predicate_policy'] = 'Valid reference polygon; uncovered set must be exactly empty. No buffer/tolerance used for acceptance.'
    output['supersedes_predicate_only_debug_report'] = str(HERE / 'safety-path-predicate-debug.json')
    (HERE / 'safety-path-audit-r1.json').write_text(json.dumps(output, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'audit': str(HERE / 'safety-path-audit-r1.json'), 'verdict': output['verdict'], 'failures': len(failures)}), flush=True)


if __name__ == '__main__':
    main()
