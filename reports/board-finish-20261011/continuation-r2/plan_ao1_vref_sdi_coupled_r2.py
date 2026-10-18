"""Restore exact local VREF copper and search a replacement owned SDI transition."""
import collections,hashlib,json,math,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE/'coupled-recovery'))
import audit_aux_exact_raw as A
import native_flash_model as NF
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
OUT=HERE/'ao1-vref-sdi-coupled-r2'
VREF='/motherboard_analog_output/AO1_VREF';SDI='/motherboard_analog_output/AO1_DAC_SDI';COM='/motherboard_analog_output/AO1_COM';DOMAIN='DOM_AO1'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh coupled analog proposal required')
    OUT.mkdir();started=time.monotonic()
    parent=HERE/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb'
    parentraw=A.read(parent)
    if sha(parentraw)!='1beb9a2296ae451daed4b905383ccc5bd3ee083b3400cf5ef2e3ab2e7b7dae6b':raise ValueError('Combined parent identity differs')
    raw=A.read(G.SOURCE);now=C.inventory(raw);final_parent=C.inventory(parentraw)
    graph=json.loads(A.read(HERE/'coupled-recovery/conflict-graph.json'))
    row=next(r for r in graph['lost_route_rows'] if r['net']==VREF)
    restores={r['uuid'] for r in row['missing_original_items']};deletes=set(row['blocking_nets'][SDI]['item_uuids'])
    if len(restores)!=7 or len(deletes)!=4 or any(now[4][u]!=final_parent[4][u] for u in deletes):raise ValueError('Exact analog ownership differs')
    r06_path=Path('Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb');r06_raw=A.read(r06_path)
    if sha(r06_raw)!='0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53':raise ValueError('r06 exact restore board identity differs')
    original=C.inventory(r06_raw)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));original_template=C.inventory(A.read(S.overlay_tool.base.BASE))
    template,_=A.fresh_template(original_template,now,template,native)
    region=box(369.5,125,379,133)
    changed={u for u in set(now[4])|set(final_parent[4]) if now[4].get(u)!=final_parent[4].get(u)}
    for u in changed:
        for inv in (now,final_parent):
            if u in inv[4] and A.shape(G.parse(u,inv[4][u],{})).distance(region)<2:raise ValueError('Root changed Cu enters analog region')
    for u in set(now[3])|set(final_parent[3]):
        ch=final_parent[3].get(u,now[3].get(u))
        if C.pcbtext.chunk_kind(ch)!='footprint' or now[3].get(u)==final_parent[3].get(u):continue
        for inv in (now,final_parent):
            if u not in inv[3]:continue
            m=re.search(rb'\n\t\t\(at\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)',inv[3][u])
            if not m or Point(tuple(float(v) for v in m.groups())).buffer(20).distance(region)<2:raise ValueError('Root changed FP may enter analog region')
    chunks={u:ch for u,ch in now[4].items() if u not in deletes};chunks.update({u:original[4][u] for u in restores})
    g=P.geometry(chunks,template);reserved,exempt=A.reservations();masks=json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'];model=NF.Model(g,reserved,exempt,native['vias'],masks)
    # Do not grandfather a restored route through changed foreign copper.
    parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items()}
    restored_errors,restored_checks,retreats=A.clearance(model,parsed,set(),restores)
    smd_shapes=[q for p in g['pads'] if p['smd'] for layer,rings in p['layers'].items() if layer in ['F.Cu','B.Cu'] for q in S.poly(rings)]
    for u in restores:
        v=parsed[u]
        if v['kind']=='via':
            gap=min(Point(v['at']).distance(q) for q in smd_shapes)-v['drill']/2
            if gap<.275:restored_errors.append({'uuid':u,'kind':'stronger_drill_SMD_aperture','gap_mm':gap,'required_mm':.275})
    write(OUT/'restoration-screen.json',{'exact_r06_restored_uuids':sorted(restores),'exact_current_owned_removed_uuids':sorted(deletes),'restored_copper_clearance_errors':restored_errors,'clearance_rows':restored_checks,'prospective_fill_antipads':retreats})
    if restored_errors:
        write(OUT/'receipt.json',{'verdict':'RESTORED_VREF_CLEARANCE_FAIL','errors':restored_errors,'board_emitted':False,'adopted':False});return
    pads=model.pads;start=(pads['U14626.8#0']['x'],pads['U14626.8#0']['y']);goal=(372.45,130.35)
    sdi_current=[r for r in model.own[SDI] if r['layer']=='In3.Cu' and r['shape'].distance(Point(goal))<1e-6]
    if not sdi_current:raise ValueError('SDI target lacks a retained physical In3 contact')
    free={}
    for layer in ['F.Cu','In3.Cu']:
        obstacles=[]
        for rec in model.records[layer]:
            if rec.get('net')==SDI:continue
            if rec['kind']=='fill' and rec.get('net')==COM:continue
            margin=.275 if rec['kind']=='hole' else .175 if rec.get('domain')==DOMAIN else .625
            if rec['shape'].distance(region)<margin+.125:obstacles.append(rec['shape'].buffer(margin+.1))
        for hard in model.hard[layer]:
            if SDI not in hard['exempt']:obstacles.append(hard['shape'].buffer(.125))
        free[layer]=region.buffer(-.125).difference(unary_union(obstacles))
    smd=STRtree([q for p in g['pads'] if p['smd'] for layer,rings in p['layers'].items() if layer in ['F.Cu','B.Cu'] for q in S.poly(rings)])
    via_tree=STRtree([Point(v['x'],v['y']) for v in g['vias']])
    sites=[]
    for at in [(371.2+i*.1,126.7+j*.1) for i in range(40) for j in range(32)]:
        at=tuple(round(v,6) for v in at);body=Point(at).buffer(.25,resolution=128);hole=Point(at).buffer(.1,resolution=128);errors=[]
        if len(smd.query(hole.buffer(.275),predicate='intersects')):continue
        if len(via_tree.query(Point(at).buffer(.8-1e-8),predicate='intersects')):continue
        for layer in g['copper_layers']:
            for i in model.trees[layer].query(body.buffer(.675),predicate='intersects'):
                r=model.records[layer][i]
                if r['kind']=='hole':gap=hole.distance(r['shape']);required=.275
                elif r.get('net')==SDI:continue
                elif r['kind']=='fill' and r.get('net')==COM:continue
                else:gap=body.distance(r['shape']);required=.175 if r.get('domain')==DOMAIN else .625
                if gap<required-1e-8:errors.append(layer+':'+r['kind']);break
            for hard in model.hard[layer]:
                if SDI not in hard['exempt'] and body.buffer(.025).intersects(hard['shape']):errors.append('hard')
        if not errors and all(free[layer].covers(Point(at)) for layer in free):sites.append(at)
    write(OUT/'site-screen.json',{'sites_mm':sites,'drill_to_SMD_margin_mm':.275,'all6_annuli_conservative':True,'minimum_ordinary_pitch_mm':.8,'new_via_size_drill_mm':[.5,.2]})
    attempts=[];success=None
    for at in sorted(sites,key=lambda p:math.dist(p,start)+math.dist(p,goal))[:32]:
        routes=[];fail=[]
        for layer,a,b in [('F.Cu',start,at),('In3.Cu',at,goal)]:
            if not free[layer].covers(Point(a)) or not free[layer].covers(Point(b)):fail.append({'layer':layer,'reason':'exact_source_target_outside_free_polygon'});break
            path,details=S.astar(free[layer],[(a,{'uuid':'AO1_SDI_SOURCE','kind':'terminal'})],[(b,{'uuid':'AO1_SDI_TARGET','kind':'terminal'})],time.monotonic()+15,node_cap=140000)
            if not path:fail.append({'layer':layer,**details});break
            points=path['points_mm']
            if not free[layer].buffer(1e-9).covers(LineString(points)):raise ValueError('Quantized analog detour escapes exact guarded polygon')
            routes.append({'net':SDI,'layer':layer,'width_mm':.2,'points_mm':points,'search':details})
        attempts.append({'via_at_mm':at,'routes':routes,'failures':fail})
        if not fail and len(routes)==2:success=attempts[-1];break
    write(OUT/'receipt.json',{'verdict':'COUPLED_ANALOG_GEOMETRY_PROPOSAL_REFERENCE_CONTACT_NATIVE_OPEN' if success else 'NO_PATH_IN_BOUNDED_COUPLED_ANALOG_SEARCH','parent_sha256':sha(parentraw),'local_source_native_sha256':sha(raw),'deletes':sorted(deletes),'restores':sorted(restores),'new_SDI_via_mm':success['via_at_mm'] if success else None,'new_SDI_routes':success['routes'] if success else None,'attempts':attempts,'legal_sites':len(sites),'reference_source_and_return_contacts':'OPEN','all_current_and_r06_pad_groups_and_surviving_contacts':'OPEN','analog_loop_noise_edge_load_qualification':'OPEN','full_native_refill_DRC':'OPEN','input_hashes':A.READS,'elapsed_seconds':time.monotonic()-started,'board_emitted':False,'adopted':False})
    print(json.dumps({'legal_sites':len(sites),'success':bool(success),'elapsed_seconds':time.monotonic()-started}),flush=True)
if __name__=='__main__':main()
