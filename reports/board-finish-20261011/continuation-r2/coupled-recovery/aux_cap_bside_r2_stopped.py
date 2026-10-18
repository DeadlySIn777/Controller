"""Frozen local AUX layout option: capacitor to B, zero support transitions.

Produces a concrete native-operation recipe only. Root must apply an actual
KiCad footprint flip/pose and attest native pad UUID/net/pose/polygons before
the candidate can enter ordinary DRC and dual continuity/electrical gates.
"""
import collections,copy,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact as A
import aux_local_move as L
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.affinity import translate,rotate
POWER,ILIM,DVDT=A.POWER,A.ILIM,A.DVDT
RTN='/motherboard_power_entry/AUX24_A_RTN'
REF='C11068'

def move(template,xy,angle):
    g=copy.copy(template)
    g['pads']=[copy.deepcopy(p) if p['ref']==REF else p for p in template['pads']]
    g['footprints']=[copy.deepcopy(f) if f['ref']==REF else f for f in template['footprints']]
    foot=next(f for f in g['footprints'] if f['ref']==REF);old=(foot['x'],foot['y'])
    # KiCad positive angles rotate clockwise in the board's y-down view;
    # mathematical world coordinates therefore use negative angle delta.
    delta=-(angle-(-90.0))
    for pad in g['pads']:
        if pad['ref']!=REF:continue
        q=translate(rotate(Point(pad['x'],pad['y']),delta,origin=old),xy[0]-old[0],xy[1]-old[1])
        pad['x'],pad['y']=q.x,q.y
        body=unary_union(S.poly(next(iter(pad['layers'].values()))))
        body=translate(rotate(body,delta,origin=old),xy[0]-old[0],xy[1]-old[1])
        pad['layers']={'B.Cu':L.rings(body)}
    court=unary_union(S.poly(foot['courtyard']['F']))
    court=translate(rotate(court,delta,origin=old),xy[0]-old[0],xy[1]-old[1])
    foot['courtyard']={'B':L.rings(court)};foot['x'],foot['y']=xy
    return g

def route(model,net,relation,masks,window,width=.2,max_length=8):
    uf,groups=P.physical(model,net,masks);touch=[g for g in groups if set(g['pad_ids'])&set(relation)]
    if len(touch)==1:return None,{'already_connected':True}
    if len(touch)!=2:return None,{'reason':'Expected two native-related components','count':len(touch)}
    saved=S.WIDTH;S.WIDTH=width
    try:
        free,_=model.free({'net':net,'domain':model.domains[net]},'B.Cu',window)
        seeds=[S.seed_sites(g,'B.Cu',free,window) for g in touch]
        path,search=S.astar(free,*seeds,time.monotonic()+8,node_cap=100000) if all(seeds) else (None,{'reason':'No exact component seed'})
    finally:S.WIDTH=saved
    if path:
        length=LineString(path['points_mm']).length
        if length>max_length:return None,{'reason':'Local support path length bound','length_mm':length,**search}
        path.update(net=net,layer='B.Cu',width_mm=width,length_mm=length,obligation=relation,new_items=[])
    return path,search

def main():
    start=time.time();out=HERE/'aux-cap-bside-r2.json'
    if out.exists():raise ValueError('Fresh output required')
    raw=A.read(G.SOURCE);oldraw=A.read(S.overlay_tool.base.BASE);now=C.inventory(raw);old=C.inventory(oldraw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen source differs')
    receipt=json.loads(A.read(HERE/'aux-power-escape-r2.json'));native=json.loads(A.read(A.NATIVE/'geometry.json'))
    template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    r06={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    deletes=set(receipt['owned_power_items'])|{u for u,ch in now[4].items() if S.norm(S.overlay_tool.netname(ch)) in (ILIM,DVDT)}
    local={u:ch for u,ch in now[4].items() if u not in deletes}
    # Reuse frozen validated ILIM recipe; no planner randomness is needed.
    paths0=[p for p in receipt['proposal']['paths'] if p['net']==ILIM]
    for path in paths0:
        for a,b in zip(path['points_mm'],path['points_mm'][1:]):u,ch=P.serial_segment(ILIM,'B.Cu',a,b,.2);local[u]=ch
    reserve,exempt=A.reservations();print('AUX_CAP_BASE_MODEL',flush=True);baseg=P.geometry(local,template);base=S.Model(baseg,reserve,exempt)
    foot=next(f for f in template['footprints'] if f['ref']==REF);sites=[]
    for angle in (0,180,-90):
        for x in (315.8,316.4,317.0,317.6,318.2,318.8,319.4,320.0):
            for y in (50.5,51.1,51.7,52.3,52.9,53.5,54.1):
                pose=move(template,(x,y),angle);pads=[p for p in pose['pads'] if p['ref']==REF]
                court=unary_union(S.poly(next(f for f in pose['footprints'] if f['ref']==REF)['courtyard']['B']))
                overlaps=[]
                for other in baseg['footprints']:
                    if other['ref']==REF or 'B' not in other['courtyard']:continue
                    area=court.intersection(unary_union(S.poly(other['courtyard']['B']))).area
                    if area>1e-10:overlaps.append({'ref':other['ref'],'area_mm2':area})
                failures,minimum=L.pad_clearance(pads,base)
                sites.append({'xy_mm':[x,y],'angle_degrees':angle,'pad_clearance_failures':failures,'courtyard_overlap':overlaps,'minimum_gap_by_kind_mm':minimum})
    feasible=[s for s in sites if not s['pad_clearance_failures'] and not s['courtyard_overlap']]
    feasible.sort(key=lambda s:math.dist(s['xy_mm'],(317.8,50.5)))
    print('AUX_CAP_FEASIBLE',len(feasible),'of',len(sites),flush=True)
    attempts=[];proposal=None
    rtn_relation=next(gs for gs in parts[RTN] if 'C11068.2#0' in gs)
    for site in feasible[:12]:
        print('AUX_CAP_POSE',site['xy_mm'],site['angle_degrees'],flush=True)
        moved=move(template,site['xy_mm'],site['angle_degrees']);chunks=dict(local);g=P.geometry(chunks,moved);model=S.Model(g,reserve,exempt)
        routes=copy.deepcopy(paths0);attempt={'pose':site,'searches':[]};window=box(310,42,331,59)
        for net,relation in ((DVDT,['C11068.1#0','U11015.8#0']),(RTN,rtn_relation)):
            path,search=route(model,net,relation,masks,window);attempt['searches'].append({'net':net,**search})
            if not path and not search.get('already_connected'):break
            if path:
                for a,b in zip(path['points_mm'],path['points_mm'][1:]):u,ch=P.serial_segment(net,'B.Cu',a,b,.2);chunks[u]=ch;path['new_items'].append(u)
                routes.append(path);g=P.geometry(chunks,moved);model=S.Model(g,reserve,exempt)
        if len(attempt['searches'])!=2 or any(r.get('reason') for r in attempt['searches']):attempts.append(attempt);continue
        import aux_power_escape as E
        fake={'uuid':'exact source power terminal','kind':'track'}
        power,search=E.path_between(model,POWER,1.2,[((316.85,51.95),fake)],[((319.25,48.95),fake)],window)
        attempt['searches'].append({'net':POWER,**search})
        if not power:attempts.append(attempt);continue
        power.update(net=POWER,layer='B.Cu',width_mm=1.2,length_mm=LineString(power['points_mm']).length,new_items=[])
        for a,b in zip(power['points_mm'],power['points_mm'][1:]):u,ch=P.serial_segment(POWER,'B.Cu',a,b,1.2);chunks[u]=ch;power['new_items'].append(u)
        routes.append(power);g=P.geometry(chunks,moved);model=S.Model(g,reserve,exempt)
        failures=[]
        for net in (POWER,ILIM,DVDT,RTN):
            uf,groups=P.physical(model,net,masks)
            for baseline,gs in (('current198b',parts[net]),('r06',r06[net])):
                for rel in gs:
                    if len({uf.find(('p',p)) for p in rel})>1:failures.append({'net':net,'baseline':baseline,'relationship':rel})
        attempt['relationship_failures']=failures;attempts.append(attempt)
        if failures:continue
        proposal={'native_operation':'Move C11068 to B.Cu with exact retained pad UUID/net/local shape, then set frozen physical target pose and attest native transformed geometry',
                  'footprint_uuid':'f2a18ff9-2826-4c67-94dc-d26f5bb1906b','ref':REF,'value':'10nF 100V C0G','source_side':'F.Cu','target_side':'B.Cu',
                  'target_pose':site,'expected_pads':[{'uuid':p['uuid'],'num':p['num'],'net':p['net'],'at_mm':[p['x'],p['y']],'layers':p['layers']} for p in moved['pads'] if p['ref']==REF],
                  'delete_copper_uuids':sorted(deletes),'routes':routes,'new_vias':0,'plane_changes':0,'r06_and_current_pad_relationship_failures_host':[],
                  'power_added_length_mm':power['length_mm']-receipt['proposal']['power_original_length_mm'],'native_and_electrical_qualification':'OPEN'}
        break
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen read changed '+p)
    result={'schema':'aux-local-no-transition-layout-r2','verdict':'CONCRETE_NATIVE_LAYOUT_RECIPE_HOST_ONLY' if proposal else 'BOUNDED_BSIDE_CAP_LAYOUT_INCOMPLETE',
            'source_sha256':A.SOURCE_SHA,'native198b_pad_fill_proof':proof,'proposal':proposal,'placement_screen':sites,'attempts':attempts,
            'read_files_sha256':A.READS,'seconds':time.time()-start,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,
            'limits':['168 finite poses;12 shortest feasible poses;8s/100000nodes/.1mm grid per support path','Local DVDT and RTN paths limited to8mm; ILIM frozen3.957mm;1.2mm power retained','Native footprint transform/pad polygons/placement/courtyard/hole/ordinary DRC and complete changed-entity/contact obligations remain mandatory','Complete r06/r07 no-loss plus all current/drop/local RTN/refill/source/thermal/electrical gates remain mandatory']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':result['verdict'],'feasible_poses':len(feasible),'receipt':str(out)}),flush=True)
if __name__=='__main__':main()
