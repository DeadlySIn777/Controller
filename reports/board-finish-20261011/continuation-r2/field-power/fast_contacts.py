"""Exact physical graph with net filtering before expensive polygon conversion."""
import json
from collections import defaultdict
from shapely.geometry import Point
from shapely.strtree import STRtree
import contact_layout as C
import power_groups as P
def build(g,nets=None,layers=None):
    records=defaultdict(list);domain=g['domains_normalized'];actual=json.loads((C.BASE/'continuation-r2/native-198b-geometry/actual-via-flashes.json').read_text(encoding='utf-8'))['vias']
    def eligible(net):return nets is None or C.norm(net) in nets
    def add(layer,sh,**r):
        if layers is not None and layer not in layers:return
        records[layer].append(dict(r,layer=layer,shape=sh,domain=domain.get(C.norm(r.get('net','')))))
    for q in g['pads']:
        if not eligible(q['net']):continue
        for l,rs in q['layers'].items():
            if layers is not None and l not in layers:continue
            for sh in C.poly(rs):add(l,sh,kind='pad',net=q['net'],ref=q['ref'],pin=q['num'],uuid=q['uuid'])
    for t in g['tracks']:
        if eligible(t['net']) and (layers is None or t['layer'] in layers):add(t['layer'],C.body(t),kind='track',net=t['net'],uuid=t['uuid'],source=t)
    for v in g['vias']:
        if not eligible(v['net']):continue
        mask=v.get('flashed',actual.get(v['uuid']));assert mask is not None,('missing explicit flash evidence',v['uuid'])
        for l in mask:
            if layers is None or l in layers:add(l,Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32),kind='via',net=v['net'],uuid=v['uuid'],source=v,flash_evidence='BOUND_EXPLICIT_EXISTING_OR_PROSPECTIVE_MASK')
    for z in g['zones']:
        if not eligible(z['net']):continue
        for l,rs in z['fills'].items():
            if layers is not None and l not in layers:continue
            for i,sh in enumerate(C.poly(rs)):add(l,sh,kind='fill',net=z['net'],uuid=z['uuid'],contour=i)
    for q in g['shapes']:
        if not eligible(q['net']):continue
        for sh in C.poly(q['poly']):add(q['layer'],sh,kind='graphic',net=q['net'],uuid=q['uuid'])
    return records,{l:STRtree([q['shape'] for q in xs]) for l,xs in records.items()}
def graph(g,net):
    prior=P.build;P.build=build
    try:return P.graph(g,net)
    finally:P.build=prior
def discrete_keys(xs):return {(q['kind'],q['uuid']) for q in xs if q['kind'] in ('pad','track','via')}
