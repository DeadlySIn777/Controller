"""Concrete XF coupled transition relocation with correct LOGIC_GND returns.

Host proposal only. Existing r07 enable gain stays obligated; the two request
pad groups must rejoin. Exact source-owned removals and surviving entity/contact
ledger are mandatory. Every new through-via needs actual native annuli after
candidate creation; nominal spans are not native connectivity evidence.
"""
import collections,json,math,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact as A
import xf_fresh_reference as X
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
REQ,EN=X.REQ,X.EN
GND='/LOGIC_GND'

def serial_via(net,at):
    u=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-coupled-r2/XF/'+net+'/'+repr(at)))
    f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    ch=(f'\t(via\n\t\t(at {f(at[0])} {f(at[1])})\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n').encode()
    return u,ch

def refs_after(model,masks,signals):
    ref={};witness={};cut=unary_union([Point(p).buffer(.475,resolution=128) for p in signals])
    for signal,plane in (('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')):
        fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']==GND]).difference(cut)
        own=[]
        for r in model.records[plane]:
            if r['net']!=GND or r['kind'] not in ('pad','track','via'):continue
            if r['kind']=='via':
                if plane not in masks.get(r['uuid'],set()):continue
                v=next(v for v in model.g['vias'] if v['uuid']==r['uuid'])
                own.append(r['shape'].difference(Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128)))
            else:own.append(r['shape'])
        entire=unary_union([fill]+own);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane]))
        connected=unary_union([part for part in P.K.D.components(entire) if part.intersects(anchor)])
        ref[signal]=fill.intersection(connected);witness[plane]={'source_pad':'J11001.2#0','source_connected_fill_area_mm2':ref[signal].area,'prospective_signal_antipads_mm':signals}
    return ref,witness

def main():
    out=HERE/'xf-coupled-transition-r1.json';start=time.time()
    if out.exists():raise ValueError('Fresh output required')
    raw=A.read(G.SOURCE);oldraw=A.read(S.overlay_tool.base.BASE);now=C.inventory(raw);old=C.inventory(oldraw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Current source pin differs')
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    native_parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    old_parts={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    graph=json.loads(A.read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==REQ)
    reserve,exempt=A.reservations();print('XF_TRANSITION_BASE_MODEL',flush=True);bg=P.geometry(now[4],template);base=S.Model(bg,reserve,exempt)
    failures,checks,old_uf,old_groups=A.relationships(base,masks,native_parts,(REQ,EN))
    if failures or not all(c['exact_native_partition_match'] for c in checks):raise ValueError('Actual baseline partition mismatch')
    blocker=set(row['blocking_nets'][EN]['item_uuids'])
    if blocker!={'1960baa4-4938-4c66-8a45-92a9b93ed1ec','1f680f52-494f-4d1f-a54d-544eb08dfd8e','5b19123d-05fe-4928-ba35-1c18ad3aebf3','d3a00642-3f2b-49fb-ab3b-1d48310b5a62'}:raise ValueError('Owned gate transition differs')
    restore={r['uuid'] for r in row['missing_original_items']}
    withheld={'b1bde65e-ae89-4c0d-9caf-bf5d95d85600','3dadaf02-aad8-4d65-ad43-99096cf08382','5350f7dd-02b4-40be-8c0d-3fecb2805543','5568a777-bb7f-423f-a181-96f36d9376a1'}
    restore-=withheld
    chunks={u:ch for u,ch in now[4].items() if u not in blocker};chunks.update({u:old[4][u] for u in restore})
    original_vias={v['uuid']:v for v in template['vias']}
    for u in restore:
        if u in original_vias:masks[u]=set(original_vias[u]['flashed'])
    # Selected from the exact conflicting source transition geometry. New
    # return stitches attach to the actual source-connected planes, not signal
    # labels. Existing return at298.8,104.15 supports the relocated first via.
    new_specs=[(REQ,[297.9,104.15]),(EN,[298.8,106.35]),(GND,[299.65,106.35]),(GND,[299.4,107.95])]
    added=set();new_vias={}
    for net,at in new_specs:
        u,ch=serial_via(net,at);chunks[u]=ch;added.add(u);new_vias[u]={'net':net,'at_mm':at}
        # Only a planning expectation. Native output must independently attest
        # every actual annulus; no nominal span receives qualification credit.
        masks[u]={'F.Cu','In3.Cu','In1.Cu','In4.Cu'}
    g=P.geometry(chunks,template);model=S.Model(g,reserve,exempt)
    parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restore}
    errors,rows,anti=A.clearance(model,parsed,added,restore)
    result={'deleted_owned_items':sorted(blocker),'restored_original_items':sorted(restore),'withheld_original_transition_items':sorted(withheld),
            'new_vias':new_vias,'initial_clearance_errors':errors,'initial_changed_item_clearance':rows,'prospective_antipads':anti,'paths':[],'searches':[]}
    signals=[[297.9,104.15],[298.8,106.35],[298.55,107.95]];refs,witness=refs_after(model,masks,signals);result['source_reference_witness']=witness
    stitch_pairs=[([297.9,104.15],[298.8,104.15],'528eda02-ba4d-4071-a423-a1e94804c852'),([298.8,106.35],[299.65,106.35],next(u for u,v in new_vias.items() if v['at_mm']==[299.65,106.35])),([298.55,107.95],[299.4,107.95],next(u for u,v in new_vias.items() if v['at_mm']==[299.4,107.95]))]
    returns=[]
    for sig,ret,uid in stitch_pairs:
        ann=Point(ret).buffer(.3,resolution=128).difference(Point(ret).buffer(.15,resolution=128))
        rows_={'signal_at_mm':sig,'return_at_mm':ret,'return_uuid':uid,'distance_mm':math.dist(sig,ret),
               'source_connected_plane_contacts_host':{'In1.Cu':refs['F.Cu'].intersects(ann),'In4.Cu':refs['B.Cu'].intersects(ann)},
               'annulus_provenance':'current198b native' if uid in original_vias else 'new ordinary via; native annuli OPEN'}
        returns.append(rows_)
    result['return_stitch_checks']=returns
    if not errors and all(all(r['source_connected_plane_contacts_host'].values()) for r in returns):
        # Three owned routes: request launch, request middle and enable launch/
        # middle. Exact coordinates delimit the mandatory splice sites.
        pairs=[(REQ,'F.Cu',[294.65,101.45],[297.9,104.15]),(REQ,'In3.Cu',[297.9,104.15],[298.55,107.95]),
               (EN,'F.Cu',[297.328,107.525],[298.8,106.35]),(EN,'In3.Cu',[298.8,106.35],[302.25,103.95])]
        for net,layer,a,b in pairs:
            window=LineString([a,b]).envelope.buffer(8,cap_style=3).envelope
            free,_=model.free({'net':net,'domain':model.domains[net]},layer,window)
            # Near the actual signal transition, its necessary antipad is
            # excluded from centerline coverage and supported by local return.
            own_holes=unary_union([Point(p).buffer(.475,resolution=128) for p in (a,b) if p in signals])
            strict=free.intersection(refs[layer].union(own_holes));fake={'uuid':'exact owned splice','kind':'track'}
            seeds=[[(tuple(p),fake)] if strict.covers(Point(p)) else [] for p in (a,b)]
            path,search=S.astar(strict,*seeds,time.monotonic()+12,node_cap=150000) if all(seeds) else (None,{'reason':'No exact source-covered splice seed'})
            result['searches'].append({'net':net,'layer':layer,'from_mm':a,'to_mm':b,'seed_counts':[len(z) for z in seeds],**search})
            if not path:break
            path.update(net=net,layer=layer,width_mm=.2,length_mm=LineString(path['points_mm']).length,new_items=[])
            for a1,b1 in zip(path['points_mm'],path['points_mm'][1:]):u,ch=P.serial_segment(net,layer,a1,b1,.2);chunks[u]=ch;added.add(u);path['new_items'].append(u)
            result['paths'].append(path);g=P.geometry(chunks,template);model=S.Model(g,reserve,exempt)
    losses=[];contact_losses=[];boundary=[]
    for net in (REQ,EN):
        uf,gs=P.physical(model,net,masks)
        for label,reln in (('current198b',native_parts[net]),('r06',old_parts[net])):
            for rel in reln:
                if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'relationship':rel})
        for gr in old_groups[net]:
            keys=sorted({r['key'] for r in gr['records'] if r['uuid'] not in blocker})
            if len({uf.find(k) for k in keys})>1:contact_losses.append({'net':net,'surviving_keys':[list(k) for k in keys]})
        for r in base.own[net]:
            if r['uuid'] not in blocker:continue
            for b in base.own[net]:
                if b['uuid'] in blocker or b['layer']!=r['layer']:continue
                if b['kind']=='via' and b['layer'] not in masks[b['uuid']]:continue
                if r['shape'].distance(b['shape'])<=.000002:boundary.append({'removed_uuid':r['uuid'],'surviving_key':list(b['key']),'layer':r['layer']})
    result.update(pad_relationship_failures=losses,surviving_contact_losses=contact_losses,removed_to_surviving_contacts=boundary)
    emitted=None
    if not losses and not contact_losses and len(result['paths'])==4:
        parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restore};errors,rows,anti=A.clearance(model,parsed,added,restore)
        result.update(final_clearance_errors=errors,final_changed_item_clearance=rows,prospective_antipads=anti)
        if not errors:
            cand=now[0]+b''.join(ch for ch in now[1] if C.pcbtext.chunk_uuid(ch) not in blocker)+b''.join(ch for u,ch in chunks.items() if u not in now[4])+now[2]
            inv=C.inventory(cand)
            if now[5]!=inv[5] or any(inv[3].get(u)!=ch for u,ch in now[3].items() if u not in blocker):raise ValueError('Unauthorized source modification')
            emitted=HERE/'xf-coupled-transition-r1-host-only.kicad_pcb';emitted.write_bytes(cand);result['candidate_sha256']=C.sha(cand)
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen read changed '+p)
    output={'schema':'xf-coupled-ordinary-transitions-r1','verdict':'HOST_CANDIDATE_NATIVE_ELECTRICAL_OPEN' if emitted else 'EXACT_COUPLED_TRANSITION_RECONSTRUCTION_INCOMPLETE',
            'source_sha256':A.SOURCE_SHA,'native_pad_fill_proof':proof,'current_native_partition_checks':checks,'result':result,
            'candidate':str(emitted) if emitted else None,'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'seconds':time.time()-start,
            'limits':['Fixed concrete geometric transition/return sites; .2mm routes,8mmwindows/.1grid/12s/150000nodes','All new vias are.6/.3 ordinary source types, actual native annuli remain OPEN','Source-connected LOGIC_GND on both fresh planes after all prospective signal antipads and actual existing masks; native whole-GND no-loss mandatory','Native full DRC/dual allnet no-loss, source reference/current/timing/return and all physical/manufacturing gates remain open']}
    out.write_text(json.dumps(output,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':output['verdict'],'candidate':str(emitted) if emitted else None,'initial_via_errors':len(result['initial_clearance_errors']),'receipt':str(out)}),flush=True)
if __name__=='__main__':main()
