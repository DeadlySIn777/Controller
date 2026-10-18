"""Independent full serialized XF coupled repair; no native/project writes."""
import json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
import audit_cm_complete_B_r1 as D
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C=A.P,A.G,A.S,A.C
REQ='/motherboard_operator/XF_REQUEST_BUFFER';EN='/motherboard_operator/XF_POWER_EN_GATED';GND='/LOGIC_GND'

def main():
    revision=sys.argv[1] if len(sys.argv)>1 else 'r6';out=HERE/f'xf-complete-independent-audit-{revision}.json'
    if out.exists():raise ValueError('Fresh audit receipt required')
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and str(path).endswith('.py') and ('pcb-runs' in str(path) or 'board-finish-20261011' in str(path)):A.read(path)
    recipe=json.loads(A.read(HERE/f'xf-continuous-landings-{revision}.json'))
    if not recipe.get('candidate'):raise ValueError('Concrete candidate required')
    attempt=next(row for row in recipe['attempts'] if row.get('candidate_sha256'))
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    candidate_raw=A.read(recipe['candidate']);inv=C.inventory(candidate_raw)
    if C.sha(raw)!=A.SOURCE_SHA or C.sha(candidate_raw)!=attempt['candidate_sha256']:raise ValueError('Frozen source/candidate differs')
    removed=set(now[4])-set(inv[4]);added=set(inv[4])-set(now[4]);modified={u for u,ch in now[4].items() if u in inv[4] and inv[4][u]!=ch}
    restored=set(recipe['restored_original_items'])
    if removed!=set(recipe['deleted_owned_items']) or modified or inv[0]!=now[0] or inv[2]!=now[2] or inv[5]!=now[5]:raise ValueError('Exact source ownership differs')
    if any(inv[3].get(u)!=ch for u,ch in now[3].items() if u not in removed):raise ValueError('Untouched exact entity differs')
    for u in restored:
        if inv[4][u]!=old[4][u]:raise ValueError('Restored original exact chunk differs '+u)
    identity.assert_no_collisions(candidate_raw);identity.assert_chunks(inv[4])
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(source_masks)
    parsed={u:G.parse(u,inv[4][u],{}) for u in added}
    for u,z in parsed.items():
        if z['kind']=='via':
            if (z['d'],z['drill'])!=(.5,.2):raise ValueError('Unexpected new ordinary via dimensions')
            masks[u]=set(template['copper_layers'])
    if len([z for z in parsed.values() if z['kind']=='via'])!=5:raise ValueError('Expected exactly five new ordinary vias')
    reserve,exempt=A.reservations();print('XF_INDEPENDENT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    print('XF_INDEPENDENT_CANDIDATE_MODEL',flush=True)
    candidate=F.Model(identity.geometry(inv[4],template),reserve,exempt,native['vias'],source_masks)
    candidate,fill_ledger,fill_errors=D.independent_ground_retreat(base,candidate,source_masks,now,parsed,added)
    errors,clear,anti=A.clearance(candidate,parsed,added-restored,restored)
    smd_records=[z for layer,records in candidate.records.items() for z in records if z['kind']=='pad' and candidate.pads[z['pad_id']]['smd']]
    smd_tree=STRtree([z['shape'] for z in smd_records]);aperture=[];aperture_errors=[]
    for uid,z in parsed.items():
        if z['kind']!='via':continue
        point=Point(z['at']);nearest=smd_records[int(smd_tree.nearest(point))]
        gap=point.distance(nearest['shape'])-z['drill']/2;lower_bound=gap-.005
        row={'uuid':uid,'exact_serialized_at_mm':z['at'],'drill_mm':z['drill'],'nearest_pad_id':nearest['pad_id'],'nearest_pad_uuid':nearest['uuid'],'nearest_pad_layer':nearest['layer'],'nearest_pad_net':nearest['net'],'minimum_drill_edge_to_SMD_copper_mm':gap,'minimum_after_native_polygon_export_error_mm':lower_bound,'required_aperture_mm':.25,'guard_mm':.025,'registered_SMD_hole_exemptions_applied':0}
        aperture.append(row)
        if lower_bound<.275:aperture_errors.append(row)
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    source_losses,checks,_,groups=A.relationships(base,source_masks,parts,(REQ,EN))
    if source_losses or not all(z['exact_native_partition_match'] for z in checks):raise ValueError('Source exact native groups differ')
    losses=[];contacts=[];ledger=[];boundary=[]
    for net in (REQ,EN):
        uf,after=P.physical(candidate,net,masks)
        for label,relations in (('current198b',parts[net]),('originalr06',prior[net])):
            for relation in relations:
                if len({uf.find(('p',pad)) for pad in relation})>1:losses.append({'net':net,'baseline':label,'pads':relation})
        for group in groups[net]:
            surviving=sorted({z['key'] for z in group['records'] if z['uuid'] not in removed});count=len({uf.find(k) for k in surviving})
            row={'net':net,'surviving_keys':[list(k) for k in surviving],'candidate_component_count':count};ledger.append(row)
            if count>1:contacts.append(row)
        for a in base.own[net]:
            if a['uuid'] not in removed:continue
            for b in base.own[net]:
                if b['uuid'] in removed or b['layer']!=a['layer']:continue
                if b['kind']=='via' and b['layer'] not in source_masks[b['uuid']]:continue
                if a['shape'].distance(b['shape'])<=.000002:boundary.append({'removed_uuid':a['uuid'],'retained_key':list(b['key']),'layer':a['layer']})
    landing=next(v for v in candidate.g['vias'] if v['uuid']=='978aead8-cf23-42f1-86b1-269a751e9b88')
    if (landing['net'],landing['x'],landing['y'],landing['d'],landing['drill'])!=(EN,326.15,100.15,.6,.3) or not {'B.Cu','In1.Cu','In4.Cu'}<=source_masks[landing['uuid']]:raise ValueError('Exact existing native EN landing differs')
    new_signals=[v for v in candidate.g['vias'] if v['uuid'] in added and v['net'] in (REQ,EN)]
    cuts=[([v['x'],v['y']],v['d']) for v in new_signals]+[([landing['x'],landing['y']],landing['d'])]
    refs,witness=D.exact_drilled_references(candidate,masks,cuts);reference=[]
    for u,z in parsed.items():
        if z['kind']!='segment':continue
        own=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+.175,resolution=128) for v in new_signals+[landing] if v['net']==z['net']])
        body=LineString([z['a'],z['b']]).buffer(z['w']/2,resolution=128);gap=body.difference(own).difference(refs[z['layer']]).area
        reference.append({'uuid':u,'net':z['net'],'layer':z['layer'],'width_mm':z['w'],'full_copper_uncovered_mm2':gap})
    returns=[];return_errors=[]
    for row in attempt['return_stitch_checks']:
        signal=row['signal_at_mm'];ret=row['return_at_mm'];v=next(v for v in candidate.g['vias'] if v['net']==GND and (v['x'],v['y'])==tuple(ret))
        annulus=Point(ret).buffer(v['d']/2,resolution=128).difference(Point(ret).buffer(v['drill']/2,resolution=128));distance=math.dist(signal,ret)
        planes={layer:refs[layer].intersects(annulus) for layer in ('F.Cu','B.Cu')}
        if not {'In1.Cu','In4.Cu'}<=masks[v['uuid']] or not .8<=distance<=1. or not all(planes.values()):return_errors.append({'uuid':v['uuid'],'distance_mm':distance,'source_plane_contacts':planes})
        returns.append({'uuid':v['uuid'],'signal_at_mm':signal,'return_at_mm':ret,'distance_mm':distance,'source_plane_contacts':planes,'actual_native_new_annuli':'OPEN' if v['uuid'] in added else sorted(source_masks[v['uuid']])})
    def identity_ledger(rows):
        return sorted((z['zone_uuid'],z['layer'],z['exact_original_fill_wkb_sha256'],tuple(sorted(z['cut_item_uuids'])),z['candidate_component_count'],tuple(sorted((tuple(e['key']),tuple(e['candidate_piece_indices'])) for e in z['old_existing_physical_contacts']))) for z in rows)
    if identity_ledger(fill_ledger)!=identity_ledger(attempt['prospective_B_ground_retreat_ledger']):raise ValueError('Independent exact fill/contact ledger differs')
    ref_errors=[z for z in reference if z['full_copper_uncovered_mm2']>1e-9]
    passed=not(errors or losses or contacts or fill_errors or ref_errors or return_errors or aperture_errors)
    report={'schema':'independent-full-xf-audit-r1','verdict':'HOST_COMPLETE_CANDIDATE_AUDIT_PASS_NATIVE_ELECTRICAL_OPEN' if passed else 'HOST_COMPLETE_CANDIDATE_AUDIT_FAIL','source_sha256':C.sha(raw),'candidate_sha256':C.sha(candidate_raw),'exact_native_source_partition_checks':checks,'native_geometry_proof':proof,'source_actual_annuli':base.source_annulus_proof,'new_conservative_all6_annuli':candidate.source_annulus_proof,'removed_owned_uuids':sorted(removed),'added_uuids':sorted(added),'restored_exact_source_uuids':sorted(restored),'all_untouched_entities_and_rules_byte_exact':True,'raw_net_collisions':identity.assert_no_collisions(candidate_raw),'pad_relationship_losses':losses,'surviving_contact_losses':contacts,'all_surviving_contact_obligations':ledger,'removed_to_retained_contact_boundary':boundary,'changed_item_clearance_errors':errors,'changed_item_clearance':clear,'prospective_via_antipads':anti,'prospective_ground_fill_contact_ledger':fill_ledger,'prospective_ground_fill_errors':fill_errors,'full_body_reference_checks':reference,'reference_errors':ref_errors,'source_connected_drilled_reference_witness':witness,'ordinary_return_checks':returns,'return_errors':return_errors,'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Native exact all6 new annuli, fresh full refill and ordinary DRC','Both complete r06/current/r07 native no-loss including all cut planes and every affected power/ground net','Actual complete source function/current/load/edge/timing/return/SI and manufacturing qualification']}
    report['ordinary_SMD_hole_aperture_checks']=aperture;report['ordinary_SMD_hole_aperture_errors']=aperture_errors
    report['ordinary_SMD_hole_predicate']='All exact new ordinary through holes versus all physical SMD copper shapes on every copper layer, no net/registry exception: centre-to-polygon distance minus drill radius, further minus .005 mm native export error >= .25+.025 mm'
    for path,h in A.READS.items():
        if C.sha(Path(path).read_bytes())!=h:raise ValueError('Frozen source/helper changed '+path)
    out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'errors':len(errors),'pad_losses':len(losses),'contact_losses':len(contacts),'fill_errors':len(fill_errors),'reference_errors':len(ref_errors)}),flush=True)
if __name__=='__main__':main()
