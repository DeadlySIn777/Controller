"""Finite analog decoupling transition probe; no board emission or qualification."""
import collections, hashlib, json, math, re, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE / 'coupled-recovery'))
import audit_aux_exact_raw as A
import native_flash_model as NF
import ordinary_routes as F
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
S,C,P,G = A.S,A.C,A.P,A.G
OUT = HERE / 'ao1-vref-coplan-r4'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def main():
    if OUT.exists(): raise ValueError('Fresh analog probe output required')
    OUT.mkdir()
    F.OUT = OUT
    started=time.monotonic()
    oldraw=A.read(G.SOURCE)
    parent=HERE / 'combined-power-source-native-r3-c92/combined-power-source-c92-corrected.kicad_pcb'
    newraw=A.read(parent)
    if sha(newraw) != '45c85ce62a624b3dc31127534a7fd434bf5bedac560da046538542d10395c603': raise ValueError('Combined parent pin mismatch')
    old,new=C.inventory(oldraw),C.inventory(newraw)
    native=json.loads(A.read(A.NATIVE / 'geometry.json'))
    template=json.loads(A.read(S.overlay_tool.base.GEOM))
    original=C.inventory(A.read(S.overlay_tool.base.BASE))
    template,proof=A.fresh_template(original,old,template,native)
    g=P.geometry(old[4],template)
    reserved,ex=A.reservations()
    masks=json.loads(A.read(A.NATIVE / 'actual-via-flashes.json'))['vias']
    model=NF.Model(g,reserved,ex,native['vias'],masks)
    annulus=model.source_annulus_proof
    region=box(370,125,381,133)
    changed_cu=set(old[4]) ^ set(new[4])
    changed_cu |= {u for u in old[4].keys() & new[4].keys() if old[4][u] != new[4][u]}
    separation=[]
    for u in changed_cu:
        for inv in (old,new):
            if u not in inv[4]: continue
            obj=G.parse(u,inv[4][u],{})
            body=A.shape(obj)
            d=body.distance(region)
            if d < 2: raise ValueError('Combined changed copper enters analog audit region: '+u)
            separation.append(d)
    changed_fp=[u for u in old[3].keys() | new[3].keys() if C.pcbtext.chunk_kind(new[3].get(u,old[3].get(u)))=='footprint' and old[3].get(u)!=new[3].get(u)]
    for u in changed_fp:
        for inv in (old,new):
            if u not in inv[3]: continue
            ch=inv[3][u]
            match=re.search(rb'\n\t\t\(at\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)',ch)
            if not match: raise ValueError('Changed footprint pose unavailable')
            at=tuple(float(v) for v in match.groups())
            # A generous20mm body radius bounds every changed regulator/cap.
            if Point(at).buffer(20).distance(region)<2: raise ValueError('Changed footprint body may enter analog region: '+u)
    net='/motherboard_analog_output/AO1_VREF'
    domain='DOM_AO1'
    padids=['C14643.1#0','U14626.9#0']
    pads={p: model.pads[p] for p in padids}
    if any(S.norm(p['net']) != net for p in pads.values()): raise ValueError('Analog pad contract differs')
    if set(pads[padids[0]]['layers']) != {'B.Cu'} or set(pads[padids[1]]['layers']) != {'F.Cu'}: raise ValueError('Analog pad copper side differs')
    pad_shapes={p:unary_union(S.poly(next(iter(pads[p]['layers'].values())))) for p in padids}
    oldvias={v['uuid']:v for v in g['vias']}
    smd=STRtree([q for pad in g['pads'] if pad['smd'] for layer,polys in pad['layers'].items() if layer in ['F.Cu','B.Cu'] for q in S.poly(polys)])
    rows=[]
    for d,drill in [(0.5,0.2),(0.6,0.3)]:
        for at in [(377.3+i*.1,129+j*.1) for i in range(23) for j in range(-2,3)] + [(374.25-i*.1,129+j*.1) for i in range(35) for j in range(-2,3)]:
            at=tuple(round(v,6) for v in at)
            body=Point(at).buffer(d/2,resolution=128)
            hole=Point(at).buffer(drill/2,resolution=128)
            errors=[];cuts=[];nearest=collections.defaultdict(lambda:1000.)
            if len(smd.query(hole.buffer(.275),predicate='intersects')): errors.append('drill_to_SMD_pad')
            for v in g['vias']:
                if math.dist(at,(v['x'],v['y'])) < .8-1e-9: errors.append('ordinary_via_pitch'); break
            for layer in g['copper_layers']:
                for i in model.trees[layer].query(body.buffer(.675),predicate='intersects'):
                    rec=model.records[layer][i]
                    if rec['kind']=='hole':
                        gap=hole.distance(rec['shape']);req=.275
                    elif rec.get('net') == net: continue
                    elif rec['kind']=='fill' and rec.get('domain')==domain:
                        if body.buffer(.175).intersects(rec['shape']): cuts.append({'uuid':rec['uuid'],'layer':layer,'net':rec['net'],'antipad_radius_mm':d/2+.176})
                        continue
                    else:
                        gap=body.distance(rec['shape']);req=.175 if rec.get('domain')==domain else .625
                    nearest[rec['kind']]=min(nearest[rec['kind']],gap)
                    if gap < req-1e-9: errors.append(layer+':'+rec['kind']+':'+str(rec.get('uuid')))
                for hard in model.hard[layer]:
                    if net not in hard['exempt'] and body.buffer(.025).intersects(hard['shape']): errors.append(layer+':hard_reservation')
            route_errors=[]
            routes=[]
            for pad_id,layer in zip(padids,['B.Cu','F.Cu']):
                pt=(pads[pad_id]['x'],pads[pad_id]['y'])
                route=LineString([pt,at]).buffer(.1,resolution=128)
                for i in model.trees[layer].query(route.buffer(.675),predicate='intersects'):
                    rec=model.records[layer][i]
                    if rec.get('net')==net or rec['kind']=='hole' and rec.get('net')==net: continue
                    if rec['kind']=='fill' and rec.get('domain')==domain: continue
                    req=.275 if rec['kind']=='hole' else .175 if rec.get('domain')==domain else .625
                    if route.distance(rec['shape']) < req-1e-9: route_errors.append(layer+':'+rec['kind']+':'+str(rec.get('uuid')))
                for hard in model.hard[layer]:
                    if net not in hard['exempt'] and route.buffer(.025).intersects(hard['shape']): route_errors.append(layer+':hard_reservation')
                routes.append({'pad':pad_id,'layer':layer,'points_mm':[list(pt),list(at)],'width_mm':.2})
            rows.append({'at':at,'diameter_mm':d,'drill_mm':drill,'via_errors':errors,'track_errors':route_errors,'nearest_gap_mm':dict(nearest),'prospective_fill_voids':cuts,'routes':routes,'geometry_candidate':not errors and not route_errors})
    # A same-domain AO1_COM fill may retreat under a new legal trace.
    # This is only a prospective construction; full fill contact/reference
    # audits and actual native refill remain mandatory.
    free_by_layer={}
    for layer in ['B.Cu','F.Cu']:
        obstacles=[]
        for rec in model.records[layer]:
            if rec.get('net')==net: continue
            if rec['kind']=='fill' and rec.get('domain')==domain and rec.get('net')=='/motherboard_analog_output/AO1_COM': continue
            clearance=.275 if rec['kind']=='hole' else .175 if rec.get('domain')==domain else .625
            if rec['shape'].distance(region)<clearance+.125: obstacles.append(rec['shape'].buffer(clearance+.1))
        for hard in model.hard[layer]:
            if net not in hard['exempt']: obstacles.append(hard['shape'].buffer(.125))
        free_by_layer[layer]=region.buffer(-.125).difference(unary_union(obstacles))
    (OUT/'site-screen.json').write_text(json.dumps({'rows':rows,'SMD_drill_margin_mm':.275,'input_hashes':A.READS},indent=1)+'\n',encoding='utf-8')
    attempts=[]
    legal_sites=sorted([r for r in rows if not r['via_errors']],key=lambda r:math.dist(r['at'],[375.498,129]))
    for row in legal_sites[:24]:
        paths=[];failed=[]
        for pad_id,layer in zip(padids,['B.Cu','F.Cu']):
            free=free_by_layer[layer];start=(pads[pad_id]['x'],pads[pad_id]['y']);goal=row['at']
            if not free.covers(Point(start)) or not free.covers(Point(goal)):
                failed.append({'layer':layer,'reason':'source_or_via_center_not_in_exact_free_polygon'});break
            path,details=S.astar(free,[(start,{'uuid':pad_id,'kind':'pad'})],[(goal,{'uuid':'prospective_analog_via','kind':'via'})],time.monotonic()+12,node_cap=120000)
            if not path:
                failed.append({'layer':layer,**details});break
            points=[[round(float(x),6),round(float(y),6)] for x,y in path['points_mm']]
            if not free.buffer(1e-9).covers(LineString(points)):
                failed.append({'layer':layer,'reason':'native_quantized_path_exits_guarded_free_polygon'});break
            paths.append({'pad':pad_id,'layer':layer,'points_mm':points,'width_mm':.2,'search':details})
        attempts.append({'at':row['at'],'diameter_mm':row['diameter_mm'],'drill_mm':row['drill_mm'],'paths':paths,'failures':failed})
        if not failed and len(paths)==2:
            row['routes']=paths;row['track_errors']=[];row['geometry_candidate']=True
            row['construction']='bounded_quantized_two_face_detour_with_prospective_AO1_COM_fill_retreat'
            break
    (OUT/'route-construction.json').write_text(json.dumps({'legal_via_sites':len(legal_sites),'attempts':attempts,'all_source_fill_polygons_unchanged':True,'full_fill_contact_reference_audit':'OPEN','adopted':False},indent=1)+'\n',encoding='utf-8')
    for p,h in A.READS.items():
        if sha(Path(p).read_bytes()) != h: raise ValueError('Analog probe input changed: '+p)
    good=[r for r in rows if r['geometry_candidate']]
    result={'verdict':'GEOMETRY_CANDIDATES_REFERENCE_ANALOG_NATIVE_OPEN' if good else 'NO_LOCAL_DIRECT_TRANSITION_IN_FINITE_SITES','parent_candidate_sha256':sha(newraw),'actual_198b_via_annuli':annulus,'all_changed_root_copper_distance_to_region_mm_min':min(separation),'changed_root_footprints_outside20mm_body_bound':True,'analog_pad_positions':{p:[pads[p]['x'],pads[p]['y']] for p in padids},'examined':len(rows),'geometry_candidates':good,'all_site_diagnostics':rows,'input_hashes':A.READS,'elapsed_seconds':time.monotonic()-started,'board_emitted':False,'reference_anchor_and_contact_cut_audit':'OPEN','analog_noise_loop_parasitics':'OPEN','native_refill_DRC_dual_connectivity':'OPEN','adopted':False}
    (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':result['verdict'],'examined':len(rows),'geometry_candidates':len(good),'output':str(OUT/'receipt.json')}),flush=True)
if __name__=='__main__': main()
