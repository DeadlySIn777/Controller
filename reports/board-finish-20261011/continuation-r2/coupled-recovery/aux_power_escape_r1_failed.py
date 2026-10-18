"""Couple AUX24_A support repair with its blocking local power trunk.

No footprint, source, via or plane change. Preserve every current relationship
in all three edited nets. Power replacement retains1.2mm width; current/drop,
short local RTN support loops and fresh native qualification remain open.
"""
import collections,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import coupled_screen as P
G,S,C,R,K=P.G,P.S,P.C,P.R,P.K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
POWER='/motherboard_motors/AUX_24V_A'
ILIM='/motherboard_power_entry/AUX24_A_ILIM'
DVDT='/motherboard_power_entry/AUX24_A_DVDT'
POWER_IDS={'24d2518a-09b9-42a0-b2ce-234e44d22495','398225d7-768e-4e4d-b092-33fc7bc399e6','3c529a51-ad62-4326-87af-dc71f9ce5799','3fab9580-e53e-4f89-b3bf-bc9671bdc6a3','d3114b32-a9d4-47d1-8fe5-14fb8e1b9598','f1961e72-15d0-47c2-ba42-033009c0b97b'}
READS={}

def read(p):
    p=Path(p).resolve();raw=p.read_bytes();READS[str(p)]=C.sha(raw);return raw

def path_between(model,net,width,starts,ends,window,seconds=12):
    saved=S.WIDTH;S.WIDTH=width
    try:
        free,blocks=model.free({'net':net,'domain':'DOM_FIELD_A'},'B.Cu',window)
        seeds=[[ (point,owner) for point,owner in group if free.covers(Point(point))] for group in (starts,ends)]
        path,search=S.astar(free,*seeds,time.monotonic()+seconds,node_cap=200000) if all(seeds) else (None,{'reason':'no exact endpoint/land seeds','nodes':0})
        return path,{'seed_counts':[len(g) for g in seeds],'blockers':len(blocks),'free_area_mm2':free.area,**search}
    finally:S.WIDTH=saved

def main():
    output=HERE/'aux-power-escape-r1.json'
    if output.exists():raise ValueError('Fresh output required')
    for p in (Path(__file__),Path(P.__file__),Path(G.__file__),Path(S.__file__),Path(C.__file__),Path(C.pcbtext.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),Path(K.__file__),Path(R.__file__)):read(p)
    original=read(G.SOURCE);old_raw=read(S.overlay_tool.base.BASE);current=C.inventory(original);old=C.inventory(old_raw)
    if C.sha(original)!='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab':raise ValueError('Current source changed')
    template=json.loads(read(S.overlay_tool.base.GEOM));parts=json.loads(read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'];native=json.loads(read(G.REPORT/'measure/r07-four-fag-shared/source-proof.json'))
    originalg=P.geometry(current[4],template);masks,provenance,reuse=K.actual_masks(originalg,old,current,template,native)
    graph=json.loads(read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==DVDT);restores={r['uuid'] for r in row['missing_original_items']}
    ilim_ids={uid for uid,ch in current[4].items() if S.norm(S.overlay_tool.netname(ch))==ILIM};removes=ilim_ids|POWER_IDS
    for uid in POWER_IDS:
        r=G.parse(uid,current[4][uid],{})
        if (r['net'],r['kind'],r['layer'],r['w'])!=(POWER,'segment','B.Cu',1.2):raise ValueError('Owned power chain differs')
    # Exact unordered chain endpoints and every former external contact are
    # recorded. Branching/extra pads require current native pad obligations.
    endpoints=collections.Counter();old_length=0.
    for uid in POWER_IDS:
        r=G.parse(uid,current[4][uid],{});endpoints.update((tuple(r['a']),tuple(r['b'])));old_length+=math.dist(r['a'],r['b'])
    terminals=[p for p,n in endpoints.items() if n==1]
    if len(terminals)!=2 or set(terminals)!={(319.25,48.95),(316.85,51.95)}:raise ValueError('Power chain topology differs')
    local={uid:ch for uid,ch in current[4].items() if uid not in removes};local.update({uid:old[4][uid] for uid in restores})
    for uid in restores:
        via=next((v for v in template['vias'] if v['uuid']==uid),None)
        if via:masks[uid]=set(via['flashed'])
    reserved=json.loads(read(G.C06/'alternate-r07/reserved-r07.json'));exempt={}
    for line in read(G.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exempt[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    print('AUX_POWER_ESCAPE_MODEL',flush=True);g=P.geometry(local,template);model=S.Model(g,reserved,exempt)
    # Route the local ILIM first. The removed power footprint is free channel;
    # the subsequent1.2mm power replacement must clear its entire final path.
    uf,groups=P.physical(model,ILIM,masks);relation=['R11056.1#0','U11015.7#0'];touched=[gr for gr in groups if set(gr['pad_ids'])&set(relation)]
    if len(touched)!=2:raise ValueError('ILIM source/load components differ')
    window=box(310,41,330,59);target={'net':ILIM,'domain':'DOM_FIELD_A'};free,_=model.free(target,'B.Cu',window);seeds=[S.seed_sites(gr,'B.Cu',free,window) for gr in touched]
    ilim,ilim_search=S.astar(free,*seeds,time.monotonic()+12,node_cap=120000) if all(seeds) else (None,{'reason':'no exact ILIM component seeds'})
    paths=[];attempts=[];proposal=None
    if ilim:
        ilim.update(net=ILIM,layer='B.Cu',width_mm=.2,obligation=relation,length_mm=LineString(ilim['points_mm']).length,new_items=[])
        if ilim['length_mm']<=8:
            for a,b in zip(ilim['points_mm'],ilim['points_mm'][1:]):
                uid,ch=P.serial_segment(ILIM,'B.Cu',a,b);local[uid]=ch;ilim['new_items'].append(uid)
            paths.append(ilim);g=P.geometry(local,template);model=S.Model(g,reserved,exempt)
            fake={'uuid':'owned exact original power chain endpoint','kind':'track'}
            for grow in (5,12,20):
                window=LineString(terminals).envelope.buffer(grow,cap_style=3).envelope
                power,search=path_between(model,POWER,1.2,[(terminals[0],fake)],[(terminals[1],fake)],window);attempts.append({'window_mm':list(window.bounds),**search})
                print('AUX_POWER_PATH',grow,search,flush=True)
                if not power:continue
                power.update(net=POWER,layer='B.Cu',width_mm=1.2,length_mm=LineString(power['points_mm']).length,new_items=[])
                for a,b in zip(power['points_mm'],power['points_mm'][1:]):
                    uid,ch=P.serial_segment(POWER,'B.Cu',a,b,1.2);local[uid]=ch;power['new_items'].append(uid)
                paths.append(power);g=P.geometry(local,template);model=S.Model(g,reserved,exempt)
                failures=[]
                for net in (POWER,ILIM,DVDT):
                    uf,gr=P.physical(model,net,masks)
                    rels=parts[net]
                    if net==DVDT:rels=rels+[r['r06_pad_relationship'] for r in row['native_lost_relationships']]
                    for rel in rels:
                        if len({uf.find(('p',p)) for p in rel})>1:failures.append({'net':net,'relationship':rel})
                proposal={'paths':paths,'native_pad_obligations_host_failures':failures,'unchanged_component_poses_and_local_pad_geometry':True,'power_original_length_mm':old_length,'power_added_length_mm':power['length_mm']-old_length,'power_width_mm':1.2,'electrical_qualification':'OPEN'}
                break
    emitted=None
    if proposal and not proposal['native_pad_obligations_host_failures']:
        cand=current[0]+b''.join(ch for ch in current[1] if C.pcbtext.chunk_uuid(ch) not in removes)+b''.join(ch for uid,ch in local.items() if uid not in current[4])+current[2];inv=C.inventory(cand)
        if inv[5]!=current[5] or any(inv[3].get(u)!=ch for u,ch in current[3].items() if u not in removes):raise ValueError('Unauthorized retained item change')
        emitted=HERE/'aux-power-escape-r1-host-only.kicad_pcb';emitted.write_bytes(cand);proposal['candidate_sha256']=C.sha(cand)
    READS.update(S.READS);READS.update(G.READS)
    for p,h in READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Source changed:'+p)
    result={'schema':'aux-power-escape-r1','verdict':'HOST_STAGED_REQUIRES_INDEPENDENT_ELECTRICAL_NATIVE_AUDIT' if emitted else 'BOUNDED_LOCAL_POWER_ESCAPE_INCOMPLETE','input_sha256':C.sha(original),'owned_power_items':sorted(POWER_IDS),'delete_ILIM_items':sorted(ilim_ids),'restore_original_DVDT_items':sorted(restores),'ilim_search':ilim_search,'power_searches':attempts,'proposal':proposal,'candidate':str(emitted) if emitted else None,'read_files_sha256':READS,'native_jobs':0,'gpu_jobs':0,'board_emitted':bool(emitted),'adopted':False,'manufacturing_ready':False,'limits':['No new via, footprint pose or plane change','Source-restored ordinary DVDT via; existing historical drill/land status still needs review','ILIM is a local AUX24_A_RTN support circuit, not a FIELD_GND-plane-controlled line','Power keeps1.2mm B width; full current/IR budget and correct source net role remain electrical gates','Current and r06 pad relationships must all survive both native no-loss gates; affected original-power contact graph separately audited','5/12/20mm windows, .1mm grid,200000 nodes,12s per power search; negative is bounded']}
    output.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(output),'verdict':result['verdict'],'candidate':str(emitted) if emitted else None}),flush=True)
if __name__=='__main__':main()
