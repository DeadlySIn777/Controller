"""Compiled exact local ordinary-via centre mask; nomination, not final audit."""
from shapely.geometry import Point
from shapely.ops import unary_union
def legal_centres(model,net,window):
    domain=model.domains[net];scan=window.buffer(1);blocked=[]
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(scan,predicate='intersects'):
            r=model.records[layer][int(i)]
            if r['kind']=='hole':margin=.1+.275
            elif r['kind']=='pad' and model.pads[r['pad_id']]['smd']:
                # Every SMD shape, including own-net, receives the complete
                # .25 aperture + .025 guard + .005 export-error allowance.
                margin=max(.38,.25+(.175 if r.get('domain')==domain else .625)) if r.get('net')!=net else .38
            elif r.get('net')==net:continue
            elif r['kind']=='fill' and r.get('domain')==domain:continue # Prospective exact local-clearance cuts, all contacts/no-split required.
            else:margin=.25+(.175 if r.get('domain')==domain else .625)
            blocked.append(r['shape'].intersection(scan).buffer(margin,resolution=128))
        for h in model.hard[layer]:
            if net not in h['exempt'] and h['shape'].intersects(scan):blocked.append(h['shape'].intersection(scan).buffer(.275,resolution=128))
    for v in model.g['vias']:
        p=Point(v['x'],v['y'])
        if scan.covers(p):blocked.append(p.buffer(.81,resolution=128))
    return window.intersection(model.outline.buffer(-.775)).difference(unary_union(blocked))
