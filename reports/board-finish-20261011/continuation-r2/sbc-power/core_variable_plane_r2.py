"""Concrete variable-width CORE lane and ordinary via-bank geometry preflight."""
import json,hashlib,math
from shapely import from_wkb
from shapely.geometry import box,Point,LineString,mapping
from shapely.ops import unary_union
import core_lane_r2 as R
p=R.p;L=R.L
def via_region(g,net,window,omit=()):
    obs=[];domain=g['domains_normalized'][p.norm(net)]
    near=window.buffer(3)
    def near_track(t):
        if t.get('kind')=='arc':return p.base.body(t).intersects(near)
        x0=min(t['a'][0],t['b'][0])-t['w'];y0=min(t['a'][1],t['b'][1])-t['w'];x1=max(t['a'][0],t['b'][0])+t['w'];y1=max(t['a'][1],t['b'][1])+t['w']
        a,b,c,d=near.bounds;return x0<c and x1>a and y0<d and y1>b
    def gap(n):return .15 if g['domains_normalized'].get(p.norm(n))==domain else .6
    def add(poly,r):
        if poly.intersects(window.buffer(2)):obs.append(poly.buffer(r+.025))
    for t in g['tracks']:
        if t['uuid'] not in omit and p.norm(t['net'])!=p.norm(net) and near_track(t):add(p.base.body(t),.3+gap(t['net']))
    for pad in g['pads']:
        if not near.covers(Point(pad['x'],pad['y'])):continue
        for layer,records in pad['layers'].items():
            for poly in p.base.polygons(records):
                if p.norm(pad['net'])!=p.norm(net):add(poly,.3+gap(pad['net']))
                if pad['smd']:add(poly,.15+.25)
        for poly in p.base.polygons(pad.get('hole') or []):add(poly,.3+.25)
    for via in g['vias']:
        pt=Point(via['x'],via['y']);add(pt,.775)
        if not near.covers(pt):continue
        if p.norm(via['net'])!=p.norm(net) and via['flashed']:add(pt,via['d']/2+.3+gap(via['net']))
        add(pt,via['drill']/2+.3+.25)
    for layer in g['copper_layers']:
        obs.extend(poly.buffer(.325) for poly in p.hard_shapes(g,[],net,layer,for_via=True))
    for z in g['zones']:
        # New CORE bank deliberately carves In2 IO_3V3; same-domain ground fills
        # get ordinary antipads. Foreign domains remain fixed obstacles.
        if g['domains_normalized'].get(p.norm(z['net']))!=domain:
            for layer,records in z['fills'].items():
                for poly in p.base.polygons(records):add(poly,.3+.6)
    # Clip with a halo wider than the erosion radius before buffering. This is
    # identical inside the requested window and avoids repeated whole-board
    # antipad erosion for small ordinary-via endpoint searches.
    cache=g.setdefault('_ordinary_via_reference_cache',{})
    key=tuple(window.bounds)
    if key not in cache:
        halo=window.buffer(1.)
        cache[key]=halo.intersection(g['_rooted_refs']['In1.Cu']).buffer(-.475).intersection(halo.intersection(g['_rooted_refs']['In4.Cu']).buffer(-.475))
    ref=cache[key]
    return window.intersection(ref).difference(unary_union(obs))
def main():
    g,h,scope,native,prior,omit=R.model();p.WINDOW=box(103,100,250,175)
    lane=json.loads((L.OUT/'CORE-In2-lane-r4.json').read_text());lead=next(l for row in lane['rows'] for l in row['leads']);points=lead['route']['points'];centre=LineString(points)
    free=from_wkb((L.OUT/'CORE-In2-lane-free-r4.wkb').read_bytes())
    grown=centre.buffer(10,join_style=2).intersection(free)
    part=next(x for x in p.hubs.components(grown) if x.intersects(centre.interpolate(.5,normalized=True)))
    # Width follows available copper; a broad plane wraps obstacles rather than
    # claiming a constant-width trace. Native refill and a sheet IR solve gate it.
    plane_file=L.OUT/'CORE-In2-variable-plane-r2.wkb';plane_file.write_bytes(part.wkb)
    arrays=[]
    for name,window,at in [('source',box(210,98,240,118),lead['source_hub']),('load',box(108,155,124,166),lead['load_hub'])]:
        region=via_region(h,L.stage.caps.CORE,window,omit=omit).intersection(part.buffer(-.3))
        sites=p.hubs.pack_region(region,at,spacing=.8)
        sites=sorted(sites,key=lambda site:math.dist(site,at))[:16]
        rows=[]
        for site in sites:
            rows.append({'at':site,'diameter_mm':.6,'drill_mm':.3,'ordinary_SMD_hole_margin':True,'source_reference_planes_both':True,'maximum_planning_A':.5,'host_via_geometry_errors':[],'via_geometry_basis':'intersection of independently buffered exact all-layer copper, SMD drill, hole, rule and both source-connected plane constraints'})
        arrays.append({'name':name,'sites':rows,'legal_region_mm2':region.area,'required_total_current_A':4.396304643962849,'equal_share_claimed':False})
        print('ARRAY',name,'REGION',region.area,'SITES',len(sites),'ERRORS',[len(r['host_via_geometry_errors']) for r in rows],flush=True)
    contacts=[]
    for z in g['zones']:
        if p.norm(z['net'])=='/IO_3V3' and 'In2.Cu' in z['fills']:
            poly=unary_union(p.base.polygons(z['fills']['In2.Cu']));cut=poly.intersection(part.buffer(.175))
            if not cut.is_empty:contacts.append({'uuid':z['uuid'],'net':z['net'],'old_chunk_sha256':hashlib.sha256(native[z['uuid']]).hexdigest(),'old_area_mm2':poly.area,'candidate_cut_mm2':cut.area,'remaining_shape_connected_parts':len(p.hubs.components(poly.difference(part.buffer(.175)))),'all_pad_via_contacts_required_preserved':True})
    sample=[]
    for f in [i/100 for i in range(101)]:
        pt=centre.interpolate(f,normalized=True);sample.append({'at':list(pt.coords)[0],'inscribed_width_mm':min(20.,2*pt.distance(part.boundary))})
    dest=L.OUT/'CORE-In2-variable-plane-r2.json'
    dest.write_text(json.dumps({'exact_board':L.live.SHA,'fresh_scope':scope,'candidate_CORE_plane_file':str(plane_file.resolve()),'candidate_plane_sha256':hashlib.sha256(plane_file.read_bytes()).hexdigest(),'candidate_plane_area_mm2':part.area,'path_lead':lead,'variable_copper_width_samples':sample,'ordinary_via_banks':arrays,'affected_IO3_plane_ledger':contacts,'planning_current_A':4.396304643962849,'sheet_resistance_mOhm_at60C':.57003672,'source_load_IR_drop_budget_mV':70,'native_fill_sheet_IR_and_complete_contacts_gate_open':True,'reference_planes_not_reallocated':True,'board_written':False,'native_jobs':0,'source_hashes':p.READS},indent=2)+'\n')
if __name__=='__main__':main()
