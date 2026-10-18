"""Independent exact-source full-item audit of C11068 B-layout operation recipe.

No native call or board output. Actual native footprint flip/pad shapes must
match this frozen geometry before a resulting board receives gate credit.
"""
import collections,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import aux_cap_bside as B
import aux_local_move as L
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
NETS=(A.POWER,A.ILIM,A.DVDT,B.RTN)

def main():
    out=HERE/'aux-cap-recipe-audit-r2.json';start=time.time()
    if out.exists():raise ValueError('Fresh audit output required')
    recipe=json.loads(A.read(HERE/'aux-cap-bside-r4-exact-native-nets.json'));p=recipe['proposal']
    if not p:raise ValueError('No concrete native operation recipe')
    raw=A.read(G.SOURCE);oldraw=A.read(S.overlay_tool.base.BASE);now=C.inventory(raw);old=C.inventory(oldraw)
    identities=N.SourceNets(raw)
    if C.sha(raw)!=A.SOURCE_SHA or recipe['source_sha256']!=A.SOURCE_SHA:raise ValueError('Frozen source differs')
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    old_parts={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    deletes=set(p['delete_copper_uuids']);chunks={u:ch for u,ch in now[4].items() if u not in deletes};added=set()
    for route in p['routes']:
        for a,b in zip(route['points_mm'],route['points_mm'][1:]):
            u,ch=identities.serial_segment(route['net'],route['layer'],a,b,route['width_mm'])
            if u in chunks:raise ValueError('New copper UUID collision')
            chunks[u]=ch;added.add(u)
    sourcefp=now[3][p['footprint_uuid']]
    if b'(property "Reference" "C11068"' not in sourcefp or b'(layer "F.Cu")' not in sourcefp or b'(at 318.788 52.6 -90)' not in sourcefp:
        raise ValueError('Source footprint identity/pose differs')
    expected=moved=B.move(template,p['target_pose']['xy_mm'],p['target_pose']['angle_degrees'])
    pads=[r for r in moved['pads'] if r['ref']=='C11068']
    for pad,wanted in zip(pads,p['expected_pads']):
        if (pad['uuid'],pad['num'],pad['net'])!=(wanted['uuid'],wanted['num'],wanted['net']) or math.dist((pad['x'],pad['y']),wanted['at_mm'])>1e-9:
            raise ValueError('Expected native transformed pad identity/pose differs')
        if pad['layers']!=wanted['layers']:raise ValueError('Frozen expected pad polygons differ')
    reserve,exempt=A.reservations();print('AUX_CAP_AUDIT_CURRENT_MODEL',flush=True);oldg=identities.geometry(now[4],template);base=S.Model(oldg,reserve,exempt)
    failures,checks,old_uf,old_groups=A.relationships(base,masks,parts,NETS)
    if failures or not all(c['exact_native_partition_match'] for c in checks):raise ValueError('Fresh current native affected-pad partition mismatch')
    print('AUX_CAP_AUDIT_FINAL_MODEL',flush=True);newg=identities.geometry(chunks,moved);model=S.Model(newg,reserve,exempt)
    failures,final_checks,new_uf,new_groups=A.relationships(model,masks,parts,NETS)
    for net in NETS:
        for rel in old_parts[net]:
            if len({new_uf[net].find(('p',pid)) for pid in rel})>1:failures.append({'net':net,'baseline':'r06','relationship':rel})
    obligations=[];contact_loss=[];boundary=[]
    for net,groups in old_groups.items():
        for group in groups:
            keys=sorted({r['key'] for r in group['records'] if r['uuid'] not in deletes})
            roots={new_uf[net].find(key) for key in keys}
            obligation={'net':net,'surviving_physical_keys':[list(k) for k in keys],'candidate_component_count':len(roots)}
            obligations.append(obligation)
            if len(roots)>1:contact_loss.append(obligation)
        for r in base.own[net]:
            if r['uuid'] not in deletes and not (r['kind']=='pad' and r['pad_id'].startswith('C11068.')):continue
            for b in base.own[net]:
                if b['uuid'] in deletes or b['uuid']==r['uuid'] or b['layer']!=r['layer']:continue
                if b['kind']=='via' and b['layer'] not in masks[b['uuid']]:continue
                if r['shape'].distance(b['shape'])<=.000002:
                    boundary.append({'owned_old_item_uuid':r['uuid'],'kind':r['kind'],'surviving_key':list(b['key']),'layer':r['layer'],'gap_mm':r['shape'].distance(b['shape'])})
    parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added};errors,rows,anti=A.clearance(model,parsed,added,set())
    pad_errors,minimum=L.pad_clearance(pads,model)
    court=unary_union(S.poly(next(f for f in moved['footprints'] if f['ref']=='C11068')['courtyard']['B']))
    overlaps=[]
    for other in moved['footprints']:
        if other['ref']=='C11068' or 'B' not in other['courtyard']:continue
        area=court.intersection(unary_union(S.poly(other['courtyard']['B']))).area
        if area>1e-10:overlaps.append({'ref':other['ref'],'area_mm2':area})
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen read changed '+q)
    result={'schema':'aux-cap-native-operation-independent-host-audit-r1','verdict':'HOST_OPERATION_AUDIT_PASS_NATIVE_FLIP_ELECTRICAL_OPEN' if not failures and not contact_loss and not errors and not pad_errors and not overlaps else 'HOST_OPERATION_AUDIT_FAILED',
            'source_sha256':A.SOURCE_SHA,'recipe_sha256':C.sha((HERE/'aux-cap-bside-r4-exact-native-nets.json').read_bytes()),'native_pad_fill_proof':proof,
            'owned_source_footprint':{'uuid':p['footprint_uuid'],'sha256':C.sha(sourcefp),'ref':'C11068','source_pose':[318.788,52.6,-90],'source_side':'F.Cu','target_side':'B.Cu','target_pose':p['target_pose'],
                                      'native_UUID_net_value_local_dimensions_and_actual_transformed_polygons_attestation':'MANDATORY'},
            'deleted_items':[{'uuid':u,'sha256':C.sha(now[4][u]),'net':S.norm(S.overlay_tool.netname(now[4][u]))} for u in sorted(deletes)],
            'added_items':[{'uuid':u,'sha256':C.sha(chunks[u]),'exact_serialized_chunk':chunks[u].decode()} for u in sorted(added)],
            'current_native_pad_graph_verification':checks,'candidate_pad_graph_checks':final_checks,'pad_relationship_failures':failures,
            'surviving_physical_component_obligations':obligations,'surviving_contact_losses':contact_loss,'removed_or_moved_to_surviving_contacts':boundary,
            'clearance_errors':errors,'changed_item_clearance_rows':rows,'moved_pad_clearance_errors':pad_errors,'minimum_moved_pad_gap_by_kind_mm':minimum,'courtyard_overlap':overlaps,
            'source_copper_definitions_outside_owned_footprint_and_deleted_items':'BYTE_EXACT_RETAINED_IN_OPERATION_RECIPE','new_vias':0,'plane_changes':0,
            'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,'seconds':time.time()-start,
            'open_gates':['Actual native C11068 flip/pose/frozen pad polygons and protected UUID/net/value/dimensions attestation','Fresh full native board ordinary DRC and complete dual-r06/live no-loss gates','Complete local TPS26624 RTN/support/thermal/current/drop/source electrical review; no FIELD_GND substitution']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':result['verdict'],'pad_loss':len(failures),'contact_loss':len(contact_loss),'clearance_errors':len(errors),'moved_pad_errors':len(pad_errors),'receipt':str(out)}),flush=True)
if __name__=='__main__':main()
