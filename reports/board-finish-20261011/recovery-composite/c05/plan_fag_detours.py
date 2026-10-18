"""Host-only prospective FAG detours against exact c04 copper and conservative r06 fills."""
import hashlib
import heapq
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'power-audit'))
import prepare_sbc_plan as helpers
pcbtext = helpers.pcbtext
SOURCE = HERE.parent / 'e1/c04-four-net-e1-dfm.kicad_pcb'
GEOM = Path('Z:/pcb-runs/claude-finish/agent-work/field-pdn/testA3/w/geom.json')
RESERVE = GEOM.parent / 'design/reserve/reservations.json'
BARRIERS = Path('Z:/pcb-runs/domains/barriers.json')
NET = '/motherboard_motors{slash}FIELD_GND'
WINDOW = box(345, 195, 370, 229)
WIDTH, MARGIN, STEP = 0.3, 0.025, 0.1
TARGETS = ['4df1fdfc-5a5f-4816-bf7b-4f196e3f07a2', '4d3903f2-269c-44cd-b493-37f3b83f9fe2',
           '0921ba5d-8a1a-42f4-843b-845be32970a4']


def sha(data): return hashlib.sha256(data).hexdigest()
def norm(net): return net.replace('{slash}', '/')
def numbers(chunk, key):
    match = re.search(rb'\(' + key.encode() + rb' ([-0-9.eE]+) ([-0-9.eE]+)\)', chunk)
    if not match: raise ValueError('native coordinate absent: ' + key)
    return tuple(float(value) for value in match.groups())
def scalar(chunk, key):
    return float(re.search(rb'\(' + key.encode() + rb' ([-0-9.eE]+)\)', chunk).group(1))
def netname(chunk):
    return json.loads(re.search(rb'\(net ("(?:[^"\\]|\\.)*")\)', chunk).group(1))


def find_path(free, start, end):
    prepared = prep(free)
    for point in (start, end):
        if not prepared.covers(Point(point)):
            return {'verdict': 'ENDPOINT_BLOCKED', 'point': point}
    bounds = tuple(round(value / STEP) for value in WINDOW.bounds)
    x0, y0, x1, y1 = bounds
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) * STEP, np.arange(y0, y1 + 1) * STEP)
    allowed = shapely.contains_xy(free, xs, ys)
    def node(point): return tuple(round(value / STEP) for value in point)
    def point(node): return tuple(round(value * STEP, 6) for value in node)
    source, goal = node(start), node(end)
    def legal(node):
        x, y = node
        return x0 <= x <= x1 and y0 <= y <= y1 and allowed[y-y0, x-x0]
    queue, cost, parent = [(math.dist(source, goal), source)], {source: 0}, {}
    directions = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    while queue:
        _, current = heapq.heappop(queue)
        if current == goal:
            chain = [current]
            while chain[-1] != source: chain.append(parent[chain[-1]])
            path = [point(item) for item in reversed(chain)]
            # Greedy line-of-sight compression is checked against full buffered geometry.
            reduced, index = [path[0]], 0
            while index < len(path)-1:
                last = index+1
                for trial in range(index+1, len(path)):
                    if prepared.covers(LineString([path[index], path[trial]])): last = trial
                reduced.append(path[last]); index = last
            return {'verdict': 'PROSPECTIVE_HOST_PATH', 'points': reduced,
                    'length_mm': LineString(reduced).length, 'expanded_nodes': len(cost)}
        for dx, dy in directions:
            other = (current[0]+dx, current[1]+dy)
            if not legal(other): continue
            new = cost[current] + math.hypot(dx, dy)
            if new >= cost.get(other, float('inf')): continue
            if not prepared.covers(LineString([point(current), point(other)])): continue
            cost[other], parent[other] = new, current
            heapq.heappush(queue, (new + math.dist(other, goal), other))
    return {'verdict': 'NO_PATH_IN_BOUNDED_WINDOW', 'expanded_nodes': len(cost)}


def main():
    raw, geom_raw = SOURCE.read_bytes(), GEOM.read_bytes()
    require_sha = 'abed2445e14ce438464a5e2f8d073eb71dc329a66fc5b882a97b6b5be6b12af7'
    if sha(raw) != require_sha: raise ValueError('frozen c04 source differs')
    g = json.loads(geom_raw)
    if g['sha256'] != helpers.BASE_SHA or g['refilled'] is not True or g['api_errors']: raise ValueError('r06 export differs')
    c03 = json.loads((HERE.parent / 'construction-r1.json').read_text())
    owned = {item['uuid']: item for item in c03['stages']['fag']['additions']}
    domains, obstacles = g['nets'], []
    query = WINDOW.buffer(2)
    def gap(net): return .15 if domains.get(net) == 'DOM_FIELD_A' else .6
    def retain(shape, clearance, label):
        if shape.intersects(query): obstacles.append((shape.buffer(clearance + WIDTH/2 + MARGIN), label))
    current = {pcbtext.chunk_uuid(chunk): chunk for chunk in pcbtext.split(raw)[1] if pcbtext.chunk_uuid(chunk)}
    arcs = {item['uuid']: item for item in g['tracks'] if item.get('kind') == 'arc'}
    for uid, chunk in current.items():
        kind = pcbtext.chunk_kind(chunk)
        if kind == 'segment' and pcbtext.chunk_layer(chunk) == 'In3.Cu':
            net = netname(chunk)
            if norm(net) != norm(NET):
                retain(LineString([numbers(chunk, 'start'), numbers(chunk, 'end')]).buffer(scalar(chunk, 'width')/2), gap(net), uid)
        elif kind == 'arc' and pcbtext.chunk_layer(chunk) == 'In3.Cu':
            net = netname(chunk)
            if norm(net) != norm(NET):
                if uid not in arcs: raise ValueError('new arc cannot be modeled from frozen export')
                retain(helpers.body(arcs[uid]), gap(net), uid)
        elif kind == 'via':
            net, centre = netname(chunk), numbers(chunk, 'at')
            if norm(net) != norm(NET):
                retain(Point(centre).buffer(scalar(chunk, 'size')/2), gap(net), uid)
                retain(Point(centre).buffer(scalar(chunk, 'drill')/2), .25, 'hole:' + uid)
    for pad in g['pads']:
        if norm(pad['net']) != norm(NET):
            for shape in helpers.polygons(pad['layers'].get('In3.Cu', [])): retain(shape, gap(pad['net']), pad['uuid'])
            for shape in helpers.polygons(pad.get('hole') or []): retain(shape, .25, 'hole:' + pad['uuid'])
    for zone in g['zones']:
        if norm(zone['net']) != norm(NET):
            for shape in helpers.polygons(zone['fills'].get('In3.Cu', [])): retain(shape, gap(zone['net']), 'fill:' + zone['uuid'])
        if norm(zone['net']) == '/CORE_1V2' and 'In3.Cu' in zone['layers']:
            for shape in helpers.polygons(zone['outline']): retain(shape, .6, 'CORE_1V2')
    for area in g['rule_areas']:
        if 'In3.Cu' in area['layers'] and (area.get('no_tracks') or 'KEEPOUT' in area.get('name', '').upper()):
            for shape in helpers.polygons(area['outline']): retain(shape, 0, area['name'])
    barrier_refs = {item['refdes'] for item in json.loads(BARRIERS.read_bytes())['barriers']}
    for footprint in g['footprints']:
        if footprint['ref'] in barrier_refs:
            for shapes in footprint['courtyard'].values():
                for shape in helpers.polygons(shapes): retain(shape, .6, 'barrier:' + footprint['ref'])
    reserve = json.loads(RESERVE.read_bytes())
    # Reservation schema is inspected fail-closed before adding its regions.
    print('reservation_schema', list(reserve) if isinstance(reserve, dict) else type(reserve).__name__, flush=True)
    (HERE / 'reservation-inspection.json').write_text(json.dumps(reserve, indent=1) + '\n')
    board = unary_union(helpers.polygons(g['outline'])).buffer(-(.5 + WIDTH/2 + MARGIN))
    free = WINDOW.intersection(board).difference(unary_union([shape for shape, _ in obstacles]))
    plans = []
    for ids, start, end in [(TARGETS[:2], (358.8,203), (353.3,203.2)), ([TARGETS[2]], (353.4,221.4), (359.4,215.8))]:
        for uid in ids:
            if uid not in owned or sha(current[uid]) != owned[uid]['sha256']: raise ValueError('non-FAG target')
        result = find_path(free, start, end)
        result.update(replaced_uuids=ids, start=start, end=end, width_mm=WIDTH, layer='In3.Cu', net=NET)
        if result['verdict'] == 'ENDPOINT_BLOCKED':
            result['blockers'] = [label for shape, label in obstacles if shape.covers(Point(result['point']))]
        plans.append(result)
    report = {'evidence_class':'Prospective host geometry only; reservation screen not yet incorporated',
              'source_board_sha256':sha(raw), 'geometry_export_sha256':sha(geom_raw), 'plans':plans,
              'obstacles_in_window':len(obstacles), 'width_mm':WIDTH, 'margin_mm':MARGIN,
              'native_jobs_started':0, 'adopted':False}
    (HERE / 'prospective-plan.json').write_text(json.dumps(report, indent=1)+'\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
