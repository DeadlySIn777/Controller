"""Fresh exact-source F-layer XF pair reconstruction, host only.

Unlike prior cache screens this uses filled198b native integer source geometry
and every actual via flash mask. It first tests a direct no-transition repair;
then restores original request F-only copper and removes only nominated F
power-enable blockers, rebuilding their complete current contact obligations.
"""
import collections,json,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact as A
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
REQ='/motherboard_operator/XF_REQUEST_BUFFER'
EN='/motherboard_operator/XF_POWER_EN_GATED'

def anchored(model,masks,layer):
    ref=S.REF_NET['DOM_LOGIC'];plane=S.REF_LAYER[layer]
    fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']==ref])
    cu=[]
    for r in model.records[plane]:
        if r['net']!=ref or r['kind'] not in ('pad','track','via'):continue
        if r['kind']=='via' and plane not in masks[r['uuid']]:continue
        cu.append(r['shape'])
    entire=unary_union([fill]+cu)
    source=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane]))
    joined=unary_union([part for part in P.K.D.components(entire) if part.intersects(source)])
    return fill.intersection(joined),{'plane':plane,'source_pad':'J11001.2#0','source_connected_area_mm2':joined.area,'source_connected_fill_mm2':fill.intersection(joined).area}

def main():
    out=HERE/'xf-fresh-reference-r1.json';start=time.time()
    if out.exists():raise ValueError('Fresh output required')
    raw=A.read(G.SOURCE);oldraw=A.read(S.overlay_tool.base.BASE);now=C.inventory(raw);old=C.inventory(oldraw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Source pin differs')
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    r06={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    graph=json.loads(A.read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==REQ)
    reserve,exempt=A.reservations();print('XF_FRESH_BASE_MODEL',flush=True);g=P.geometry(now[4],template);base=S.Model(g,reserve,exempt)
    failures,checks,uf,groups=A.relationships(base,masks,parts,(REQ,EN))
    if failures or not all(c['exact_native_partition_match'] for c in checks):raise ValueError('Current exact native pad partitions differ')
    sourcegroups=groups;results=[];emitted=None
    for mode in ('direct_F_repair','coupled_F_owned_blockers'):
        chunks=dict(now[4]);restores=set();deletes=set();paths=[];result={'mode':mode,'paths':[],'searches':[]}
        if mode=='coupled_F_owned_blockers':
            restores={r['uuid'] for r in row['missing_original_items'] if r['kind']=='segment' and r['layer']=='F.Cu'}
            # Keep the actual gate via and In3 signal. Only blocking F copper
            # may move, with every original physical contact still obligated.
            blockers=row['blocking_nets'][EN]['item_uuids']
            deletes={u for u in blockers if C.pcbtext.chunk_kind(now[4][u])=='segment' and C.pcbtext.chunk_layer(now[4][u])=='F.Cu'}
            chunks={u:ch for u,ch in chunks.items() if u not in deletes};chunks.update({u:old[4][u] for u in restores})
            g=P.geometry(chunks,template);model=S.Model(g,reserve,exempt)
        else:model=base
        result.update(restored_original_items=sorted(restores),deleted_owned_items=sorted(deletes))
        for net in ((EN,REQ) if deletes else (REQ,)):
            relations=parts[net]+(r06[net] if net==REQ else [])
            for rel in relations:
                uf,gs=P.physical(model,net,masks);touch=[gr for gr in gs if set(gr['pad_ids'])&set(rel)]
                if len(touch)<=1:continue
                touch.sort(key=lambda x:len(x['pad_ids']),reverse=True)
                for i in range(1,len(touch)):
                    bodies=[unary_union([r['shape'] for r in z['records']]) for z in (touch[0],touch[i])]
                    pa,pb=nearest_points(*bodies);window=LineString([pa,pb]).envelope.buffer(12,cap_style=3).envelope
                    free,_=model.free({'net':net,'domain':model.domains[net]},'F.Cu',window);refs,witness=anchored(model,masks,'F.Cu');strict=free.intersection(refs)
                    seeds=[S.seed_sites(z,'F.Cu',strict,window) for z in (touch[0],touch[i])]
                    path,search=S.astar(strict,*seeds,time.monotonic()+12,node_cap=150000) if all(seeds) else (None,{'reason':'No fresh source-covered component seeds'})
                    result['searches'].append({'net':net,'relationship':rel,'seed_counts':[len(z) for z in seeds],'reference':witness,**search})
                    if not path:break
                    path.update(net=net,layer='F.Cu',width_mm=.2,length_mm=LineString(path['points_mm']).length,new_items=[])
                    for a,b in zip(path['points_mm'],path['points_mm'][1:]):u,ch=P.serial_segment(net,'F.Cu',a,b,.2);chunks[u]=ch;path['new_items'].append(u)
                    paths.append(path);g=P.geometry(chunks,template);model=S.Model(g,reserve,exempt)
                else:continue
                break
            else:continue
            break
        new_failures=[];contact_loss=[]
        for net in (REQ,EN):
            uf,gs=P.physical(model,net,masks)
            for baseline,reln in (('current198b',parts[net]),('r06',r06[net])):
                for rel in reln:
                    if len({uf.find(('p',p)) for p in rel})>1:new_failures.append({'net':net,'baseline':baseline,'relationship':rel})
            for gr in sourcegroups[net]:
                keys={r['key'] for r in gr['records'] if r['uuid'] not in deletes}
                if len({uf.find(k) for k in keys})>1:contact_loss.append({'net':net,'keys':[list(k) for k in keys]})
        result.update(paths=paths,pad_relationship_failures=new_failures,surviving_physical_contact_losses=contact_loss)
        if not new_failures and not contact_loss:
            added={u for p in paths for u in p['new_items']};parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restores}
            errors,clearance,anti=A.clearance(model,parsed,added,restores);result.update(clearance_errors=errors,changed_item_clearance=clearance,prospective_antipads=anti)
            if not errors:
                candidate=now[0]+b''.join(ch for ch in now[1] if C.pcbtext.chunk_uuid(ch) not in deletes)+b''.join(ch for u,ch in chunks.items() if u not in now[4])+now[2]
                inv=C.inventory(candidate)
                if now[5]!=inv[5] or any(inv[3].get(u)!=ch for u,ch in now[3].items() if u not in deletes):raise ValueError('Unauthorized source item differs')
                emitted=HERE/'xf-fresh-reference-r1-host-only.kicad_pcb';emitted.write_bytes(candidate);result['candidate_sha256']=C.sha(candidate)
        result['verdict']='HOST_CANDIDATE_NATIVE_ELECTRICAL_OPEN' if emitted else 'BOUNDED_EXACT_SOURCE_LAYOUT_INCOMPLETE';results.append(result)
        print('XF_FRESH_RESULT',mode,result['verdict'],flush=True)
        if emitted:break
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen read changed '+p)
    r={'schema':'xf-fresh-native-source-pair-r1','source_sha256':A.SOURCE_SHA,'native_pad_fill_proof':proof,'current_native_partition_checks':checks,
       'results':results,'candidate':str(emitted) if emitted else None,'read_files_sha256':A.READS,'seconds':time.time()-start,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,
       'limits':['Fresh source-connected In1 reference; fixed F.Cu only, no new or restored vias','12mm window growth/.1mm grid/12s/150000nodes','Coupled mode retains existing gate via/In3 geometry; all native pads and surviving physical entities mandatory','Native refill/full ordinary DRC/dual no-loss and complete electrical source-reference/timing/return gates remain open']}
    out.write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(out),'candidate':str(emitted) if emitted else None}),flush=True)
if __name__=='__main__':main()
