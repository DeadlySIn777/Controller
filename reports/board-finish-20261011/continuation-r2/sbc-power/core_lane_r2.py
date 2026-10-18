"""Local In2 CORE lane: explicitly repour IO_3V3 only where changed geometry requires."""
import json,hashlib,math,sys
from shapely.geometry import box,Point,LineString,mapping
from shapely.ops import unary_union
import fresh_model_r2 as F
L=F.L;p=L.p
def free_layer(g,net,layer,window,repour_nets=(),reference_guard=.6,allow_own_via_connection=False):
    domain=g['domains_normalized'][p.norm(net)];obs=[]
    def gap(n):return .15 if g['domains_normalized'].get(p.norm(n))==domain else .6
    def add(shape,clear):
        if shape.intersects(window.buffer(3)):obs.append(shape.buffer(clear+.025))
    for t in g['tracks']:
        if t['layer']==layer and p.norm(t['net'])!=p.norm(net):add(p.base.body(t),gap(t['net']))
    for pad in g['pads']:
        if p.norm(pad['net'])!=p.norm(net):
            for poly in p.base.polygons(pad['layers'].get(layer,[])):add(poly,gap(pad['net']))
        for poly in p.base.polygons(pad.get('hole') or []):add(poly,.25)
    for via in g['vias']:
        pt=Point(via['x'],via['y'])
        if layer in via['flashed'] and p.norm(via['net'])!=p.norm(net):add(pt.buffer(via['d']/2),gap(via['net']))
        if not allow_own_via_connection or p.norm(via['net'])!=p.norm(net):add(pt.buffer(via['drill']/2),.25)
    for z in g['zones']:
        if p.norm(z['net']) not in set(repour_nets)|{p.norm(net)}:
            for poly in p.base.polygons(z['fills'].get(layer,[])):add(poly,gap(z['net']))
    for gr in g['shapes']:
        if gr['layer']==layer and p.norm(gr['net'])!=p.norm(net):
            for poly in p.base.polygons(gr['poly']):add(poly,gap(gr['net']))
    obs.extend(poly.buffer(.025) for poly in p.hard_shapes(g,[],net,layer))
    plane='In1.Cu' if layer in ('F.Cu','In2.Cu') else 'In4.Cu'
    reference=window if reference_guard is None else window.buffer(reference_guard+.1).intersection(g['_rooted_refs'][plane]).buffer(-reference_guard)
    if allow_own_via_connection and reference_guard is not None:
        # An existing ordinary plated via has an antipad in the reference plane.
        # Permit only its bounded endpoint escape, not an unreferenced trunk.
        escapes=[Point(v['x'],v['y']).buffer(v['d']/2+.15+reference_guard+.025)
                 for v in g['vias'] if p.norm(v['net'])==p.norm(net)
                 and layer in v['flashed'] and Point(v['x'],v['y']).intersects(window)]
        reference=reference.union(unary_union(escapes))
    return window.intersection(reference).difference(unary_union(obs))
def model():
    g,h,scope,native,prior,omit=F.load();pair=json.loads((L.OUT/'cap-pair-r1.json').read_text());extra={r['uuid'] for r in pair['C15002_new_owned_tracks']}
    h={**h,'tracks':[r for r in h['tracks'] if r['uuid'] not in extra]}
    h=L.stage.caps.moved(h,{'C15001':[1.15,0.],'C15002':[1.,-.9]})
    return g,h,scope,native,prior,set(omit)|extra
def main():
    g,h,scope,native,prior,omit=model();p.WINDOW=box(8,8,442,227) if '--whole' in sys.argv else box(103,100,250,175);rows=[]
    suffix=('r5' if '--whole' in sys.argv else 'r4') if '--exact-reference' in sys.argv else ('r3' if '--whole' in sys.argv else 'r2')
    guard=.025 if '--exact-reference' in sys.argv else .6
    free=free_layer(h,L.stage.caps.CORE,'In2.Cu',p.WINDOW,('/IO_3V3',),reference_guard=guard)
    (L.OUT/('CORE-In2-lane-free-'+suffix+'.wkb')).write_bytes(free.wkb)
    source=Point(224.425,107.15).buffer(8);load=Point(116,161.4).buffer(8)
    for width in (6.,5.,4.,3.,2.5,2.,1.5,1.,.6):
        cs=p.hubs.components(free.buffer(-width/2));shared=[]
        for part in cs:
            if part.intersects(source) and part.intersects(load):
                aa=part.intersection(source).representative_point().coords[0];bb=part.intersection(load).representative_point().coords[0]
                print('ROUTING',width,aa,bb,flush=True)
                route=L.six.five.exact_path(part,aa,bb,step=.5,node_cap=400000)
                if route.get('verdict')=='HOST_PATH':
                    shape=LineString(route['points']).buffer(width/2)
                    contacts={'pads':[],'vias':[],'zones':[]}
                    for pad in g['pads']:
                        if p.norm(pad['net'])=='/IO_3V3' and any(poly.intersects(shape.buffer(.175)) for poly in p.base.polygons(pad['layers'].get('In2.Cu',[]))):contacts['pads'].append({'uuid':pad['uuid'],'ref':pad['ref'],'pad':pad['num']})
                    for via in g['vias']:
                        if p.norm(via['net'])=='/IO_3V3' and Point(via['x'],via['y']).buffer(via['d']/2).intersects(shape.buffer(.175)):contacts['vias'].append({'uuid':via['uuid'],'at':[via['x'],via['y']],'flashed':via['flashed']})
                    for z in g['zones']:
                        if p.norm(z['net'])=='/IO_3V3' and 'In2.Cu' in z['fills']:
                            poly=unary_union(p.base.polygons(z['fills']['In2.Cu']));cut=poly.intersection(shape.buffer(.175))
                            if not cut.is_empty:contacts['zones'].append({'uuid':z['uuid'],'cut_area_mm2':cut.area,'old_chunk_sha256':hashlib.sha256(native[z['uuid']]).hexdigest()})
                    shared.append({'source_hub':aa,'load_hub':bb,'route':route,'contacts':contacts,'trunk_resistance_mOhm_at60C':.57003672*route['length_mm']/width,'full_common_path_drop_mV_at60C':.57003672*route['length_mm']/width*4.396304643962849})
        row={'width_mm':width,'component_count':len(cs),'source_components':[x.area for x in cs if x.intersects(source)],'load_components':[x.area for x in cs if x.intersects(load)],'leads':shared};rows.append(row)
        print('LANE',width,len(cs),len(shared),flush=True)
        if shared:break
    (L.OUT/('CORE-In2-lane-'+suffix+'.json')).write_text(json.dumps({'exact_board_sha256':L.live.SHA,'fresh_scope':scope,'current_A':4.396304643962849,'net':L.stage.caps.CORE,'layer':'In2.Cu','reference':'In1.Cu','source_reference_extra_guard_mm':guard,'window':p.WINDOW.bounds,'rows':rows,'only_power_pour_reallocation':'IO_3V3 locally along chosen exact lane','existing_track_pad_and_actual_annulus_clearance_preserved':True,'hole_clearance_preserved':True,'reference_planes_unchanged':True,'no_current_or_complete_source_landing_proof':True,'native_jobs':0,'board_written':False,'source_hashes':p.READS},indent=2)+'\n')
if __name__=='__main__':main()
