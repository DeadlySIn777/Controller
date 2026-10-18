"""Independent positive AO1 operation audit on frozen native 198b geometry.

No native load/save, candidate board, source changes, or assumed generic ground.
Optional JSON input is an exact root-owned operation manifest with new chunks.
"""
import collections,copy,json,math,re,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C=A.P,A.G,A.S,A.C
VREF='/motherboard_analog_output/AO1_VREF'
SDI='/motherboard_analog_output/AO1_DAC_SDI'
COM='/motherboard_analog_output/AO1_COM'
ANCHOR='U14619.7#0'

def zone_gaps(inv):
    result={}
    for u,ch in inv[3].items():
        if C.pcbtext.chunk_kind(ch)!='zone':continue
        match=re.search(r'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',ch.decode())
        if not match:raise ValueError('Explicit exact source zone clearance required '+u)
        result[u]=float(match.group(1))
    return result

def drilled_metal(model,masks):
    holes=[Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128) for v in model.g['vias']]
    holes += [q for p in model.g['pads'] for q in S.poly(p.get('hole') or [])]
    tree=STRtree(holes);result=collections.defaultdict(list)
    for layer,records in model.records.items():
        for r in records:
            if r['kind'] not in ('pad','track','via'):continue
            if r['kind']=='via' and layer not in masks.get(r['uuid'],set()):continue
            cutters=unary_union([holes[int(i)] for i in tree.query(r['shape'],predicate='intersects')])
            body=r['shape'].difference(cutters)
            if not body.is_empty:result[layer].append(dict(r,shape=body))
    return result,holes

def prospective_fill(source,candidate,masks,inventory,parsed,changed):
    """All exact affected nets; every subtracted fill piece receives a new key."""
    gaps=zone_gaps(inventory);metal,_=drilled_metal(source,masks)
    cuts=[]
    for u in changed:
        z=parsed[u]
        if z['kind']=='via':cuts.append((u,z['net'],set(candidate.g['copper_layers']),Point(z['at']).buffer(z['d']/2,resolution=128),Point(z['at']).buffer(z['drill']/2,resolution=128)))
        elif z['kind']=='segment':cuts.append((u,z['net'],{z['layer']},LineString([z['a'],z['b']]).buffer(z['w']/2,resolution=128),None))
        else:raise ValueError('Only exact segment/via operation supported')
    altered=copy.copy(candidate);altered.records=dict(candidate.records);altered.trees=dict(candidate.trees)
    ledger=[];errors=[]
    for layer,records in candidate.records.items():
        old=metal[layer];tree=STRtree([r['shape'] for r in old]);rows=[]
        for index,r in enumerate(records):
            if r['kind']!='fill':rows.append(r);continue
            clips=[];cutrows=[]
            for u,net,layers,body,hole in cuts:
                if layer not in layers:continue
                if net==r['net']:
                    if hole is None:continue
                    region=hole;required=0.
                else:
                    domain=.15 if candidate.domains[net]==r.get('domain') else .6
                    required=max(domain,gaps[r['uuid']]);region=body.buffer(required+.025,resolution=128)
                if region.intersects(r['shape']):clips.append(region);cutrows.append({'uuid':u,'net':net,'required_zone_domain_clearance_mm':required})
            if not clips:rows.append(r);continue
            remaining=r['shape'].difference(unary_union(clips));pieces=P.K.D.components(remaining);contacts=[]
            if len(pieces)!=1:errors.append({'zone_uuid':r['uuid'],'net':r['net'],'layer':layer,'reason':'Old fill component removed or split','new_piece_count':len(pieces)})
            for i in tree.query(r['shape'],predicate='intersects'):
                q=old[int(i)]
                if q['net']!=r['net'] or q['shape'].distance(r['shape'])>.000002:continue
                hits=[j for j,p in enumerate(pieces) if q['shape'].distance(p)<=.000002]
                contacts.append({'key':list(q['key']),'uuid':q['uuid'],'kind':q['kind'],'candidate_piece_indices':hits})
                if not hits:errors.append({'zone_uuid':r['uuid'],'net':r['net'],'layer':layer,'reason':'Old physical contact lost','key':list(q['key'])})
            ledger.append({'zone_uuid':r['uuid'],'net':r['net'],'layer':layer,'old_fill_index':index,'exact_original_fill_wkb_sha256':C.sha(r['shape'].wkb),'exact_serialized_local_zone_clearance_mm':gaps[r['uuid']],'original_area_mm2':r['shape'].area,'candidate_area_mm2':remaining.area,'cut_items':cutrows,'candidate_component_count':len(pieces),'old_existing_physical_contacts':contacts})
            for j,p in enumerate(pieces):rows.append(dict(r,shape=p,key=('z',r['uuid'],layer,C.sha(p.wkb),j)))
        altered.records[layer]=rows;altered.trees[layer]=STRtree([r['shape'] for r in rows])
    return altered,ledger,errors

def rooted_reference(model,masks,raw_com):
    """Actual AO1_COM source rooted through physical annuli/pads, all drills first."""
    metal,holes=drilled_metal(model,masks);hole_tree=STRtree(holes);uf=S.UF();bylayer={};allrows=[]
    anchor=model.pads[ANCHOR]
    if anchor['net']!=raw_com:raise ValueError('Actual functional AO1 source pad raw net differs')
    for layer in model.g['copper_layers']:
        rows=[r for r in metal[layer] if r['net']==COM]
        for r in model.records[layer]:
            if r['kind']!='fill' or r['net']!=COM:continue
            cutters=unary_union([holes[int(i)] for i in hole_tree.query(r['shape'],predicate='intersects')])
            # Every disconnected physical polygon has its own graph identity.
            for j,p in enumerate(P.K.D.components(r['shape'].difference(cutters))):
                rows.append(dict(r,shape=p,key=('z',r['uuid'],layer,C.sha(p.wkb),j)))
        tree=STRtree([r['shape'] for r in rows])
        for i,r in enumerate(rows):
            uf.find(r['key'])
            for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
                if i<int(j) and r['shape'].distance(rows[int(j)]['shape'])<=.000002:uf.join(r['key'],rows[int(j)]['key'])
        bylayer[layer]=rows;allrows+=rows
    root=uf.find(('p',ANCHOR));refs={};witness={}
    for signal,plane in (('F.Cu','In1.Cu'),('B.Cu','In4.Cu')):
        rooted=[r for r in bylayer[plane] if uf.find(r['key'])==root]
        fill=unary_union([r['shape'] for r in rooted if r['kind']=='fill'])
        refs[signal]=fill
        witness[plane]={'source_pad_id':ANCHOR,'source_pad_uuid':anchor['uuid'],'source_net':COM,'source_pad_exact_at_mm':[anchor['x'],anchor['y']],'source_pad_actual_layers':sorted(anchor['layers']),'all_drills_subtracted_first':True,'all_fill_pieces_have_distinct_graph_keys':True,'source_rooted_fill_mm2':fill.area,'rooted_physical_keys':[list(r['key']) for r in rooted if r['kind']!='fill']}
    refs['In3.Cu']=refs['B.Cu']
    return refs,witness,uf,bylayer

def serial_via(identity,net,at):
    raw=identity.raw(net);u=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-independent-ao1-operation-r1/'+raw+'/'+repr(tuple(at))))
    ch=(f'\t(via\n\t\t(at {at[0]:.9f} {at[1]:.9f})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{raw}")\n\t\t(uuid "{u}")\n\t)\n').encode()
    return u,ch

def main():
    started=time.monotonic();out=HERE/'ao1-positive-independent-operation-r3.json'
    if out.exists():raise ValueError('Fresh independent operation audit required')
    recipe=json.loads(A.read(HERE.parent/'ao1-vref-sdi-components-r3/receipt.json'))
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    policies={S.norm(n):r for n,r in json.loads(A.read(S.CONTROLLED))['nets'].items()}
    if policies.get(SDI,{}).get('class')!='NONE':raise ValueError('Exact frozen SDI policy is not ordinary NONE')
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen source differs')
    removed=set(recipe['deletes']);restored=set(recipe['restores']);new={}
    for route in recipe['new_SDI_routes']:
        for a,b in zip(route['points_mm'],route['points_mm'][1:]):
            u,ch=identity.serial_segment(route['net'],route['layer'],a,b,route['width_mm']);new[u]=ch
    u,ch=serial_via(identity,SDI,recipe['new_SDI_via_mm']);new[u]=ch
    manifest=None
    if len(sys.argv)>1:
        manifest=json.loads(A.read(Path(sys.argv[1])))
        for row in manifest['return_vias']:
            u,ch=serial_via(identity,COM,row['at_mm']);new[u]=ch
    chunks={u:ch for u,ch in now[4].items() if u not in removed};chunks.update({u:old[4][u] for u in restored});chunks.update(new)
    if restored&set(now[4]) or removed-set(now[4]):raise ValueError('Restore/delete ownership differs')
    identity.assert_chunks(chunks)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(source_masks)
    parsed={u:G.parse(u,chunks[u],{}) for u in restored|set(new)}
    for u,z in parsed.items():
        if z['kind']=='via':masks[u]=set(template['copper_layers'])
    reserve,exempt=A.reservations();print('AO1_INDEPENDENT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    print('AO1_INDEPENDENT_OPERATION_MODEL',flush=True)
    candidate=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],source_masks)
    candidate,fillledger,fillerrors=prospective_fill(base,candidate,source_masks,now,parsed,set(parsed))
    errors,clear,anti=A.clearance(candidate,parsed,set(new),restored)
    smd=[r for ls,rs in candidate.records.items() for r in rs if r['kind']=='pad' and candidate.pads[r['pad_id']]['smd']];stree=STRtree([r['shape'] for r in smd]);aperture=[]
    for u,z in parsed.items():
        if z['kind']!='via':continue
        at=Point(z['at']);r=smd[int(stree.nearest(at))];gap=at.distance(r['shape'])-z['drill']/2-.005
        row={'uuid':u,'at_mm':z['at'],'nearest_pad_id':r['pad_id'],'nearest_pad_uuid':r['uuid'],'nearest_pad_layer':r['layer'],'drill_edge_after_native_polygon_error_mm':gap,'required_with_guard_mm':.275};aperture.append(row)
        if gap<.275:errors.append(dict(row,reason='Ordinary all-SMD drill aperture'))
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    failures,checks,_,groups=A.relationships(base,source_masks,parts,(VREF,SDI))
    if failures or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Independent exact current source partition differs')
    losses=[];contacts=[];obligations=[];boundary=[]
    for net in (VREF,SDI):
        uf,after=P.physical(candidate,net,masks)
        for label,relations in (('current198b',parts[net]),('originalr06',prior[net])):
            for rel in relations:
                if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'pads':rel})
        for group in groups[net]:
            keys=sorted({r['key'] for r in group['records'] if r['uuid'] not in removed});count=len({uf.find(k) for k in keys})
            row={'net':net,'surviving_keys':[list(k) for k in keys],'candidate_component_count':count};obligations.append(row)
            if count>1:contacts.append(row)
        for r in base.own[net]:
            if r['uuid'] not in removed:continue
            for q in base.own[net]:
                if q['uuid'] in removed or q['layer']!=r['layer']:continue
                if r['shape'].distance(q['shape'])<=.000002:boundary.append({'removed_uuid':r['uuid'],'retained_key':list(q['key']),'layer':r['layer']})
    print('AO1_INDEPENDENT_REFERENCE_GRAPH',flush=True)
    refs,witness,guf,groundrows=rooted_reference(candidate,masks,identity.raw(COM))
    signals=[v for v in candidate.g['vias'] if v['uuid'] in parsed and v['net'] in (VREF,SDI)]
    retained_transitions=[]
    for v in candidate.g['vias']:
        if v['uuid'] in parsed or v['net'] not in (VREF,SDI):continue
        contacted=[u for u,z in parsed.items() if z['kind']=='segment' and z['net']==v['net'] and z['layer'] in source_masks.get(v['uuid'],set()) and A.shape(z).intersects(Point(v['x'],v['y']).buffer(v['d']/2,resolution=128))]
        if contacted:retained_transitions.append(dict(v,contacted_added_or_restored_segments=contacted))
    signals+=retained_transitions
    gaps=zone_gaps(now);refchecks=[]
    for u,z in parsed.items():
        if z['kind']!='segment':continue
        plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu'
        local_voids=[];voidrows=[]
        for v in signals:
            if v['net']!=z['net']:continue
            exact=Point(v['x'],v['y']).buffer(v['d']/2,resolution=128)
            zones=[r for r in base.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].distance(exact)<=max(.15,gaps[r['uuid']])+.025]
            required=max([.15]+[gaps[r['uuid']] for r in zones]);radius=v['d']/2+required+.025
            local_voids.append(Point(v['x'],v['y']).buffer(radius,resolution=128));voidrows.append({'signal_via_uuid':v['uuid'],'radius_mm':radius,'exact_source_zone_uuids':sorted({r['uuid'] for r in zones}),'local_zone_clearance_mm':required})
        local=unary_union(local_voids)
        body=A.shape(z);uncovered=body.difference(local).difference(refs[z['layer']])
        refchecks.append({'uuid':u,'net':z['net'],'layer':z['layer'],'width_mm':z['w'],'exact_own_transition_reference_voids':voidrows,'uncovered_full_copper_mm2':uncovered.area,'uncovered_bounds_mm':list(uncovered.bounds) if not uncovered.is_empty else []})
    returns=[]
    for signal in signals:
        choices=[]
        for v in candidate.g['vias']:
            if v['net']!=COM or not {'In1.Cu','In4.Cu'}<=masks.get(v['uuid'],set()):continue
            distance=math.dist((signal['x'],signal['y']),(v['x'],v['y']))
            if not .8<=distance<=1.:continue
            ann=Point(v['x'],v['y']).buffer(v['d']/2,resolution=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128))
            plane_contacts={layer:refs[layer].intersects(ann) for layer in ('F.Cu','B.Cu')}
            choices.append({'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':distance,'actual_source_or_conservative_new_annuli':sorted(masks[v['uuid']]),'source_rooted_plane_contacts':plane_contacts})
        returns.append({'signal_uuid':signal['uuid'],'signal_at_mm':[signal['x'],signal['y']],'paired_return_choices':choices,'pass':any(all(v['source_rooted_plane_contacts'].values()) for v in choices)})
    referrors=[r for r in refchecks if r['uncovered_full_copper_mm2']>1e-9]
    returnerrors=[r for r in returns if not r['pass']]
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    report={'schema':'ao1-independent-positive-operation-r3','verdict':'INDEPENDENT_HOST_OPERATION_PASS_NATIVE_ANALOG_OPEN' if not(errors or losses or contacts or fillerrors or referrors or returnerrors) else 'INDEPENDENT_HOST_OPERATION_INCOMPLETE','source_sha256':C.sha(raw),'operation_new_chunks_sha256':C.sha(b''.join(new[u] for u in sorted(new))),'native_geometry_proof':proof,'raw_net_identity':{n:identity.raw(n) for n in (VREF,SDI,COM)},'exact_frozen_SDI_controlled_policy':policies[SDI],'SCLK_all_source_chunks_unchanged':True,'exact_current_native_partition_checks':checks,'removed_owned_uuids':sorted(removed),'restored_exact_original_uuids':sorted(restored),'new_parsed_items':{u:{k:v for k,v in z.items() if k!='shape'} for u,z in parsed.items()},'derived_shape_WKB_sha256':{u:C.sha(z['shape'].wkb) for u,z in parsed.items() if 'shape' in z},'new_conservative_all6_annuli':candidate.source_annulus_proof,'pad_relationship_losses':losses,'surviving_contact_losses':contacts,'all_surviving_contact_obligations':obligations,'deleted_to_retained_contact_boundary':boundary,'clearance_errors':errors,'changed_item_clearance':clear,'ordinary_SMD_drilled_aperture':aperture,'prospective_all_affected_fill_contact_ledger':fillledger,'prospective_fill_contact_errors':fillerrors,'source_rooted_reference_witness':witness,'full_copper_reference_checks':refchecks,'reference_errors':referrors,'paired_return_checks':returns,'return_errors':returnerrors,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Root exact final recipe serialization and latest combined-parent local/remote ownership binding','Fresh candidate native fill, exact via annuli/raw nets, all-net originalr06/r07/current no-loss and full DRC','Complete source analog loop/noise/edge/load/return and electrical manufacturing qualification'],'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen helper/source changed '+p)
    print(json.dumps({'prewrite_counts':{'clearance':len(errors),'pads':len(losses),'contacts':len(contacts),'fill':len(fillerrors),'references':len(referrors),'returns':len(returnerrors)}}),flush=True)
    out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'clearance_errors':len(errors),'pad_losses':len(losses),'contact_losses':len(contacts),'fill_errors':len(fillerrors),'reference_errors':len(referrors),'missing_paired_returns':len(returnerrors)}),flush=True)
if __name__=='__main__':main()
