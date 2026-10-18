"""Read-only host preflight of the partial FIELD_A return donor on actual r07.

This emits no native board, current qualification or acceptance decision.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent.parent
sys.path.insert(0, str(REPORT / 'recovery-composite/c06/alternate-r07'))
import screen_r07 as R
S = R.S
from shapely.geometry import Point, LineString

DONOR = REPORT / 'power-audit/fag-r06/candidate/board.kicad_pcb'
DONOR_SHA = 'a10803bbfa3aa5b7e1a859ca4c5a7b6481969c97dc038a66cef21f92e5f61789'
MARGIN = .025


def main():
    for p in (Path(__file__), Path(R.__file__), Path(S.__file__),
              Path(S.overlay_tool.__file__), Path(S.overlay_tool.base.__file__),
              Path(R.composition.__file__), Path(R.composition.pcbtext.__file__),
              R.PRO, R.DRU, REPORT / 'power-audit/fag-r06/final-proof.json',
              Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md')):
        S.read(p)
    raw = S.read(DONOR)
    if hashlib.sha256(raw).hexdigest() != DONOR_SHA:
        raise ValueError('Donor identity differs')
    g, _, overlay = R.overlay_and_targets()
    before = R.composition.inventory(S.read(S.overlay_tool.base.BASE))
    donor = R.composition.inventory(raw)
    live = R.composition.inventory(S.read(R.R07))
    if donor[0] != before[0] or donor[2] != before[2] or donor[5] != before[5]:
        raise ValueError('Donor changes noncopper definitions')
    if any(donor[4].get(u) != ch for u, ch in before[4].items()):
        raise ValueError('Donor changes original r06 copper')
    additions = {u: ch for u, ch in donor[4].items() if u not in before[4]}
    if len(additions) != 261 or any(u in live[3] for u in additions):
        raise ValueError('Unexpected donor delta or UUID collision')
    reservations = json.loads(S.read(R.HERE / 'reserved-r07.json'))
    rules = S.read(R.HERE / 'reserve/board.kicad_dru').decode()
    exemptions = {}
    for line in rules.splitlines():
        m = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if m:
            exemptions[m[1]] = {S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'", m[2])}
    print('MODEL_START', flush=True)
    model = S.Model(g, reservations, exemptions)
    print('MODEL_READY', flush=True)
    barriers = {r['refdes'] for r in json.loads(S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
    rows = []
    for uid, chunk in additions.items():
        kind = R.composition.pcbtext.chunk_kind(chunk)
        net = S.norm(S.overlay_tool.netname(chunk))
        if net != '/motherboard_motors/FIELD_GND':
            raise ValueError('Unexpected donor net')
        domain = g['domains_normalized'][net]
        if kind == 'segment':
            line = LineString([S.overlay_tool.numbers(chunk, 'start'), S.overlay_tool.numbers(chunk, 'end')])
            radius = S.overlay_tool.scalar(chunk, 'width') / 2
            shape = line.buffer(radius)
            layers = [R.composition.pcbtext.chunk_layer(chunk)]
            point = None
        elif kind == 'via':
            point = Point(S.overlay_tool.numbers(chunk, 'at'))
            radius = S.overlay_tool.scalar(chunk, 'size') / 2
            shape = point.buffer(radius)
            layers = g['copper_layers']
        else:
            raise ValueError('Unsupported donor copper')
        fails = []
        for layer in layers:
            for index in model.trees[layer].query(shape.buffer(.7 + MARGIN)):
                r = model.records[layer][index]
                if r['net'] == net:
                    continue
                gap = .25 if r['kind'] == 'hole' else .15 if r.get('domain') == domain else .6
                # Candidate copper radius, including for existing hole bodies.
                distance = (point if point is not None else line).distance(r['shape']) - radius
                if distance < gap + MARGIN - 1e-6:
                    fails.append({'layer': layer, 'kind': r['kind'], 'uuid': r.get('uuid'),
                                  'net': r['net'], 'gap_mm': distance, 'minimum_mm': gap + MARGIN})
            for hard in model.hard.get(layer, []):
                if net not in hard['exempt'] and shape.buffer(MARGIN).intersects(hard['shape']):
                    fails.append({'layer': layer, 'kind': hard['kind'], 'name': hard['name']})
        if point is not None:
            for v in g['vias']:
                distance = point.distance(Point(v['x'], v['y']))
                if distance < .8 - 1e-6:
                    fails.append({'kind': 'ordinary_via_spacing', 'uuid': v['uuid'],
                                  'centre_mm': distance, 'minimum_mm': .8})
            for area in g['rule_areas']:
                if area.get('no_vias') and any(shape.buffer(MARGIN).intersects(p) for p in S.poly(area['outline'])):
                    fails.append({'kind': 'native_no_vias', 'name': area['name']})
            for foot in g['footprints']:
                if foot['ref'] in barriers and any(shape.buffer(.6 + MARGIN).intersects(p)
                    for polygons in foot['courtyard'].values() for p in S.poly(polygons)):
                    fails.append({'kind': 'barrier_courtyard', 'ref': foot['ref']})
        rows.append({'uuid': uid, 'kind': kind, 'net': net, 'failures': fails})
    for p, expected in S.READS.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != expected:
            raise ValueError('Input changed during host screen: ' + p)
    failed = [r for r in rows if r['failures']]
    result = {'scope': 'Partial 96 mA FIELD_A return donor; source/host geometry only',
              'verdict': 'HOST_BLOCKED' if failed else 'HOST_FEASIBLE_NATIVE_OPEN',
              'live_board_sha256': R.R07_SHA, 'donor_sha256': DONOR_SHA,
              'items': len(rows), 'failing_items': len(failed), 'rows': rows,
              'overlay': overlay, 'source_hashes': S.READS, 'native_jobs': 0,
              'gpu_jobs': 0, 'board_emitted': False, 'adopted': False,
              'manufacturing_ready': False,
              'limits': ['Conservative older r06 foreign fills, exact actual r07 copper',
                         'Donor self-clearance comes only from its separate r06 native measurement',
                         'No fresh r07 fills, native no-loss/DRC, full field load or current/thermal proof']}
    destination = HERE / 'screen.json'
    if destination.exists():
        raise ValueError('Use a distinct receipt folder for a repeated screen')
    destination.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('verdict', 'items', 'failing_items', 'board_emitted')}), flush=True)


if __name__ == '__main__':
    main()
