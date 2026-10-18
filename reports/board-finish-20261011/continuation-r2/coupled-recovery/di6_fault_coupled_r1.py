"""DI6 recovery using exact existing fault vias and a single owned blocker.

This is an isolated host constructor. It preserves sources, exact net tokens,
current/r06 pad relationships and surviving copper contacts. No native/GPU jobs.
The original DI6 via at114.65/119.45 is withheld because the actual unchanged
DI6 via113.95/119.35 is only .7071mm away; the old In3 end is spliced to it.
"""
import itertools,json,math,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
import incremental_exact_model as I
import prospective_B_ground as B
import xf_continuous_landings_r6 as X
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C=A.P,A.G,A.S,A.C
DI='/motherboard_di/DI6_LOGIC'
FAULT='/motherboard_io_control/DI_SENSOR_G2_FAULT'
GND='/LOGIC_GND'
WITHHELD='583bf99d-e1f6-45d5-a5cc-692686cd56e9'
BLOCKER='db89a07d-09fb-4801-ad1a-7d84f421f166'
EXISTING_SIGNALS={
 '0ff4e506-7bc1-48ad-91fd-aeb598e74c7a':(DI,[113.95,119.35]),
 'e0c0b3b3-b357-4427-99c2-632157b04835':(FAULT,[114.25,99.55]),
 'd6a4b719-eff0-4abc-b59a-62f40bae6995':(FAULT,[120.05,99.95])}
EXISTING_RETURNS={
 'cb1390c8-49e9-4971-9ee8-740c03e5b93f':[113.4,120.15],
 '6eab194c-39c0-4f9d-bf29-4b2390dc97b7':[113.971786,98.788714]}

def serial_ground(at):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-coupled-DI6-fault-r1-ground/'+repr(at)))
    f=lambda x:format(x,'.9f').rstrip('0').rstrip('.')
    return uid,(f'\t(via\n\t\t(at {f(at[0])} {f(at[1])})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "/LOGIC_GND")\n\t\t(uuid "{uid}")\n\t)\n').encode()

def aperture(model,parsed):
    pads=[r for rs in model.records.values() for r in rs if r['kind']=='pad' and model.pads[r['pad_id']]['smd']]
    tree=STRtree([r['shape'] for r in pads]);rows=[]
    for uid,z in parsed.items():
        if z['kind']!='via':continue
        p=Point(z['at']);r=pads[int(tree.nearest(p))]
        gap=p.distance(r['shape'])-z['drill']/2-.005
        rows.append({'uuid':uid,'minimum_drill_SMD_gap_after_005_export_error_mm':gap,'required_with_guard_mm':.275,'nearest_pad':r['pad_id'],'net':r['net'],'layer':r['layer']})
    return rows,[r for r in rows if r['minimum_drill_SMD_gap_after_005_export_error_mm']<.275]

def main():
    started=time.time();output=HERE/'di6-fault-coupled-r1.json'
    if output.exists():raise ValueError('Fresh receipt required')
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE))
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen source differs')
    identity=N.SourceNets(raw);native=json.loads(A.read(A.NATIVE/'geometry.json'))
    template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    prior={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    policy=json.loads(A.read(G.REPORT/'controlled-geometry/controlled-net-map.json'))
    if any(policy.get(n,{}).get('class') not in (None,'NONE') for n in (DI,FAULT)):raise ValueError('Ordinary route policy differs')
    graph=json.loads(A.read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==DI)
    if set(row['blocking_nets'][FAULT]['item_uuids'])!={BLOCKER}:raise ValueError('Direct blocker ownership differs')
    restored={z['uuid'] for z in row['missing_original_items']}-{WITHHELD}
    if len(restored)!=19 or WITHHELD not in old[4]:raise ValueError('Original recovery inventory differs')
    reserve,exempt=A.reservations();zone_clearance=B.zone_clearances(now)
    frozen_rules=A.read(G.SOURCE.with_suffix('.kicad_dru'))
    print('DI6_FAULT_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    source_errors,checks,_,groups=A.relationships(base,source_masks,parts,(DI,FAULT))
    if source_errors or not all(z['exact_native_partition_match'] for z in checks):raise ValueError('Exact source partitions differ')
    for uid,(net,at) in EXISTING_SIGNALS.items():
        v=next(v for v in base.g['vias'] if v['uuid']==uid)
        if (v['net'],v['x'],v['y'],v['d'],v['drill'])!=(net,*at,.6,.3) or not set(template['copper_layers'])<=source_masks[uid]:raise ValueError('Existing exact signal annuli differ')
    for uid,at in EXISTING_RETURNS.items():
        v=next(v for v in base.g['vias'] if v['uuid']==uid)
        if (v['net'],v['x'],v['y'])!=(GND,*at) or not {'In1.Cu','In4.Cu'}<=source_masks[uid]:raise ValueError('Existing exact return differs')
    old_via=G.parse(WITHHELD,old[4][WITHHELD],{})
    pitch_conflict={'withheld_uuid':WITHHELD,'original_at_mm':old_via['at'],'unchanged_actual_via_uuid':next(iter(EXISTING_SIGNALS)),'unchanged_at_mm':EXISTING_SIGNALS[next(iter(EXISTING_SIGNALS))][1],'pitch_mm':math.dist(old_via['at'],EXISTING_SIGNALS[next(iter(EXISTING_SIGNALS))][1]),'required_mm':.8}
    initial={u:ch for u,ch in now[4].items() if u!=BLOCKER};initial.update({u:old[4][u] for u in restored})
    masks=dict(source_masks);restore_parsed={u:G.parse(u,initial[u],{}) for u in restored}
    signals=[{'uuid':u,'net':r['net'],'at_mm':r['at']} for u,r in restore_parsed.items() if r['kind']=='via']
    if len(signals)!=3:raise ValueError('Expected three restored ordinary DI6 vias')
    for r in signals:masks[r['uuid']]=set(template['copper_layers'])
    signals.append({'uuid':'d6a4b719-eff0-4abc-b59a-62f40bae6995','net':FAULT,'at_mm':[120.05,99.95]})
    cuts=[r['at_mm'] for r in signals]+[[114.25,99.55],[113.95,119.35]]
    model=F.Model(identity.geometry(initial,template),reserve,exempt,native['vias'],source_masks)
    early_errors,early_clear,early_antipads=A.clearance(model,restore_parsed,set(),restored)
    early_aperture,early_aperture_errors=aperture(model,restore_parsed)
    choices=[];initial_refs,witness=X.refs_after(model,masks,cuts)
    if not early_errors and not early_aperture_errors:
        all_smd=unary_union([z['shape'] for rs in model.records.values() for z in rs if z['kind']=='pad' and model.pads[z['pad_id']]['smd']])
        for signal in signals:
            at=signal['at_mm'];window=Point(at).buffer(2).envelope
            free,_=B.freevia(model,GND,window)
            region=free.intersection(Point(at).buffer(1.,resolution=128).difference(Point(at).buffer(.825,resolution=128)))
            region=region.intersection(initial_refs['F.Cu']).intersection(initial_refs['B.Cu']).difference(all_smd.buffer(.1+.275+.005,resolution=128))
            choices.append([dict(x,signal=signal) for x in X.sites(region,[at[0]+.9,at[1]],2)])
    attempts=[];emitted=None
    for ci,choice in enumerate(itertools.product(*choices) if choices and all(choices) else []):
        if ci>=16:break
        print('DI6_FAULT_COMBINATION',ci,flush=True)
        chunks=dict(initial);added=set();cmasks=dict(masks)
        for item in choice:
            u,ch=serial_ground(item['at_mm']);chunks[u]=ch;added.add(u);cmasks[u]=set(template['copper_layers'])
        candidate=I.append(model,{u:chunks[u] for u in added},identity)
        refs,reference_witness=X.refs_after(candidate,cmasks,cuts)
        attempt={'returns':list(choice),'paths':[],'searches':[]};attempts.append(attempt)
        return_rows=[]
        for sig,ret in [(z['signal']['at_mm'],z['at_mm']) for z in choice]+[([113.95,119.35],[113.4,120.15]),([114.25,99.55],[113.971786,98.788714])]:
            v=next(v for v in candidate.g['vias'] if v['net']==GND and (v['x'],v['y'])==tuple(ret))
            annulus=Point(ret).buffer(v['d']/2,resolution=128).difference(Point(ret).buffer(v['drill']/2,resolution=128))
            return_rows.append({'signal_at_mm':sig,'return_at_mm':ret,'return_uuid':v['uuid'],'distance_mm':math.dist(sig,ret),'source_contacts':{l:refs[l].intersects(annulus) for l in ('F.Cu','B.Cu')}})
        attempt['return_checks']=return_rows
        if not all(.8<=z['distance_mm']<=1. and all(z['source_contacts'].values()) for z in return_rows):continue
        for net,layer,a,b in ((FAULT,'B.Cu',[114.25,99.55],[120.05,99.95]),(DI,'In3.Cu',[113.95,119.35],[114.65,119.45])):
            window=LineString([a,b]).envelope.buffer(6,cap_style=3).envelope
            void=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+.175,resolution=128) for v in candidate.g['vias'] if v['net']==net and [v['x'],v['y']] in cuts])
            free,_=B.free(candidate,net,layer,window);strict=free.intersection(refs[layer].union(void).buffer(-.1))
            seed=[[((tuple(p)),{'uuid':'exact owned splice','kind':'track'})] if strict.covers(Point(p)) else [] for p in (a,b)]
            path,search=S.astar(strict,*seed,time.monotonic()+12,node_cap=150000) if all(seed) else (None,{'reason':'No exact full-body referenced splice'})
            attempt['searches'].append({'net':net,'layer':layer,'from_mm':a,'to_mm':b,**search})
            if not path:break
            path.update(net=net,layer=layer,width_mm=.2,new_items=[])
            for p,q in zip(path['points_mm'],path['points_mm'][1:]):
                u,ch=identity.serial_segment(net,layer,p,q,.2);chunks[u]=ch;added.add(u);path['new_items'].append(u)
            attempt['paths'].append(path)
        if len(attempt['paths'])!=2:continue
        candidate=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],source_masks)
        losses=[];contact_losses=[];obligations=[];boundary=[]
        for net in (DI,FAULT):
            uf,_=P.physical(candidate,net,cmasks)
            for label,relations in (('current198b',parts[net]),('r06',prior[net])):
                for relation in relations:
                    if len({uf.find(('p',p)) for p in relation})>1:losses.append({'net':net,'baseline':label,'pads':relation})
            for group in groups[net]:
                keys=sorted({r['key'] for r in group['records'] if r['uuid']!=BLOCKER});count=len({uf.find(k) for k in keys})
                item={'net':net,'surviving_keys':[list(k) for k in keys],'candidate_component_count':count};obligations.append(item)
                if count>1:contact_losses.append(item)
        for a in base.own[FAULT]:
            if a['uuid']!=BLOCKER:continue
            for b in base.own[FAULT]:
                if b['uuid']==BLOCKER or b['layer']!=a['layer'] or (b['kind']=='via' and b['layer'] not in source_masks[b['uuid']]):continue
                if a['shape'].distance(b['shape'])<=.000002:boundary.append({'removed_uuid':BLOCKER,'surviving_key':list(b['key']),'layer':a['layer']})
        parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restored}
        candidate,fill_ledger,fill_errors=B.retreat(candidate,parsed,added|restored,cmasks,zone_clearance,base)
        errors,clear,anti=A.clearance(candidate,parsed,added,restored);ap,ap_errors=aperture(candidate,parsed)
        refs,reference_witness=X.refs_after(candidate,cmasks,cuts);reference=[]
        for u,z in parsed.items():
            if z['kind']!='segment':continue
            void=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+.175,resolution=128) for v in candidate.g['vias'] if v['net']==z['net'] and [v['x'],v['y']] in cuts])
            gap=LineString([z['a'],z['b']]).buffer(z['w']/2,resolution=128).difference(void).difference(refs[z['layer']]).area
            reference.append({'uuid':u,'net':z['net'],'layer':z['layer'],'full_copper_uncovered_mm2':gap})
        attempt.update(pad_relationship_losses=losses,surviving_contact_losses=contact_losses,surviving_contact_obligations=obligations,removed_to_surviving_contacts=boundary,clearance_errors=errors,changed_item_clearance=clear,prospective_antipads=anti,prospective_ground_fill_contact_ledger=fill_ledger,prospective_ground_fill_errors=fill_errors,full_body_reference_checks=reference,ordinary_SMD_aperture=ap,ordinary_SMD_aperture_errors=ap_errors,source_reference_witness=reference_witness)
        if errors or losses or contact_losses or fill_errors or ap_errors or any(z['full_copper_uncovered_mm2']>1e-9 for z in reference):continue
        cand=now[0]+b''.join(ch for ch in now[1] if C.pcbtext.chunk_uuid(ch)!=BLOCKER)+b''.join(ch for u,ch in chunks.items() if u not in now[4])+now[2];inv=C.inventory(cand)
        if inv[5]!=now[5] or any(inv[3].get(u)!=ch for u,ch in now[3].items() if u!=BLOCKER):raise ValueError('Untouched exact entity differs')
        identity.assert_no_collisions(cand);emitted=HERE/'di6-fault-coupled-r1-host-only.kicad_pcb';emitted.write_bytes(cand);attempt['candidate_sha256']=C.sha(cand);break
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen read changed '+q)
    result={'schema':'di6-fault-coupled-r1','verdict':'HOST_CANDIDATE_INDEPENDENT_NATIVE_ELECTRICAL_OPEN' if emitted else 'BOUNDED_COUPLED_PLAN_INCOMPLETE','source_sha256':C.sha(raw),'source_native_geometry_proof':proof,'source_actual_annuli':base.source_annulus_proof,'native_partition_checks':checks,'exact_ordinary_policy':{n:policy.get(n) for n in (DI,FAULT)},'deleted_owned_items':[BLOCKER],'restored_original_items':sorted(restored),'withheld_original_via_pitch_conflict':pitch_conflict,'existing_signal_identity':EXISTING_SIGNALS,'existing_return_identity':EXISTING_RETURNS,'initial_clearance_errors':early_errors,'initial_changed_item_clearance':early_clear,'initial_aperture':early_aperture,'initial_aperture_errors':early_aperture_errors,'signal_return_choices':choices,'attempts':attempts,'candidate':str(emitted) if emitted else None,'frozen_rules_sha256':C.sha(frozen_rules),'prospective_zone_clearances_mm':zone_clearance,'read_files_sha256':A.READS,'seconds':time.time()-started,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'open_gates':['Separate full serialized constructor audit','Exact native new/restored annuli and net identity, full fresh refill/DRC and both complete no-loss guards','Current-function electrical/edge/load/timing/return/DFM review']}
    output.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':result['verdict'],'candidate':result['candidate'],'receipt':str(output)}),flush=True)
if __name__=='__main__':main()
