"""Coupled recovery screen on immutable198b. No native load, save, or GPU.

Restore withdrawn original geometry in one cluster and repair the exact current
contact obligations lost by removing only nominated blockers. Serialized native
coordinates are retained; native baseline pad partitions verify the graph before
its use. A path is a staged proposal, never native/electrical qualification.
"""
import collections,copy,hashlib,json,math,re,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_graph as G
S,C,R=G.S,G.C,G.R
sys.path.insert(0,str(G.C06/'four-fag/next-closure'))
import screen_closure_r1 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree

def geometry(chunks,template):
    g=copy.deepcopy(template); arcs={t['uuid']:t for t in template['tracks'] if t.get('kind')=='arc'}
    tracks=[];vias=[]
    for uid,ch in chunks.items():
        r=G.parse(uid,ch,arcs)
        if r['kind']=='via':
            vias.append({'uuid':uid,'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'span':['F.Cu','B.Cu'],'flashed':g['copper_layers']})
        elif r['kind']=='segment':tracks.append({'uuid':uid,'net':r['net'],'a':r['a'],'b':r['b'],'w':r['w'],'layer':r['layer']})
        else:tracks.append(arcs[uid])
    g['tracks'],g['vias']=tracks,vias
    g['domains_normalized']={S.norm(n):d for n,d in g['nets'].items()}
    return g

def physical(model,net,masks):
    records=[r for r in model.own[net] if r['kind']!='via' or r['layer'] in masks.get(r['uuid'],set())]
    uf=S.UF()
    for r in records:uf.find(r['key'])
    for layer in model.g['copper_layers']:
        rows=[r for r in records if r['layer']==layer]
        tree=STRtree([r['shape'] for r in rows])
        for i,r in enumerate(rows):
            for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
                if i<j and r['shape'].distance(rows[j]['shape'])<=.000002:uf.join(r['key'],rows[j]['key'])
    groups=collections.defaultdict(lambda:{'pad_ids':[],'records':[],'layers':set()})
    for r in records:
        group=groups[uf.find(r['key'])];group['records'].append(r)
        if r['kind']=='pad' and r['pad_id'] not in group['pad_ids']:group['pad_ids'].append(r['pad_id'])
        # Nominal/suppressed via span alone does not create a routing landing.
        if r['kind'] in ('pad','track') or (r['kind']=='via' and r['uuid'] in masks):group['layers'].add(r['layer'])
    return uf,list(groups.values())

def exact_partitions(groups):return {frozenset(g['pad_ids']) for g in groups if g['pad_ids']}

def update(model,g,chunks,template,reserved,exempt):
    # Rebuild exact serialized geometry after each coupled path. Kept separate
    # from the initial immutable model so an unsuccessful cluster is discarded.
    g=geometry(chunks,template)
    return S.Model(g,reserved,exempt),g

def serial_segment(net,layer,a,b,width=.2):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-coupled-r2/'+net+'/'+layer+'/'+repr((a,b,width))))
    f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    chunk=(f'\t(segment\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(width {f(width)})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
    return uid,chunk

def reference_only(model,net,domain,layer,window):
    # Existing fill caches are conservative r06 source. This records coverage
    # only; source anchoring after all coupled changes stays a separate gate.
    return model.reference(domain,layer,window)

def main():
    started=time.time();output=HERE/'coupled-screen-r1.json'
    if output.exists():raise ValueError('Distinct receipt required')
    graph=json.loads(G.read(HERE/'conflict-graph.json'));raw=G.read(G.SOURCE);base_raw=G.read(S.overlay_tool.base.BASE)
    if C.sha(raw)!=graph['candidate_sha256']:raise ValueError('Graph current source differs')
    current=C.inventory(raw);old=C.inventory(base_raw);template=json.loads(G.read(S.overlay_tool.base.GEOM))
    native_new=json.loads(G.read(G.REPORT/'measure/r07-four-fag-shared/source-proof.json'))
    parts=json.loads(G.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets']
    controlled={S.norm(n):p for n,p in json.loads(G.read(S.CONTROLLED))['nets'].items()}
    reserved=json.loads(G.read(G.C06/'alternate-r07/reserved-r07.json'));exempt={}
    for line in G.read(G.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exempt[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    g=geometry(current[4],template);masks,provenance,reuse=K.actual_masks(g,old,current,template,native_new)
    print('BUILD_EXACT_CURRENT_MODEL',flush=True); initial=S.Model(g,reserved,exempt)
    current_shapes={};verifications=[]
    affected=set(n for cluster in graph['coupled_net_clusters'] for n in cluster)
    for net in sorted(affected):
        uf,groups=physical(initial,net,masks);pn=next(n for n in parts if S.norm(n)==net)
        if exact_partitions(groups)!={frozenset(x) for x in parts[pn]}:raise ValueError('Actual current native partition mismatch '+net)
        current_shapes[net]=groups;verifications.append({'net':net,'native_groups':parts[pn],'host_exact_partition_match':True})
    # Begin with local two-net clusters; the multi-net clusters are attempted
    # after these successes and keep the same explicit obligation method.
    clusters=sorted(graph['coupled_net_clusters'],key=lambda ns:(len(ns),sum(len(e['item_uuids']) for row in graph['lost_route_rows'] if row['net'] in ns for e in row['blocking_nets'].values())))
    results=[];successes=[];combined_chunks=dict(current[4])
    for ci,cluster in enumerate(clusters):
        print('CLUSTER',ci,cluster,flush=True);local=dict(combined_chunks);rows=[r for r in graph['lost_route_rows'] if r['net'] in cluster]
        restoring={r['uuid'] for row in rows for r in row['missing_original_items']}
        removing={e['blocker_uuid'] for e in graph['conflict_edges'] if e['restore_net'] in cluster}
        if restoring&removing:raise ValueError('Restored/withdrawn roles overlap')
        for uid in removing:local.pop(uid)
        for uid in restoring:
            if uid in local:raise ValueError('Restored source UUID currently exists')
            local[uid]=old[4][uid]
        removed_nets={S.norm(S.overlay_tool.netname(current[4][uid])) for uid in removing}
        result={'cluster':cluster,'restored_original_items':sorted(restoring),'removed_blockers':sorted(removing),'removed_nets':sorted(removed_nets),'reroutes':[],'failures':[],'source_reference_qualification':'OPEN','native_qualification':'NOT_RUN'}
        # Native observed masks of original r06 items are restored unchanged.
        local_masks=dict(masks)
        for uid in restoring:
            found=next((v for v in template['vias'] if v['uuid']==uid),None)
            if found:local_masks[uid]=set(found['flashed'])
        print('REBUILD_CLUSTER',len(restoring),len(removing),flush=True);model,lg=update(None,None,local,template,reserved,exempt)
        for net in sorted(removed_nets):
            policy=controlled.get(net)
            if policy and policy.get('class') not in (None,'NONE'):
                result['failures'].append({'net':net,'reason':'New geometry requires controlled impedance qualification','policy':policy['class']});continue
            obligations=[g['pad_ids'] for g in current_shapes[net] if len(g['pad_ids'])>1]
            domain=lg['domains_normalized'][net]
            for obligation in obligations:
                for attempt in range(len(obligation)-1):
                    uf,groups=physical(model,net,local_masks);touched=[gr for gr in groups if set(gr['pad_ids'])&set(obligation)]
                    if len(touched)==1:break
                    touched.sort(key=lambda gr:len(set(gr['pad_ids'])&set(obligation)),reverse=True)
                    groups_pair=touched[:2];a=unary_union([r['shape'] for r in groups_pair[0]['records']]);b=unary_union([r['shape'] for r in groups_pair[1]['records']]);pa,pb=nearest_points(a,b)
                    found=None;details=[]
                    for grow in (5,12,25):
                        window=LineString([pa,pb]).envelope.buffer(grow,cap_style=3).envelope
                        for layer in S.LAYERS:
                            if not all(layer in gr['layers'] for gr in groups_pair):continue
                            target={'net':net,'domain':domain};free,_=model.free(target,layer,window)
                            refs=reference_only(model,net,domain,layer,window);strict=free.intersection(refs)
                            seeds=[S.seed_sites(gr,layer,strict,window) for gr in groups_pair]
                            route,search=S.astar(strict,*seeds,time.monotonic()+7,node_cap=60000) if all(seeds) else (None,{'reason':'No reference-covered seeds','nodes':0})
                            details.append({'layer':layer,'window_mm':list(window.bounds),'seeds':[len(z) for z in seeds],**search})
                            if route:found=dict(route,net=net,layer=layer,width_mm=.2,restored_current_obligation=obligation,reference_layer=S.REF_LAYER[layer]);break
                        if found:break
                    if not found:
                        result['failures'].append({'net':net,'obligation':obligation,'reason':'No zero-via coupled path in declared windows','searches':details});break
                    emitted=[]
                    for a,b in zip(found['points_mm'],found['points_mm'][1:]):
                        uid,ch=serial_segment(net,found['layer'],a,b)
                        if uid in local:raise ValueError('New coupled segment UUID collides')
                        local[uid]=ch;emitted.append(uid)
                    found['new_items']=emitted;result['reroutes'].append(found)
                    print('COUPLED_ZERO_VIA',net,found['layer'],len(emitted),flush=True)
                    model,lg=update(None,None,local,template,reserved,exempt)
        # Check all old/current pad relationship obligations after construction.
        for net in cluster:
            uf,groups=physical(model,net,local_masks)
            relations=[g['pad_ids'] for g in current_shapes[net]]
            relations.extend(rel['r06_pad_relationship'] for row in rows if row['net']==net for rel in row['native_lost_relationships'])
            for rel in relations:
                if len({uf.find(('p',p)) for p in rel})>1:result['failures'].append({'net':net,'relationship':rel,'reason':'Final coupled native-baseline relationship not restored in host graph'})
        result['verdict']='HOST_GEOMETRY_PLAN_NATIVE_REFERENCE_OPEN' if not result['failures'] else 'BOUNDED_COUPLED_SCREEN_INCOMPLETE'
        if not result['failures']:
            combined_chunks=local;successes.append(result)
        results.append(result)
        (HERE/'coupled-progress-r1.json').write_text(json.dumps({'results':results},indent=1)+'\n',encoding='utf-8')
        print('CLUSTER_RESULT',result['verdict'],len(result['failures']),flush=True)
    # Retained item bytes are exact outside an explicit successful ownership set.
    deleted=set().union(*(set(x['removed_blockers']) for x in successes)) if successes else set()
    restored=set().union(*(set(x['restored_original_items']) for x in successes)) if successes else set()
    head,chunks,tail,*_=current
    candidate=head+b''.join(ch for ch in chunks if C.pcbtext.chunk_uuid(ch) not in deleted)+b''.join(ch for uid,ch in combined_chunks.items() if uid not in current[4])+tail
    final=C.inventory(candidate)
    if final[5]!=current[5] or any(final[4].get(uid)!=ch for uid,ch in current[4].items() if uid not in deleted):raise ValueError('Unauthorized retained-item change')
    for p,h in G.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Read source changed '+p)
    if successes:(HERE/'coupled-r1-host-only.kicad_pcb').write_bytes(candidate)
    receipt={'schema':'coupled-recovery-r1','verdict':'STAGED_HOST_ONLY_NATIVE_AND_REFERENCE_OPEN' if successes else 'NO_COMPLETE_COUPLED_ZERO_VIA_CLUSTER','input_sha256':C.sha(raw),'candidate_sha256':C.sha(candidate) if successes else None,'native_partition_verification':verifications,'successful_clusters':len(successes),'deleted_items':sorted(deleted),'restored_items':sorted(restored),'results':results,'read_files_sha256':G.READS,'seconds':time.time()-started,'native_jobs':0,'gpu_jobs':0,'board_emitted':bool(successes),'adopted':False,'manufacturing_ready':False,'limits':['Zero new vias; .2mm ordinary signals only','Conservative unchanged r06 fill coverage, no fresh source-reference qualification','5/12/25mm local window growth; 7s per layer and 60000 nodes; .1mm planner grid','Restored original r06 via annuli observed natively; changed ordinary KEEP_ALL existing vias remain source-only where current native annuli were not exported','All 198b and r06 native pad relationships in each changed net are mandatory; fresh full native dual guards mandatory']}
    output.write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(output),'clusters':len(successes),'candidate_sha256':receipt['candidate_sha256']}),flush=True)
if __name__=='__main__':main()
