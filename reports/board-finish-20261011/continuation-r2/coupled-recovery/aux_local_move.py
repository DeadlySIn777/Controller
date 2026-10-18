"""Local TPS26624 support repair, exact-source host only.

Restore original dV/dt connection and relocate only R11056 to make both ILIM
and its separate RTN return short. RTN is explicitly not FIELD_GND; no plane,
thermal, reverse-polarity, or native electrical qualification is claimed.
"""
import collections,copy,hashlib,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import coupled_screen as P
G,S,C,R,K=P.G,P.S,P.C,P.R,P.K
sys.path.insert(0,str(G.REPORT))
import reconcile_dfm as F
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.affinity import translate
from shapely.strtree import STRtree

NET='/motherboard_power_entry/AUX24_A_ILIM'
RTN='/motherboard_power_entry/AUX24_A_RTN'
DVDT='/motherboard_power_entry/AUX24_A_DVDT'
REF='R11056'
READS={}

def read(p):
    p=Path(p).resolve();raw=p.read_bytes();READS[str(p)]=C.sha(raw);return raw

def rings(shape):
    return [[[list(pt) for pt in part.exterior.coords[:-1]],[[list(pt) for pt in ring.coords[:-1]] for ring in part.interiors]] for part in K.D.components(shape)]

def move_template(template,dx,dy):
    g=copy.deepcopy(template)
    for pad in g['pads']:
        if pad['ref']!=REF:continue
        pad['x']+=dx;pad['y']+=dy
        for layer,polys in pad['layers'].items():pad['layers'][layer]=rings(translate(unary_union(S.poly(polys)),dx,dy))
    for foot in g['footprints']:
        if foot['ref']!=REF:continue
        foot['x']+=dx;foot['y']+=dy
        for side,polys in foot['courtyard'].items():foot['courtyard'][side]=rings(translate(unary_union(S.poly(polys)),dx,dy))
    return g

def pad_clearance(pads,model):
    failures=[];mins=collections.defaultdict(lambda:999.)
    for pad in pads:
        net=S.norm(pad['net']);domain=model.domains[net]
        for layer,polys in pad['layers'].items():
            body=unary_union(S.poly(polys))
            for i in model.trees[layer].query(body.buffer(.7),predicate='intersects'):
                r=model.records[layer][i]
                if r['uuid'] in {p['uuid'] for p in pads}:continue
                if r['kind']=='hole':
                    # Even same-net ordinary holes cannot enter an SMD land.
                    required=.10;gap=body.distance(r['shape'])
                elif r['net']==net:continue
                else:required=(.15 if r.get('domain')==domain else .6)+S.MARGIN;gap=body.distance(r['shape'])
                mins[r['kind']]=min(mins[r['kind']],gap)
                if gap<required-1e-8:failures.append({'pad_uuid':pad['uuid'],'foreign_uuid':r['uuid'],'foreign_net':r.get('net'),'kind':r['kind'],'gap_mm':gap,'required_mm':required})
            for r in model.hard[layer]:
                if net not in r['exempt'] and r['shape'].intersects(body.buffer(S.MARGIN)):failures.append({'pad_uuid':pad['uuid'],'kind':r['kind'],'name':r['name']})
    return failures,dict(mins)

def main():
    started=time.time();output=HERE/'aux-local-move-r1.json'
    if output.exists():raise ValueError('Fresh output required')
    for p in (Path(__file__),Path(P.__file__),Path(G.__file__),Path(S.__file__),Path(C.__file__),Path(F.__file__),Path(C.pcbtext.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),Path(K.__file__),Path(R.__file__)):read(p)
    original=read(G.SOURCE);old_raw=read(S.overlay_tool.base.BASE);current=C.inventory(original);old=C.inventory(old_raw)
    if C.sha(original)!='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab':raise ValueError('Current source changed')
    template=json.loads(read(S.overlay_tool.base.GEOM));parts=json.loads(read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))
    native_new=json.loads(read(G.REPORT/'measure/r07-four-fag-shared/source-proof.json'))
    ds_path=Path('Z:/pcb-runs/claude-finish/review/schematic/ds/tps2662.txt');ds=read(ds_path).decode('utf-8',errors='replace');lines=ds.splitlines()
    first=next(i for i,l in enumerate(lines) if 'Do not connect RTN to GND' in l);second=next(i for i,l in enumerate(lines) if 'RTN, which is the reference ground' in l)
    contract='\n'.join(lines[first:first+5]+lines[second:second+6])
    if 'Do not connect RTN to GND' not in contract or 'shortest trace length' not in contract:raise ValueError('Original support return contract missing')
    graph=json.loads(read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==DVDT)
    restores={r['uuid'] for r in row['missing_original_items']}
    removes={uid for uid,ch in current[4].items() if S.norm(S.overlay_tool.netname(ch))==NET}
    local={uid:ch for uid,ch in current[4].items() if uid not in removes};local.update({uid:old[4][uid] for uid in restores})
    reserved=json.loads(read(G.C06/'alternate-r07/reserved-r07.json'));exempt={}
    for line in read(G.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exempt[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    initialg=P.geometry(current[4],template);masks,provenance,reuse=K.actual_masks(initialg,old,current,template,native_new)
    for uid in restores:
        via=next((v for v in template['vias'] if v['uuid']==uid),None)
        if via:masks[uid]=set(via['flashed'])
    print('AUX_MOVEMENT_BASE_MODEL',flush=True);baseg=P.geometry(local,template);base=S.Model(baseg,reserved,exempt)
    foot=next(f for f in baseg['footprints'] if f['ref']==REF);oldpads=[p for p in baseg['pads'] if p['ref']==REF]
    uf,groups=P.physical(base,RTN,masks)
    # The pose move intentionally disconnects R11056.2, then reconnects the
    # moved pad to this exact retained native RTN component. Existing contacts
    # to the old pad are nominated explicitly; they are retained as stubs.
    oldpad=next(p for p in oldpads if p['num']=='2');oldshape=unary_union(S.poly(oldpad['layers']['B.Cu']))
    contact_items=[{k:r[k] for k in ('kind','uuid','net','layer')} for r in base.own[RTN] if r['layer']=='B.Cu' and r['kind']!='pad' and r['shape'].distance(oldshape)<=.000002]
    original_rtn_group=next(g for g in parts['nets'][RTN] if 'R11056.2#0' in g)
    sites=[]
    # Keep all orientations and local pads exact; only direct footprint pose
    # changes. Positions are bounded by the local IC/support compartment.
    for x in (318.8,319.0,319.2,319.4,319.6,319.8,320.0):
        for y in (51.1,51.3,51.5,51.7,51.9,52.1,52.3):
            dx,dy=x-foot['x'],y-foot['y'];moved=[copy.deepcopy(p) for p in oldpads]
            for p in moved:
                p['x']+=dx;p['y']+=dy
                for layer,polys in p['layers'].items():p['layers'][layer]=rings(translate(unary_union(S.poly(polys)),dx,dy))
            newcourt=translate(unary_union(S.poly(foot['courtyard']['B'])),dx,dy)
            overlap=[]
            for other in baseg['footprints']:
                if other['ref']==REF or 'B' not in other['courtyard']:continue
                area=newcourt.intersection(unary_union(S.poly(other['courtyard']['B']))).area
                if area>1e-10:overlap.append({'ref':other['ref'],'area_mm2':area})
            bad,minimum=pad_clearance(moved,base)
            sites.append({'xy_mm':[x,y],'pad_clearance_failures':bad,'courtyard_overlap':overlap,'minimum_gap_by_kind_mm':minimum})
    feasible=[s for s in sites if not s['pad_clearance_failures'] and not s['courtyard_overlap']]
    feasible.sort(key=lambda s:math.dist(s['xy_mm'],(317.788,50.8)))
    print('AUX_FEASIBLE_R11056_POSES',len(feasible),'of',len(sites),flush=True)
    proposal=None;attempts=[]
    for site in feasible[:10]:
        dx,dy=site['xy_mm'][0]-foot['x'],site['xy_mm'][1]-foot['y'];moved_template=move_template(template,dx,dy);lg=P.geometry(local,moved_template);model=S.Model(lg,reserved,exempt)
        candidate_local=dict(local);paths=[];entry={'xy_mm':site['xy_mm'],'routes':[]};window=box(313,44,325,56)
        for net,relation in ((NET,['R11056.1#0','U11015.7#0']),(RTN,original_rtn_group)):
            uf,groups=P.physical(model,net,masks);touched=[g for g in groups if set(g['pad_ids'])&set(relation)]
            if len(touched)!=2:entry['routes'].append({'net':net,'reason':'Expected two exact RTN/ILIM components differs','count':len(touched)});break
            free,_=model.free({'net':net,'domain':'DOM_FIELD_A'},'B.Cu',window)
            seeds=[S.seed_sites(g,'B.Cu',free,window) for g in touched]
            path,search=S.astar(free,*seeds,time.monotonic()+8,node_cap=80000) if all(seeds) else (None,{'reason':'No exact local pad/component seeds'})
            entry['routes'].append({'net':net,'seed_counts':[len(v) for v in seeds],'search':search})
            if not path:break
            path.update(net=net,layer='B.Cu',width_mm=.2,obligation=relation,length_mm=LineString(path['points_mm']).length)
            # The regulator support circuits remain short local traces, never
            # a route to FIELD_GND or an impedance/return-plane qualification.
            if path['length_mm']>8:entry['routes'][-1]['reason']='Local support path exceeds8mm screen bound';break
            path['new_items']=[]
            for a,b in zip(path['points_mm'],path['points_mm'][1:]):
                uid,ch=P.serial_segment(net,'B.Cu',a,b);candidate_local[uid]=ch;path['new_items'].append(uid)
            paths.append(path);lg=P.geometry(candidate_local,moved_template);model=S.Model(lg,reserved,exempt)
        entry['complete']=len(paths)==2;attempts.append(entry)
        if len(paths)==2:
            failures=[]
            for net in (NET,RTN,DVDT):
                uf,gr=P.physical(model,net,masks)
                rels=parts['nets'][net]
                if net==DVDT:rels=rels+[r['r06_pad_relationship'] for r in row['native_lost_relationships']]
                for rel in rels:
                    if len({uf.find(('p',p)) for p in rel})>1:failures.append({'net':net,'relationship':rel})
            if failures:entry['relationship_failures']=failures;continue
            proposal={'new_R11056_pose_mm':site['xy_mm'],'translation_mm':[dx,dy],'routes':paths,'source_contract_excerpt':contract,'native_pad_relationships_preserved_host':True,'local_RTNs_separate_from_FIELD_GND':True,'native_and_return_geometry_qualification':'OPEN'}
            break
    emitted=None
    if proposal:
        footprintuid=next(u for u,ch in current[3].items() if C.pcbtext.chunk_kind(ch)=='footprint' and F.ref_of(ch)==REF);fchunk=current[3][footprintuid]
        head,nodes=F.children(fchunk);oldat=next(n for n in nodes if F.kind(n)==b'at');newat=f'(at {proposal["new_R11056_pose_mm"][0]:.6f} {proposal["new_R11056_pose_mm"][1]:.6f} {F.pose(nodes)[2]:.6f})'.encode()
        if fchunk.count(oldat)!=1:raise ValueError('Direct pose expression not unique')
        newfp=fchunk.replace(oldat,newat,1)
        _,newnodes=F.children(newfp)
        if F.protected_children(nodes)!=F.protected_children(newnodes):raise ValueError('Moved footprint changed protected local geometry')
        cand=current[0]+b''.join(newfp if C.pcbtext.chunk_uuid(ch)==footprintuid else ch for ch in current[1] if C.pcbtext.chunk_uuid(ch) not in removes)+b''.join(ch for uid,ch in candidate_local.items() if uid not in current[4])+current[2]
        inv=C.inventory(cand)
        allowed=removes|{footprintuid}
        if any(inv[3].get(u)!=ch for u,ch in current[3].items() if u not in allowed):raise ValueError('Unauthorized item change')
        emitted=HERE/'aux-local-r1-host-only.kicad_pcb';emitted.write_bytes(cand)
        proposal.update(candidate_sha256=C.sha(cand),changed_footprint_uuid=footprintuid,footprint_before_sha256=C.sha(fchunk),footprint_after_sha256=C.sha(newfp))
    for p,h in READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Source changed:'+p)
    report={'schema':'aux24-local-coupled-move-r1','verdict':'HOST_CANDIDATE_REQUIRES_INDEPENDENT_NATIVE_ELECTRICAL_AUDIT' if proposal else 'NO_LOCAL_PLACEMENT_ROUTE_IN_DECLARED_SCREEN','input_sha256':C.sha(original),'restore_original_DVDT_items':sorted(restores),'delete_ILIM_route_items':sorted(removes),'old_R11056_RTN_contacts_retained':contact_items,'candidate':str(emitted) if emitted else None,'proposal':proposal,'placement_screen':sites,'route_attempts':attempts,'read_files_sha256':READS,'seconds':time.time()-started,'native_jobs':0,'gpu_jobs':0,'board_emitted':bool(proposal),'adopted':False,'manufacturing_ready':False,'limits':['49 poses;10 shortest feasible placements; local3pin+support layout only','Only R11056 pose and own ILIM route change; DVDT source-restored; RTN reconnect to exact existing native pad group','No new vias and no plane changes; moved SMD pads require0.10mm hole-edge registration gap','Native full DRC/dual continuity, fresh placed footprints/actual pad polygons, local RTN loop and reverse-polarity support qualification remain mandatory']}
    output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(output),'verdict':report['verdict'],'candidate':str(emitted) if emitted else None}),flush=True)
if __name__=='__main__':main()
