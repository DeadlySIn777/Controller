"""Exact198b native refill adapter. Preserve trusted complete source pad definitions."""
import json,hashlib,pickle,copy,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
import layout_r1 as L
p=L.p;HERE=L.OUT;DIR=HERE.parent/'native-198b-geometry'
def load():
    old,h,scope,native,prior,omit=L.load();cache=HERE/'fresh-exact-model.pkl';bind=HERE/'fresh-exact-model-binding.json'
    paths=[DIR/'geometry.json',DIR/'actual-via-flashes.json',DIR/'receipt.json',Path(__file__),HERE/'exact-source-model-binding.json']
    hashes={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
    receipt=json.loads((DIR/'receipt.json').read_text());assert receipt['verdict']=='PASS' and receipt['fresh_fill_in_memory'] and not receipt['board_saved']
    assert receipt['inputs_before']==receipt['inputs_after']
    assert receipt['outputs'][str((DIR/'geometry.json').resolve())]==hashes[str((DIR/'geometry.json').resolve())]
    if cache.exists():
        b=json.loads(bind.read_text());assert b['source_hashes']==hashes
        data=cache.read_bytes();assert hashlib.sha256(data).hexdigest()==b['cache_sha256']
        g,scope2=pickle.loads(data)
    else:
        d=json.loads((DIR/'geometry.json').read_text());a=json.loads((DIR/'actual-via-flashes.json').read_text())
        assert a['board_sha256']==L.live.SHA and a['refilled_in_memory']
        assert set(a['vias'])=={v['uuid'] for v in old['vias']}
        g=copy.deepcopy(old)
        newtracks=[];bytrack={r['uuid']:r for r in old['tracks']}
        for r in d['tracks']:
            oldr=bytrack[r['uuid']]
            assert oldr['a']==r['s'] and oldr['b']==r['e'] and oldr['w']==r['w'] and oldr['net']==r['net'] and oldr['layer']==r['layer']
            if 'm' in r:assert oldr.get('kind')=='arc'
            newtracks.append(oldr)
        assert len(newtracks)==len(old['tracks']);g['tracks']=newtracks
        byvia={r['uuid']:r for r in old['vias']}
        for r in d['vias']:
            o=byvia[r['uuid']];assert [o['x'],o['y']]==r['at'] and o['d']==r['w'] and o['drill']==r['drill'] and o['net']==r['net']
        g['vias']=[{**r,'flashed':a['vias'][r['uuid']],'mask_provenance':'fresh198b exact native refill'} for r in old['vias']]
        # Fresh pad export intentionally contains only first-layer polygon. Retain
        # complete unchanged native padstack/hole/graphic data from source binding.
        pp={}
        for r in old['pads']:pp.setdefault((r['ref'],r['num']),[]).append(r)
        for r in d['pads']:
            matches=[o for o in pp[(r['ref'],r['num'])] if [o['x'],o['y']]==r['at'] and o['net']==r['net']]
            if not matches:raise ValueError({'fresh_pad':r,'old_pad':pp[(r['ref'],r['num'])]})
        assert len(d['pads'])==len(old['pads'])
        def polygons(records):return [[row[0],row[1:]] for row in records]
        zones=[{**z,'outline':polygons(z['outline']),'fills':{layer:polygons(rows) for layer,rows in z['fills'].items()}} for z in d['zones']]
        # Native rule-area and graphic definitions are unchanged; complete trusted
        # source geometry carries them in the format used by the existing checker.
        g.update(zones=zones,outline=polygons(d['outline']),refilled=True)
        g['domains_normalized']={p.norm(n):row['domain'] for n,row in d['nets'].items()}
        anchor=next(r for r in g['pads'] if r['ref']=='J11001' and r['num']=='2');rooted={};witness={}
        for layer in ('In1.Cu','In4.Cu'):
            print('ROOTING',layer,flush=True)
            fill=unary_union([poly for z in g['zones'] if p.norm(z['net'])=='/LOGIC_GND' for poly in p.base.polygons(z['fills'].get(layer,[]))])
            own=[poly for pad in g['pads'] if p.norm(pad['net'])=='/LOGIC_GND' for poly in p.base.polygons(pad['layers'].get(layer,[]))]
            own.extend(p.base.body(t) for t in g['tracks'] if t['layer']==layer and p.norm(t['net'])=='/LOGIC_GND')
            own.extend(Point(r['x'],r['y']).buffer(r['d']/2) for r in g['vias'] if p.norm(r['net'])=='/LOGIC_GND' and layer in r['flashed'])
            conductor=unary_union([fill]+own);source=unary_union(p.base.polygons(anchor['layers'][layer]))
            connected=unary_union([part for part in p.hubs.components(conductor) if part.intersects(source)])
            rooted[layer]=fill.intersection(connected)
            witness[layer]={'source':'J11001.2','source_uuid':anchor['uuid'],'actual_LOGIC_via_annuli':sum(p.norm(r['net'])=='/LOGIC_GND' and layer in r['flashed'] for r in g['vias']),'fresh_source_connected_fill_mm2':rooted[layer].area}
        g['_rooted_refs']=rooted
        scope2={**scope,'actual198b_fill_claimed':True,'conservative_r06_fill_only':False,'all_via_flash_masks_fresh198b':True,'native_fresh_source_reference_witnesses':witness,'prospective_new_power_antipads_not_qualified':True}
        data=pickle.dumps((g,scope2),protocol=5);cache.write_bytes(data)
        bind.write_text(json.dumps({'source_hashes':hashes,'cache_sha256':hashlib.sha256(data).hexdigest(),'scope':scope2},indent=2)+'\n')
    p.READS.update(hashes)
    for r in g['vias']:L.live.ACTUAL[r['uuid']]=dict(r)
    model={**g,'tracks':[r for r in g['tracks'] if r['uuid'] not in omit],'vias':[r for r in g['vias'] if r['uuid'] not in omit]}
    candidate=L.stage.caps.moved(model,prior['deltas_mm'])
    return g,candidate,scope2,native,prior,omit
if __name__=='__main__':
    g,h,s,*_=load();print(json.dumps({'pads':len(g['pads']),'vias':len(g['vias']),'tracks':len(g['tracks']),'scope':s}))
