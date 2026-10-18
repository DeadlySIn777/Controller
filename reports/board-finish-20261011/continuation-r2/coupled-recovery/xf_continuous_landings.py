"""Coupled XF routes from all-layer continuous legal transition/return regions.

Owned r07 gate transition may move; retained native gains are mandatory. Uses
exact current pads/fills/source chunks and actual existing annuli. Full copper
body reference is screened, including prospective antipads, not centerline only.
No native/GPU calls; new actual native annuli and full native/electrical gates
remain open even if a concrete host candidate is staged.
"""
import collections,itertools,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact as A
import xf_coupled_transition as T
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.affinity import translate
REQ,EN,GND=T.REQ,T.EN,T.GND

def freevia(model,net,window):
    obstacles=[];domain=model.domains[net];counts=collections.Counter()
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=model.records[layer][i]
            if r['kind']=='hole':gap=.25
            elif r['kind']=='pad' and r['net']==net:gap=.1 if model.pads[r['pad_id']]['smd'] else .25
            elif r['net']==net:continue
            elif r['kind']=='fill' and layer in ('In1.Cu','In2.Cu','In4.Cu') and r.get('domain')==domain:continue
            else:gap=.15 if r.get('domain')==domain else .6
            obstacles.append(r['shape'].buffer(.3+gap+S.MARGIN));counts[r['kind']]+=1
        for r in model.hard[layer]:
            if net not in r['exempt'] and r['shape'].intersects(window.buffer(2)):
                obstacles.append(r['shape'].buffer(.3+S.MARGIN));counts[r['kind']]+=1
    for v in model.g['vias']:
        if window.buffer(2).covers(Point(v['x'],v['y'])):obstacles.append(Point(v['x'],v['y']).buffer(.8+S.MARGIN,resolution=128))
    free=window.intersection(model.outline.buffer(-.5-.3-S.MARGIN)).difference(unary_union(obstacles))
    return free,dict(counts)

def sites(region,desired,limit=8):
    rows=[]
    for part in P.K.D.components(region):
        if part.area<=1e-10:continue
        rep=part.representative_point();near=nearest_points(part,Point(desired))[0]
        for q in (rep,near,Point((rep.x+near.x)/2,(rep.y+near.y)/2)):
            p=[round(q.x,6),round(q.y,6)]
            if region.covers(Point(p)) and all(math.dist(p,r['at_mm'])>.05 for r in rows):rows.append({'at_mm':p,'cost_mm':math.dist(p,desired),'region_area_mm2':part.area})
    return sorted(rows,key=lambda r:r['cost_mm'])[:limit]

def main():
    out=HERE/'xf-continuous-landings-r1.json';start=time.time()
    if out.exists():raise ValueError('Fresh output required')
    raw=A.read(G.SOURCE);oldraw=A.read(S.overlay_tool.base.BASE);now=C.inventory(raw);old=C.inventory(oldraw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen source differs')
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    oldparts={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    graph=json.loads(A.read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==REQ)
    reserve,exempt=A.reservations();print('XF_CONTINUOUS_BASE_MODEL',flush=True);g=P.geometry(now[4],template);base=S.Model(g,reserve,exempt)
    failure,checks,_,oldgroups=A.relationships(base,masks,parts,(REQ,EN))
    if failure or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Fresh actual-annulus native partition mismatch')
    deletes=set(row['blocking_nets'][EN]['item_uuids'])
    withheld={'b1bde65e-ae89-4c0d-9caf-bf5d95d85600','a7198170-18ee-42dd-858d-061a27366980','3dadaf02-aad8-4d65-ad43-99096cf08382','5350f7dd-02b4-40be-8c0d-3fecb2805543','5568a777-bb7f-423f-a181-96f36d9376a1','139229ed-d773-4742-9431-88372f838056','2eb80f08-7b8b-4437-b5af-bdf8be4dc990'}
    restores={r['uuid'] for r in row['missing_original_items']}-withheld
    initial={u:ch for u,ch in now[4].items() if u not in deletes};initial.update({u:old[4][u] for u in restores})
    g=P.geometry(initial,template);model=S.Model(g,reserve,exempt)
    refs,witness=T.refs_after(model,masks,[]);reference_both=refs['F.Cu'].intersection(refs['B.Cu'])
    window=box(294,101,304,111);free={};stats={}
    for net in (REQ,EN,GND):free[net],stats[net]=freevia(model,net,window);free[net]=free[net].intersection(reference_both)
    first=[]
    for v in model.g['vias']:
        if v['net']!=GND or not {'In1.Cu','In4.Cu'}<=masks.get(v['uuid'],set()) or not window.buffer(2).covers(Point(v['x'],v['y'])):continue
        ann=Point(v['x'],v['y']).buffer(.3,resolution=128).difference(Point(v['x'],v['y']).buffer(.15,resolution=128))
        if not refs['F.Cu'].intersects(ann) or not refs['B.Cu'].intersects(ann):continue
        ring=Point(v['x'],v['y']).buffer(1.,resolution=128).difference(Point(v['x'],v['y']).buffer(.8+S.MARGIN,resolution=128))
        for s in sites(free[REQ].intersection(ring),[297.15,103.95],6):
            if not .8+S.MARGIN<=math.dist(s['at_mm'],(v['x'],v['y']))<=1.:continue
            first.append(dict(s,existing_return_uuid=v['uuid'],return_at_mm=[v['x'],v['y']]))
    first.sort(key=lambda r:r['cost_mm']);first=first[:6]
    paired={}
    offsets=[(.9,0),(-.9,0),(0,.9),(0,-.9),(.636396,.636396),(.636396,-.636396),(-.636396,.636396),(-.636396,-.636396)]
    for net,desired in ((REQ,[298.55,107.95]),(EN,[298.65,107.55])):
        rows=[]
        for dx,dy in offsets:
            region=free[net].intersection(translate(free[GND],-dx,-dy))
            for s in sites(region,desired,5):rows.append(dict(s,return_at_mm=[round(s['at_mm'][0]+dx,6),round(s['at_mm'][1]+dy,6)],return_distance_mm=math.hypot(dx,dy)))
        paired[net]=sorted(rows,key=lambda r:r['cost_mm'])[:12]
    print('XF_CONTINUOUS_SITES',len(first),len(paired[REQ]),len(paired[EN]),flush=True)
    combinations=[]
    for a,b,c in itertools.product(first,paired[REQ],paired[EN]):
        positions=[a['at_mm'],b['at_mm'],b['return_at_mm'],c['at_mm'],c['return_at_mm']]
        if any(math.dist(x,y)<.8+S.MARGIN for x,y in itertools.combinations(positions,2)):continue
        combinations.append((sum(r['cost_mm'] for r in (a,b,c)),a,b,c))
    combinations.sort(key=lambda r:r[0]);attempts=[];emitted=None
    for ci,(_,firstsite,secondsite,gatesite) in enumerate(combinations[:4]):
        print('XF_CONTINUOUS_COMBINATION',ci,flush=True);chunks=dict(initial);cmasks=dict(masks);added=set();via_specs=[]
        for net,at in ((REQ,firstsite['at_mm']),(REQ,secondsite['at_mm']),(GND,secondsite['return_at_mm']),(EN,gatesite['at_mm']),(GND,gatesite['return_at_mm'])):
            u,ch=T.serial_via(net,at);chunks[u]=ch;added.add(u);via_specs.append({'uuid':u,'net':net,'at_mm':at});cmasks[u]={'F.Cu','In3.Cu','In1.Cu','In4.Cu'}
        g=P.geometry(chunks,template);candidate=S.Model(g,reserve,exempt)
        parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restores};errs,clear,anti=A.clearance(candidate,parsed,added,restores)
        attempt={'via_sites':via_specs,'initial_clearance_errors':errs,'paths':[],'searches':[]};attempts.append(attempt)
        if errs:continue
        sigs=[firstsite['at_mm'],secondsite['at_mm'],gatesite['at_mm']];r,w=T.refs_after(candidate,cmasks,sigs);attempt['source_reference_witness']=w
        returns=[]
        for signal,returnsite in ((firstsite,firstsite),(secondsite,secondsite),(gatesite,gatesite)):
            ann=Point(returnsite['return_at_mm']).buffer(.3,resolution=128).difference(Point(returnsite['return_at_mm']).buffer(.15,resolution=128))
            returns.append({'signal_at_mm':signal['at_mm'],'return_at_mm':returnsite['return_at_mm'],'distance_mm':math.dist(signal['at_mm'],returnsite['return_at_mm']),
                            'source_contacts':{'In1.Cu':r['F.Cu'].intersects(ann),'In4.Cu':r['B.Cu'].intersects(ann)}})
        attempt['return_stitch_checks']=returns
        if not all(all(z['source_contacts'].values()) for z in returns):continue
        pairs=[(REQ,'F.Cu',[294.65,101.45],firstsite['at_mm']),(REQ,'In3.Cu',firstsite['at_mm'],secondsite['at_mm']),
               (REQ,'F.Cu',[297.328,108.025],secondsite['at_mm']),(EN,'F.Cu',[297.328,107.525],gatesite['at_mm']),
               (EN,'In3.Cu',gatesite['at_mm'],[302.25,103.95])]
        for net,layer,a,b in pairs:
            routewindow=LineString([a,b]).envelope.buffer(8,cap_style=3).envelope
            unref=unary_union([Point(p).buffer(.475,resolution=128) for p in (a,b) if p in sigs])
            legal=r[layer].union(unref).buffer(-.1)
            free_route,_=candidate.free({'net':net,'domain':candidate.domains[net]},layer,routewindow);strict=free_route.intersection(legal)
            fake={'uuid':'exact owned splice','kind':'track'};seeds=[[(tuple(p),fake)] if strict.covers(Point(p)) else [] for p in (a,b)]
            path,search=S.astar(strict,*seeds,time.monotonic()+12,node_cap=150000) if all(seeds) else (None,{'reason':'No exact full-body reference-covered splice'})
            attempt['searches'].append({'net':net,'layer':layer,'from_mm':a,'to_mm':b,'seed_counts':[len(z) for z in seeds],**search})
            if not path:break
            body=LineString(path['points_mm']).buffer(.1,resolution=128);miss=body.difference(unref).difference(r[layer]).area
            if miss>1e-9:attempt['searches'][-1]['full_body_reference_uncovered_mm2']=miss;break
            path.update(net=net,layer=layer,width_mm=.2,length_mm=LineString(path['points_mm']).length,new_items=[],full_body_reference_uncovered_mm2=miss)
            for a1,b1 in zip(path['points_mm'],path['points_mm'][1:]):u,ch=P.serial_segment(net,layer,a1,b1,.2);chunks[u]=ch;added.add(u);path['new_items'].append(u)
            attempt['paths'].append(path);g=P.geometry(chunks,template);candidate=S.Model(g,reserve,exempt)
        losses=[];contact_losses=[];obligations=[];boundary=[]
        for net in (REQ,EN):
            uf,groups=P.physical(candidate,net,cmasks)
            for label,reln in (('current198b',parts[net]),('r06',oldparts[net])):
                for rel in reln:
                    if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'relationship':rel})
            for gr in oldgroups[net]:
                keys=sorted({z['key'] for z in gr['records'] if z['uuid'] not in deletes});n=len({uf.find(k) for k in keys})
                obligation={'net':net,'surviving_keys':[list(k) for k in keys],'component_count':n};obligations.append(obligation)
                if n>1:contact_losses.append(obligation)
            for z in base.own[net]:
                if z['uuid'] not in deletes:continue
                for b in base.own[net]:
                    if b['uuid'] in deletes or b['layer']!=z['layer']:continue
                    if b['kind']=='via' and b['layer'] not in masks[b['uuid']]:continue
                    if z['shape'].distance(b['shape'])<=.000002:boundary.append({'deleted_uuid':z['uuid'],'surviving_key':list(b['key']),'layer':z['layer']})
        attempt.update(pad_relationship_failures=losses,surviving_contact_losses=contact_losses,surviving_contact_obligations=obligations,removed_to_surviving_contacts=boundary)
        if losses or contact_losses or len(attempt['paths'])!=5:continue
        parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restores};errs,clear,anti=A.clearance(candidate,parsed,added,restores)
        attempt.update(final_clearance_errors=errs,final_changed_item_clearance=clear,prospective_antipads=anti)
        if errs:continue
        cand=now[0]+b''.join(ch for ch in now[1] if C.pcbtext.chunk_uuid(ch) not in deletes)+b''.join(ch for u,ch in chunks.items() if u not in now[4])+now[2];inv=C.inventory(cand)
        if now[5]!=inv[5] or any(inv[3].get(u)!=ch for u,ch in now[3].items() if u not in deletes):raise ValueError('Unauthorized retained source bytes differ')
        emitted=HERE/'xf-continuous-landings-r1-host-only.kicad_pcb';emitted.write_bytes(cand);attempt['candidate_sha256']=C.sha(cand);break
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen read changed '+q)
    result={'schema':'xf-continuous-coupled-landings-r1','verdict':'HOST_CANDIDATE_NATIVE_ELECTRICAL_OPEN' if emitted else 'BOUNDED_CONTINUOUS_COUPLED_PLAN_INCOMPLETE',
            'source_sha256':A.SOURCE_SHA,'native_pad_fill_proof':proof,'current_native_pad_partition_checks':checks,'deleted_owned_items':sorted(deletes),'restored_original_items':sorted(restores),
            'withheld_original_transition_items':sorted(withheld),'source_reference_witness':witness,'free_via_area_mm2':{n:f.area for n,f in free.items()},'blocker_counts':stats,
            'first_via_existing_return_sites':first,'paired_new_return_sites':paired,'joint_nonoverlap_combinations':len(combinations),'attempts':attempts,'candidate':str(emitted) if emitted else None,
            'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'seconds':time.time()-start,
            'limits':['Continuous .6/.3 ordinary via regions, all6layer copper/hole/hard/pitch checks;6first/12pair sites;4 joint combinations','Fresh source-connected both reference planes and actual existing annuli; all prospective signal antipads included','Full .2mm copper body reference, except declared necessary signal antipads supported by correct local stitches','New actual native via annuli, full native ordinary DRC/dual all-net no-loss and all source/current/timing/return/electrical gates remain mandatory']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':result['verdict'],'joint':len(combinations),'candidate':str(emitted) if emitted else None,'receipt':str(out)}),flush=True)
if __name__=='__main__':main()
