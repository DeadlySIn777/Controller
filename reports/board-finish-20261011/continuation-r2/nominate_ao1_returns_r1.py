"""Bounded AO1 return nomination using exact native source geometry.

Emits an owned operation manifest only. Native and electrical gates remain open.
"""
import copy,hashlib,json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'coupled-recovery'))
import audit_ao1_positive_operation_r2 as Q
A,P,G,S,C,F,N=Q.A,Q.P,Q.G,Q.S,Q.C,Q.F,Q.N
from shapely.geometry import Point
from shapely.strtree import STRtree
OUT=HERE/'ao1-return-nomination-r1'

def write(name,data):
    (OUT/name).write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')

def add_returns(model,rows,identity):
    out=copy.copy(model);out.g=dict(model.g);out.g['vias']=list(model.g['vias'])
    out.records={layer:list(records) for layer,records in model.records.items()}
    out.own={net:list(records) for net,records in model.own.items()}
    parsed={};chunks={};masks={}
    for row in rows:
        at=tuple(row['at_mm']);u,ch=Q.serial_via(identity,Q.COM,at)
        chunks[u]=ch;parsed[u]=G.parse(u,ch,{})
        p=Point(at);out.g['vias'].append({'uuid':u,'net':identity.raw(Q.COM),'x':at[0],'y':at[1],'d':.5,'drill':.2,'span':['F.Cu','B.Cu'],'flashed':list(model.g['copper_layers'])})
        masks[u]=set(model.g['copper_layers'])
        for layer in model.g['copper_layers']:
            rec={'shape':p.buffer(.25,resolution=128),'net':Q.COM,'domain':model.domains[Q.COM],'kind':'via','uuid':u,'key':('v',u),'layer':layer,'sites':[at]}
            out.records[layer].append(rec);out.own.setdefault(Q.COM,[]).append(rec)
            out.records[layer].append({'shape':p.buffer(.1,resolution=128),'net':Q.COM,'kind':'hole','uuid':u})
    out.trees={layer:STRtree([r['shape'] for r in rs]) for layer,rs in out.records.items()}
    return out,parsed,chunks,masks

def main():
    if OUT.exists():raise ValueError('Fresh return nomination required')
    OUT.mkdir();started=time.monotonic()
    recipe=json.loads(A.read(HERE/'ao1-vref-sdi-components-r3/receipt.json'))
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    if C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen native source differs')
    parent=A.read(HERE/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb')
    if C.sha(parent)!='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a':raise ValueError('Final staged parent differs')
    parent_inv=C.inventory(parent)
    removed=set(recipe['deletes']);restored=set(recipe['restores']);new={}
    for u in removed:
        if parent_inv[4].get(u)!=now[4][u]:raise ValueError('Staged parent changed owned removal')
    for route in recipe['new_SDI_routes']:
        for a,b in zip(route['points_mm'],route['points_mm'][1:]):
            u,ch=identity.serial_segment(route['net'],route['layer'],a,b,route['width_mm']);new[u]=ch
    u,ch=Q.serial_via(identity,Q.SDI,recipe['new_SDI_via_mm']);new[u]=ch
    chunks={u:ch for u,ch in now[4].items() if u not in removed};chunks.update({u:old[4][u] for u in restored});chunks.update(new)
    identity.assert_chunks(chunks)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(source_masks)
    parsed={u:G.parse(u,chunks[u],{}) for u in restored|set(new)}
    for u,z in parsed.items():
        if z['kind']=='via':masks[u]=set(template['copper_layers'])
    reserve,exempt=A.reservations();print('AO1_RETURN_SOURCE_MODEL',flush=True)
    base=F.Model(identity.geometry(now[4],template),reserve,exempt,native['vias'],source_masks)
    print('AO1_RETURN_SIGNAL_MODEL',flush=True)
    candidate=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],source_masks)
    projected,ledger,fillerrors=Q.prospective_fill(base,candidate,masks,now,parsed,set(parsed))
    print('AO1_RETURN_SOURCE_REFERENCE_GRAPH',flush=True)
    refs,witness,uf,ground=Q.rooted_reference(projected,masks,identity.raw(Q.COM))
    signals=[]
    for v in candidate.g['vias']:
        if S.norm(v['net']) not in (Q.VREF,Q.SDI):continue
        if v['uuid'] in parsed or any(z['kind']=='segment' and z['net']==S.norm(v['net']) and z['layer'] in source_masks.get(v['uuid'],set()) and A.shape(z).intersects(Point(v['x'],v['y']).buffer(v['d']/2)) for z in parsed.values()):signals.append(v)
    existing=[];needed=[]
    for signal in signals:
        choices=[]
        for v in candidate.g['vias']:
            if S.norm(v['net'])!=Q.COM or not {'In1.Cu','In4.Cu'}<=masks.get(v['uuid'],set()):continue
            d=math.dist((signal['x'],signal['y']),(v['x'],v['y']))
            if not .8<=d<=1.:continue
            ann=Point(v['x'],v['y']).buffer(v['d']/2,resolution=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128))
            if all(refs[layer].intersects(ann) for layer in ('F.Cu','B.Cu')):choices.append({'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':d})
        existing.append({'signal_uuid':signal['uuid'],'at_mm':[signal['x'],signal['y']],'source_rooted_paired_returns':choices})
        if not choices:needed.append(signal)
    smd=[r for rs in candidate.records.values() for r in rs if r['kind']=='pad' and candidate.pads[r['pad_id']]['smd']]
    smd_tree=STRtree([r['shape'] for r in smd]);via_tree=STRtree([Point(v['x'],v['y']) for v in candidate.g['vias']])
    gaps=Q.zone_gaps(now);sites={};rejected={}
    for signal in needed:
        for radius in (.85,.9,.95,1.):
            for i in range(96):
                at=tuple(round(q,9) for q in (signal['x']+radius*math.cos(2*math.pi*i/96),signal['y']+radius*math.sin(2*math.pi*i/96)))
                if at in sites or at in rejected:continue
                p=Point(at);body=p.buffer(.25,resolution=128);hole=p.buffer(.1,resolution=128);why=[]
                near=smd[int(smd_tree.nearest(p))]
                gap=p.distance(near['shape'])-.1-.005
                if gap<.275:why.append('SMD drill aperture')
                if len(via_tree.query(p.buffer(.81-1e-9),predicate='intersects')):why.append('Ordinary via pitch with guard')
                for layer in candidate.g['copper_layers']:
                    if why:break
                    for index in candidate.trees[layer].query(body.buffer(.675),predicate='intersects'):
                        r=candidate.records[layer][int(index)]
                        if r['kind']=='hole':distance=hole.distance(r['shape']);required=.275
                        elif r.get('net')==Q.COM:continue
                        elif r['kind']=='fill':continue # Exact local-clearance retreat audited after nomination.
                        else:distance=body.distance(r['shape']);required=.175 if r.get('domain')==candidate.domains[Q.COM] else .625
                        if distance<required-1e-9:why.append(layer+':'+r['kind']);break
                    for hard in candidate.hard[layer]:
                        if Q.COM not in hard['exempt'] and body.buffer(.025).intersects(hard['shape']):why.append('Hard area '+layer)
                # Full guarded new annulus body must land in both actual source-rooted planes.
                if not why and not all(refs[layer].covers(body.buffer(.025)) for layer in ('F.Cu','B.Cu')):why.append('Not fully rooted in both reference planes')
                if why:rejected[at]=why;continue
                covers=[v['uuid'] for v in needed if .8<=math.dist(at,(v['x'],v['y']))<=1.000000001]
                sites[at]={'at_mm':list(at),'covers_signal_uuids':covers,'nearest_SMD_pad':near['pad_id'],'guarded_SMD_aperture_mm':gap}
    remaining={v['uuid'] for v in needed};selected=[]
    while remaining:
        ranked=sorted([r for r in sites.values() if remaining&set(r['covers_signal_uuids']) and all(math.dist(r['at_mm'],q['at_mm'])>=.81 for q in selected)],key=lambda r:(-len(remaining&set(r['covers_signal_uuids'])),r['at_mm']))
        if not ranked:break
        chosen=ranked[0];selected.append(chosen);remaining-=set(chosen['covers_signal_uuids'])
    write('screen.json',{'existing_returns':existing,'legal_sites':list(sites.values()),'selected':selected,'uncovered_signal_uuids':sorted(remaining),'rejected_site_counts':{why:sum(why in rows for rows in rejected.values()) for why in sorted({w for rows in rejected.values() for w in rows})},'initial_fill_errors':fillerrors,'source_reference_witness':witness})
    # Reproject from the original native fills once all selected plated holes exist.
    final,return_parsed,return_chunks,return_masks=add_returns(candidate,selected,identity)
    allparsed=dict(parsed);allparsed.update(return_parsed);allmasks=dict(masks);allmasks.update(return_masks)
    final,final_ledger,final_fill_errors=Q.prospective_fill(base,final,allmasks,now,allparsed,set(allparsed))
    errors,clear,anti=A.clearance(final,allparsed,set(new)|set(return_chunks),restored)
    final_refs,final_witness,guf,ground=Q.rooted_reference(final,allmasks,identity.raw(Q.COM))
    paired=[]
    for signal in signals:
        choices=[]
        for v in final.g['vias']:
            if S.norm(v['net'])!=Q.COM or not {'In1.Cu','In4.Cu'}<=allmasks.get(v['uuid'],set()):continue
            d=math.dist((signal['x'],signal['y']),(v['x'],v['y']))
            if not .8<=d<=1.000000001:continue
            ann=Point(v['x'],v['y']).buffer(v['d']/2,resolution=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128))
            contact={layer:final_refs[layer].intersects(ann) for layer in ('F.Cu','B.Cu')}
            if all(contact.values()):choices.append({'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':d,'source_rooted_plane_contacts':contact})
        paired.append({'signal_uuid':signal['uuid'],'paired_choices':choices,'pass':bool(choices)})
    new.update(return_chunks)
    report={'verdict':'AO1_RETURN_NOMINATION_HOST_READY_INDEPENDENT_NATIVE_OPEN' if not(remaining or errors or final_fill_errors or any(not r['pass'] for r in paired)) else 'AO1_RETURN_NOMINATION_INCOMPLETE','exact_staged_parent_sha256':C.sha(parent),'local_native_source_sha256':C.sha(raw),'native_template_proof':proof,'return_vias':selected,'all_paired_returns':paired,'clearance_errors':errors,'clearance_rows':clear,'prospective_fill_contact_errors':final_fill_errors,'prospective_fill_ledger':final_ledger,'source_reference_witness':final_witness,'uncovered_signal_uuids':sorted(remaining),'exact_removed_chunks':{u:now[4][u].decode() for u in sorted(removed)},'exact_restored_chunks':{u:old[4][u].decode() for u in sorted(restored)},'exact_new_chunks':{u:new[u].decode() for u in sorted(new)},'full_copper_reference_audit':'INDEPENDENT_PENDING','raw_net_identity':{n:identity.raw(n) for n in (Q.VREF,Q.SDI,Q.COM)},'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started,'board_emitted':False,'adopted':False,'native_refill_DRC':'OPEN','electrical_analog_qualification':'OPEN'}
    write('receipt.json',report)
    print(json.dumps({'verdict':report['verdict'],'legal_sites':len(sites),'selected_returns':len(selected),'uncovered_signals':len(remaining),'clearance_errors':len(errors),'fill_contact_errors':len(final_fill_errors),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
