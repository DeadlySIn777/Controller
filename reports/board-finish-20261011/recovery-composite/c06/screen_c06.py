"""Bounded host-only pure-add signal screen on frozen c05. No native/GPU calls.

Candidate paths use already-contacted copper layers and create no vias. This is
geometry planning, not native or source-anchored return qualification.
"""
import hashlib
import heapq
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
POWER = ROOT / 'power-audit'
sys.path.insert(0, str(POWER))
import prepare_sbc_c05_proposal as overlay_tool
from shapely.geometry import Point, LineString, Polygon, box, mapping
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep
from shapely.strtree import STRtree

WIDTH, MARGIN, STEP = .2, .025, .1
LAYERS = ('F.Cu', 'B.Cu', 'In3.Cu')
REF_LAYER = {'F.Cu': 'In1.Cu', 'B.Cu': 'In4.Cu', 'In3.Cu': 'In4.Cu'}
REF_NET = {'DOM_LOGIC': '/LOGIC_GND', 'DOM_FIELD_A': '/motherboard_motors/FIELD_GND',
           'DOM_AO1': '/motherboard_analog_output/AO1_COM'}
EXT = Path('Z:/pcb-runs/claude-finish')
CONTROLLED = Path('Z:/pcb-runs/impedance/controlled-nets.json')
READS = {}


def read(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    READS[str(path)] = hashlib.sha256(raw).hexdigest()
    return raw


def norm(net): return net.replace('{slash}', '/')
def poly(records): return overlay_tool.base.polygons(records)


class UF:
    def __init__(self): self.p = {}
    def find(self, key):
        self.p.setdefault(key, key)
        if self.p[key] != key: self.p[key] = self.find(self.p[key])
        return self.p[key]
    def join(self, a, b): self.p[self.find(a)] = self.find(b)


class Model:
    def __init__(self, g, reservations, exemptions):
        self.g = g
        self.domains = g['domains_normalized']
        self.records = defaultdict(list)
        self.hard = defaultdict(list)
        self.own = defaultdict(list)
        self.pads = {}
        counts = Counter()
        for pad in g['pads']:
            key = pad['ref'] + '.' + pad['num']
            pid = key + '#' + str(counts[key]); counts[key] += 1
            self.pads[pid] = pad
            for layer, polygons in pad['layers'].items():
                for shape in poly(polygons):
                    record = {'shape': shape, 'net': norm(pad['net']), 'domain': self.domains.get(norm(pad['net'])),
                              'uuid':pad['uuid'], 'kind':'pad', 'pad_id':pid, 'key':('p', pid), 'layer':layer,
                              'sites':[(pad['x'],pad['y'])]}
                    self.records[layer].append(record); self.own[norm(pad['net'])].append(record)
            # No exemption for other-net/nonplated holes. Own PTH terminals are
            # deliberately not used by this bounded first attempt.
            for shape in poly(pad.get('hole') or []):
                for layer in g['copper_layers']:
                    self.records[layer].append({'shape':shape,'net':norm(pad['net']), 'kind':'hole', 'uuid':pad['uuid']})
        for track in g['tracks']:
            shape = overlay_tool.base.body(track)
            if track.get('kind') == 'arc':
                sites = [tuple(shape.representative_point().coords[0])]
            else:
                line=LineString([track['a'],track['b']])
                sites=[tuple(track['a']),tuple(track['b'])]
                sites += [tuple(line.interpolate(i/max(1,math.ceil(line.length)),normalized=True).coords[0])
                          for i in range(1,max(1,math.ceil(line.length)))]
            rec={'shape':shape,'net':norm(track['net']),'domain':self.domains.get(norm(track['net'])),
                 'kind':'track','uuid':track['uuid'],'key':('t',track['uuid']), 'layer':track['layer'], 'sites':sites}
            self.records[track['layer']].append(rec); self.own[norm(track['net'])].append(rec)
        for via in g['vias']:
            p=Point(via['x'],via['y'])
            for layer in g['copper_layers']:
                rec={'shape':p.buffer(via['d']/2), 'net':norm(via['net']), 'domain':self.domains.get(norm(via['net'])),
                     'kind':'via','uuid':via['uuid'],'key':('v',via['uuid']), 'layer':layer, 'sites':[(via['x'],via['y'])]}
                self.records[layer].append(rec); self.own[norm(via['net'])].append(rec)
                self.records[layer].append({'shape':p.buffer(via['drill']/2),'net':norm(via['net']), 'kind':'hole','uuid':via['uuid']})
        for zone in g['zones']:
            for layer, polygons in zone['fills'].items():
                for shape in poly(polygons):
                    self.records[layer].append({'shape':shape,'net':norm(zone['net']), 'domain':self.domains.get(norm(zone['net'])),
                                                'kind':'fill','uuid':zone['uuid']})
        for graphic in g['shapes']:
            for shape in poly(graphic['poly']):
                self.records[graphic['layer']].append({'shape':shape,'net':norm(graphic['net']),
                    'domain':self.domains.get(norm(graphic['net'])),'kind':'graphic','uuid':graphic['uuid']})
        for area in g['rule_areas']:
            if area.get('no_tracks') or area.get('no_zones'):
                for layer in area['layers']:
                    for shape in poly(area['outline']):
                        self.hard[layer].append({'shape':shape,'kind':'native_rule_area','name':area['name'], 'exempt':set()})
        for area in reservations['keepouts']:
            for layer in area['layers']:
                for shape in poly(area['outline']):
                    self.hard[layer].append({'shape':shape,'kind':'reserved_corridor','name':area['name'],
                                             'exempt':exemptions.get(area['name'],set())})
        barrier=json.loads(read(Path('Z:/pcb-runs/domains/barriers.json')))
        refs={item['refdes'] for item in barrier['barriers']}
        for foot in g['footprints']:
            if foot['ref'] in refs:
                for polygons in foot['courtyard'].values():
                    for shape in poly(polygons):
                        # In3 protected approach and through-via barrier are
                        # conservative. Outer layers use real native rule areas.
                        self.hard['In3.Cu'].append({'shape':shape.buffer(.6),'kind':'barrier_courtyard','name':foot['ref'],'exempt':set()})
        for zone in g['zones']:
            if norm(zone['net']) == '/CORE_1V2' and 'In3.Cu' in zone['layers']:
                for shape in poly(zone['outline']):
                    self.hard['In3.Cu'].append({'shape':shape,'kind':'core_supply_region','name':zone['uuid'],'exempt':set()})
        self.trees={layer:STRtree([r['shape'] for r in recs]) for layer,recs in self.records.items()}
        self.hard_trees={layer:STRtree([r['shape'] for r in recs]) for layer,recs in self.hard.items() if recs}
        self.outline=unary_union(poly(g['outline']))

    def contact_groups(self, target):
        net=norm(target['net']); records=self.own[net]; uf=UF()
        for r in records: uf.find(r['key'])
        for layer in self.g['copper_layers']:
            own=[r for r in records if r['layer']==layer]
            if not own: continue
            tree=STRtree([r['shape'] for r in own])
            for i,r in enumerate(own):
                for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
                    if i<j and r['shape'].distance(own[j]['shape']) <= .000002:
                        uf.join(r['key'],own[j]['key'])
        # Native partition membership must be reproduced exactly for this
        # target signal by physical item contact; no nearest-pad attribution.
        host=defaultdict(set)
        for group in target['c05_groups']:
            for pid in group: host[uf.find(('p',pid))].add(pid)
        expected={frozenset(group) for group in target['c05_groups']}
        if {frozenset(group) for group in host.values()} != expected:
            raise ValueError('physical host contact graph differs from saved c05 pad partitions')
        rel=target['lost_relationships'][0]['r07_connected_pad_ids']
        roots={uf.find(('p',pid)) for pid in rel}
        if len(roots)!=2: raise ValueError('expected two lost-relationship contact roots')
        groups=[]
        for root in sorted(roots,key=str):
            # A via's unused plane/layer is not an allowed new transition.
            existing_layers={r['layer'] for r in records if uf.find(r['key'])==root and r['kind'] in ('track','pad')}
            own=[r for r in records if uf.find(r['key'])==root and r['layer'] in existing_layers]
            groups.append({'pad_ids':sorted(host[root]),'records':own,'layers':existing_layers})
        return groups

    def free(self, target, layer, window):
        net=norm(target['net']); domain=target['domain']; obstacles=[]; blockers=[]
        for i in self.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=self.records[layer][i]
            if r['kind']=='hole':
                if r['net']==net: continue  # existing same-net attachment only
                gap=.25
            else:
                if r['net']==net: continue
                gap=.15 if r.get('domain')==domain else .6
            obstacles.append(r['shape'].buffer(gap+WIDTH/2+MARGIN))
            blockers.append({k:r[k] for k in ('kind','uuid','net') if k in r})
        tree=self.hard_trees.get(layer)
        if tree is not None:
            for i in tree.query(window.buffer(2),predicate='intersects'):
                r=self.hard[layer][i]
                if net not in r['exempt']:
                    obstacles.append(r['shape'].buffer(WIDTH/2+MARGIN))
                    blockers.append({'kind':r['kind'],'name':r['name']})
        result=window.intersection(self.outline.buffer(-.5-WIDTH/2-MARGIN)).difference(unary_union(obstacles))
        return result, blockers

    def reference(self, domain, layer, window):
        ref=REF_NET[domain]; plane=REF_LAYER[layer]
        fill=[r['shape'].intersection(window) for r in self.records[plane]
              if r['kind']=='fill' and r['net']==ref and r['shape'].intersects(window)]
        return unary_union(fill)


def seed_sites(group,layer,free,window):
    allowed=prep(free); seeds=[]
    for r in group['records']:
        if r['layer'] != layer or not r['shape'].intersects(window): continue
        for p in r['sites']:
            if allowed.covers(Point(p)): seeds.append((p,r))
        # Exact contact on broad body sections, retaining the existing item's
        # UUID and physical pad component. Sample at the 0.1 mm planner grid.
        available=r['shape'].intersection(free).intersection(window)
        if not available.is_empty:
            for component in getattr(available,'geoms',[available]):
                if component.area < .0000001: continue
                p=tuple(component.representative_point().coords[0])
                if allowed.covers(Point(p)): seeds.append((p,r))
    unique={tuple(round(x,6) for x in p):(p,r) for p,r in seeds}
    return list(unique.values())


def astar(free,start,goals,deadline,node_cap=70000):
    prepared=prep(free); starts=[]; targets={}; cache={}
    def allowed(node):
        if node not in cache: cache[node]=prepared.covers(Point(node[0]*STEP,node[1]*STEP))
        return cache[node]
    def nearby(p):
        nx,ny=[round(x/STEP) for x in p]; candidates=[]
        for dx in range(-3,4):
            for dy in range(-3,4):
                n=(nx+dx,ny+dy); q=(n[0]*STEP,n[1]*STEP)
                if allowed(n) and prepared.covers(LineString([p,q])): candidates.append((math.dist(p,q),n))
        return [n for _,n in sorted(candidates)[:2]]
    for i,(p,r) in enumerate(goals):
        for n in nearby(p): targets.setdefault(n,(p,r))
    for p,r in start:
        for n in nearby(p): starts.append((n,p,r))
    if not starts or not targets: return None,{'reason':'no exact grid attachment','nodes':0}
    # Set-to-set A*: admissible distance to bounding box of targets.
    xs=[n[0] for n in targets]; ys=[n[1] for n in targets]; bounds=(min(xs),min(ys),max(xs),max(ys))
    def h(n): return math.hypot(max(bounds[0]-n[0],0,n[0]-bounds[2]),max(bounds[1]-n[1],0,n[1]-bounds[3]))
    queue=[]; cost={}; previous={}; origin={}
    for n,p,r in starts:
        initial=math.dist(p,(n[0]*STEP,n[1]*STEP))/STEP
        if initial<cost.get(n,math.inf): cost[n]=initial; origin[n]=(p,r); heapq.heappush(queue,(initial+h(n),initial,n))
    while queue and len(cost)<node_cap and time.monotonic()<deadline:
        _,value,n=heapq.heappop(queue)
        if value>cost[n]+1e-9: continue
        if n in targets:
            nodes=[n]
            while nodes[-1] in previous: nodes.append(previous[nodes[-1]])
            nodes.reverse(); p,r=origin[nodes[0]]; q,s=targets[n]
            path=[p]+[(x*STEP,y*STEP) for x,y in nodes]+[q]
            merged=[path[0]]; i=0
            while i<len(path)-1:
                j=len(path)-1
                while j>i+1 and not prepared.covers(LineString([path[i],path[j]])): j-=1
                if math.dist(path[i],path[j])>.000001: merged.append(path[j])
                i=j
            if any(not free.covers(LineString([a,b])) for a,b in zip(merged,merged[1:])):
                raise ValueError('exact line segment escaped free shape')
            return {'points_mm':[[round(x,6),round(y,6)] for x,y in merged],
                    'source_uuid':r['uuid'],'source_kind':r['kind'],'target_uuid':s['uuid'],'target_kind':s['kind']}, {'reason':'exact path','nodes':len(cost)}
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
            nxt=n[0]+dx,n[1]+dy
            if not allowed(nxt): continue
            if not prepared.covers(LineString([(n[0]*STEP,n[1]*STEP),(nxt[0]*STEP,nxt[1]*STEP)])): continue
            candidate=value+math.hypot(dx,dy)
            if candidate<cost.get(nxt,math.inf):
                cost[nxt]=candidate; previous[nxt]=n; heapq.heappush(queue,(candidate+h(nxt),candidate,nxt))
    reason='time budget exhausted' if time.monotonic()>=deadline else 'node budget exhausted' if len(cost)>=node_cap else 'bounded open set exhausted'
    return None,{'reason':reason,'nodes':len(cost)}


def main():
    targets=json.loads(read(HERE/'target-inventory.json'))
    for role,record in targets['source_files'].items():
        if hashlib.sha256(read(record['path'])).hexdigest()!=record['sha256']: raise ValueError('target source changed:'+role)
    controlled=json.loads(read(CONTROLLED))['nets']
    controlled={norm(n):v for n,v in controlled.items()}
    # Source overlay's exact keepout exclusion is expanded to all thirteen
    # target windows; the new fiducial keepout remains outside this rectangle.
    overlay_tool.WINDOW=box(95,40,390,180)
    g,overlay=overlay_tool.overlay()
    READS.update(overlay_tool.READS)
    reservation_path=POWER/'sbc-c05-source-proposal/reserved-c05.json'
    reservation_rules=POWER/'sbc-c05-source-proposal/reserve/board.kicad_dru'
    reservations=json.loads(read(reservation_path)); dru=read(reservation_rules).decode()
    exemptions={}
    for line in dru.splitlines():
        match=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if match: exemptions[match.group(1)]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",match.group(2))}
    read(POWER/'sbc-c05-source-proposal/split-network-screen.json')
    read(EXT/'tools/verify/return_path.py')
    read(Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md'))
    print('MODEL_START',flush=True); model=Model(g,reservations,exemptions); print('MODEL_READY',flush=True)
    results=[]
    for target in targets['targets']:
        name=target['net']; record={'net':name,'domain':target['domain'],'native_lost_relationship':target['lost_relationships'][0],
            'new_vias':0,'new_stitches':0,'width_mm':WIDTH,'layers_screened':[], 'paths':[]}
        spec=controlled.get(norm(name))
        if spec and spec.get('class') not in (None,'NONE'):
            record.update(verdict='WITHHELD_CONTROLLED_GEOMETRY', controlled_spec=spec,
                          reason='Effective provisional IMP class/layer geometry and independent impedance methods must be bound; generic0.2mm is not accepted')
            results.append(record); print(name,record['verdict'],flush=True); continue
        try: groups=model.contact_groups(target)
        except ValueError as error:
            record.update(verdict='WITHHELD_COMPONENT_MODEL',reason=str(error)); results.append(record); print(name,record['verdict'],flush=True); continue
        record['physical_component_pad_ids']=[group['pad_ids'] for group in groups]
        all_shapes=[r['shape'] for group in groups for r in group['records'] if r['layer'] in LAYERS]
        bounds=unary_union(all_shapes).bounds
        # Retained tails can extend far; cap local window around nearest exact
        # component copper contact rather than silently sweeping the board.
        shape_a=unary_union([r['shape'] for r in groups[0]['records'] if r['layer'] in LAYERS])
        shape_b=unary_union([r['shape'] for r in groups[1]['records'] if r['layer'] in LAYERS])
        pa,pb=nearest_points(shape_a,shape_b); window=LineString([pa,pb]).envelope.buffer(8,cap_style=3).envelope
        record['window_mm']=list(window.bounds); deadline=time.monotonic()+24
        for layer in LAYERS:
            if layer not in groups[0]['layers'] or layer not in groups[1]['layers']:
                record['layers_screened'].append({'layer':layer,'reason':'one component has no pre-existing contacted layer; new transition forbidden'})
                continue
            free,blockers=model.free(target,layer,window)
            seeds=[seed_sites(group,layer,free,window) for group in groups]
            detail={'layer':layer,'physical_start_seed_count':len(seeds[0]),'physical_end_seed_count':len(seeds[1]),
                    'obstacle_count':len(blockers),'blockers':blockers}
            if not seeds[0] or not seeds[1]:
                detail['reason']='no existing component copper attachment survives exact clearance/reservations'
                record['layers_screened'].append(detail); continue
            # A continuous candidate reference fill is a separate screen. It
            # uses retained r06 native fill, so source anchor and c05 refill are
            # explicitly open even when geometric continuity survives.
            reference=model.reference(target['domain'],layer,window)
            ref_free=free.intersection(reference)
            ref_seeds=[seed_sites(group,layer,ref_free,window) for group in groups]
            path,search=astar(ref_free,ref_seeds[0],ref_seeds[1],deadline) if all(ref_seeds) else (None,{'reason':'no conservative reference-covered attachment','nodes':0})
            detail['reference_net']=REF_NET[target['domain']]; detail['reference_layer']=REF_LAYER[layer]
            detail['reference_seed_counts']=[len(x) for x in ref_seeds]; detail['search']=search
            if path:
                path.update(layer=layer,width_mm=WIDTH,length_mm=LineString(path['points_mm']).length,
                            reference_net=REF_NET[target['domain']],reference_layer=REF_LAYER[layer],
                            return_source_anchor_proven=False, fresh_c05_fill_proven=False)
                record['paths'].append(path); record['layers_screened'].append(detail); break
            record['layers_screened'].append(detail)
        record['verdict']='HOST_GEOMETRY_PATH_RETURN_UNPROVED' if record['paths'] else 'NO_BOUNDED_ZERO_NEW_VIA_PATH'
        record['reason']='No native/electrical qualification or global impossibility is inferred'
        results.append(record)
        (HERE/'screen-progress.json').write_text(json.dumps({'results':results},indent=1)+'\n')
        print(name,record['verdict'],[(r['layer'],r.get('physical_start_seed_count'),r.get('physical_end_seed_count'),r.get('search',{}).get('reason')) for r in record['layers_screened']],flush=True)
    for path in [Path(__file__),Path(overlay_tool.__file__),Path(overlay_tool.base.__file__)]: read(path)
    for path,expected in READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected: raise ValueError('source changed during screen:'+path)
    report={'schema':'c06-bounded-zero-new-via-screen-v1','source_board_sha256':overlay_tool.C05_SHA,'overlay':overlay,
        'evidence_class':'Host geometric source feasibility only; source anchored return and native electrical proof open',
        'results':results,'source_files_sha256':READS,'adopted':False,'manufacturing_ready':False,'board_emitted':False,
        'new_vias':0,'native_jobs':0,'gpu_jobs':0,'native_baseline_c05_status':'PASS 20completed0lost vsr06; live13losses withheld',
        'limits':['0.1mm grid,70000nodes and24seconds per target, bounded8mm contact-window growth',
          'No new vias or stitches; unused via layers are excluded; at most one existing layer per path',
          'All existing c05 source copper/pad poses retained, conservative r06 foreign refilled copper retained',
          'Filled-reference continuity is geometrically screened; actual c05 refill/source-anchored component and return gate remain unproved',
          'Analog3H aggressor separation, controlled impedance/current/critical/safety review not run; paths cannot be adopted',
          'No-path only applies to this bounded additive model, not global feasibility']}
    output=HERE/'zero-via-screen.json'; output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(output),'paths':sum(bool(r['paths']) for r in results),'targets':len(results)}),flush=True)


if __name__=='__main__': main()
