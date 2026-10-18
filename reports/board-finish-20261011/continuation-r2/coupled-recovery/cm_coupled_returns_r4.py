"""Concrete CM outer controlled bulk, exact connector neck and ordinary MOSI dive.

Frozen host-only source geometry. Original rules remain unchanged; a scoped
terminal profile is a separate reviewable proposal, not installed authority.
"""
import itertools,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
import xf_continuous_landings_r3 as X
import incremental_exact_model as I
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree
CLK='/motherboard_compute/CM_CAN_SPI_SCLK'
MOSI='/motherboard_compute/CM_CAN_SPI_MOSI'
GND='/LOGIC_GND'

def references(model,masks,signals):
    ref={};witness={}
    hole_shapes=[Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128) for v in model.g['vias']]+[shape for pad in model.g['pads'] for shape in S.poly(pad.get('hole') or [])]
    holes=unary_union(hole_shapes);hole_tree=STRtree(hole_shapes)
    cut=unary_union([Point(p).buffer(d/2+.15+.025,resolution=128) for p,d in signals])
    for signal,plane in (('F.Cu','In1.Cu'),('B.Cu','In4.Cu')):
        fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']==GND]).difference(holes).difference(cut)
        own=[];filled=prep(fill);via_by_uuid={v['uuid']:v for v in model.g['vias']}
        for r in model.records[plane]:
            if r['net']!=GND or r['kind'] not in ('pad','track','via'):continue
            if r['kind']=='via':
                if plane not in masks.get(r['uuid'],set()):continue
            nearby=unary_union([hole_shapes[i] for i in hole_tree.query(r['shape'],predicate='intersects')])
            metal=r['shape'].difference(nearby)
            if not filled.covers(metal):own.append(metal.difference(fill))
        entire=unary_union([fill]+own)
        anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane])).difference(holes)
        connected=unary_union([p for p in P.K.D.components(entire) if p.intersects(anchor)])
        ref[signal]=fill.intersection(connected)
        witness[plane]={'source_pad':'J11001.2#0','source_connected_fill_area_mm2':ref[signal].area,'prospective_signal_antipads':signals,'actual_source_new_via_pad_drills_subtracted':True}
    ref['In3.Cu']=ref['B.Cu']
    return ref,witness

def main():
    out=HERE/'cm-coupled-returns-r4.json';start=time.time()
    if out.exists():raise ValueError('Fresh receipt required')
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    recipe=json.loads(A.read(HERE/'cm-controlled-initial-r2.json'))
    if recipe['source_sha256']!=A.SOURCE_SHA or recipe['initial_clearance_errors']:raise ValueError('Initial clock recipe differs')
    deletes=set(recipe['deleted_owned_clock_and_MOSI_items']);restores=set(recipe['restored_original_vias'])
    initial={u:ch for u,ch in now[4].items() if u not in deletes};initial.update({u:old[4][u] for u in restores})
    initial.update({r['uuid']:r['chunk'].encode() for r in recipe['added_serialized_chunks']})
    clock_added={r['uuid'] for r in recipe['added_serialized_chunks']}
    masks=dict(source_masks)
    original_vias={v['uuid']:v for v in template['vias']}
    restore_attest=[]
    for u in sorted(restores):
        v=original_vias[u];flags=[line.strip() for line in old[4][u].decode().splitlines() if 'unused' in line or 'remove' in line or 'tent' in line]
        if flags or set(v['flashed'])!=set(template['copper_layers']):raise ValueError('Restored source annulus/suppression differs')
        masks[u]=set(template['copper_layers']);restore_attest.append({'uuid':u,'exact_chunk_sha256':C.sha(old[4][u]),'original_actual_flash_layers':v['flashed'],'suppression_flag_lines':flags,'candidate_policy':'Exact unchanged source chunk; conservative all6 copper, final native annuli mandatory'})
    reserve,exempt=A.reservations();print('CM_RETURNS_BASE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    model=F.Model(identity.geometry(initial,template),reserve,exempt,native['vias'],source_masks)
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    oldparts={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    policy=json.loads(A.read(S.CONTROLLED))['nets'];mosi_policy=next(value for key,value in policy.items() if S.norm(key)==MOSI)
    if mosi_policy.get('class')!='NONE':raise ValueError('This exact ordinary In3 recipe requires the frozen MOSI NONE assignment')
    failures,checks,_,basegroups=A.relationships(base,source_masks,parts,(CLK,MOSI))
    if failures or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Actual source pad partitions differ')
    fixed=[{'net':CLK,'at_mm':[original_vias[u]['x'],original_vias[u]['y']],'d_mm':original_vias[u]['d'],'uuid':u} for u in sorted(restores)]
    existing=next(v for v in model.g['vias'] if v['net']==MOSI and (v['x'],v['y'])==(129.25,164.95))
    old_mosi_same_layer={'net':MOSI,'at_mm':[existing['x'],existing['y']],'d_mm':existing['d'],'uuid':existing['uuid'],'role':'Unchanged actual In3 same-layer splice, no new signal-layer transition here'}
    signal_cuts=[(v['at_mm'],v['d_mm']) for v in fixed]
    refs,witness=references(model,masks,signal_cuts);both=refs['F.Cu'].intersection(refs['B.Cu'])
    clock_reference=[]
    for u in sorted(clock_added):
        r=G.parse(u,initial[u],{});body=LineString([r['a'],r['b']]).buffer(r['w']/2,resolution=128)
        unref=unary_union([Point(v['at_mm']).buffer(v['d_mm']/2+.175,resolution=128) for v in fixed if v['net']==CLK])
        clock_reference.append({'uuid':u,'layer':r['layer'],'w_mm':r['w'],'full_copper_uncovered_mm2':body.difference(unref).difference(refs[r['layer']]).area})
    return_sites=[]
    for v in fixed:
        window=Point(v['at_mm']).buffer(1.01,resolution=128).envelope
        region,_=X.freevia(model,GND,window)
        ring=Point(v['at_mm']).buffer(1.,resolution=128).difference(Point(v['at_mm']).buffer(.8+S.MARGIN,resolution=128))
        candidates=X.sites(region.intersection(both).intersection(ring),v['at_mm'],8)
        return_sites.append({'signal':v,'ordinary_return_sites':candidates})
    terminal_window=box(124,162,133,169)
    free_signal,_=X.freevia(model,MOSI,terminal_window);free_return,_=X.freevia(model,GND,terminal_window)
    free_signal=free_signal.intersection(both);free_return=free_return.intersection(both)
    terminal_point=Point(127.852,166.225)
    local_f_free,_=model.free({'net':MOSI,'domain':model.domains[MOSI]},'F.Cu',terminal_window.buffer(10).envelope)
    local_f_legal=local_f_free.intersection(refs['F.Cu'].buffer(-.1))
    terminal_component=unary_union([part for part in P.K.D.components(local_f_legal) if part.covers(terminal_point)])
    free_signal=free_signal.intersection(terminal_component)
    _,mosi_groups=P.physical(model,MOSI,masks)
    target_group=next(group for group in mosi_groups if {'R15071.1#0','U15036.2#0'}<=set(group['pad_ids']))
    target_window=terminal_window.buffer(14).envelope
    inner_free,_=model.free({'net':MOSI,'domain':model.domains[MOSI]},'In3.Cu',target_window)
    inner_legal=inner_free.intersection(refs['In3.Cu'].buffer(-.1))
    target_seeds=S.seed_sites(target_group,'In3.Cu',inner_legal,target_window)
    inner_components=[part for part in P.K.D.components(inner_legal) if any(part.covers(Point(p)) for p,_ in target_seeds)]
    target_component=unary_union(inner_components)
    free_signal=free_signal.intersection(target_component)
    from shapely.affinity import translate
    paired=[]
    for distance in (.85,.9,.975):
        for angle in range(16):
            dx,dy=distance*math.cos(angle*math.pi/8),distance*math.sin(angle*math.pi/8)
            region=free_signal.intersection(translate(free_return,-dx,-dy))
            for site in X.sites(region,[127.852,166.225],8):
                paired.append(dict(site,return_at_mm=[round(site['at_mm'][0]+dx,6),round(site['at_mm'][1]+dy,6)]))
    paired.sort(key=lambda r:r['cost_mm']);paired=paired[:64]
    print('CM_RETURN_SITES',[len(r['ordinary_return_sites']) for r in return_sites],'MOSI_PAIRS',len(paired),flush=True)
    attempts=[];emitted=None
    if all(r['ordinary_return_sites'] for r in return_sites) and max(z['full_copper_uncovered_mm2'] for z in clock_reference)<1e-9:
        fixedchoice=[r['ordinary_return_sites'][0]['at_mm'] for r in return_sites]
        for idx,pair in enumerate(paired[:12]):
            print('CM_MOSI_PAIR',idx,flush=True);chunks=dict(initial);cmasks=dict(masks);added=set(clock_added)
            specs=[(GND,p) for p in fixedchoice]+[(MOSI,pair['at_mm']),(GND,pair['return_at_mm'])]
            all_new_positions=[p for _,p in specs]
            if any(math.dist(a,b)<.8+S.MARGIN for a,b in itertools.combinations(all_new_positions,2)):continue
            for net,p in specs:
                u,ch=X.serial_via(identity.raw(net),p);chunks[u]=ch;added.add(u);cmasks[u]=set(template['copper_layers'])
            candidate=I.append(model,{u:ch for u,ch in chunks.items() if u not in initial},identity)
            parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restores}
            errors,clear,anti=A.clearance(candidate,parsed,added,restores)
            attempt={'mosi_pair':pair,'fixed_returns_mm':fixedchoice,'initial_clearance_errors':errors,'paths':[]};attempts.append(attempt)
            if errors:continue
            cuts=signal_cuts+[(pair['at_mm'],.5)];r,w=references(candidate,cmasks,cuts);attempt['reference_witness']=w
            clock_checks=[]
            clock_unref=unary_union([Point(v['at_mm']).buffer(v['d_mm']/2+.175,resolution=128) for v in fixed if v['net']==CLK])
            for clock_uuid in sorted(clock_added):
                cr=G.parse(clock_uuid,chunks[clock_uuid],{});cb=LineString([cr['a'],cr['b']]).buffer(cr['w']/2,resolution=128)
                clock_checks.append({'uuid':clock_uuid,'layer':cr['layer'],'full_copper_uncovered_mm2':cb.difference(clock_unref).difference(r[cr['layer']]).area})
            attempt['all_clock_reference_after_candidate_antipads']=clock_checks
            if any(z['full_copper_uncovered_mm2']>1e-9 for z in clock_checks):continue
            returns=[]
            for signal,ret in list(zip(fixed,fixedchoice))+[({'at_mm':pair['at_mm']},pair['return_at_mm'])]:
                ann=Point(ret).buffer(.25,resolution=128).difference(Point(ret).buffer(.1,resolution=128))
                returns.append({'signal_mm':signal['at_mm'],'return_mm':ret,'distance_mm':math.dist(signal['at_mm'],ret),'contacts':{layer:r[layer].intersects(ann) for layer in ('F.Cu','B.Cu')}})
            attempt['return_checks']=returns
            if not all(all(z['contacts'].values()) for z in returns):continue
            for layer,a,b in [('F.Cu',[127.852,166.225],pair['at_mm']),('In3.Cu',pair['at_mm'],[129.25,164.95])]:
                window=LineString([a,b]).envelope.buffer(10).envelope;free,_=candidate.free({'net':MOSI,'domain':candidate.domains[MOSI]},layer,window)
                unref=unary_union([Point(p).buffer(d/2+.175,resolution=128) for p,d in cuts if p in (a,b)])
                if layer=='In3.Cu':unref=unref.union(Point(old_mosi_same_layer['at_mm']).buffer(old_mosi_same_layer['d_mm']/2+.175,resolution=128))
                strict=free.intersection(r[layer].union(unref).buffer(-.1));fake={'uuid':'exact owned MOSI splice','kind':'track'}
                seeds=[[(tuple(p),fake)] if strict.covers(Point(p)) else [] for p in (a,b)]
                if layer=='In3.Cu':
                    seeds[1]=S.seed_sites(target_group,layer,strict,window)
                path,search=S.astar(strict,*seeds,time.monotonic()+15,node_cap=150000) if all(seeds) else (None,{'reason':'No full-body reference covered exact splice'})
                attempt.setdefault('searches',[]).append({'layer':layer,'from_mm':a,'to_mm':b,'actual_source_target_seed_count':len(seeds[1]),**search})
                if not path:break
                body=LineString(path['points_mm']).buffer(.1,resolution=128);miss=body.difference(unref).difference(r[layer]).area
                if miss>1e-9:attempt['searches'][-1]['uncovered_mm2']=miss;break
                path.update(net=MOSI,layer=layer,width_mm=.2,length_mm=LineString(path['points_mm']).length,new_items=[])
                for a1,b1 in zip(path['points_mm'],path['points_mm'][1:]):
                    u,ch=identity.serial_segment(MOSI,layer,a1,b1,.2);chunks[u]=ch;added.add(u);path['new_items'].append(u)
                attempt['paths'].append(path)
            if len(attempt['paths'])!=2:continue
            candidate=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],source_masks)
            losses=[];contact_losses=[];obligations=[];boundary=[]
            for net in (CLK,MOSI):
                uf,groups=P.physical(candidate,net,cmasks)
                for label,rels in (('current198b',parts[net]),('r06',oldparts[net])):
                    for rel in rels:
                        if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'pads':rel})
                for gr in basegroups[net]:
                    keys=sorted({z['key'] for z in gr['records'] if z['uuid'] not in deletes});count=len({uf.find(k) for k in keys})
                    row={'net':net,'surviving_keys':[list(k) for k in keys],'component_count':count};obligations.append(row)
                    if count>1:contact_losses.append(row)
                for z in base.own[net]:
                    if z['uuid'] not in deletes:continue
                    for b in base.own[net]:
                        if b['uuid'] in deletes or b['layer']!=z['layer']:continue
                        if b['kind']=='via' and b['layer'] not in source_masks[b['uuid']]:continue
                        if z['shape'].distance(b['shape'])<=.000002:boundary.append({'deleted_uuid':z['uuid'],'surviving_key':list(b['key']),'layer':z['layer']})
            attempt.update(pad_losses=losses,contact_losses=contact_losses,surviving_contact_obligations=obligations,deleted_surviving_boundary=boundary)
            parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restores};errors,clear,anti=A.clearance(candidate,parsed,added,restores)
            attempt.update(final_clearance_errors=errors,changed_item_clearance=clear,prospective_antipads=anti)
            if losses or contact_losses or errors:continue
            cand=now[0]+b''.join(ch for ch in now[1] if C.pcbtext.chunk_uuid(ch) not in deletes)+b''.join(ch for u,ch in chunks.items() if u not in now[4])+now[2]
            inv=C.inventory(cand);identity.assert_no_collisions(cand);identity.assert_chunks(chunks)
            if inv[5]!=now[5] or any(inv[3].get(u)!=ch for u,ch in now[3].items() if u not in deletes):raise ValueError('Unowned source changed')
            emitted=HERE/'cm-coupled-returns-r4-host-only.kicad_pcb';emitted.write_bytes(cand);attempt['candidate_sha256']=C.sha(cand);break
    profile=dict(recipe['scoped_terminal_profile']);profile['terminal_region_polygon_mm']=[[128.142,165.84],[128.362,165.84],[128.362,167.285],[128.142,167.285]]
    result={'schema':'cm-coupled-returns-r1','verdict':'HOST_CANDIDATE_NATIVE_ELECTRICAL_OPEN' if emitted else 'COUPLED_CONTROLLED_CM_RECIPE_INCOMPLETE','source_sha256':A.SOURCE_SHA,'source_annulus_proof':base.source_annulus_proof,'fresh_native_pad_fill_proof':proof,'actual_source_pad_partition_checks':checks,'deleted_owned_items':sorted(deletes),'restored_via_exact_flags_annuli':restore_attest,'clock_full_body_reference_checks':clock_reference,'fixed_transition_return_sites':return_sites,'paired_ordinary_MOSI_sites':paired,'attempts':attempts,'candidate':str(emitted) if emitted else None,'scoped_terminal_profile':profile,'reference_witness':witness,'read_files_sha256':A.READS,'seconds':time.time()-start,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Independent host full-candidate audit; reference bodies rechecked after every candidate signal antipad','Exact new/restored native annuli, candidate refill and ordinary DRC; all-net r06/current native no-loss','Exact isolated terminal-neck profile effective native parse/enforcement; original project remains frozen','Extracted SI/current bus timing/load/neck and actual manufacturing/process qualification']}
    result['schema']='cm-coupled-returns-r4';result['MOSI_F_terminal_reachable_component_area_mm2']=terminal_component.area;result['exact_frozen_MOSI_controlled_policy']=mosi_policy;result['unchanged_MOSI_In3_splice']=old_mosi_same_layer
    result['actual_MOSI_In3_target_current_pad_group']=target_group['pad_ids'];result['actual_target_source_seed_count']=len(target_seeds);result['MOSI_In3_target_connected_region_area_mm2']=target_component.area;result['joint_F_terminal_and_actual_In3_target_ordinary_via_area_mm2']=free_signal.area
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen source/helper input changed '+q)
    out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'receipt':str(out),'candidate':str(emitted) if emitted else None,'reference_errors':sum(r['full_copper_uncovered_mm2']>1e-9 for r in clock_reference),'return_sites':[len(r['ordinary_return_sites']) for r in return_sites]}),flush=True)
if __name__=='__main__':main()
