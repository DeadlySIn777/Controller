"""Independent full serialized rebuild of a concrete paired AO1 operation.

Reads constructor chunks but never uses its projection or path/return decisions.
Native jobs, live/shared board writes, and generic ground credit are forbidden.
"""
import json,math,sys,time
from decimal import Decimal
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_ao1_positive_operation_r4 as Q
import ao1_independent_fill_r1 as IF
import ao1_reference_gap_diagnostic_r2 as GD
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
A,P,G,S,C,F,N=Q.A,Q.P,Q.G,Q.S,Q.C,Q.F,Q.N
VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM
MON='/motherboard_analog_output/AO1_MON_12V'
MON_REMOVED={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'}

def ledger_identity(rows):
    return sorted((r['zone_uuid'],r['net'],r['layer'],r['exact_original_fill_wkb_sha256'],r['exact_serialized_local_zone_clearance_mm'],tuple(sorted((q['uuid'],q['net'],q['required_zone_domain_clearance_mm']) for q in r['cut_items'])),r['candidate_component_count'],tuple(sorted((tuple(q['key']),tuple(q['candidate_piece_indices'])) for q in r['old_existing_physical_contacts']))) for r in rows)

def main():
    started=time.monotonic()
    if len(sys.argv)!=2:raise ValueError('Exact positive constructor receipt required')
    path=Path(sys.argv[1]).resolve();out=HERE/(path.stem+'-independent-mon-r4.json')
    if out.exists():raise ValueError('Fresh independent audit required')
    recipe=json.loads(A.read(path))
    operation=recipe.get('success') or recipe.get('held_diagnostic_candidate')
    if not operation or not recipe['exact_new_chunks']:raise ValueError('Concrete chunks required; finite negative nomination is not a candidate')
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    if C.sha(raw)!=A.SOURCE_SHA or C.sha(raw)!=recipe['source_sha256']:raise ValueError('Frozen full native source differs')
    policies={S.norm(n):r for n,r in json.loads(A.read(S.CONTROLLED))['nets'].items()}
    if policies.get(SDI,{}).get('class')!='NONE':raise ValueError('Exact frozen ordinary SDI classification differs')
    removed=set(recipe['removed_owned_items']);new={u:ch.encode() for u,ch in recipe['exact_new_chunks'].items()};withdrawn=set(recipe['owned_r06_withdrawables_replaced'])
    original=json.loads(A.read(HERE.parent/'ao1-vref-sdi-components-r3/receipt.json'))
    if removed!=set(original['deletes'])|MON_REMOVED or withdrawn!=set(original['restores']):raise ValueError('Exact owned SDI removals/VREF absent withdrawables differ')
    if {u:now[4][u] for u in removed}!={u:ch.encode() for u,ch in recipe['exact_removed_chunks'].items()}:raise ValueError('Exact original native removal chunks differ')
    if withdrawn&set(now[4]) or set(new)&set(now[3]):raise ValueError('Withdrawable is present or new UUID collides')
    if set(recipe['exact_original_recovered_relation'])!={'C14643.1#0','U14626.9#0'}:raise ValueError('Actual original native VREF relationship differs')
    parent_path=HERE.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
    parent=A.read(parent_path);pinv=C.inventory(parent);pn=N.SourceNets(parent)
    if any(pinv[4].get(u)!=now[4][u] for u in removed) or withdrawn&set(pinv[4]) or set(new)&set(pinv[3]):raise ValueError('Latest staged parent changed owned operation')
    if any(pn.raw(n)!=identity.raw(n) for n in (VREF,SDI,MON,COM)):raise ValueError('Latest parent exact raw native tokens differ')
    for uid in MON_REMOVED:
        item=G.parse(uid,now[4][uid],{})
        if item['kind']!='segment' or item['net']!=MON or item['layer']!='F.Cu' or item['w']!=.2:raise ValueError('Exact native monitor wall differs')
    monitor_policy=policies.get(MON)
    if monitor_policy is not None and monitor_policy.get('class')!='NONE':raise ValueError('Monitor controlled assignment requires separate profile')
    chunks={u:ch for u,ch in now[4].items() if u not in removed};chunks.update(new);identity.assert_chunks(chunks)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    smasks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(smasks)
    parsed={u:G.parse(u,ch,{}) for u,ch in new.items()};vias={u:z for u,z in parsed.items() if z['kind']=='via'}
    source_mon_uuid='6b5d7465-3e16-4492-82be-cd9ae2fb2ad5'
    exact_fraction=(Decimal('372.85')-Decimal('369.35'))/(Decimal('373.75')-Decimal('369.35'))
    exact_y=Decimal('125.15')+exact_fraction*(Decimal('129.549999')-Decimal('125.15'))
    preserved_uuid,preserved_chunk=identity.serial_segment(MON,'F.Cu',(369.35,125.15),(372.85,round(float(exact_y),9)),.2)
    if new.get(preserved_uuid)!=preserved_chunk:raise ValueError('Source-derived retained MON chunk differs')
    old_mon=G.parse(source_mon_uuid,now[4][source_mon_uuid],{});preserved_body=A.shape(parsed[preserved_uuid]);source_body=A.shape(old_mon)
    if tuple(old_mon['a'])!=(373.75,129.549999) or tuple(old_mon['b'])!=(369.35,125.15) or old_mon['w']!=.2 or old_mon['layer']!='F.Cu' or old_mon['net']!=MON:raise ValueError('Exact native source MON line differs')
    outside=preserved_body.difference(source_body.buffer(.000001)).area
    if outside>1e-12:raise ValueError('Retained metal differs beyond source native 1nm lattice')
    preserved={'uuid':preserved_uuid,'source_uuid':source_mon_uuid,'source_chunk_SHA256':C.sha(now[4][source_mon_uuid]),'exact_rational_line_fraction':str(exact_fraction),'exact_rational_y_mm':str(exact_y),'source_native_lattice_error_bound_mm':.000001,'outside_source_plus_lattice_error_mm2':outside,'newly_routed_reference_waivers':0}
    changed=set(parsed)-{preserved_uuid}
    signals={z['net']:z for z in vias.values() if z['net'] in (VREF,SDI)}
    if len(signals)!=2 or len([z for z in vias.values() if z['net'] in (VREF,SDI)])!=2 or not 1<=len(vias)-2<=2:raise ValueError('Expected exactly one VREF/SDI transition and one or two ordinary returns')
    for u,z in parsed.items():
        if z['kind']=='via':
            if (z['d'],z['drill'])!=(.5,.2) or z['net'] not in (VREF,SDI,COM):raise ValueError('Exact ordinary via net/dimensions differ')
            masks[u]=set(template['copper_layers'])
        elif z['kind']!='segment' or z['w']!=.2 or z['net'] not in (VREF,SDI,MON) or z['layer'] not in (('F.Cu','B.Cu') if z['net']==VREF else ('F.Cu','In3.Cu') if z['net']==SDI else ('F.Cu',)):raise ValueError('Unowned or unqualified geometry')
    reserve,exempt=A.reservations();print('AO1_COUPLED_INDEPENDENT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],smasks)
    print('AO1_COUPLED_INDEPENDENT_SERIALIZED_REBUILD',flush=True)
    final=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],smasks)
    final,ledger,fillerrors=IF.prospective_fill(base,final,smasks,now,parsed,changed)
    if ledger_identity(ledger)!=ledger_identity(operation['prospective_fill_contact_ledger']):raise ValueError('Separate sequential fill/contact projection disagrees with constructor')
    errors,clear,anti=A.clearance(final,parsed,changed,set())
    smd=[r for rows in final.records.values() for r in rows if r['kind']=='pad' and final.pads[r['pad_id']]['smd']];stree=STRtree([r['shape'] for r in smd]);aperture=[];pitch=[]
    for u,z in vias.items():
        p=Point(z['at']);r=smd[int(stree.nearest(p))];gap=p.distance(r['shape'])-.1-.005
        row={'uuid':u,'at_mm':z['at'],'nearest_SMD_pad':r['pad_id'],'nearest_SMD_pad_uuid':r['uuid'],'guarded_drill_aperture_mm':gap,'required_mm':.275,'net_or_process_exemptions':0};aperture.append(row)
        if gap<.275:errors.append(dict(row,reason='All-SMD drill aperture'))
        near=min((v for v in final.g['vias'] if v['uuid']!=u),key=lambda v:math.dist(z['at'],(v['x'],v['y'])))
        distance=math.dist(z['at'],(near['x'],near['y']));row={'uuid':u,'nearest_via_uuid':near['uuid'],'distance_mm':distance,'required_mm':.81};pitch.append(row)
        if distance<.81-1e-9:errors.append(dict(row,reason='Ordinary centre pitch with guard'))
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    failed,checks,_,groups=A.relationships(base,smasks,parts,(VREF,SDI,MON))
    if failed or not all(r['exact_native_partition_match'] for r in checks):raise ValueError('Actual uncapped native source groups differ')
    losses=[];contacts=[];obligations=[];boundary=[]
    for net in (VREF,SDI,MON):
        uf,_=P.physical(final,net,masks)
        for label,rels in (('current198b',parts[net]),('originalr06',prior[net])):
            for rel in rels:
                if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'pads':rel})
        for group in groups[net]:
            keys=sorted({r['key'] for r in group['records'] if r['uuid'] not in removed});count=len({uf.find(k) for k in keys})
            row={'net':net,'surviving_keys':[list(k) for k in keys],'candidate_component_count':count};obligations.append(row)
            if count>1:contacts.append(row)
        for r in base.own[net]:
            if r['uuid'] not in removed:continue
            for q in base.own[net]:
                if q['uuid'] not in removed and q['layer']==r['layer'] and q['shape'].distance(r['shape'])<=.000002:boundary.append({'removed_uuid':r['uuid'],'retained_key':list(q['key']),'layer':r['layer']})
    print('AO1_COUPLED_INDEPENDENT_SOURCE_ROOTED_REFERENCE',flush=True)
    original_refs,original_witness,_,_=Q.rooted_reference(base,smasks,identity.raw(COM));refs,witness,_,_=Q.rooted_reference(final,masks,identity.raw(COM))
    retained_covered=preserved_body.intersection(original_refs['F.Cu']);retained_lost=retained_covered.difference(refs['F.Cu'])
    preserved.update(original_source_uncovered_mm2=source_body.difference(original_refs['F.Cu']).area,retained_body_original_uncovered_mm2=preserved_body.difference(original_refs['F.Cu']).area,retained_body_final_uncovered_mm2=preserved_body.difference(refs['F.Cu']).area,previously_covered_retained_body_lost_mm2=retained_lost.area)
    if retained_lost.area>1e-9:contacts.append({'reason':'Source-derived retained MON body lost previous rooted reference','mm2':retained_lost.area})
    gaps=Q.zone_gaps(now);reference=[]
    for u,z in parsed.items():
        if z['kind']!='segment' or u==preserved_uuid:continue
        v=signals.get(z['net']);plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';body=Point(v['at']).buffer(.25,resolution=128) if v else A.shape(z)
        zones=[r for r in base.records[plane] if r['kind']=='fill' and r['net']==COM and r['shape'].distance(body)<=max(.15,gaps[r['uuid']])+.025]
        required=max([.15]+[gaps[r['uuid']] for r in zones]);radius=.25+required+.025 if v else 0.;own=Point(v['at']).buffer(radius,resolution=128) if v else Point().buffer(0)
        uncovered=A.shape(z).difference(own).difference(refs[z['layer']])
        reference.append({'uuid':u,'net':z['net'],'layer':z['layer'],'own_transition_uuid':v['uuid'] if v else None,'own_void_radius_mm':radius,'exact_native_local_zone_clearance_mm':required,'full_body_uncovered_mm2':uncovered.area,'uncovered_bounds_mm':list(uncovered.bounds) if not uncovered.is_empty else []})
    reference_errors=[r for r in reference if r['full_body_uncovered_mm2']>1e-9]
    unchanged=[];unchanged_errors=[];changed_union=unary_union([A.shape(z) for z in parsed.values()])
    for layer,rows in base.records.items():
        if layer not in refs:continue
        for r in rows:
            if r['kind']!='track' or r['uuid'] in removed or r.get('domain')!=base.domains[COM] or r.get('net')==COM:continue
            covered=r['shape'].intersection(original_refs[layer]);lost=covered.difference(refs[layer])
            if not lost.is_empty or r['shape'].distance(changed_union)<1.:
                row={'uuid':r['uuid'],'net':r['net'],'layer':layer,'exact_body_WKB_sha256':C.sha(r['shape'].wkb),'original_uncovered_mm2':r['shape'].difference(original_refs[layer]).area,'previously_source_rooted_reference_lost_mm2':lost.area};unchanged.append(row)
                if lost.area>1e-9:unchanged_errors.append(row)
    returns=[]
    for net,signal in signals.items():
        choices=[]
        for v in final.g['vias']:
            if v['net']!=COM or not {'In1.Cu','In4.Cu'}<=masks.get(v['uuid'],set()):continue
            distance=math.dist(signal['at'],(v['x'],v['y']))
            if not .81-1e-9<=distance<=1.+1e-9:continue
            at=Point(v['x'],v['y']);ann=at.buffer(v['d']/2,resolution=128).difference(at.buffer(v['drill']/2,resolution=128));areas={layer:refs[layer].buffer(-.075).intersection(ann).area for layer in ('F.Cu','B.Cu')}
            choices.append({'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':distance,'actual_source_or_conservative_new_flash_layers':sorted(masks[v['uuid']]),'source_rooted_finite_annular_interior_mm2':areas,'pass':all(a>=.004 for a in areas.values())})
        returns.append({'signal_uuid':signal['uuid'],'signal_net':net,'choices':choices,'pass':any(r['pass'] for r in choices)})
    return_errors=[r for r in returns if not r['pass']]
    gap_dir=HERE/(path.stem+'-independent-reference-gaps-mon-r4');gap_dir.mkdir()
    gap_diagnostics=GD.diagnose(base,final,{u:z for u,z in parsed.items() if u!=preserved_uuid},removed,smasks,refs,now,gap_dir)
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):A.read(p)
    passed=not(errors or losses or contacts or fillerrors or reference_errors or unchanged_errors or return_errors)
    report={'verdict':'INDEPENDENT_COUPLED_AO1_HOST_PASS_NATIVE_ANALOG_OPEN' if passed else 'INDEPENDENT_COUPLED_AO1_INCOMPLETE','constructor_receipt':str(path),'constructor_reference_gate_held':bool(recipe.get('held_diagnostic_candidate')),'source_sha256':C.sha(raw),'exact_new_chunk_sha256':C.sha(b''.join(new[u] for u in sorted(new))),'native_template_proof':proof,'latest_parent_owned_operation':{'path':str(parent_path),'sha256':C.sha(parent),'owned_chunks_and_raw_tokens_exact':True,'full_combined_parent_reference_and_current':'OPEN'},'exact_frozen_SDI_policy':policies[SDI],'exact_monitor_policy':monitor_policy,'owned_exact_MON_F_segments':sorted(MON_REMOVED),'independent_preserved_source_MON_piece':preserved,'newly_changed_source_UUIDs':sorted(changed),'new_MON_vias':0,'MON_original_width_mm':.2,'source_native_partition_checks':checks,'removed_exact_source_UUIDs':sorted(removed),'replaced_absent_r06_withdrawables':sorted(withdrawn),'exact_original_relation':recipe['exact_original_recovered_relation'],'all_surviving_contact_obligations':obligations,'removed_to_retained_contact_boundary':boundary,'pad_relationship_losses':losses,'surviving_contact_losses':contacts,'clearance_errors':errors,'changed_item_clearance':clear,'ordinary_SMD_drill_aperture':aperture,'ordinary_pitch':pitch,'prospective_fill_contact_errors':fillerrors,'prospective_fill_contact_ledger':ledger,'separate_constructor_ledger_match':True,'full_new_signal_reference':reference,'reference_errors':reference_errors,'exact_reference_gap_classification':gap_diagnostics,'unchanged_same_domain_track_reference':unchanged,'unchanged_reference_losses':unchanged_errors,'paired_returns':returns,'paired_return_errors':return_errors,'functional_source_root_witness':witness,'original_source_root_witness':original_witness,'all_ordinary_new_native_annuli':'OPEN; host conservative all6','native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,'open_gates':['Fresh root-composed latest parent exact new native raw net/pose/all6 annuli and current+r07+r06 all-net no-loss/DRC','Actual SI/edge/timing and VREF analog loop/noise/decoupling/PDN/manufacturing qualification'],'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
    for p,h in A.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen source/helper changed '+p)
    out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'clearance':len(errors),'pad_losses':len(losses),'contact_losses':len(contacts),'fill':len(fillerrors),'reference':len(reference_errors),'unchanged_reference':len(unchanged_errors),'returns':len(return_errors)}),flush=True)
if __name__=='__main__':main()
