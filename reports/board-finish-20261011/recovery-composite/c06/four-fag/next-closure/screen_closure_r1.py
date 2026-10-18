"""Bounded additive closure on exact198b. Host only; no native/API/board save.

Actual annuli restrict own-net contacts. All-layer projected foreign annuli are
conservative obstacles. A found path still needs independent/native gates.
"""
import hashlib,json,math,re,sys,time,types
from collections import defaultdict
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
STAGE=HERE.parent
sys.path.insert(0,str(STAGE));sys.path.insert(0,str(STAGE.parent));sys.path.insert(0,str(STAGE.parent/'alternate-r07'))
import validate_combined as V
import screen_c06 as S
import screen_r07 as R
import screen_dive_c06 as D
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.prepared import prep
from shapely.strtree import STRtree

NAMES=('DOA_SDO_FIELD','DIC_IOL1_CS_BUFFER','DOA_Q0_READY_N','XF_REQUEST_BUFFER')
ANCHORS={'DOM_LOGIC':'J11001.2#0','DOM_FIELD_A':'J11003.2#0'}
RADIUS=.25

def ordinary_keep_all(chunk):
    return b'(layers "F.Cu" "B.Cu")' in chunk and not any(flag in chunk for flag in (b'remove_unused_layers',b'start_end_only',b'via blind',b'via micro'))

def actual_masks(g,old_inventory,current_inventory,native_old,native_new):
    observed={v['uuid']:v for v in native_old['vias']}
    added={v['uuid']:v for v in native_new['native_api']['added_via_annuli']['rows']}
    masks={};provenance={};reuse={}
    for v in g['vias']:
        uid=v['uuid'];ch=current_inventory[4][uid]
        if old_inventory[4].get(uid)==ch and uid in observed:
            prior=observed[uid]
            if any(v[k]!=prior[k] for k in ('x','y','d','drill')):raise ValueError('Inherited geometry differs')
            masks[uid]=set(prior['flashed']);provenance[uid]='unchanged r06 native'
        elif uid in added:
            masks[uid]=set(added[uid]['actual_flashed_layers']);provenance[uid]='same198b native API'
        elif ordinary_keep_all(ch):
            masks[uid]=set(g['copper_layers']);provenance[uid]='changed ordinary KEEP_ALL source default; native flash open'
        else:masks[uid]=set();provenance[uid]='withheld unknown/suppressed'
        # Reuse a layer absent from older tracks only with actual annulus plus
        # immutable ordinary KEEP_ALL, never merely a nominal through span.
        reuse[uid]=ordinary_keep_all(ch) and provenance[uid] in ('unchanged r06 native','same198b native API')
    return masks,provenance,reuse

def physical_groups(model,target,masks,reuse):
    net=S.norm(target['net'])
    records=[r for r in model.own[net] if r['kind']!='via' or r['layer'] in masks[r['uuid']]]
    uf=S.UF()
    for r in records:uf.find(r['key'])
    for layer in model.g['copper_layers']:
        local=[r for r in records if r['layer']==layer]
        if not local:continue
        tree=STRtree([r['shape'] for r in local])
        for i,r in enumerate(local):
            for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
                if i<j and r['shape'].distance(local[j]['shape'])<=.000002:uf.join(r['key'],local[j]['key'])
    native=defaultdict(set)
    for group in target['c05_groups']:
        for pid in group:native[uf.find(('p',pid))].add(pid)
    if {frozenset(x) for x in native.values()}!={frozenset(x) for x in target['c05_groups']}:
        raise ValueError('Actual-annulus contact graph differs from fresh native pad partitions')
    roots={uf.find(('p',pid)) for pid in target['lost_relationships'][0]['r07_connected_pad_ids']}
    if len(roots)!=2:raise ValueError('Expected two current physical components')
    groups=[]
    for root in sorted(roots,key=str):
        own=[r for r in records if uf.find(r['key'])==root]
        layers={r['layer'] for r in own if r['kind'] in ('track','pad') or (r['kind']=='via' and reuse[r['uuid']])}
        groups.append({'pad_ids':sorted(native[root]),'records':[r for r in own if r['layer'] in layers], 'layers':layers})
    return groups

def anchored_references(model,g,old,current,masks,domain,prospective=()):
    ref=S.REF_NET[domain];anchor=model.pads[ANCHORS[domain]];refs={};conductive={};witness={}
    changed={uid for uid,ch in current[4].items() if old[4].get(uid)!=ch}
    cutters=[]
    for v in g['vias']:
        if v['uuid'] in changed and S.norm(v['net'])!=ref:
            gap=.15 if model.domains.get(S.norm(v['net']))==domain else .6
            cutters.append(Point(v['x'],v['y']).buffer(v['d']/2+gap+S.MARGIN))
    cutters.extend(Point(p).buffer(RADIUS+.15+S.MARGIN) for p in prospective)
    cut=unary_union(cutters)
    for layer in ('In1.Cu','In4.Cu'):
        fill=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']==ref]).difference(cut)
        own=[];excluded=0
        for r in model.records[layer]:
            if r['net']!=ref or r['kind'] not in ('pad','track','via'):continue
            if r['kind']=='via':
                if layer not in masks[r['uuid']]:excluded+=1;continue
                v=next(v for v in g['vias'] if v['uuid']==r['uuid'])
                own.append(r['shape'].difference(Point(v['x'],v['y']).buffer(v['drill']/2)))
            else:own.append(r['shape'])
        entire=unary_union([fill]+own)
        if layer not in anchor['layers']:raise ValueError('Source anchor has no native annulus')
        source=unary_union(S.poly(anchor['layers'][layer]))
        anchored=unary_union([part for part in D.components(entire) if part.intersects(source)])
        refs[layer]=fill.intersection(anchored);conductive[layer]=anchored
        witness[layer]={'source_pad':ANCHORS[domain],'source_uuid':anchor['uuid'],'source_net':ref,'current_foreign_antipads':len(cutters)-len(prospective),'prospective_signal_antipads':len(prospective),'unflashed_or_unknown_own_vias_excluded':excluded,'source_connected_fill_area_mm2':refs[layer].area}
    return refs,conductive,witness

def return_vias(model,g,masks,provenance,refs,conductive,domain,window):
    ref=S.REF_NET[domain];out=[]
    for v in g['vias']:
        if S.norm(v['net'])!=ref or not window.buffer(2).covers(Point(v['x'],v['y'])):continue
        if not {'In1.Cu','In4.Cu'}<=masks[v['uuid']]:continue
        if provenance[v['uuid']] not in ('unchanged r06 native','same198b native API'):continue
        annulus=Point(v['x'],v['y']).buffer(v['d']/2).difference(Point(v['x'],v['y']).buffer(v['drill']/2))
        if all(refs[layer].intersects(annulus) and conductive[layer].intersects(annulus) for layer in refs):
            out.append(dict(uuid=v['uuid'],x=v['x'],y=v['y'],diameter=v['d'],return_net=ref,source_anchor_proven_host=True,annulus_provenance=provenance[v['uuid']]))
    return out

def continuous_landings(landing,returns,desired,layer,max_sites=12):
    points=[];count=0;area=0
    for rv in returns:
        ring=Point(rv['x'],rv['y']).buffer(1.0,resolution=64).difference(Point(rv['x'],rv['y']).buffer(.8+S.MARGIN,resolution=64))
        region=landing.intersection(ring);area+=region.area
        for part in D.components(region):
            if part.area<=1e-10:continue
            count+=1
            candidates=[part.representative_point()]
            near=nearest_points(part,Point(desired))[0]
            candidates.append(near)
            # Interior points remain valid even when no .1mm grid intersects
            # a narrow positive-area landing. Exact A* connectors follow.
            rep=candidates[0]
            candidates.append(Point((near.x+rep.x)/2,(near.y+rep.y)/2))
            for q in candidates:
                p=(round(q.x,6),round(q.y,6));d=math.dist(p,(rv['x'],rv['y']))
                if region.covers(Point(p)) and .8+S.MARGIN<=d<=1.0:
                    points.append((math.dist(p,desired),p,rv,d))
    selected=[]
    for score,p,rv,d in sorted(points,key=lambda x:(x[0],x[1],x[2]['uuid'])):
        if any(math.dist(p,r['point_mm'])<.05 for r in selected):continue
        selected.append({'point_mm':list(p),'return_via':rv,'return_distance_mm':d,'contact_layer':layer})
        if len(selected)>=max_sites:break
    return selected,{'continuous_return_intersection_components':count,'continuous_return_intersection_area_mm2':area,'selected_sites':len(selected)}

def via_free(model,target,window,refs):
    blockers=[];classes=defaultdict(int);net=S.norm(target['net']);domain=target['domain']
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(window.buffer(2),predicate='intersects'):
            r=model.records[layer][i]
            if r['kind']=='hole':gap=.25+RADIUS
            elif r['kind']=='pad' and r['net']==net:gap=.1+RADIUS
            elif r['net']==net:continue
            elif r['kind']=='fill' and layer in ('In1.Cu','In2.Cu','In4.Cu') and r.get('domain')==domain:continue
            else:gap=(.15 if r.get('domain')==domain else .6)+RADIUS
            blockers.append(r['shape'].buffer(gap+S.MARGIN));classes[r['kind']]+=1
        if layer in model.hard_trees:
            for i in model.hard_trees[layer].query(window.buffer(2),predicate='intersects'):
                r=model.hard[layer][i]
                if net not in r['exempt']:blockers.append(r['shape'].buffer(RADIUS+S.MARGIN));classes[r['kind']]+=1
    for v in model.g['vias']:
        if window.buffer(2).covers(Point(v['x'],v['y'])):blockers.append(Point(v['x'],v['y']).buffer(.8+S.MARGIN))
    return window.intersection(model.outline.buffer(-.5-RADIUS-S.MARGIN)).intersection(refs['In1.Cu']).intersection(refs['In4.Cu']).difference(unary_union(blockers)),dict(classes)

def coverage(path,refs,via_points):
    holes=unary_union([Point(p).buffer(RADIUS+.15+S.MARGIN) for p in via_points])
    rows=[]
    for seg in path['segments']:
        wire=LineString(seg['points_mm']).difference(holes)
        missing={layer:wire.difference(refs[layer]).length for layer in refs}
        rows.append({'layer':seg['layer'],'uncovered_reference_mm':missing})
    return rows,all(all(value<1e-8 for value in r['uncovered_reference_mm'].values()) for r in rows)

def main():
    output=HERE/'bounded-closure-r1.json'
    if output.exists():raise ValueError('Distinct immutable receipt required')
    candidate=V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb';receipt=V.FAG/'staged/construction.json'
    contract=V.validate_construction(receipt,candidate)
    pins=V.construction_hashes(receipt)
    for p,digest in pins.items():
        if hashlib.sha256(S.read(p)).hexdigest()!=digest:raise ValueError('Input differs:'+p)
    current=R.composition.inventory(S.read(candidate));old=R.composition.inventory(S.read(S.overlay_tool.base.BASE));r07=R.composition.inventory(S.read(R.R07))
    g,_,overlay=R.overlay_and_targets()
    for uid,ch in current[4].items():
        if uid in r07[4]:continue
        r=V.C.W.parse_copper(uid,ch)
        if r['kind']=='via':g['vias'].append({'uuid':uid,'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'span':['F.Cu','B.Cu'],'flashed':g['copper_layers']})
        else:g['tracks'].append({'uuid':uid,'net':r['net'],'a':r['a'],'b':r['b'],'w':r['width'],'layer':r['layer']})
    g['sha256']=contract['candidate_sha256'];g['board']=str(candidate)
    native_old=json.loads(S.read(S.overlay_tool.base.GEOM));native_new=json.loads(S.read(V.REPORT/'measure/r07-four-fag-shared/source-proof.json'))
    if native_new['verdict']!='PASS' or native_new['candidate_sha256']!=contract['candidate_sha256']:raise ValueError('Current added-via API source mismatch')
    masks,provenance,reuse=actual_masks(g,old,current,native_old,native_new)
    inventory=json.loads(S.read(HERE/'remaining-r06-losses.json'));partitions=json.loads(S.read(V.REPORT/'measure/r07-four-fag-shared/partitions.json'))
    if inventory['candidate_sha256']!=g['sha256'] or partitions['sha256']!=g['sha256'] or not partitions['refilled']:raise ValueError('Actual partitions mismatch')
    reservations=json.loads(S.read(STAGE.parent/'alternate-r07/reserved-r07.json'));exempt={}
    for line in S.read(STAGE.parent/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exempt[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    controlled={S.norm(n):p for n,p in json.loads(S.read(S.CONTROLLED))['nets'].items()};power={S.norm(n) for n in json.loads(S.read(S.EXT/'tools/power_widths.json'))}
    project=json.loads(S.read(R.PRO));classes={c['name']:c for c in project['net_settings']['classes']}
    for p in (Path(__file__),Path(S.__file__),Path(R.__file__),Path(D.__file__),S.EXT/'tools/verify/return_path.py',Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md'),R.DRU):S.read(p)
    print('CLOSURE_MODEL_START',flush=True);model=S.Model(g,reservations,exempt);print('CLOSURE_MODEL_READY',flush=True)
    domains={};results=[]
    for name in NAMES:
        record=next(r for r in inventory['rows'] if r['net'].endswith('/'+name));net=record['net'];domain=record['domain'];policy=controlled.get(S.norm(net))
        row={'net':net,'domain':domain,'controlled_policy':policy,'width_mm':.2,'via_size_drill_mm':[.5,.2],'native_relationships':record['relationships'],'paths':[],'windows':[],'current_retained_copper_items':len(current[4])}
        if S.norm(net) in power or (policy and policy.get('class') not in ('NONE',None)) or classes[domain]['track_width']!=.2:
            row.update(verdict='WITHHELD_CURRENT_OR_CONTROLLED_POLICY');results.append(row);continue
        row['current_policy']='Ordinary signal, not listed power trunk; .2mm effective domain default. Driver/current/timing remains electrical gate open.'
        rel=record['relationships'][0];target={'net':net,'domain':domain,'c05_groups':partitions['nets'][net],'lost_relationships':[{'r07_connected_pad_ids':rel['r06_pad_relationship']}]}
        try:groups=physical_groups(model,target,masks,reuse)
        except ValueError as exc:row.update(verdict='WITHHELD_PHYSICAL_MODEL',reason=str(exc));results.append(row);continue
        row['physical_pad_groups']=[x['pad_ids'] for x in groups]
        if domain not in domains:domains[domain]=anchored_references(model,g,old,current,masks,domain)
        refs,conductive,witness=domains[domain];row['reference_witnesses']=witness
        first=unary_union([r['shape'] for r in groups[0]['records'] if r['layer'] in S.LAYERS]);second=unary_union([r['shape'] for r in groups[1]['records'] if r['layer'] in S.LAYERS]);pa,pb=nearest_points(first,second)
        center=LineString([pa,pb]).envelope;desired=[tuple(pb.coords[0]),tuple(pa.coords[0])]
        for grow in (8,14):
            window=center.buffer(grow,cap_style=3).envelope;detail={'window_mm':list(window.bounds),'zero_via':[],'landings':[]};deadline=time.monotonic()+40
            for layer in S.LAYERS:
                if layer not in groups[0]['layers'] or layer not in groups[1]['layers']:
                    detail['zero_via'].append({'layer':layer,'reason':'no actual flashed/KEEP_ALL contact layer on both components'});continue
                free,blockers=model.free(target,layer,window)
                strict=free.intersection(refs['In1.Cu']).intersection(refs['In4.Cu'])
                seeds=[S.seed_sites(x,layer,strict,window) for x in groups]
                path,search=S.astar(strict,*seeds,deadline,node_cap=70000) if all(seeds) else (None,{'reason':'no strict source-reference attachment','nodes':0})
                detail['zero_via'].append({'layer':layer,'seed_counts':[len(x) for x in seeds],'search':search,'blocker_count':len(blockers)})
                if path:
                    proposal={'segments':[dict(path,layer=layer,width_mm=.2)],'new_signal_vias':[],'new_return_vias':[]}
                    cover,ok=coverage(proposal,refs,[])
                    if not ok:raise ValueError('Found zero-via path failed exact reference coverage')
                    proposal['reference_coverage']=cover;row['paths'].append(proposal);break
            if row['paths']:row['windows'].append(detail);break
            via_region,blocker_classes=via_free(model,target,window,refs);returns=return_vias(model,g,masks,provenance,refs,conductive,domain,window)
            detail['via_landing_area_mm2']=via_region.area;detail['via_blocker_classes']=blocker_classes;detail['qualified_existing_returns']=len(returns)
            free_mid,_=model.free(target,'In3.Cu',window);middle=free_mid.intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);possible=[[],[]];outer={}
            for gi,group in enumerate(groups):
                for layer in ('F.Cu','B.Cu'):
                    if layer not in group['layers']:continue
                    free,_=model.free(target,layer,window);free=free.intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);seeds=S.seed_sites(group,layer,free,window)
                    reachable=D.reachable_part(free,seeds);landing=via_region.intersection(reachable).intersection(middle)
                    sites,stats=continuous_landings(landing,returns,desired[gi],layer)
                    detail['landings'].append({'component':gi,'layer':layer,'reachable_landing_area_mm2':landing.area,'source_seed_count':len(seeds),**stats,'sites':sites})
                    outer[(gi,layer)]=(free,seeds);possible[gi].extend((site,layer) for site in sites)
            pairs=sorted([(math.dist(a['point_mm'],b['point_mm']),a,la,b,lb) for a,la in possible[0] for b,lb in possible[1] if math.dist(a['point_mm'],b['point_mm'])>=.8+S.MARGIN],key=lambda x:(x[0],x[1]['point_mm'],x[3]['point_mm']))
            detail['landing_pairs']=len(pairs);detail['middle_searches']=[]
            for _,a,la,b,lb in pairs[:12]:
                if time.monotonic()>=deadline:break
                fakea={'uuid':'prospective signal A','kind':'new via'};fakeb={'uuid':'prospective signal B','kind':'new via'}
                mid,search=S.astar(middle,[(tuple(a['point_mm']),fakea)],[(tuple(b['point_mm']),fakeb)],min(deadline,time.monotonic()+5),node_cap=45000);detail['middle_searches'].append(search)
                if not mid:continue
                fa,seeda=outer[(0,la)];fb,seedb=outer[(1,lb)]
                start,sa=S.astar(fa,seeda,[(tuple(a['point_mm']),fakea)],deadline,node_cap=30000)
                end,sb=S.astar(fb,[(tuple(b['point_mm']),fakeb)],seedb,deadline,node_cap=30000)
                if not start or not end:continue
                proposal={'segments':[dict(start,layer=la,width_mm=.2),dict(mid,layer='In3.Cu',width_mm=.2),dict(end,layer=lb,width_mm=.2)],'new_signal_vias':[dict(a,size_mm=.5,drill_mm=.2),dict(b,size_mm=.5,drill_mm=.2)],'new_return_vias':[]}
                points=[a['point_mm'],b['point_mm']];pros_refs,pros_cond,pros_witness=anchored_references(model,g,old,current,masks,domain,points);cover,ok=coverage(proposal,pros_refs,points)
                return_checks=[]
                for site in (a,b):
                    rv=next(v for v in g['vias'] if v['uuid']==site['return_via']['uuid']);ann=Point(rv['x'],rv['y']).buffer(rv['d']/2).difference(Point(rv['x'],rv['y']).buffer(rv['drill']/2))
                    return_checks.append({'uuid':rv['uuid'],'source_connected_after_prospective_antipads':{layer:pros_refs[layer].intersects(ann) and pros_cond[layer].intersects(ann) for layer in refs}})
                if not ok or any(not all(c['source_connected_after_prospective_antipads'].values()) for c in return_checks):
                    detail.setdefault('prospective_reference_rejections',[]).append({'coverage':cover,'return_checks':return_checks});continue
                proposal.update(reference_coverage=cover,return_checks=return_checks,prospective_reference_witnesses=pros_witness)
                row['paths'].append(proposal);break
            row['windows'].append(detail)
            if row['paths']:break
        row['verdict']='HOST_WHOLE_PATH_PENDING_INDEPENDENT_NATIVE' if row['paths'] else 'NO_PATH_IN_BOUNDED_STRICT_SOURCE_MODEL'
        results.append(row)
        (HERE/'closure-r1-progress.json').write_text(json.dumps({'results':results},indent=1)+'\n',encoding='utf-8')
        print(name,row['verdict'],[(d['window_mm'],d.get('landing_pairs'),[x.get('search',{}).get('reason') for x in d['zero_via']]) for d in row['windows']],flush=True)
    for path,digest in S.READS.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('Input changed:'+path)
    result={'schema':'strict-source-combined-bounded-closure-r1','evidence_class':'Host source screen only','candidate_sha256':contract['candidate_sha256'],'native_partition_sha256':hashlib.sha256(S.read(V.REPORT/'measure/r07-four-fag-shared/partitions.json')).hexdigest(),'source_files_sha256':S.READS,'results':results,'source_via_annuli_provenance_counts':{p:list(provenance.values()).count(p) for p in set(provenance.values())},'old_copper_preservation':True,'combined287_additions_preservation':True,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,'limits':['Four targets only;8/14mm window growth,40s/window,12continuous sites/side,12pairs and45000middle nodes','Exact endpoints-to-grid checked connectors; .1mm search grid can still miss narrow feasible paths','Foreign copper/via annuli are conservatively projected on all6 layers; own contacts require actual annuli or explicit unchanged KEEP_ALL source','Conservative exact r06 fills+all current foreign antipads, both planes explicitly source anchored by actual domain','Native refill/DRC, dual no-loss guards, complete electrical/current/timing/return and physical/manufacturing gates remain open','No route or global impossibility is inferred from a bounded negative result']}
    output.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'report':str(output),'paths':sum(bool(r['paths']) for r in results),'targets':len(results)}),flush=True)

if __name__=='__main__':main()
