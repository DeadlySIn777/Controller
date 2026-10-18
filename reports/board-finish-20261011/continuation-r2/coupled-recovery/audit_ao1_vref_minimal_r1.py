"""Separate exact rebuilt audit for the minimal VREF-only operation."""
import json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_positive_operation_r4 as Q
import ao1_independent_fill_r1 as IF
from shapely.geometry import Point
from shapely.strtree import STRtree
A,P,G,S,C,F,N=Q.A,Q.P,Q.G,Q.S,Q.C,Q.F,Q.N
VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM

def main():
    started=time.monotonic();out=HERE/'ao1-vref-minimal-independent-r1.json'
    if out.exists():raise ValueError('Fresh full independent audit required')
    recipe=json.loads(A.read(HERE/'ao1-reference-coupled-r4.json'))
    if not recipe['success']:raise ValueError('A positive concrete exact operation is required')
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    if C.sha(raw)!=recipe['source_sha256'] or C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen exact source differs')
    if recipe['removed_owned_items'] or recipe['exact_removed_chunks']:raise ValueError('Minimal branch may remove no current source item')
    new={u:ch.encode() for u,ch in recipe['exact_new_chunks'].items()}
    if set(new)&set(now[3]):raise ValueError('Exact new UUID collides with source')
    withdrawn=set(recipe['owned_r06_withdrawables_replaced'])
    graph=json.loads(A.read(HERE/'conflict-graph.json'));lost=next(r for r in graph['lost_route_rows'] if r['net']==VREF)
    if withdrawn!={r['uuid'] for r in lost['missing_original_items']} or withdrawn&set(now[4]):raise ValueError('Exact original withdrawable ownership differs')
    if set(recipe['exact_original_recovered_relation'])!={'C14643.1#0','U14626.9#0'}:raise ValueError('Actual original native relationship differs')
    chunks=dict(now[4]);chunks.update(new);identity.assert_chunks(chunks)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    smasks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(smasks)
    parsed={u:G.parse(u,ch,{}) for u,ch in new.items()}
    vias={u:z for u,z in parsed.items() if z['kind']=='via'}
    if len(vias)!=2 or {z['net'] for z in vias.values()}!={VREF,COM}:raise ValueError('Expected one ordinary VREF transition and one own-domain return')
    for u,z in parsed.items():
        if z['kind']=='via':
            if (z['d'],z['drill'])!=(.5,.2):raise ValueError('Ordinary new dimensions differ')
            masks[u]=set(template['copper_layers'])
        elif z['kind']!='segment' or z['net']!=VREF or z['layer'] not in ('F.Cu','B.Cu') or z['w']!=.2:raise ValueError('Unowned or unqualified new geometry')
    reserve,exempt=A.reservations();print('AO1_MINIMAL_INDEPENDENT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],smasks)
    print('AO1_MINIMAL_INDEPENDENT_REBUILT_MODEL',flush=True)
    final=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],smasks)
    final,ledger,fillerrors=IF.prospective_fill(base,final,smasks,now,parsed,set(parsed))
    errors,clear,anti=A.clearance(final,parsed,set(parsed),set())
    smd=[r for records in final.records.values() for r in records if r['kind']=='pad' and final.pads[r['pad_id']]['smd']];tree=STRtree([r['shape'] for r in smd]);aperture=[]
    for u,z in vias.items():
        p=Point(z['at']);r=smd[int(tree.nearest(p))];gap=p.distance(r['shape'])-z['drill']/2-.005
        row={'uuid':u,'exact_at_mm':z['at'],'nearest_SMD_pad_id':r['pad_id'],'nearest_SMD_pad_uuid':r['uuid'],'layer':r['layer'],'minimum_drill_edge_after_export_error_mm':gap,'minimum_required_with_guard_mm':.275,'net_or_registered_process_exemptions':0};aperture.append(row)
        if gap<.275:errors.append(dict(row,reason='All-SMD ordinary drill aperture'))
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    losses,checks,_,groups=A.relationships(base,smasks,parts,(VREF,SDI))
    if losses or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Exact baseline native groups differ')
    losses=[];contacts=[];obligations=[]
    for net in (VREF,SDI):
        uf,gs=P.physical(final,net,masks)
        for label,rels in (('current198b',parts[net]),('originalr06',prior[net])):
            for rel in rels:
                if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'pads':rel})
        for group in groups[net]:
            keys=sorted({r['key'] for r in group['records']});count=len({uf.find(k) for k in keys})
            row={'net':net,'all_unchanged_source_physical_keys':[list(k) for k in keys],'candidate_component_count':count};obligations.append(row)
            if count>1:contacts.append(row)
    source_refs,source_witness,_,_=Q.rooted_reference(base,smasks,identity.raw(COM));refs,witness,_,_=Q.rooted_reference(final,masks,identity.raw(COM))
    signal=next(z for z in vias.values() if z['net']==VREF);ret=next(z for z in vias.values() if z['net']==COM)
    gaps=Q.zone_gaps(now);reference=[]
    for u,z in parsed.items():
        if z['kind']!='segment':continue
        plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu'
        nearby=[r for r in base.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].distance(Point(signal['at']))<1.]
        clearance=max([.15]+[gaps[r['uuid']] for r in nearby]);radius=signal['d']/2+clearance+.025
        own=Point(signal['at']).buffer(radius,resolution=128);gap=A.shape(z).difference(own).difference(refs[z['layer']]).area
        reference.append({'uuid':u,'layer':z['layer'],'width_mm':z['w'],'route_own_transition_uuid':signal['uuid'],'exact_own_transition_void_radius_mm':radius,'source_local_clearance_mm':clearance,'full_body_reference_uncovered_mm2':gap})
    reference_errors=[r for r in reference if r['full_body_reference_uncovered_mm2']>1e-9]
    old_sdi=[];old_sdi_errors=[]
    for r in base.own[SDI]:
        if r['kind']!='track' or r['layer'] not in refs:continue
        covered=r['shape'].intersection(source_refs[r['layer']]);loss=covered.difference(refs[r['layer']]).area
        row={'uuid':r['uuid'],'layer':r['layer'],'exact_unchanged_source_body_WKB_sha256':C.sha(r['shape'].wkb),'original_source_plane_uncovered_full_body_mm2':r['shape'].difference(source_refs[r['layer']]).area,'previously_source_rooted_body_reference_lost_mm2':loss}
        old_sdi.append(row)
        if loss>1e-9:old_sdi_errors.append(row)
    ann=Point(ret['at']).buffer(ret['d']/2,resolution=128).difference(Point(ret['at']).buffer(ret['drill']/2,resolution=128));distance=math.dist(signal['at'],ret['at'])
    returns={'signal_uuid':signal['uuid'],'return_uuid':ret['uuid'],'distance_mm':distance,'all6_native_annuli':'OPEN; conservative host all6','complete_annulus_uncovered_mm2':{layer:ann.difference(refs[layer]).area for layer in ('F.Cu','B.Cu')}}
    return_errors=[]
    if not .8<=distance<=1.+1e-9 or any(v>1e-9 for v in returns['complete_annulus_uncovered_mm2'].values()):return_errors.append(returns)
    def ledger_id(rows):return sorted((r['zone_uuid'],r['net'],r['layer'],r['exact_original_fill_wkb_sha256'],r['exact_serialized_local_zone_clearance_mm'],tuple(sorted((q['uuid'],q['net'],q['required_zone_domain_clearance_mm']) for q in r['cut_items'])),r['candidate_component_count'],tuple(sorted((tuple(q['key']),tuple(q['candidate_piece_indices'])) for q in r['old_existing_physical_contacts']))) for r in rows)
    if ledger_id(ledger)!=ledger_id(recipe['success']['prospective_fill_contact_ledger']):raise ValueError('Separate sequential clipping/contact audit disagrees with constructor')
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    passed=not(errors or losses or contacts or fillerrors or reference_errors or old_sdi_errors or return_errors)
    report={'verdict':'INDEPENDENT_NEW_VREF_HOST_PASS_EXISTING_SDI_NATIVE_ANALOG_QUALIFICATION_OPEN' if passed else 'INDEPENDENT_MINIMAL_VREF_HOST_INCOMPLETE','source_sha256':C.sha(raw),'exact_new_chunk_sha256':C.sha(b''.join(new[u] for u in sorted(new))),'native_template_proof':proof,'all_current_source_copper_byte_exact':True,'all_7_owned_r06_withdrawables_replaced':sorted(withdrawn),'exact_original_relation':recipe['exact_original_recovered_relation'],'source_native_partition_checks':checks,'pad_relationship_losses':losses,'surviving_contact_losses':contacts,'all_surviving_contact_obligations':obligations,'clearance_errors':errors,'changed_item_clearance':clear,'ordinary_SMD_drill_aperture':aperture,'prospective_fill_contact_errors':fillerrors,'prospective_fill_contact_ledger':ledger,'separate_constructor_ledger_match':True,'full_new_VREF_reference_checks':reference,'new_VREF_reference_errors':reference_errors,'unchanged_SDI_reference_baseline_and_preservation':old_sdi,'unchanged_SDI_new_reference_losses':old_sdi_errors,'ordinary_new_VREF_return':returns,'ordinary_return_errors':return_errors,'functional_source_root_witness':witness,'original_source_root_witness':source_witness,'all_ordinary_new_via_actual_native_annuli':'OPEN','native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,'open_gates':['Latest exact root parent ownership/geometry rebinding','Fresh exact native all6 new annuli and actual candidate refill all-net r06/r07/current no-loss plus full ordinary DRC','Existing complete SDI source/timing/noise/SI/return and final analog DC/quiet-loop/decoupling/thermal/manufacturing qualification'],'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen source/helper changed '+p)
    out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'clearance':len(errors),'pad_losses':len(losses),'contact_losses':len(contacts),'fill':len(fillerrors),'new_reference':len(reference_errors),'old_SDI_new_reference_losses':len(old_sdi_errors),'return_errors':len(return_errors)}),flush=True)
if __name__=='__main__':main()
