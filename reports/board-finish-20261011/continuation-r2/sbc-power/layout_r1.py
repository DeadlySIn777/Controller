"""Concrete source-bound SBC routing work. Never edits live or invokes KiCad."""
import sys,json,hashlib,copy,math,pickle
from pathlib import Path
from shapely.geometry import Point,LineString,box,mapping
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
POWER=HERE.parents[1]/'power-audit'
sys.path.insert(0,str(POWER))
import prepare_sbc_198b_five_part as A
import sbc_198b_overlay as live
p=A.p;stage=A.stage;C=A.C;six=A.six
OUT=HERE

def load():
    for name in ('PROJECT_MEMORY.md','docs/BUILD_PLAN.md','docs/PLATFORM_ROADMAP.md','docs/MOTHERBOARD_IS2.md','reports/ENGINEERING_STATUS.md','hardware/motherboard_power_entry/README.md','reports/motherboard-power-entry-20260930/core7a-r04/receipt-r04.json'):
        p.read(Path.cwd()/name)
    cache=OUT/'exact-source-model.pkl'; binding=OUT/'exact-source-model-binding.json'
    if cache.exists() and binding.exists():
        b=json.loads(binding.read_text(encoding='utf-8'))
        for path,sha in b['source_hashes'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:raise ValueError('Cached source model input changed '+path)
        data=cache.read_bytes()
        if hashlib.sha256(data).hexdigest()!=b['cache_sha256']:raise ValueError('Generated cache differs')
        g,scope,native=pickle.loads(data)
        p.READS.update(b['source_hashes'])
    else:
        g,scope=live.overlay(); native=p.base.inventory(p.read(live.COMBINED))[3]
        data=pickle.dumps((g,scope,native),protocol=5);cache.write_bytes(data)
        sources={path:sha for path,sha in p.READS.items() if not path.endswith(('PROJECT_MEMORY.md','ENGINEERING_STATUS.md'))}
        binding.write_text(json.dumps({'cache_sha256':hashlib.sha256(data).hexdigest(),'source_hashes':sources},indent=2)+'\n',encoding='utf-8')
    prior=json.loads(p.read(POWER/'sbc-198b-source-proposal/bounded-five-part-fanout-proposal.json'))
    ct={r['uuid'] for r in prior['whole_private_CT_old_manifest']}
    omit=set(C.REMOVED)|A.FANOUT|{A.GND_STUB}|ct
    model=copy.copy(g);model['tracks']=[r for r in g['tracks'] if r['uuid'] not in omit];model['vias']=[r for r in g['vias'] if r['uuid'] not in ct]
    delta=prior['deltas_mm'];candidate=stage.caps.moved(model,delta)
    return g,candidate,scope,native,prior,omit

def body_pad(pad,layer='F.Cu'):return unary_union(p.base.polygons(pad['layers'].get(layer,[])))

def site_errors(g,net,site,diameter=.6,drill=.3,areas=(),source_planes=True):
    """Ordinary through drill: no implicit same-net SMD aperture exception."""
    at=Point(site);rows=[];domain=g['domains_normalized'].get(p.norm(net));radius=diameter/2
    def check(poly,minimum,identity):
        if at.distance(poly)<minimum-1e-8:rows.append({**identity,'gap':at.distance(poly),'required':minimum})
    for pad in g['pads']:
        for layer,records in pad['layers'].items():
            for poly in p.base.polygons(records):
                if p.norm(pad['net'])!=p.norm(net):check(poly,radius+(.15 if g['domains_normalized'].get(p.norm(pad['net']))==domain else .6)+.025,{'kind':'pad','ref':pad['ref'],'pad':pad['num'],'layer':layer})
                if pad['smd']:check(poly,drill/2+.25+.025,{'kind':'ordinary_SMD_hole','ref':pad['ref'],'pad':pad['num'],'layer':layer})
        for poly in p.base.polygons(pad.get('hole') or []):check(poly,radius+.25+.025,{'kind':'pad_hole','uuid':pad['uuid']})
    for r in g['tracks']:
        if p.norm(r['net'])!=p.norm(net):check(p.base.body(r),radius+(.15 if g['domains_normalized'].get(p.norm(r['net']))==domain else .6)+.025,{'kind':'track','uuid':r['uuid'],'layer':r['layer']})
    for r in g['vias']:
        centre=Point(r['x'],r['y']);distance=at.distance(centre)
        if distance<.8-1e-8:rows.append({'kind':'via_pitch','uuid':r['uuid'],'distance':distance})
        if p.norm(r['net'])!=p.norm(net):check(centre,radius+r['d']/2+(.15 if g['domains_normalized'].get(p.norm(r['net']))==domain else .6)+.025,{'kind':'via_copper','uuid':r['uuid']})
        check(centre,radius+r['drill']/2+.25+.025,{'kind':'via_hole','uuid':r['uuid']})
    for layer in g['copper_layers']:
        for poly in p.hard_shapes(g,areas,net,layer,for_via=True):check(poly,radius+.025,{'kind':'rule_barrier','layer':layer})
    for zone in g['zones']:
        if g['domains_normalized'].get(p.norm(zone['net']))!=domain:
            for layer,records in zone['fills'].items():
                for poly in p.base.polygons(records):check(poly,radius+.6+.025,{'kind':'foreign_fill','layer':layer,'uuid':zone['uuid']})
    if source_planes:
        disc=at.buffer(radius+.175)
        for layer in ('In1.Cu','In4.Cu'):
            if not g['_rooted_refs'][layer].covers(disc):rows.append({'kind':'source_ground_reference','layer':layer})
    return rows

def main():
    g,h,scope,native,prior,omit=load();areas=[] if '--physical' in sys.argv else live.reservations();p.WINDOW=box(103,109,249,174)
    via_uid=C.GROUND_VIA
    ground=next(r for r in h['vias'] if r['uuid']==via_uid)
    no_ground={**h,'vias':[r for r in h['vias'] if r['uuid']!=via_uid]}
    local=box(109,158,120,168)
    localg={**no_ground,'pads':[r for r in no_ground['pads'] if local.buffer(3).covers(Point(r['x'],r['y']))],
        'tracks':[r for r in no_ground['tracks'] if p.base.body(r).intersects(local.buffer(2))],
        'vias':[r for r in no_ground['vias'] if local.buffer(2).covers(Point(r['x'],r['y']))],
        'zones':[z for z in no_ground['zones'] if g['domains_normalized'].get(p.norm(z['net']))!='DOM_LOGIC']}
    obstacles=[]
    for pad in localg['pads']:
        for layer,records in pad['layers'].items():
            for poly in p.base.polygons(records):
                if p.norm(pad['net'])!='/LOGIC_GND':obstacles.append(poly.buffer(.3+(.15 if g['domains_normalized'].get(p.norm(pad['net']))=='DOM_LOGIC' else .6)+.025))
                if pad['smd']:obstacles.append(poly.buffer(.15+.25+.025))
        obstacles.extend(poly.buffer(.3+.25+.025) for poly in p.base.polygons(pad.get('hole') or []))
    for r in localg['tracks']:
        if p.norm(r['net'])!='/LOGIC_GND':obstacles.append(p.base.body(r).buffer(.3+(.15 if g['domains_normalized'].get(p.norm(r['net']))=='DOM_LOGIC' else .6)+.025))
    for r in localg['vias']:
        pt=Point(r['x'],r['y']);obstacles.append(pt.buffer(.8))
        if p.norm(r['net'])!='/LOGIC_GND':obstacles.append(pt.buffer(.3+r['d']/2+(.15 if g['domains_normalized'].get(p.norm(r['net']))=='DOM_LOGIC' else .6)+.025))
    for layer in g['copper_layers']:
        obstacles.extend(poly.buffer(.3+.025) for poly in p.hard_shapes(g,areas,'/LOGIC_GND',layer,for_via=True))
    allowed=local.difference(unary_union(obstacles)).intersection(g['_rooted_refs']['In1.Cu'].buffer(-.475)).intersection(g['_rooted_refs']['In4.Cu'].buffer(-.475))
    legal=[];fail=[]
    cap=next(r for r in h['pads'] if r['ref']=='C15001' and r['num']=='2')
    for ix in range(1120,1171):
        for iy in range(1610,1651):
            pt=(ix/10,iy/10)
            if math.dist(pt,(cap['x'],cap['y']))>1.2:continue
            errors=[] if allowed.covers(Point(pt)) else [{'kind':'exact_all_layer_ordinary_geometry'}]
            if not errors:legal.append(pt)
            elif len(fail)<5:fail.append({'site':pt,'errors':errors[:3]})
    print('CAPGND',cap['x'],cap['y'],'LEGAL',len(legal),legal[:30],flush=True)
    fp={p.base.ref_of(ch):{'sha256':hashlib.sha256(ch).hexdigest()} for ch in native.values() if p.base.pcbtext.chunk_kind(ch)=='footprint'}
    contacts={layer:C.contacts(g,native,fp,Point(ground['x'],ground['y']).buffer(.3),'/LOGIC_GND',layer,omit={A.GND_STUB},native_vias=live.ACTUAL) for layer in g['copper_layers']}
    result={'source_sha256':live.SHA,'scope':scope,'C15001_moved_pad2':[cap['x'],cap['y']],'ground_via_to_move':ground,'ground_via_external_contacts':contacts,'legal_relocation_sites':legal,'sample_failures':fail,'removed_ids':sorted(omit),'source_hashes':p.READS}
    dest=OUT/('cap-ground-relocation-physical.json' if '--physical' in sys.argv else 'cap-ground-relocation.json')
    if dest.exists():raise ValueError('Immutable receipt exists')
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
