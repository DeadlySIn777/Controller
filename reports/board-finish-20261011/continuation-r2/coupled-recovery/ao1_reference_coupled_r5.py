"""Targeted AO1 full-body referenced coupled signal constructor, host only."""
import collections,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_positive_operation_r2 as Q
import incremental_exact_model as I
import ao1_astar_exact_r1 as E
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
A,P,G,S,C,F,N=Q.A,Q.P,Q.G,Q.S,Q.C,Q.F,Q.N
VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM
OUT=HERE/'ao1-reference-coupled-r5.json'
WINDOW=box(369.5,125,379,133);GUARD=.025;HALF=.1

def free(model,net,layer):
    domain=model.domains[net];obstacles=[]
    for i in model.trees[layer].query(WINDOW.buffer(1),predicate='intersects'):
        r=model.records[layer][int(i)]
        if r.get('net')==net:continue
        if r['kind']=='fill' and r.get('net')==COM and r.get('domain')==domain:continue
        required=.25 if r['kind']=='hole' else .15 if r.get('domain')==domain else .6
        obstacles.append(r['shape'].buffer(required+HALF+GUARD))
    for h in model.hard[layer]:
        if net not in h['exempt'] and h['shape'].intersects(WINDOW.buffer(1)):obstacles.append(h['shape'].buffer(HALF+GUARD))
    return WINDOW.intersection(model.outline.buffer(-.5-HALF-GUARD)).difference(unary_union(obstacles))

def via_legal(model,net,at,smdtree,centres,selected=()):
    p=Point(at);body=p.buffer(.25,resolution=128);hole=p.buffer(.1,resolution=128);domain=model.domains[net]
    nearest=int(smdtree.nearest(p));smdgap=p.distance(smdtree.geometries[nearest])-.1-.005
    if smdgap<.275 or len(centres.query(p.buffer(.81-1e-9),predicate='intersects')):return False
    if any(math.dist(at,q)<.81-1e-9 for q in selected):return False
    if not model.outline.buffer(-.5-.025).covers(body):return False
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(body.buffer(.675),predicate='intersects'):
            r=model.records[layer][int(i)]
            if r['kind']=='hole':distance=hole.distance(r['shape']);required=.275
            elif r.get('net')==net:continue
            elif r['kind']=='fill' and r.get('net')==COM and r.get('domain')==domain:continue
            else:distance=body.distance(r['shape']);required=.175 if r.get('domain')==domain else .625
            if distance<required-1e-9:return False
        for h in model.hard[layer]:
            if net not in h['exempt'] and body.buffer(.025).intersects(h['shape']):return False
    return True

def containing(shape,point):return unary_union([p for p in P.K.D.components(shape) if p.covers(Point(point))])
def body_refs(refs,positions,gaps,model):
    result={}
    for layer,plane in (('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')):
        maximum=max([.15]+[gaps[r['uuid']] for r in model.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].intersects(WINDOW)])
        voids=unary_union([Point(at).buffer(.25+maximum+.025,resolution=128) for at in positions])
        result[layer]=refs[layer].difference(voids)
    return result

def path_shape(free_shape,refs,layer,own,model,gaps):
    plane='In1.Cu' if layer=='F.Cu' else 'In4.Cu'
    maximum=max([.15]+[gaps[r['uuid']] for r in model.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].intersects(WINDOW)])
    # Only the current path's own signal transition void is excepted. Other
    # signal barrels, old stale-fill voids and return drills remain obstacles.
    own_void=Point(own).buffer(.25+maximum+.025,resolution=128)
    return free_shape.intersection(refs[layer].union(own_void).buffer(-HALF-.010))

def proof_contacts(base,candidate,source_masks,masks,removed,parts,prior):
    failures,checks,_,groups=A.relationships(base,source_masks,parts,(VREF,SDI))
    if failures or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Exact native source signal partitions differ')
    losses=[];contacts=[];ledger=[]
    for net in (VREF,SDI):
        uf,after=P.physical(candidate,net,masks)
        for label,rels in (('current198b',parts[net]),('originalr06',prior[net])):
            for rel in rels:
                if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'pads':rel})
        for group in groups[net]:
            keys=sorted({r['key'] for r in group['records'] if r['uuid'] not in removed});count=len({uf.find(k) for k in keys})
            row={'net':net,'surviving_keys':[list(k) for k in keys],'candidate_component_count':count};ledger.append(row)
            if count>1:contacts.append(row)
    return losses,contacts,ledger,checks

def main():
    if OUT.exists():raise ValueError('Fresh bounded reference-aware constructor required')
    started=time.monotonic();recipe=json.loads(A.read(HERE.parent/'ao1-vref-sdi-components-r3/receipt.json'))
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Native source differs')
    policies={S.norm(n):p for n,p in json.loads(A.read(S.CONTROLLED))['nets'].items()}
    if policies[SDI]['class']!='NONE':raise ValueError('Exact ordinary SDI policy differs')
    removed=set(recipe['deletes']);withdrawn=set(recipe['restores'])
    lost=json.loads(A.read(HERE/'conflict-graph.json'))['lost_route_rows']
    relation=next(r for r in lost if r['net']==VREF)['native_lost_relationships'][0]['r06_pad_relationship']
    if set(relation)!={'C14643.1#0','U14626.9#0'}:raise ValueError('Exact native lost VREF relation differs')
    chunks={u:ch for u,ch in now[4].items() if u not in removed}
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,padproof=A.fresh_template(old,now,template,native)
    smasks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    reserve,exempt=A.reservations();print('AO1_REFERENCED_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],smasks)
    print('AO1_REFERENCED_OWNED_MODEL',flush=True)
    initial=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],smasks)
    refs,witness,uf,ground=Q.rooted_reference(initial,smasks,identity.raw(COM));gaps=Q.zone_gaps(now)
    smd=STRtree([r['shape'] for rs in initial.records.values() for r in rs if r['kind']=='pad' and initial.pads[r['pad_id']]['smd']]);centres=STRtree([Point(v['x'],v['y']) for v in initial.g['vias']])
    vstart=(initial.pads['U14626.9#0']['x'],initial.pads['U14626.9#0']['y']);vend=(initial.pads['C14643.1#0']['x'],initial.pads['C14643.1#0']['y']);sstart=(initial.pads['U14626.8#0']['x'],initial.pads['U14626.8#0']['y'])
    for pid,net in (('U14626.9#0',VREF),('C14643.1#0',VREF),('U14626.8#0',SDI)):
        if initial.pads[pid]['net']!=identity.raw(net):raise ValueError('Exact actual target pad net differs '+pid)
    physical_free={(net,layer):free(initial,net,layer) for net,layers in ((VREF,('F.Cu','B.Cu')),(SDI,('F.Cu','In3.Cu'))) for layer in layers}
    strict={(net,layer):shape.intersection(refs[layer].buffer(-.11)) for (net,layer),shape in physical_free.items()}
    _,vgroups=P.physical(initial,VREF,smasks)
    vtarget=next(g for g in vgroups if 'C14643.1#0' in g['pad_ids'])
    vtarget_records=S.seed_sites(vtarget,'B.Cu',physical_free[VREF,'B.Cu'],WINDOW)
    vtargets=[p for p,r in vtarget_records]
    vfront=containing(physical_free[VREF,'F.Cu'],vstart)
    vback=unary_union([p for p in P.K.D.components(physical_free[VREF,'B.Cu']) if any(p.covers(Point(q)) for q in vtargets)])
    vspace=vfront.intersection(vback)
    sfront=containing(physical_free[SDI,'F.Cu'],sstart)
    _,sgroups=P.physical(initial,SDI,smasks);target=next(g for g in sgroups if 'U14623.14#0' in g['pad_ids'])
    target_records=S.seed_sites(target,'In3.Cu',physical_free[SDI,'In3.Cu'],WINDOW)
    target_seeds=[p for p,r in target_records]
    starget=unary_union([p for p in P.K.D.components(physical_free[SDI,'In3.Cu']) if any(p.covers(Point(q)) for q in target_seeds)])
    sspace=sfront.intersection(starget)
    print('AO1_REFERENCED_COMPONENTS',flush=True)
    vsite=[]
    for i in range(75):
        for j in range(65):
            at=(round(370.5+i*.1,9),round(125.5+j*.1,9))
            if vspace.covers(Point(at)) and via_legal(initial,VREF,at,smd,centres):vsite.append(at)
    old_sites=json.loads(A.read(HERE.parent/'ao1-vref-sdi-components-r3/site-screen.json'))['sites_mm']
    ssites=[tuple(at) for at in old_sites if sspace.covers(Point(at)) and via_legal(initial,SDI,at,smd,centres)]
    vsite.sort(key=lambda p:(math.dist(p,vstart),p));ssites.sort(key=lambda p:(math.dist(p,sstart),p))
    diagnostic={'vref_start_mm':vstart,'vref_back_remote_pad_mm':vend,'vref_actual_retained_B_target_seeds':vtargets,'sdi_start_mm':sstart,'vref_front_component_mm2':vfront.area,'vref_back_component_mm2':vback.area,'vref_common_component_mm2':vspace.area,'vref_legal_sites':vsite,'sdi_front_component_mm2':sfront.area,'sdi_target_components_mm2':starget.area,'sdi_common_component_mm2':sspace.area,'sdi_legal_sites_from_saved162':ssites,'sdi_actual_target_seeds':target_seeds,'initial_rooted_reference_witness':witness,'source_pad_full_reference_component_areas_mm2':{VREF:containing(strict[VREF,'F.Cu'],vstart).area,SDI:containing(strict[SDI,'F.Cu'],sstart).area}}
    diagnostic['actual_initial_full_reference_F_components']={}
    for net,start in ((VREF,vstart),(SDI,sstart)):
        comp=containing(strict[net,'F.Cu'],start)
        path=HERE/('ao1-r5-initial-'+net.rsplit('/',1)[-1]+'.wkb');path.write_bytes(comp.wkb)
        diagnostic['actual_initial_full_reference_F_components'][net]={'area_mm2':comp.area,'bounds_mm':list(comp.bounds),'WKB_path':str(path.resolve()),'WKB_sha256':C.sha(comp.wkb)}
    attempts=[];success=None;S.STEP=.025
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    for vat in vsite[:12]:
        for sat in ssites[:12]:
            if math.dist(vat,sat)<.81:continue
            new={};signals={}
            for net,at in ((VREF,vat),(SDI,sat)):
                u,ch=Q.serial_via(identity,net,at);new[u]=ch;signals[net]=(u,at)
            temp=I.append(initial,new,identity);parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};masks=dict(smasks);masks.update({u:set(template['copper_layers']) for u in new})
            # Fast conservative reference subtraction nominates paths only.
            # Final serialized rebuild below reruns every fill-contact ledger
            # and the complete all-layer functional-source rooted graph.
            case_refs=body_refs(refs,[vat,sat],gaps,initial)
            attempt={'VREF_via_mm':vat,'SDI_via_mm':sat,'paths':[],'failures':[]};attempts.append(attempt)
            # Nominate conservative full-disk source-connected ordinary returns.
            returns=[];all_positions=[vat,sat]
            for net,at in ((VREF,vat),(SDI,sat)):
                chosen=None
                for radius in (.9,.95,1.):
                    for angle in range(64):
                        ret=tuple(round(v,9) for v in (at[0]+radius*math.cos(2*math.pi*angle/64),at[1]+radius*math.sin(2*math.pi*angle/64)))
                        disk=Point(ret).buffer(.275,resolution=128)
                        if not all(case_refs[layer].covers(disk) for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
                        chosen=ret;break
                    if chosen:break
                if chosen is None:attempt['failures'].append({'kind':'No finite all6/SMD/full-rooted-annulus return','net':net});break
                returns.append({'net':net,'signal_at_mm':at,'at_mm':chosen});all_positions.append(chosen);u,ch=Q.serial_via(identity,COM,chosen);new[u]=ch
            if attempt['failures']:continue
            temp=I.append(initial,new,identity);parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};masks.update({u:set(template['copper_layers']) for u in new})
            return_holes=unary_union([Point(r['at_mm']).buffer(.1,resolution=128) for r in returns])
            case_refs={layer:shape.difference(return_holes) for layer,shape in case_refs.items()}
            jobs=[(VREF,'F.Cu',[vstart],[vat]),(VREF,'B.Cu',[vat],vtargets),(SDI,'F.Cu',[sstart],[sat]),(SDI,'In3.Cu',[sat],target_seeds)]
            for net,layer,starts,goals in jobs:
                free_now=free(temp,net,layer);shape=path_shape(free_now,case_refs,layer,signals[net][1],temp,gaps)
                starts=[p for p in starts if shape.covers(Point(p))];goals=[p for p in goals if shape.covers(Point(p))]
                pieces=P.K.D.components(shape)
                shared=[p for p in pieces if any(p.covers(Point(a)) for a in starts) and any(p.covers(Point(b)) for b in goals)]
                if not shared:
                    source_parts=[p for p in pieces if any(p.covers(Point(a)) for a in starts)]
                    attempt['failures'].append({'net':net,'layer':layer,'reason':'Exact continuous own-transition/reference/free components disconnected','source_component_areas_mm2':[p.area for p in source_parts],'source_component_bounds_mm':[list(p.bounds) for p in source_parts],'own_transition_mm':signals[net][1]})
                    break
                shape=unary_union(shared)

                start_rows=[(p,{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['U14626.9#0' if net==VREF else 'U14626.8#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'}) for p in starts]
                goal_rows=[(p,next((r for q,r in target_records+vtarget_records if q==p),{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['C14643.1#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'})) for p in goals]
                path,search=E.astar(shape,start_rows,goal_rows,time.monotonic()+5,node_cap=50000) if starts and goals else (None,{'reason':'Full-body referenced endpoint absent','nodes':0})
                if not path:attempt['failures'].append({'net':net,'layer':layer,**search});break
                row=dict(path,net=net,layer=layer,width_mm=.2,search=search);attempt['paths'].append(row);items={}
                for a,b in zip(row['points_mm'],row['points_mm'][1:]):u,ch=identity.serial_segment(net,layer,a,b,.2);items[u]=ch
                new.update(items);temp=I.append(temp,items,identity)
            if attempt['failures']:continue
            finalchunks=dict(chunks);finalchunks.update(new);print('AO1_REFERENCED_FINAL_REBUILD',flush=True)
            final=F.Model(identity.geometry(finalchunks,template),reserve,exempt,native['vias'],smasks)
            parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};final,fillledger,fillerrors=Q.prospective_fill(base,final,masks,now,parsed,set(parsed));frefs,fwitness,_,_=Q.rooted_reference(final,masks,identity.raw(COM))
            errors,clear,anti=A.clearance(final,parsed,set(parsed),set());losses,contacts,ledger,checks=proof_contacts(base,final,smasks,masks,removed,parts,prior)
            ref_errors=[]
            for u,z in parsed.items():
                if z['kind']!='segment':continue
                plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';maximum=max([.15]+[gaps[r['uuid']] for r in initial.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].intersects(WINDOW)])
                own=Point(signals[z['net']][1]).buffer(.25+maximum+.025,resolution=128);gap=A.shape(z).difference(own).difference(frefs[z['layer']]).area
                if gap>1e-9:ref_errors.append({'uuid':u,'net':z['net'],'layer':z['layer'],'full_copper_uncovered_mm2':gap})
            attempt.update(clearance_errors=errors,pad_losses=losses,surviving_contact_losses=contacts,fill_errors=fillerrors,reference_errors=ref_errors,returns=returns)
            if errors or losses or contacts or fillerrors or ref_errors:continue
            success={'new_chunks':{u:ch.decode() for u,ch in new.items()},'all_surviving_contact_obligations':ledger,'native_source_partition_checks':checks,'reference_witness':fwitness,'prospective_fill_contact_ledger':fillledger,'clearance_rows':clear,'new_antipads':anti,'selected_attempt_index':len(attempts)-1};break
        if success:break
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    report={'verdict':'POSITIVE_HOST_REFERENCE_AWARE_OPERATION_INDEPENDENT_NATIVE_ANALOG_OPEN' if success else 'FINITE_REFERENCE_AWARE_OPERATION_INCOMPLETE','source_sha256':C.sha(raw),'native_template_proof':padproof,'removed_owned_items':sorted(removed),'owned_r06_withdrawables_replaced':sorted(withdrawn),'exact_removed_chunks':{u:now[4][u].decode() for u in removed},'exact_new_chunks':success['new_chunks'] if success else {},'component_diagnostic':diagnostic,'exact_original_recovered_relation':relation,'attempts':attempts,'success':success,'nominal_requirements':{'VREF':'Analog DC reference loop; preserve actual source, loading, decoupling, quiet-return and noise obligations. No speed/plane waiver.','SDI':'Historical frozen ordinary NONE class; actual ISO7761→AD5683R 32MHz sampled bus with 1ns driver edge requires actual timing/settling/noise/return qualification. No qualification inferred from old length estimates.'},'SCLK_all_source_geometry_exact':True,'no_neighbor_signal_void_exemption':True,'no_removed_source_antipad_fill_credit':True,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen helper/source changed '+p)
    OUT.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(OUT),'verdict':report['verdict'],'VREF_sites':len(vsite),'SDI_sites':len(ssites),'attempts':len(attempts),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
