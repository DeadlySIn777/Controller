"""Exact combined host audit; no native/save/board emission."""
import hashlib, json, math, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / 'alternate-r07'))
import screen_r07 as R
import screen_c06 as S
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

NETS = {'/motherboard_io_control/DIC_NRST_N', '/motherboard_acc_control/AI_POWER_GOOD_HOST',
        '/BANK_B_BUFFER_ENABLE_QUALIFIED', '/motherboard_io_control/DI_SAFETY_SUPPLY_FAULT'}


def main():
    audit_paths = [HERE.parent / 'two-zero-via/audit.json', HERE.parent / 'ordinary-batch/audit.json',
                   HERE.parent / 'alternate-r07-small/safety-path-audit-r1.json']
    audits = [json.loads(S.read(path)) for path in audit_paths]
    for audit in audits:
        if audit['source_board_sha256'] != R.R07_SHA or 'PASS' not in audit['verdict']:
            raise ValueError('Unqualified component audit')
        for path, expected in audit['source_files_sha256'].items():
            if hashlib.sha256(S.read(path)).hexdigest() != expected:
                raise ValueError('Frozen input changed: ' + path)
    for path in (Path(__file__), Path(R.__file__), Path(S.__file__), Path(S.overlay_tool.__file__),
                 Path(S.overlay_tool.base.__file__), Path(R.composition.__file__), Path(R.composition.pcbtext.__file__)):
        S.read(path)
    paths = []
    for row in audits[0]['rows']:
        paths.append({'net': row['net'], 'segments': row['segments'], 'new_signal_vias': [],
                      'physical_pad_groups': row['physical_pad_groups'], 'component_audit': str(audit_paths[0])})
    row = audits[1]['rows'][0]
    paths.append({'net': row['net'], 'segments': [row['route']], 'new_signal_vias': [],
                  'physical_pad_groups': row['physical_native_groups'], 'component_audit': str(audit_paths[1])})
    row = audits[2]
    paths.append({'net': row['net'], 'segments': row['route']['segments'],
                  'new_signal_vias': row['route']['new_signal_vias'],
                  'physical_pad_groups': [endpoint['native_group_pad_ids'] for endpoint in row['endpoints']],
                  'component_audit': str(audit_paths[2])})
    if len(paths) != 4 or {S.norm(path['net']) for path in paths} != NETS:
        raise ValueError('Wrong four-net set')
    g, _, overlay = R.overlay_and_targets(); parts = json.loads(S.read(R.R07_PART))
    reserved = json.loads(S.read(HERE.parent / 'alternate-r07/reserved-r07.json'))
    dru = S.read(HERE.parent / 'alternate-r07/reserve/board.kicad_dru').decode(); exemptions = {}
    for line in dru.splitlines():
        match = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if match: exemptions[match.group(1)] = {S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'", match.group(2))}
    print('FOUR_MODEL_START', flush=True); model = S.Model(g, reserved, exemptions); print('FOUR_MODEL_READY', flush=True)
    old = R.composition.inventory(S.read(S.overlay_tool.base.BASE)); current = R.composition.inventory(S.read(R.R07))
    changed = set(current[4]) - {uid for uid, chunk in old[4].items() if current[4].get(uid) == chunk}
    changed_plane = [uid for uid in changed if R.composition.pcbtext.chunk_kind(current[4][uid]) in ('segment', 'arc') and R.composition.pcbtext.chunk_layer(current[4][uid]) in ('In1.Cu', 'In4.Cu')]
    if changed_plane: raise ValueError('Reference-plane track/arc changed')
    all_new_vias = [via for path in paths for via in path['new_signal_vias']]
    if len(all_new_vias) != 2: raise ValueError('Only two approved small signal vias')
    foreign = [via for via in g['vias'] if via['uuid'] in changed and S.norm(via['net']) != '/LOGIC_GND']
    old_cuts = unary_union([Point(via['x'], via['y']).buffer(via['d']/2 + (.15 if g['domains_normalized'].get(S.norm(via['net'])) == 'DOM_LOGIC' else .6) + .025) for via in foreign])
    new_cuts = unary_union([Point(via['point_mm']).buffer(.425) for via in all_new_vias])
    refs, conductive_refs, witnesses = {}, {}, {}
    for layer in ('In1.Cu', 'In4.Cu'):
        fill = unary_union([item['shape'] for item in model.records[layer] if item['kind'] == 'fill' and item['net'] == '/LOGIC_GND'])
        safe = fill.difference(old_cuts).difference(new_cuts)
        own = [item['shape'] for item in model.records[layer] if item['net'] == '/LOGIC_GND' and item['kind'] in ('pad', 'via', 'track')]
        conductive = unary_union([safe] + own); anchor = model.pads['J11001.2#0']
        source = unary_union(S.poly(anchor['layers'][layer]))
        components = [conductive] if conductive.geom_type == 'Polygon' else list(conductive.geoms)
        anchored = unary_union([component for component in components if component.intersects(source)])
        refs[layer] = safe.intersection(anchored); conductive_refs[layer] = anchored
        if not refs[layer].is_valid: raise ValueError('Invalid reference geometry')
        witnesses[layer] = {'source_anchor_pad_id': 'J11001.2#0', 'source_anchor_uuid': anchor['uuid'],
                            'old_foreign_via_cutters': len(foreign), 'new_signal_antipads': 2,
                            'new_signal_antipad_radius_mm': .425}
    barriers = {row['refdes'] for row in json.loads(S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
    additions = []
    for path in paths:
        for segment in path['segments']:
            for a, b in zip(segment['points_mm'], segment['points_mm'][1:]):
                additions.append({'net': S.norm(path['net']), 'layer': segment['layer'], 'kind': 'track',
                                  'shape': LineString([a, b]).buffer(.1)})
        for via in path['new_signal_vias']:
            for layer in g['copper_layers']:
                additions.append({'net': S.norm(path['net']), 'layer': layer, 'kind': 'via', 'shape': Point(via['point_mm']).buffer(.25)})
    rows, failures = [], []
    for path in paths:
        net = S.norm(path['net']); local, gaps = [], {}
        target = {'net': path['net'], 'domain': 'DOM_LOGIC', 'c05_groups': parts['nets'][path['net']],
                  'lost_relationships': [{'r07_connected_pad_ids': sum(path['physical_pad_groups'], [])}]}
        groups = model.contact_groups(target)
        endpoints = [(path['segments'][0]['points_mm'][0], path['segments'][0]['source_uuid'], groups[0]),
                     (path['segments'][-1]['points_mm'][-1], path['segments'][-1]['target_uuid'], groups[1])]
        for point, uid, group in endpoints:
            if not any(item['uuid'] == uid and item['layer'] == path['segments'][0]['layer'] and item['shape'].covers(Point(point)) for item in group['records']):
                local.append({'kind': 'exact_endpoint', 'uuid': uid})
        ref_rows = []
        for segment in path['segments']:
            if segment['width_mm'] != .2 or segment['layer'] not in ('F.Cu', 'B.Cu', 'In3.Cu'): raise ValueError('Unexpected geometry')
            line = LineString(segment['points_mm']); layer = segment['layer']
            if not model.outline.buffer(-.625).covers(line): local.append({'kind': 'board_edge', 'layer': layer})
            for item in model.records[layer]:
                if item['net'] == net: continue
                required = .25 if item['kind'] == 'hole' else .15 if item.get('domain') == 'DOM_LOGIC' else .6
                gap = line.distance(item['shape']) - .1
                key = layer+'/'+item['kind']; gaps[key] = min(gaps.get(key, 999), gap)
                if gap < required+.025-.000001: local.append({'kind': 'existing_trace_clearance', 'uuid': item.get('uuid'), 'layer': layer, 'gap_mm': gap, 'required_mm': required+.025})
            for item in additions:
                if item['net'] != net and item['layer'] == layer:
                    gap = line.distance(item['shape'])-.1
                    if gap < .175-.000001: local.append({'kind': 'cross_path_clearance', 'other_net': item['net'], 'layer': layer, 'gap_mm': gap})
            for item in model.hard[layer]:
                if net not in item['exempt'] and line.buffer(.125).intersects(item['shape']): local.append({'kind': 'rule_reservation', 'layer': layer, 'name': item['name']})
            remainder = line.difference(new_cuts)
            uncovered = {reference: remainder.difference(shape) for reference, shape in refs.items()}
            ref_rows.append({'layer': layer, 'source_connected_reference_both_planes': {name: missing.is_empty for name, missing in uncovered.items()},
                             'uncovered_length_mm': {name: missing.length for name, missing in uncovered.items()}})
            if any(not missing.is_empty for missing in uncovered.values()): local.append({'kind': 'combined_source_reference', 'layer': layer})
        return_rows = []
        for via in path['new_signal_vias']:
            if via['size_mm'] != .5 or via['drill_mm'] != .2: raise ValueError('Unexpected via')
            point = Point(via['point_mm'])
            if not model.outline.buffer(-.775).covers(point): local.append({'kind': 'via_board_edge'})
            for layer in g['copper_layers']:
                for item in model.records[layer]:
                    if item['kind'] == 'hole': required = .25
                    elif item['net'] == net: continue
                    elif item['kind'] == 'fill' and layer in ('In1.Cu', 'In2.Cu', 'In4.Cu') and item.get('domain') == 'DOM_LOGIC': continue
                    else: required = .15 if item.get('domain') == 'DOM_LOGIC' else .6
                    gap = point.distance(item['shape'])-.25
                    if gap < required+.025-.000001: local.append({'kind': 'existing_via_clearance', 'layer': layer, 'uuid': item.get('uuid'), 'gap_mm': gap, 'required_mm': required+.025})
                for item in additions:
                    if item['net'] != net and item['layer'] == layer and point.distance(item['shape'])-.25 < .175-.000001:
                        local.append({'kind': 'cross_path_via_clearance', 'layer': layer, 'other_net': item['net']})
                for item in model.hard[layer]:
                    if net not in item['exempt'] and point.buffer(.275).intersects(item['shape']): local.append({'kind': 'via_rule_reservation', 'layer': layer, 'name': item['name']})
            nearest = min(math.dist(via['point_mm'], [old['x'], old['y']]) for old in g['vias'])
            if nearest < .825-.000001: local.append({'kind': 'ordinary_via_spacing', 'distance_mm': nearest})
            actual = next(old for old in g['vias'] if old['uuid'] == via['return_via']['uuid'])
            distance = math.dist(via['point_mm'], [actual['x'], actual['y']]); circle = Point(actual['x'], actual['y']).buffer(actual['d']/2)
            connected = {layer: S.norm(actual['net']) == '/LOGIC_GND' and shape.intersects(circle) and refs[layer].intersects(circle) and distance <= 1.0+.000001 for layer, shape in conductive_refs.items()}
            return_rows.append({'uuid': actual['uuid'], 'distance_mm': distance, 'source_connected_after_all_new_antipads': connected})
            if not all(connected.values()): local.append({'kind': 'combined_existing_return'})
        for footprint in g['footprints']:
            if footprint['ref'] in barriers:
                for polys in footprint['courtyard'].values():
                    for polygon in S.poly(polys):
                        if any(LineString(segment['points_mm']).buffer(.125).intersects(polygon.buffer(.6)) for segment in path['segments']) or any(Point(via['point_mm']).buffer(.275).intersects(polygon.buffer(.6)) for via in path['new_signal_vias']): local.append({'kind': 'barrier', 'ref': footprint['ref']})
        rows.append({**path, 'reference_checks': ref_rows, 'return_checks': return_rows,
                     'existing_trace_minimum_gaps_mm': gaps, 'failures': local,
                     'verdict': 'HOST_PASS_NATIVE_ELECTRICAL_OPEN' if not local else 'HOST_BLOCKED'})
        failures.extend(local)
    if math.dist(all_new_vias[0]['point_mm'], all_new_vias[1]['point_mm']) < .825: failures.append({'kind': 'new_via_spacing'})
    for path, expected in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected: raise ValueError('Audit input changed: '+path)
    output = {'schema': 'r07-four-path-combined-direct-audit-v1', 'verdict': 'HOST_PASS_NATIVE_ELECTRICAL_OPEN' if not failures else 'HOST_BLOCKED',
              'source_board_sha256': R.R07_SHA, 'rows': rows, 'failures': failures, 'reference_witnesses': witnesses,
              'changed_plane_tracks_or_arcs': changed_plane, 'source_files_sha256': S.READS, 'overlay': overlay,
              'native_jobs': 0, 'gpu_jobs': 0, 'board_emitted': False, 'adopted': False, 'manufacturing_ready': False,
              'limits': ['Host conservative r06 fill over exact actual r07 copper; no fresh current r07 fill',
                         'Reference set difference exactly empty; no acceptance buffer/tolerance',
                         'Native DRC, strict lost=0 against r06 AND actual live r07 required; remaining losses fatal',
                         'Full critical/safety/current/SI and native return/zone-island-neck ledgers remain OPEN']}
    (HERE/'audit.json').write_text(json.dumps(output, indent=1)+'\n', encoding='utf-8')
    print(json.dumps({'audit': str(HERE/'audit.json'), 'verdict': output['verdict'], 'failures': len(failures)}), flush=True)


if __name__ == '__main__': main()
