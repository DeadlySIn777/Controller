"""Targeted AO1 full-body referenced coupled signal constructor, host only."""
import collections,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_positive_operation_r2 as Q
import incremental_exact_model as I
import ao1_astar_exact_r1 as E
import ao1_via_region_r2 as VR
import ao1_continuous_return_r1 as CR
import ao1_scoped_cache_nomination_r2 as SC
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
A,P,G,S,C,F,N=Q.A,Q.P,Q.G,Q.S,Q.C,Q.F,Q.N
VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM
MON='/motherboard_analog_output/AO1_MON_12V'
MON_REMOVED={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'}
OUT=HERE/'ao1-reference-coupled-r13.json'
WINDOW=box(368.8,124.7,379,133);GUARD=.025;HALF=.1

def free(model,net,layer):
    domain=model.domains[net];obstacles=[]
    for i in model.trees[layer].query(WINDOW.buffer(1),predicate='intersects'):
        r=model.records[layer][int(i)]
        if r.get('net')==net:continue
        if r['kind']=='fill' and r.get('domain')==domain:continue
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
            elif r['kind']=='fill' and r.get('domain')==domain:continue
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
        result[layer]=refs[layer].intersection(WINDOW.buffer(1)).difference(voids)
    return result

def path_shape(free_shape,refs,layer,own,model,gaps):
    plane='In1.Cu' if layer=='F.Cu' else 'In4.Cu'
    maximum=max([.15]+[gaps[r['uuid']] for r in model.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].intersects(WINDOW)])
    # Only the current path's own signal transition void is excepted. Other
    # signal barrels, old stale-fill voids and return drills remain obstacles.
    own_void=Point(own).buffer(.25+maximum+.025,resolution=128)
    return free_shape.intersection(refs[layer].union(own_void).buffer(-HALF-.010))

def proof_contacts(base,candidate,source_masks,masks,removed,parts,prior):
    failures,checks,_,groups=A.relationships(base,source_masks,parts,(VREF,SDI,MON))
    if failures or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Exact native source signal partitions differ')
    losses=[];contacts=[];ledger=[]
    for net in (VREF,SDI,MON):
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
    removed=set(recipe['deletes'])|MON_REMOVED;withdrawn=set(recipe['restores'])
    for uid in MON_REMOVED:
        item=G.parse(uid,now[4][uid],{})
        if item['kind']!='segment' or item['net']!=MON or item['layer']!='F.Cu' or item['w']!=.2:raise ValueError('Exact original monitor ownership differs')
    monitor_policy=policies.get(MON)
    if monitor_policy is not None and monitor_policy.get('class')!='NONE':raise ValueError('Monitor has a controlled assignment; separate constructor required')
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
    via_regions={net:VR.legal_centres(initial,net,WINDOW) for net in (VREF,SDI)}
    vsite=[];ssites=[]
    sample={(round(370.5+i*.1,9),round(125.5+j*.1,9)) for i in range(75) for j in range(65)}
    sample.update((round(373.65+i*.025,9),round(128.25+j*.025,9)) for i in range(33) for j in range(37))
    sample.update((round(376.625+i*.025,9),round(127.8+j*.025,9)) for i in range(25) for j in range(57))
    for at in sorted(sample):
        point=Point(at)
        if vspace.covers(point) and via_regions[VREF].covers(point):vsite.append(at)
        if sspace.covers(point) and via_regions[SDI].covers(point):ssites.append(at)
    for net,region in via_regions.items():
        p=HERE/('ao1-r13-legal-centres-'+net.rsplit('/',1)[-1]+'.wkb');p.write_bytes(region.wkb)
    old_sites=json.loads(A.read(HERE.parent/'ao1-vref-sdi-components-r3/site-screen.json'))['sites_mm']
    vsite.sort(key=lambda p:(math.dist(p,(374.,129.1)),p));ssites.sort(key=lambda p:(math.dist(p,(374.8,128.5)),p))
    diagnostic={'vref_start_mm':vstart,'vref_back_remote_pad_mm':vend,'vref_actual_retained_B_target_seeds':vtargets,'sdi_start_mm':sstart,'vref_front_component_mm2':vfront.area,'vref_back_component_mm2':vback.area,'vref_common_component_mm2':vspace.area,'vref_legal_sites':vsite,'sdi_front_component_mm2':sfront.area,'sdi_target_components_mm2':starget.area,'sdi_common_component_mm2':sspace.area,'newly_freed_SDI_sites':ssites,'frozen_old162_site_evidence_count':len(old_sites),'sdi_actual_target_seeds':target_seeds,'initial_rooted_reference_witness':witness,'source_pad_full_reference_component_areas_mm2':{VREF:containing(strict[VREF,'F.Cu'],vstart).area,SDI:containing(strict[SDI,'F.Cu'],sstart).area}}
    diagnostic['actual_initial_full_reference_F_components']={}
    for net,start in ((VREF,vstart),(SDI,sstart)):
        comp=containing(strict[net,'F.Cu'],start)
        path=HERE/('ao1-r13-initial-'+net.rsplit('/',1)[-1]+'.wkb');path.write_bytes(comp.wkb)
        diagnostic['actual_initial_full_reference_F_components'][net]={'area_mm2':comp.area,'bounds_mm':list(comp.bounds),'WKB_path':str(path.resolve()),'WKB_sha256':C.sha(comp.wkb)}
    # Every candidate is first tested for continuous source-to-via and
    # via-to-actual-target reachability with only its own transition void.
    # This avoids a nearest-prefix silently rejecting every pair by pitch.
    frozen=json.loads(A.read(HERE/'ao1-reference-coupled-r9.json'))
    if frozen['source_sha256']!=C.sha(raw) or frozen['native_template_proof']!=padproof:raise ValueError('Frozen single-site nomination source differs')
    single_diagnostics=frozen['component_diagnostic']['reference_aware_site_nomination']
    single={n:[tuple(p) for p in single_diagnostics[n]['individually_continuous_sites']] for n in (VREF,SDI)}
    # Frozen points nominate only; exact final serialized rebuild and all gates
    # remain independent of this preserved earlier bounded reachability receipt.
    pairs=sorted([(vat,sat) for vat in single[VREF] for sat in single[SDI] if math.dist(vat,sat)>=.81-1e-9],key=lambda pair:(math.dist(pair[0],vstart)+math.dist(pair[1],sstart),pair))
    diagnostic['reference_aware_site_nomination']=single_diagnostics
    diagnostic['ordinary_pitch_compatible_individually_reachable_pairs']=len(pairs)
    strict_pairs=[] # Fixed exact promising r12 case; no repeat prefix sweep.
    # A frozen physical diagnostic is useful for resolving an actual removed
    # barrel's stale fill cache. It never receives reference or adoption credit.
    nominations=[((374.0,129.0),(373.4,128.3))]
    physical_pairs=[p for p in nominations if math.dist(*p)>=.81-1e-9 and all(via_regions[n].covers(Point(a)) for n,a in zip((VREF,SDI),p))]
    cases=[(a,b,True) for a,b in strict_pairs]+[(a,b,False) for a,b in physical_pairs]
    diagnostic['physical_diagnostic_pairs_without_reference_credit']=physical_pairs
    return_region=VR.legal_centres(initial,COM,WINDOW)
    provisional_refs,cache_scope=SC.provisional(initial,refs,native,now)
    diagnostic['strictly_exploratory_scoped_withdrawn_SDI_cache_nomination']=cache_scope
    attempts=[];success=None;held=None;S.STEP=.025
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    for vat,sat,enforce_reference in cases:
        for _one_case in (0,):
            new={};signals={}
            for net,at in ((VREF,vat),(SDI,sat)):
                u,ch=Q.serial_via(identity,net,at);new[u]=ch;signals[net]=(u,at)
            temp=I.append(initial,new,identity);parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};masks=dict(smasks);masks.update({u:set(template['copper_layers']) for u in new})
            # Fast conservative reference subtraction nominates paths only.
            # Final serialized rebuild below reruns every fill-contact ledger
            # and the complete all-layer functional-source rooted graph.
            case_refs=body_refs(refs,[vat,sat],gaps,initial)
            attempt={'VREF_via_mm':vat,'SDI_via_mm':sat,'enforce_reference_during_nomination':enforce_reference,'paths':[],'failures':[]};attempts.append(attempt)
            # Nominate finite .15-mm-interior source-rooted annular contact.
            # Exact final drilled graph and native gates still apply.
            returns=[];all_positions=[vat,sat]
            for net,at in ((VREF,vat),(SDI,sat)):
                existing=[]
                for oldvia in initial.g['vias']:
                    if S.norm(oldvia['net'])!=COM or not {'In1.Cu','In4.Cu'}<=smasks.get(oldvia['uuid'],set()):continue
                    oldat=(oldvia['x'],oldvia['y']);distance=math.dist(at,oldat)
                    if not .81-1e-9<=distance<=1.+1e-9:continue
                    oldann=Point(oldat).buffer(oldvia['d']/2,resolution=128).difference(Point(oldat).buffer(oldvia['drill']/2,resolution=128))
                    if all(case_refs[layer].buffer(-.075).intersection(oldann).area>=.004 for layer in ('F.Cu','B.Cu')):existing.append(oldvia)
                existing.sort(key=lambda v:(math.dist(at,(v['x'],v['y'])),v['uuid']))
                reuse=existing[0] if existing else None
                shared=[r['at_mm'] for r in returns if .81-1e-9<=math.dist(at,r['at_mm'])<=1.+1e-9]
                chosen=(reuse['x'],reuse['y']) if reuse else shared[0] if shared else None
                preferred=(373.5,129.15)
                pann=Point(preferred).buffer(.25,resolution=128).difference(Point(preferred).buffer(.1,resolution=128))
                if chosen is None and all(.81-1e-9<=math.dist(preferred,q)<=1.+1e-9 for q in (vat,sat)) and all(case_refs[layer].buffer(-.075).intersection(pann).area>=.004 for layer in ('F.Cu','B.Cu')) and via_legal(temp,COM,preferred,smd,centres,all_positions):chosen=preferred
                if chosen is None:
                    sites,space,physical,areas=CR.candidates(return_region,case_refs,at,all_positions)
                    attempt.setdefault('continuous_return_nomination',[]).append({'net':net,'signal_at_mm':at,'areas_mm2':areas,'candidate_count':len(sites),'exact_space_WKB_sha256':C.sha(space.wkb),'exact_physical_space_WKB_sha256':C.sha(physical.wkb),'space_bounds_mm':list(space.bounds) if not space.is_empty else []})
                    for ret in sites:
                        body=Point(ret).buffer(.25,resolution=128);hole=Point(ret).buffer(.1,resolution=128);ann=body.difference(hole)
                        if not all(case_refs[layer].buffer(-.075).intersection(ann).area>=.004 for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
                        chosen=ret;break
                    if chosen is None:
                        probes=[(at[0],at[1]+.9),(at[0]-.7,at[1]+.65),(at[0]-.7,at[1]-.65),(at[0]+.7,at[1]+.65)]
                        attempt.setdefault('failed_return_exact_blocker_probes',[]).append({'net':net,'signal_at_mm':at,'probes':[{'at_mm':ret,'ordinary_geometry_blockers':CR.site_blockers(temp,COM,ret,smd,centres,all_positions),'source_rooted_plane_annular_interior_mm2':{layer:case_refs[layer].buffer(-.075).intersection(Point(ret).buffer(.25,resolution=128).difference(Point(ret).buffer(.1,resolution=128))).area for layer in ('F.Cu','B.Cu')}} for ret in probes]})
                if chosen is None:attempt['failures'].append({'kind':'No finite all6/SMD/source-rooted .15mm-interior annular return','net':net});break
                row={'net':net,'signal_at_mm':at,'at_mm':chosen,'existing_uuid':reuse['uuid'] if reuse else None,'diameter_mm':reuse['d'] if reuse else .5,'drill_mm':reuse['drill'] if reuse else .2,'actual_existing_flash_layers':sorted(smasks[reuse['uuid']]) if reuse else None}
                returns.append(row)
                if chosen not in all_positions:all_positions.append(chosen)
                if not reuse:u,ch=Q.serial_via(identity,COM,chosen);new[u]=ch
            if attempt['failures']:continue
            temp=I.append(initial,new,identity);parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};masks.update({u:set(template['copper_layers']) for u in new})
            return_holes=unary_union([Point(r['at_mm']).buffer(r['drill_mm']/2,resolution=128) for r in returns])
            case_refs={layer:shape.difference(return_holes) for layer,shape in case_refs.items()}
            nomination_refs=body_refs(provisional_refs,[vat,sat],gaps,initial)
            nomination_refs={layer:shape.difference(return_holes) for layer,shape in nomination_refs.items()}
            jobs=[(VREF,'F.Cu',[vstart],[vat]),(VREF,'B.Cu',[vat],vtargets),(SDI,'F.Cu',[sstart],[sat]),(SDI,'In3.Cu',[sat],target_seeds),(MON,'F.Cu',[(369.35,125.15)],[(374.55,130.049999)])]
            for net,layer,starts,goals in jobs:
                free_now=free(temp,net,layer)
                if net==MON:shape=free_now.intersection(case_refs[layer].buffer(-.11))
                else:shape=path_shape(free_now,case_refs if enforce_reference else nomination_refs,layer,signals[net][1],temp,gaps)
                starts=[p for p in starts if shape.covers(Point(p))];goals=[p for p in goals if shape.covers(Point(p))]
                pieces=P.K.D.components(shape)
                shared=[p for p in pieces if any(p.covers(Point(a)) for a in starts) and any(p.covers(Point(b)) for b in goals)]
                if not shared:
                    source_parts=[p for p in pieces if any(p.covers(Point(a)) for a in starts)]
                    attempt['failures'].append({'net':net,'layer':layer,'reason':'Exact continuous own-transition/reference/free components disconnected','source_component_areas_mm2':[p.area for p in source_parts],'source_component_bounds_mm':[list(p.bounds) for p in source_parts],'own_transition_mm':signals[net][1] if net in signals else None})
                    break
                shape=unary_union(shared)

                if net==MON:
                    start_rows=[(p,{'uuid':'036f4f5d-d8f0-4b5f-bd20-72e5cdeecb36','kind':'track'}) for p in starts]
                    goal_rows=[(p,{'uuid':'6a7a6862-5b3a-4764-bead-1acf9ac7b861','kind':'track'}) for p in goals]
                else:
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
                own=Point(signals[z['net']][1]).buffer(.25+maximum+.025,resolution=128) if z['net'] in signals else Point().buffer(0)
                gap=A.shape(z).difference(own).difference(frefs[z['layer']])
                if gap.area>1e-9:ref_errors.append({'uuid':u,'net':z['net'],'layer':z['layer'],'full_copper_uncovered_mm2':gap.area,'uncovered_bounds_mm':list(gap.bounds),'exact_gap_WKB_sha256':C.sha(gap.wkb)})
            paired=[]
            for ret in returns:
                p=Point(ret['at_mm']);ann=p.buffer(ret['diameter_mm']/2,resolution=128).difference(p.buffer(ret['drill_mm']/2,resolution=128))
                contact={layer:frefs[layer].buffer(-.075).intersection(ann).area for layer in ('F.Cu','B.Cu')}
                paired.append(dict(ret,distance_mm=math.dist(ret['signal_at_mm'],ret['at_mm']),source_rooted_finite_annular_contacts_mm2=contact,pass_=all(a>=.004 for a in contact.values())))
            attempt.update(clearance_errors=errors,pad_losses=losses,surviving_contact_losses=contacts,fill_errors=fillerrors,reference_errors=ref_errors,returns=paired)
            if errors or losses or contacts or fillerrors or any(not r['pass_'] for r in paired):continue
            candidate={'new_chunks':{u:ch.decode() for u,ch in new.items()},'all_surviving_contact_obligations':ledger,'native_source_partition_checks':checks,'reference_witness':fwitness,'prospective_fill_contact_ledger':fillledger,'clearance_rows':clear,'new_antipads':anti,'selected_attempt_index':len(attempts)-1,'full_body_reference_errors':ref_errors,'reference_and_adoption_credit':not bool(ref_errors)}
            if ref_errors:
                if not enforce_reference:held=candidate;break
                continue
            success=candidate;break
        if success or held:break
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    report={'verdict':'POSITIVE_HOST_REFERENCE_AWARE_OPERATION_INDEPENDENT_NATIVE_ANALOG_OPEN' if success else 'HELD_PHYSICAL_DIAGNOSTIC_REFERENCE_GATE_OPEN' if held else 'FINITE_REFERENCE_AWARE_OPERATION_INCOMPLETE','source_sha256':C.sha(raw),'native_template_proof':padproof,'removed_owned_items':sorted(removed),'owned_r06_withdrawables_replaced':sorted(withdrawn),'exact_removed_chunks':{u:now[4][u].decode() for u in removed},'exact_new_chunks':(success or held)['new_chunks'] if success or held else {},'component_diagnostic':diagnostic,'exact_original_recovered_relation':relation,'attempts':attempts,'success':success,'held_diagnostic_candidate':held,'nominal_requirements':{'VREF':'Analog DC reference loop; preserve actual source, loading, decoupling, quiet-return and noise obligations. No speed/plane waiver.','SDI':'Historical frozen ordinary NONE class; actual ISO7761→AD5683R 32MHz sampled bus with 1ns driver edge requires actual timing/settling/noise/return qualification. No qualification inferred from old length estimates.'},'owned_original_MON_F_segments':sorted(MON_REMOVED),'exact_monitor_policy':monitor_policy,'monitor_width_mm':.2,'new_monitor_vias':0,'monitor_current_r06_and_surviving_contact_obligations_mandatory':True,'SCLK_all_source_geometry_exact':True,'new_SDI_sites_freed_by_replacing_old_VREF':True,'shared_return_allowed_only_if_source_rooted_and_ordinary_pitch_for_both':True,'same_domain_fill_retreat_nominates_only_with_exact_final_local_clearance_contact_no_split_gates':True,'cross_domain_fill_and_real_hards_preserved':True,'actual_existing_source_rooted_return_reuse':True,'no_neighbor_signal_void_exemption':True,'no_removed_source_antipad_fill_credit':True,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen helper/source changed '+p)
    OUT.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(OUT),'verdict':report['verdict'],'VREF_sites':len(vsite),'SDI_sites':len(ssites),'attempts':len(attempts),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
