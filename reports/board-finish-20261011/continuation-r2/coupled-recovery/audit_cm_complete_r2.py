"""Independent full serialized CM candidate audit, no native/project writes."""
import json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
import cm_coupled_returns_r2 as T
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree
P,G,S,C=A.P,A.G,A.S,A.C
CLK,MOSI,GND=T.CLK,T.MOSI,T.GND

def exact_drilled_references(model,masks,cuts):
    hole_shapes=[Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128) for v in model.g['vias']]+[shape for pad in model.g['pads'] for shape in S.poly(pad.get('hole') or [])]
    holes=unary_union(hole_shapes);hole_tree=STRtree(hole_shapes)
    antipads=unary_union([Point(p).buffer(d/2+.175,resolution=128) for p,d in cuts]);refs={};witness={}
    for layer,plane in (('F.Cu','In1.Cu'),('B.Cu','In4.Cu')):
        fill=unary_union([z['shape'] for z in model.records[plane] if z['kind']=='fill' and z['net']==GND]).difference(holes).difference(antipads)
        copper=[];filled=prep(fill)
        for z in model.records[plane]:
            if z['net']!=GND or z['kind'] not in ('pad','track','via'):continue
            if z['kind']=='via' and plane not in masks.get(z['uuid'],set()):continue
            nearby_holes=unary_union([hole_shapes[i] for i in hole_tree.query(z['shape'],predicate='intersects')])
            metal=z['shape'].difference(nearby_holes)
            if not filled.covers(metal):copper.append(metal.difference(fill))
        connected=unary_union([fill]+copper);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane])).difference(holes)
        rooted=unary_union([part for part in P.K.D.components(connected) if part.intersects(anchor)])
        refs[layer]=fill.intersection(rooted);witness[plane]={'source_pad':'J11001.2#0','actual_drill_holes_subtracted':True,'prospective_signal_antipads':cuts,'source_connected_fill_area_mm2':refs[layer].area,'new_return_annuli_expected_all6_but_native_actual_open':True}
    refs['In3.Cu']=refs['B.Cu']
    return refs,witness

def main():
    arg=sys.argv[1] if len(sys.argv)>1 else 'r2'
    receipt=HERE/f'cm-coupled-returns-{arg}.json';out=HERE/f'cm-complete-independent-audit-{arg}-r2.json'
    if out.exists():raise ValueError('Fresh independent audit output required')
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    r=json.loads(A.read(receipt))
    if not r.get('candidate'):raise ValueError('A concrete emitted candidate is required')
    attempt=next(a for a in r['attempts'] if a.get('candidate_sha256'))
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    cand_raw=A.read(Path(r['candidate']));cand=C.inventory(cand_raw)
    if C.sha(cand_raw)!=attempt['candidate_sha256']:raise ValueError('Constructor candidate hash differs')
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    removed=set(now[4])-set(cand[4]);added=set(cand[4])-set(now[4]);changed={u for u,ch in now[4].items() if u in cand[4] and cand[4][u]!=ch}
    expected_removed=set(r['deleted_owned_items']);restores={v['uuid'] for v in r['restored_via_exact_flags_annuli']}
    if removed!=expected_removed or changed or cand[0]!=now[0] or cand[2]!=now[2] or cand[5]!=now[5]:raise ValueError('Candidate source parity ownership differs')
    if any(cand[3].get(u)!=ch for u,ch in now[3].items() if u not in removed):raise ValueError('An untouched top-level entity differs')
    identity.assert_no_collisions(cand_raw);identity.assert_chunks(cand[4])
    for u in restores:
        if cand[4][u]!=old[4][u]:raise ValueError('Restored clock via exact original chunk differs')
    parsed={u:G.parse(u,cand[4][u],{}) for u in added}
    masks=dict(source_masks)
    for u in added:
        if parsed[u]['kind']=='via':masks[u]=set(template['copper_layers'])
    reserve,exempt=A.reservations();print('CM_COMPLETE_INDEPENDENT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    print('CM_COMPLETE_INDEPENDENT_CANDIDATE_MODEL',flush=True)
    candidate=F.Model(identity.geometry(cand[4],template),reserve,exempt,native['vias'],source_masks)
    errors,clear,anti=A.clearance(candidate,parsed,added-restores,restores)
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    oldparts={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    source_losses,source_checks,_,basegroups=A.relationships(base,source_masks,parts,(CLK,MOSI))
    if source_losses or not all(z['exact_native_partition_match'] for z in source_checks):raise ValueError('Independent full source differs from native partitions')
    losses=[];contacts=[];obligations=[];boundary=[];groups_after={}
    for net in (CLK,MOSI):
        uf,groups=P.physical(candidate,net,masks);groups_after[net]=[z['pad_ids'] for z in groups if z['pad_ids']]
        for label,rels in (('current198b',parts[net]),('r06',oldparts[net])):
            for rel in rels:
                if len({uf.find(('p',p)) for p in rel})>1:losses.append({'net':net,'baseline':label,'relationship':rel})
        for group in basegroups[net]:
            keys=sorted({z['key'] for z in group['records'] if z['uuid'] not in removed});count=len({uf.find(k) for k in keys})
            row={'net':net,'surviving_keys':[list(k) for k in keys],'component_count':count};obligations.append(row)
            if count>1:contacts.append(row)
        for z in base.own[net]:
            if z['uuid'] not in removed:continue
            for b in base.own[net]:
                if b['uuid'] in removed or b['layer']!=z['layer']:continue
                if b['kind']=='via' and b['layer'] not in source_masks[b['uuid']]:continue
                if z['shape'].distance(b['shape'])<=.000002:boundary.append({'removed_uuid':z['uuid'],'surviving_key':list(b['key']),'layer':z['layer']})
    fixed_transitions=[row['signal'] for row in r['fixed_transition_return_sites']]
    cuts=[(v['at_mm'],v['d_mm']) for v in fixed_transitions]
    mosi_new=[v for v in candidate.g['vias'] if v['uuid'] in added-restores and v['net']==MOSI]
    if len(mosi_new)!=1:raise ValueError('Expected exactly one new ordinary MOSI dive')
    cuts.append(([mosi_new[0]['x'],mosi_new[0]['y']],mosi_new[0]['d']))
    refs,witness=exact_drilled_references(candidate,masks,cuts)
    own_clock_unref=unary_union([Point(v['at_mm']).buffer(v['d_mm']/2+.175,resolution=128) for v in fixed_transitions if v['net']==CLK])
    own_mosi_unref=unary_union([Point(p).buffer(d/2+.175,resolution=128) for p,d in cuts if p not in [v['at_mm'] for v in fixed_transitions if v['net']==CLK]])
    if r.get('unchanged_MOSI_In3_splice'):
        splice=r['unchanged_MOSI_In3_splice'];sv=next(v for v in candidate.g['vias'] if v['uuid']==splice['uuid'])
        if (sv['net'],sv['x'],sv['y'],sv['d'])!=(MOSI,splice['at_mm'][0],splice['at_mm'][1],splice['d_mm']) or 'In3.Cu' not in source_masks[sv['uuid']]:raise ValueError('Actual unchanged same-layer MOSI splice differs')
        policy=json.loads(A.read(S.CONTROLLED))['nets'];mp=next(value for key,value in policy.items() if S.norm(key)==MOSI)
        if mp.get('class')!='NONE' or mp!=r['exact_frozen_MOSI_controlled_policy']:raise ValueError('Independent exact ordinary MOSI policy differs')
        own_mosi_unref=own_mosi_unref.union(Point(splice['at_mm']).buffer(splice['d_mm']/2+.175,resolution=128))
    refs_checks=[]
    for u,z in parsed.items():
        if z['kind']!='segment':continue
        unref=own_clock_unref if z['net']==CLK else own_mosi_unref
        body=LineString([z['a'],z['b']]).buffer(z['w']/2,resolution=128)
        refs_checks.append({'uuid':u,'net':z['net'],'layer':z['layer'],'width_mm':z['w'],'full_copper_uncovered_mm2':body.difference(unref).difference(refs[z['layer']]).area})
    returns=[]
    for check in attempt['return_checks']:
        sig=check['signal_mm'];ret=check['return_mm'];match=[v for v in candidate.g['vias'] if v['net']==GND and (v['x'],v['y'])==tuple(ret)]
        if len(match)!=1:raise ValueError('Exact constructed return via is not unique')
        v=match[0];ann=Point(ret).buffer(v['d']/2,resolution=128).difference(Point(ret).buffer(v['drill']/2,resolution=128))
        contacts_plane={layer:refs[layer].intersects(ann) for layer in ('F.Cu','B.Cu')}
        returns.append({'signal_mm':sig,'return_mm':ret,'uuid':v['uuid'],'distance_mm':math.dist(sig,ret),'source_connected_actual_plane_contacts_host':contacts_plane,'new_actual_native_annuli':'OPEN'})
    profile=json.loads(A.read(HERE/'cm-terminal-profile-r1/proposal.json'))
    neck_uuid=profile['exact_selected_neck_uuid'];neck=parsed[neck_uuid]
    exact_pad=next(p for p in candidate.g['pads'] if p['uuid']==profile['exact_selected_pad']['uuid'])
    if (exact_pad['ref'],exact_pad['num'],exact_pad['net'],exact_pad['x'],exact_pad['y'])!=('J15001','25',profile['native_raw_net'],128.252,167.175):raise ValueError('Scoped native pad binding differs')
    neck_length=math.dist(neck['a'],neck['b']);neck_body=LineString([neck['a'],neck['b']]).buffer(.1,resolution=128)
    controlled_errors=[]
    for u,z in parsed.items():
        if z['net']!=CLK or z['kind']!='segment':continue
        if u==neck_uuid:
            if z['w']!=.2 or z['layer']!='F.Cu' or abs(neck_length-1.225)>1e-9 or not Polygon(profile['terminal_region_polygon_mm']).covers(neck_body):controlled_errors.append({'uuid':u,'reason':'Exact isolated terminal scope mismatch'})
        elif z['w']!=.385 or z['layer'] not in ('F.Cu','B.Cu'):controlled_errors.append({'uuid':u,'reason':'Outer provisional controlled bulk mismatch'})
    return_bad=[z for z in returns if not .8<=z['distance_mm']<=1. or not all(z['source_connected_actual_plane_contacts_host'].values())]
    ref_bad=[z for z in refs_checks if z['full_copper_uncovered_mm2']>1e-9]
    passed=not(errors or losses or contacts or ref_bad or return_bad or controlled_errors)
    report={'schema':'independent-full-cm-audit-r1','verdict':'HOST_COMPLETE_CANDIDATE_AUDIT_PASS_NATIVE_SI_OPEN' if passed else 'HOST_COMPLETE_CANDIDATE_AUDIT_FAIL','source_sha256':C.sha(raw),'candidate_sha256':C.sha(cand_raw),'native_geometry_provenance':proof,'source_actual_annuli':base.source_annulus_proof,'candidate_conservative_all6_new_restored_annuli':candidate.source_annulus_proof,'exact_native_source_partition_checks':source_checks,'removed_owned_uuids':sorted(removed),'added_uuids':sorted(added),'all_untouched_top_level_entities_byte_exact':True,'normalized_raw_net_collisions':identity.assert_no_collisions(cand_raw),'same_uuid_mutations':sorted(changed),'pad_relationship_failures':losses,'surviving_contacts_failures':contacts,'all_surviving_contact_obligations':obligations,'deleted_to_retained_contact_boundary':boundary,'new_pad_groups':groups_after,'changed_item_clearance_errors':errors,'changed_item_clearance':clear,'prospective_antipads':anti,'full_copper_reference_checks':refs_checks,'reference_errors':ref_bad,'source_connected_reference_witness':witness,'ordinary_return_checks':returns,'return_errors':return_bad,'controlled_bulk_and_scoped_terminal_errors':controlled_errors,'selected_neck_length_mm':neck_length,'mathematical_neck_discontinuity':profile['mathematical_neck_discontinuity'],'profile_proposal_sha256':C.sha((HERE/'cm-terminal-profile-r1/proposal.json').read_bytes()),'all_original_project_rules_preserved':True,'new_profile_installed':False,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Native exact new/restored six-layer annuli, full refill/ordinary DRC, current/r07/r06 all-net no-loss','Native source-connected candidate references after all holes/antipads, full LOGIC_GND no-loss','Isolated named area/rules native parse and exact effective bulk/terminal constraints','Actual extracted edge/bus/pad/load/neck/current manufacturing qualification'],'read_files_sha256':A.READS}
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen source/helper changed '+q)
    out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'audit':str(out),'verdict':report['verdict'],'clearance':len(errors),'pad_losses':len(losses),'contacts':len(contacts),'reference':len(ref_bad),'returns':len(return_bad),'controlled':len(controlled_errors)}),flush=True)
if __name__=='__main__':main()
