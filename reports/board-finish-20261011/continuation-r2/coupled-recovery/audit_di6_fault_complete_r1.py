"""Independent exact serialized DI6/fault coupled candidate audit; host only."""
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
DI='/motherboard_di/DI6_LOGIC';FAULT='/motherboard_io_control/DI_SENSOR_G2_FAULT';GND='/LOGIC_GND'
BLOCKER='db89a07d-09fb-4801-ad1a-7d84f421f166'
WITHHELD='583bf99d-e1f6-45d5-a5cc-692686cd56e9'
FIXED={
 '0ff4e506-7bc1-48ad-91fd-aeb598e74c7a':(DI,[113.95,119.35]),
 'e0c0b3b3-b357-4427-99c2-632157b04835':(FAULT,[114.25,99.55]),
 'd6a4b719-eff0-4abc-b59a-62f40bae6995':(FAULT,[120.05,99.95])}

def main():
    out=HERE/'di6-fault-complete-independent-audit-r1.json'
    if out.exists():raise ValueError('Fresh independent receipt required')
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    recipe=json.loads(A.read(HERE/'di6-fault-coupled-r1.json'))
    if not recipe.get('candidate'):raise ValueError('Concrete candidate required')
    successful=next(z for z in recipe['attempts'] if z.get('candidate_sha256'))
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    candidate_raw=A.read(recipe['candidate']);inv=C.inventory(candidate_raw)
    if C.sha(raw)!=A.SOURCE_SHA or C.sha(candidate_raw)!=successful['candidate_sha256']:raise ValueError('Frozen source/candidate differs')
    removed=set(now[4])-set(inv[4]);added=set(inv[4])-set(now[4]);modified={u for u,ch in now[4].items() if u in inv[4] and ch!=inv[4][u]}
    restored=set(recipe['restored_original_items'])
    if removed!={BLOCKER} or modified or inv[0]!=now[0] or inv[2]!=now[2] or inv[5]!=now[5]:raise ValueError('Exact single-blocker ownership differs')
    if len(restored)!=19 or WITHHELD in inv[4] or any(inv[4][u]!=old[4][u] for u in restored):raise ValueError('Exact original recovery/withheld inventory differs')
    if any(inv[3].get(u)!=ch for u,ch in now[3].items() if u!=BLOCKER):raise ValueError('Untouched exact entity differs')
    identity.assert_no_collisions(candidate_raw);identity.assert_chunks(inv[4])
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(source_masks)
    parsed={u:G.parse(u,inv[4][u],{}) for u in added};new_ground=[];restored_signal=[]
    for u,z in parsed.items():
        if z['kind']=='via':
            if u in restored:
                if (z['net'],z['d'],z['drill'])!=(DI,.6,.3):raise ValueError('Restored ordinary via identity differs')
                restored_signal.append(u)
            else:
                if (z['net'],z['d'],z['drill'])!=(GND,.5,.2):raise ValueError('Unexpected new ordinary via')
                new_ground.append(u)
            masks[u]=set(template['copper_layers'])
    if len(new_ground)!=4 or len(restored_signal)!=3:raise ValueError('Expected four new GND and three restored signal vias')
    policy=json.loads(A.read(G.REPORT/'controlled-geometry/controlled-net-map.json'))
    if any(policy.get(n,{}).get('class') not in (None,'NONE') for n in (DI,FAULT)):raise ValueError('Exact ordinary policy differs')
    reserve,exempt=A.reservations();print('DI6_INDEPENDENT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    print('DI6_INDEPENDENT_CANDIDATE_MODEL',flush=True)
    candidate=F.Model(identity.geometry(inv[4],template),reserve,exempt,native['vias'],source_masks)
    candidate,fill_ledger,fill_errors=D.independent_ground_retreat(base,candidate,source_masks,now,parsed,added)
    errors,clear,antipads=A.clearance(candidate,parsed,added-restored,restored)
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    source_losses,checks,_,groups=A.relationships(base,source_masks,parts,(DI,FAULT))
    if source_losses or not all(z['exact_native_partition_match'] for z in checks):raise ValueError('Exact source native partition mismatch')
    losses=[];contacts=[];ledger=[];boundary=[]
    for net in (DI,FAULT):
        uf,_=P.physical(candidate,net,masks)
        for label,relations in (('current198b',parts[net]),('r06',prior[net])):
            for relation in relations:
                if len({uf.find(('p',p)) for p in relation})>1:losses.append({'net':net,'baseline':label,'pads':relation})
        for group in groups[net]:
            surviving=sorted({z['key'] for z in group['records'] if z['uuid'] not in removed});count=len({uf.find(k) for k in surviving})
            row={'net':net,'surviving_keys':[list(k) for k in surviving],'candidate_component_count':count};ledger.append(row)
            if count>1:contacts.append(row)
    for a in base.own[FAULT]:
        if a['uuid']!=BLOCKER:continue
        for b in base.own[FAULT]:
            if b['uuid']==BLOCKER or b['layer']!=a['layer'] or (b['kind']=='via' and b['layer'] not in source_masks[b['uuid']]):continue
            if a['shape'].distance(b['shape'])<=.000002:boundary.append({'removed_uuid':BLOCKER,'surviving_key':list(b['key']),'layer':a['layer']})
    fixed_vias=[]
    for uid,(net,at) in FIXED.items():
        v=next(v for v in candidate.g['vias'] if v['uuid']==uid)
        if inv[4][uid]!=now[4][uid] or (v['net'],v['x'],v['y'],v['d'],v['drill'])!=(net,*at,.6,.3) or not set(template['copper_layers'])<=source_masks[uid]:raise ValueError('Actual existing signal landing differs')
        fixed_vias.append(v)
    old=G.parse(WITHHELD,old[4][WITHHELD],{})
    if old['at']!=[114.65,119.45] or math.dist(old['at'],FIXED['0ff4e506-7bc1-48ad-91fd-aeb598e74c7a'][1])>=.8:raise ValueError('Withheld original pitch evidence differs')
    signal_vias=[v for v in candidate.g['vias'] if v['uuid'] in restored_signal]+fixed_vias
    refs,witness=D.exact_drilled_references(candidate,masks,[([v['x'],v['y']],v['d']) for v in signal_vias]);reference=[]
    for uid,z in parsed.items():
        if z['kind']!='segment':continue
        void=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+.175,resolution=128) for v in signal_vias if v['net']==z['net']])
        gap=LineString([z['a'],z['b']]).buffer(z['w']/2,resolution=128).difference(void).difference(refs[z['layer']]).area
        reference.append({'uuid':uid,'net':z['net'],'layer':z['layer'],'width_mm':z['w'],'full_copper_uncovered_mm2':gap})
    returns=[];return_errors=[]
    for row in successful['return_checks']:
        at=row['return_at_mm'];sig=row['signal_at_mm'];v=next(v for v in candidate.g['vias'] if v['net']==GND and (v['x'],v['y'])==tuple(at))
        annulus=Point(at).buffer(v['d']/2,resolution=128).difference(Point(at).buffer(v['drill']/2,resolution=128));distance=math.dist(sig,at)
        planes={l:refs[l].intersects(annulus) for l in ('F.Cu','B.Cu')}
        item={'return_uuid':v['uuid'],'signal_at_mm':sig,'return_at_mm':at,'distance_mm':distance,'source_rooted_plane_contacts':planes,'source_actual_mask':sorted(source_masks[v['uuid']]) if v['uuid'] in source_masks else 'OPEN_NATIVE_CONSERVATIVE_ALL6'}
        if not .8<=distance<=1. or not all(planes.values()) or not {'In1.Cu','In4.Cu'}<=masks[v['uuid']]:return_errors.append(item)
        returns.append(item)
    smd=[r for rs in candidate.records.values() for r in rs if r['kind']=='pad' and candidate.pads[r['pad_id']]['smd']];tree=STRtree([r['shape'] for r in smd]);aperture=[];aperture_errors=[]
    for uid,z in parsed.items():
        if z['kind']!='via':continue
        p=Point(z['at']);r=smd[int(tree.nearest(p))];gap=p.distance(r['shape'])-z['drill']/2-.005
        item={'uuid':uid,'minimum_drill_SMD_gap_after_005_export_error_mm':gap,'required_with_guard_mm':.275,'nearest_pad':r['pad_id'],'net':r['net'],'layer':r['layer'],'source_registry_waivers':0};aperture.append(item)
        if gap<.275:aperture_errors.append(item)
    def ledger_identity(rows):
        return sorted((r['zone_uuid'],r['layer'],r['exact_original_fill_wkb_sha256'],tuple(sorted(r['cut_item_uuids'])),r['candidate_component_count'],tuple(sorted((tuple(z['key']),tuple(z['candidate_piece_indices'])) for z in r['old_existing_physical_contacts']))) for r in rows)
    if ledger_identity(fill_ledger)!=ledger_identity(successful['prospective_ground_fill_contact_ledger']):raise ValueError('Independent prospective plane/contact ledger differs')
    ref_errors=[z for z in reference if z['full_copper_uncovered_mm2']>1e-9]
    passed=not(errors or losses or contacts or fill_errors or return_errors or aperture_errors or ref_errors)
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen input changed '+q)
    report={'schema':'independent-di6-fault-coupled-r1','verdict':'HOST_COMPLETE_CANDIDATE_AUDIT_PASS_NATIVE_ELECTRICAL_OPEN' if passed else 'HOST_COMPLETE_CANDIDATE_AUDIT_FAIL','source_sha256':C.sha(raw),'candidate_sha256':C.sha(candidate_raw),'source_native_pad_geometry_proof':proof,'source_actual_annuli':base.source_annulus_proof,'candidate_conservative_new_restored_annuli':candidate.source_annulus_proof,'source_native_partition_checks':checks,'removed_owned_uuids':sorted(removed),'restored_original_uuids':sorted(restored),'added_uuids':sorted(added),'all_untouched_entities_rules_exact':True,'raw_net_identity':identity.assert_no_collisions(candidate_raw),'ordinary_policy':{n:policy.get(n) for n in (DI,FAULT)},'pad_relationship_losses':losses,'surviving_contact_losses':contacts,'complete_surviving_contact_ledger':ledger,'removed_to_retained_boundary':boundary,'changed_item_clearance_errors':errors,'changed_item_clearance':clear,'prospective_antipads':antipads,'prospective_ground_fill_contact_ledger':fill_ledger,'prospective_ground_fill_errors':fill_errors,'full_body_reference_checks':reference,'reference_errors':ref_errors,'drilled_source_rooted_reference_witness':witness,'qualified_source_return_checks':returns,'return_errors':return_errors,'ordinary_SMD_drill_aperture_checks':aperture,'ordinary_SMD_aperture_errors':aperture_errors,'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Root parent delta comparison and complete merged geometric contact/reference obligations','Native exact actual new/restored vias, fresh full refill/ordinary DRC and both complete no-loss guards','Actual complete electrical/function/edge/load/timing/SI/DFM qualification']}
    out.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':report['verdict'],'receipt':str(out),'pad_losses':len(losses),'contact_losses':len(contacts),'clearance_errors':len(errors),'fill_errors':len(fill_errors),'reference_errors':len(ref_errors),'aperture_errors':len(aperture_errors)}),flush=True)
if __name__=='__main__':main()
