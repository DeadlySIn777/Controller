"""One bounded DIC-CS attempt with ordinary own LOGIC return stitches.

No native jobs, board edits, SMD holes, plane-outline edits or exceptions.
Every prospective return has a checked stub to actual native-source ground.
"""
import hashlib,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import screen_closure_r1 as C
S,R,V,D=C.S,C.R,C.V,C.D
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points

def sample_parts(region,desired,limit=8):
    rows=[]
    for part in D.components(region):
        if part.area<1e-10:continue
        rep=part.representative_point();near=nearest_points(part,Point(desired))[0]
        for q in (rep,near,Point((rep.x+near.x)/2,(rep.y+near.y)/2)):
            p=(round(q.x,6),round(q.y,6))
            if region.covers(Point(p)):rows.append((math.dist(p,desired),p))
    selected=[]
    for _,p in sorted(rows):
        if all(math.dist(p,q)>=.04 for q in selected):selected.append(p)
        if len(selected)>=limit:break
    return selected

def load_model():
    candidate=V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb';receipt=V.FAG/'staged/construction.json'
    contract=V.validate_construction(receipt,candidate)
    for p,digest in V.construction_hashes(receipt).items():
        if hashlib.sha256(S.read(p)).hexdigest()!=digest:raise ValueError('Frozen input differs:'+p)
    current=R.composition.inventory(S.read(candidate));old=R.composition.inventory(S.read(S.overlay_tool.base.BASE));r07=R.composition.inventory(S.read(R.R07))
    g,_,overlay=R.overlay_and_targets()
    for uid,ch in current[4].items():
        if uid in r07[4]:continue
        row=V.C.W.parse_copper(uid,ch)
        if row['kind']=='via':g['vias'].append({'uuid':uid,'net':row['net'],'x':row['at'][0],'y':row['at'][1],'d':row['d'],'drill':row['drill'],'span':['F.Cu','B.Cu'],'flashed':g['copper_layers']})
        else:g['tracks'].append({'uuid':uid,'net':row['net'],'a':row['a'],'b':row['b'],'w':row['width'],'layer':row['layer']})
    g['sha256']=contract['candidate_sha256'];g['board']=str(candidate)
    native_old=json.loads(S.read(S.overlay_tool.base.GEOM));native_new=json.loads(S.read(V.REPORT/'measure/r07-four-fag-shared/source-proof.json'))
    if native_new['verdict']!='PASS' or native_new['candidate_sha256']!=g['sha256']:raise ValueError('Samecandidate native annuli source differs')
    masks,provenance,reuse=C.actual_masks(g,old,current,native_old,native_new)
    partitions=json.loads(S.read(V.REPORT/'measure/r07-four-fag-shared/partitions.json'));inventory=json.loads(S.read(HERE.parent/'remaining-r06-losses.json'))
    if not partitions['refilled'] or partitions['sha256']!=g['sha256']:raise ValueError('Current partition evidence differs')
    reservations=json.loads(S.read(C.STAGE.parent/'alternate-r07/reserved-r07.json'));exempt={}
    for line in S.read(C.STAGE.parent/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exempt[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    print('DIC_STITCH_MODEL_START',flush=True);model=S.Model(g,reservations,exempt);print('DIC_STITCH_MODEL_READY',flush=True)
    source_refs,conductive,witness=C.anchored_references(model,g,old,current,masks,'DOM_LOGIC')
    target_row=next(r for r in inventory['rows'] if r['net'].endswith('/DIC_IOL1_CS_BUFFER'))
    target={'net':target_row['net'],'domain':'DOM_LOGIC','c05_groups':partitions['nets'][target_row['net']],'lost_relationships':[{'r07_connected_pad_ids':target_row['relationships'][0]['r06_pad_relationship']}]}
    controlled={S.norm(n):policy for n,policy in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    if controlled[S.norm(target['net'])]['class']!='NONE':raise ValueError('DIC-CS is controlled; generic geometry forbidden')
    if S.norm(target['net']) in {S.norm(n) for n in json.loads(S.read(S.EXT/'tools/power_widths.json'))}:raise ValueError('DIC-CS became power net')
    rules=S.read(R.DRU).decode()
    if '(constraint hole_size (min 0.20mm))' not in rules or '(constraint hole_to_hole (min 0.25mm))' not in rules:raise ValueError('Original ordinaryvia/hole contract differs')
    groups=C.physical_groups(model,target,masks,reuse)
    source_group=next(group for net,groupset in partitions['nets'].items() if S.norm(net)=='/LOGIC_GND' for group in groupset if 'J11001.2#0' in group)
    return {'candidate':candidate,'contract':contract,'current':current,'old':old,'g':g,'model':model,'masks':masks,'provenance':provenance,'reuse':reuse,'parts':partitions,'groups':groups,'target':target,'refs':source_refs,'conductive':conductive,'witness':witness,'source_ground_pad_ids':set(source_group),'controlled':controlled[S.norm(target['net'])]}

def grounded_targets(model,window,masks,provenance,source_ids,refs,conductive):
    # Pad owners are in the actual refilled native SOURCE group. Via owners
    # additionally require actually flashed annuli and source-plane contact.
    out={}
    for layer in ('F.Cu','B.Cu'):
        records=[]
        for row in model.own['/LOGIC_GND']:
            if row['layer']!=layer or not row['shape'].intersects(window):continue
            if row['kind']=='pad' and row['pad_id'] in source_ids:records.append(row)
            elif row['kind']=='via' and layer in masks[row['uuid']] and provenance[row['uuid']] in ('unchanged r06 native','same198b native API'):
                v=next(v for v in model.g['vias'] if v['uuid']==row['uuid']);ann=Point(v['x'],v['y']).buffer(v['d']/2).difference(Point(v['x'],v['y']).buffer(v['drill']/2))
                if all(refs[p].intersects(ann) and conductive[p].intersects(ann) for p in refs):records.append(row)
        out[layer]={'records':records,'layers':{layer}}
    return out

def new_copper_cut(vias,stubs,layer,net):
    obstacles=[]
    for via in vias:
        if via['net']!=net:obstacles.append(Point(via['point_mm']).buffer(via['size_mm']/2+.15+.1+S.MARGIN))
    for stub in stubs:
        if stub['layer']==layer and stub['net']!=net:obstacles.append(LineString(stub['points_mm']).buffer(stub['width_mm']/2+.15+.1+S.MARGIN))
    return unary_union(obstacles)

def prepare_returns(data,window,signal_sites,ground_free,ground_targets,refs,deadline):
    model=data['model'];ground={'net':'/LOGIC_GND','domain':'DOM_LOGIC'};options=[];diagnostics=[]
    for signal in signal_sites[:8]:
        p=signal['point_mm']
        ring=Point(p).buffer(1.,resolution=64).difference(Point(p).buffer(.9,resolution=64))
        # Full prospective ground annulus must already be inside physical
        # source-connected fills on BOTH reference planes, preventing islands.
        ground_lands=ground_free.intersection(ring).intersection(refs['In1.Cu'].buffer(-.25)).intersection(refs['In4.Cu'].buffer(-.25))
        return_sites=sample_parts(ground_lands,p,limit=6)
        detail={'signal_point_mm':p,'source_connected_newreturn_landing_area_mm2':ground_lands.area,'sampled_return_sites':len(return_sites),'stub_searches':[]}
        for q in return_sites:
            if time.monotonic()>=deadline:break
            separation=math.dist(p,q)
            if not .9<=separation<=1.0:continue
            for layer in ('F.Cu','B.Cu'):
                free,_=model.free(ground,layer,window)
                # Prospective SIGNALvia already constrains this ground stub.
                free=free.difference(Point(p).buffer(.25+.15+.1+S.MARGIN))
                target_window=Point(q).buffer(2.5).envelope.intersection(window)
                seeds=S.seed_sites(ground_targets[layer],layer,free,target_window)
                proposed={'uuid':'NEW_RETURN_'+str(q),'kind':'new_ground_via'}
                stub,search=S.astar(free,[(q,proposed)],seeds,min(deadline,time.monotonic()+1.5),node_cap=18000) if seeds else (None,{'reason':'no actual source-grounded pad/via reachable within2.5mm','nodes':0})
                detail['stub_searches'].append({'return_point_mm':q,'layer':layer,'seed_count':len(seeds),'search':search})
                if not stub:continue
                if LineString(stub['points_mm']).length>5.0:continue
                options.append({'signal':signal,'return':{'point_mm':list(q),'net':'/LOGIC_GND','size_mm':.5,'drill_mm':.2,'signal_distance_mm':separation,'ordinary_keep_all':True},'stub':dict(stub,layer=layer,width_mm=.2,net='/LOGIC_GND'),'ground_owner_native_source_pad_component':'J11001.2#0'})
                break
            if options and options[-1]['signal']==signal:break
        diagnostics.append(detail)
        if time.monotonic()>=deadline:break
    return options,diagnostics

def main():
    destination=HERE/'stitch-screen.json'
    if destination.exists():raise ValueError('Distinct immutable receipt required')
    for path in (Path(__file__),Path(C.__file__),Path(S.__file__),Path(D.__file__),Path(R.__file__),S.EXT/'tools/verify/return_path.py',Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md')):S.read(path)
    data=load_model();model=data['model'];g=data['g'];target=data['target'];groups=data['groups'];refs=data['refs']
    first=unary_union([r['shape'] for r in groups[0]['records'] if r['layer'] in S.LAYERS]);second=unary_union([r['shape'] for r in groups[1]['records'] if r['layer'] in S.LAYERS]);pa,pb=nearest_points(first,second);center=LineString([pa,pb]).envelope;desired=[tuple(pb.coords[0]),tuple(pa.coords[0])]
    windows=[];proposal=None
    for grow in (8,14):
        deadline=time.monotonic()+100;window=center.buffer(grow,cap_style=3).envelope;detail={'window_mm':list(window.bounds),'signal_landing_components':[],'newreturn_component_diagnostics':[]}
        signal_free,signal_blocks=C.via_free(model,target,window,refs);ground_free,ground_blocks=C.via_free(model,{'net':'/LOGIC_GND','domain':'DOM_LOGIC'},window,refs)
        detail.update(signal_via_free_area_mm2=signal_free.area,ground_via_free_area_mm2=ground_free.area,signal_blockers=signal_blocks,ground_blockers=ground_blocks)
        mid0,_=model.free(target,'In3.Cu',window);mid0=mid0.intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);outer={};options=[[],[]]
        gt=grounded_targets(model,window,data['masks'],data['provenance'],data['source_ground_pad_ids'],refs,data['conductive'])
        detail['actual_native_source_ground_targets']={layer:len(row['records']) for layer,row in gt.items()}
        for gi,group in enumerate(groups):
            signals=[]
            for layer in ('F.Cu','B.Cu'):
                if layer not in group['layers']:continue
                free,_=model.free(target,layer,window);free=free.intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);seeds=S.seed_sites(group,layer,free,window);outer[(gi,layer)]=(free,seeds)
                lands=signal_free.intersection(D.reachable_part(free,seeds)).intersection(mid0)
                sites=sample_parts(lands,desired[gi],limit=8)
                detail['signal_landing_components'].append({'component':gi,'layer':layer,'area_mm2':lands.area,'continuous_sites':len(sites),'sites':sites})
                signals.extend({'point_mm':list(p),'contact_layer':layer,'net':target['net'],'size_mm':.5,'drill_mm':.2} for p in sites)
            options[gi],diagnosis=prepare_returns(data,window,signals,ground_free,gt,refs,deadline)
            detail['newreturn_component_diagnostics'].append({'component':gi,'complete_grounded_return_options':len(options[gi]),'rows':diagnosis})
        pairs=sorted([(math.dist(a['signal']['point_mm'],b['signal']['point_mm']),a,b) for a in options[0] for b in options[1]],key=lambda x:x[0]);detail['complete_return_pairs']=len(pairs);detail['path_searches']=[]
        for _,a,b in pairs[:12]:
            if time.monotonic()>=deadline:break
            signals=[a['signal'],b['signal']];returns=[a['return'],b['return']];stubs=[a['stub'],b['stub']];vias=signals+returns
            if any(math.dist(x['point_mm'],y['point_mm'])<.8+S.MARGIN for i,x in enumerate(vias) for y in vias[i+1:]):continue
            # All prospective signal/return additions constrain each other.
            middle=mid0.difference(new_copper_cut(vias,stubs,'In3.Cu',target['net']))
            fakea={'uuid':'NEW_SIGNAL_A','kind':'new_via'};fakeb={'uuid':'NEW_SIGNAL_B','kind':'new_via'}
            mid,ms=S.astar(middle,[(tuple(signals[0]['point_mm']),fakea)],[(tuple(signals[1]['point_mm']),fakeb)],min(deadline,time.monotonic()+4),node_cap=45000)
            detail['path_searches'].append({'middle':ms})
            if not mid:continue
            fa,seeda=outer[(0,signals[0]['contact_layer'])];fb,seedb=outer[(1,signals[1]['contact_layer'])]
            fa=fa.difference(new_copper_cut(vias,stubs,signals[0]['contact_layer'],target['net']));fb=fb.difference(new_copper_cut(vias,stubs,signals[1]['contact_layer'],target['net']))
            start,sa=S.astar(fa,seeda,[(tuple(signals[0]['point_mm']),fakea)],deadline,node_cap=30000);end,sb=S.astar(fb,[(tuple(signals[1]['point_mm']),fakeb)],seedb,deadline,node_cap=30000)
            detail['path_searches'][-1].update(start=sa,end=sb)
            if not start or not end:continue
            signal_segments=[dict(start,layer=signals[0]['contact_layer'],width_mm=.2,net=target['net']),dict(mid,layer='In3.Cu',width_mm=.2,net=target['net']),dict(end,layer=signals[1]['contact_layer'],width_mm=.2,net=target['net'])]
            # Revalidate both complete ground stubs against BOTHsignalvias and
            # all final signal segments, rather than only their own local via.
            ground_valid=True
            for stub in stubs:
                free,_=model.free({'net':'/LOGIC_GND','domain':'DOM_LOGIC'},stub['layer'],window)
                for v in signals:free=free.difference(Point(v['point_mm']).buffer(.25+.15+.1+S.MARGIN))
                for seg in signal_segments:
                    if seg['layer']==stub['layer']:free=free.difference(LineString(seg['points_mm']).buffer(.1+.15+.1+S.MARGIN))
                if not free.covers(LineString(stub['points_mm'])):ground_valid=False
            if not ground_valid:detail['path_searches'][-1]['reason']='final signal copper blocks grounded returnstub';continue
            prospective_refs,prospective_cond,witness=C.anchored_references(model,g,data['old'],data['current'],data['masks'],'DOM_LOGIC',[v['point_mm'] for v in signals])
            # Ground-via holes are inherent perforations, no plane-outline cut.
            ground_holes=unary_union([Point(v['point_mm']).buffer(.1+S.MARGIN) for v in returns])
            prospective_refs={plane:shape.difference(ground_holes) for plane,shape in prospective_refs.items()}
            path={'segments':signal_segments,'new_signal_vias':signals,'new_return_vias':returns,'ground_stubs':stubs}
            cover,ok=C.coverage(path,prospective_refs,[v['point_mm'] for v in signals])
            contacts=[]
            for rv in returns:
                ann=Point(rv['point_mm']).buffer(.25).difference(Point(rv['point_mm']).buffer(.1))
                contacts.append({plane:prospective_refs[plane].intersects(ann) for plane in refs})
            if not ok or not all(all(c.values()) for c in contacts):detail['path_searches'][-1]['reason']='final prospective source reference contact/coverage fails';continue
            path.update(reference_coverage=cover,newreturn_source_reference_contacts=contacts,reference_witnesses=witness,grounded_owner_options=[a,b],qualified=False)
            proposal=path;break
        windows.append(detail)
        print('DIC_STITCH_WINDOW',grow,'return_options',[len(x) for x in options],'pairs',len(pairs),'path',bool(proposal),flush=True)
        (HERE/'progress.json').write_text(json.dumps({'windows':windows,'proposal':proposal},indent=1)+'\n',encoding='utf-8')
        if proposal:break
    for path,digest in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('Read input changed:'+path)
    report={'schema':'dic-own-return-stitch-bounded-source-r1','verdict':'HOST_WHOLE_PATH_REQUIRES_INDEPENDENT_AUDIT' if proposal else 'NO_COMPLETE_PATH_IN_BOUNDED_MODEL','candidate_sha256':data['contract']['candidate_sha256'],'source_files_sha256':S.READS,'net':target['net'],'domain':'DOM_LOGIC','native_physical_pad_groups':[g['pad_ids'] for g in groups],'controlled_policy':data['controlled'],'reference_source_witnesses':data['witness'],'windows':windows,'proposal':proposal,'all_r07_and287_combined_additions_preserved':True,'native_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,'limits':['One ordinarysignal only,8/14mm windows,100s/window,8signal sites/side,6return sites/signal,12completepairs','New LOGIC return stitch .9–1.0mm from signalvia; full-radius hole/copper/barrier/.8spacing, noSMDholes','Returnvia fullannuli inside sourceconnected In1/In4 plus checked<=5mm stub to actualnative-sourcegroundpad/via','Exact198b actual copper over conservative exactr06 refilled pad/plane geometry; old/current nativeannuli pins bound','Source-only negative is bounded; electrical/current/thermal/SI/timing, freshrefill and strictdual no-loss gates remainopen']}
    destination.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(destination),'verdict':report['verdict']}),flush=True)

if __name__=='__main__':main()
