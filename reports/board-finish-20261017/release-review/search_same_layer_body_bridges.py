"""Bounded short bridges from genuine cached R299 named-pad groups.

No graph rebuild/native run. Existing source-backed reference copper, all
actual foreign fills, every unrelated drill, and frozen current peers are hard.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
import collections, hashlib, itertools, json, math, pickle, sys, time, uuid, xml.etree.ElementTree as ET
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import STRtree
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
OLD=ROOT/'reports/board-finish-20261011/continuation-r2';CACHE=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
CURRENT=ROOT/'reports/board-finish-20261017/combined-route-stage-r1';OUT=HERE/'short-same-layer-body-bridges-r2'
for d in (OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
import gpu_existing_port_routes as GPU
import re
K=N.K;L=N.L;norm=L.norm
LAYERS=('F.Cu','In2.Cu','In3.Cu','B.Cu');REF_LAYER={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'}
ROOTS={'DOM_LOGIC':('/LOGIC_GND','J11001','2'),'DOM_FIELD_A':('/motherboard_motors/FIELD_GND','J11003','2'),'DOM_FIELD_B':('/motherboard_do/FIELD_B_0V','J11005','2')}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def outer(s,r):return shapely.set_precision(s.buffer((r+.000002)/math.cos(math.pi/256),quad_segs=64),.000001)
def info(s):return {'area_mm2':s.area,'bounds':list(s.bounds) if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def body(path):return outer(LineString(path),.1)
def paths(a,b):
    ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
    d=min(abs(dx),abs(dy)); proposals=[[a,b],[a,[ax,by],b],[a,[bx,ay],b],[a,[ax+sx*d,ay+sy*d],b],[a,[bx-sx*d,by-sy*d],b]]
    seen=set()
    for p in proposals:
        p=[list(q) for q,_ in itertools.groupby(p)]
        if len(p)<2:continue
        t=tuple(tuple(q) for q in p)
        if t not in seen:seen.add(t);yield p
def fmt(x):return format(x,'.6f').rstrip('0').rstrip('.')
def native(t):
    return ('\t(segment\n\t\t(start '+' '.join(fmt(v) for v in t['a'])+')\n\t\t(end '+' '.join(fmt(v) for v in t['b'])+')\n\t\t(width 0.2)\n\t\t(layer "'+t['layer']+'")\n\t\t(net '+json.dumps(t['net'])+')\n\t\t(uuid "'+t['uuid']+'")\n\t)\n').encode()

def main():
    assert not OUT.exists();OUT.mkdir();t0=time.monotonic()
    files=[CACHE/'actual-combined-full-after-model.pkl',CACHE/'actual-combined-full-after-all-net-groups.pkl',CACHE/'actual-graph-cache-receipt.json',
           CURRENT/'native/board.kicad_pcb',CURRENT/'all-copper-expected.json',CURRENT/'construction-receipt.json',
           OLD/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json',HERE/'R299-fresh-source.xml',Path(__file__),
           CURRENT/'native/board.kicad_dru',CURRENT/'native/board.kicad_pro',Path(GPU.__file__)]
    pins={str(f):sha(f) for f in files}
    assert pins[str(files[0])]=='c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806'
    assert pins[str(files[1])]=='c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd'
    assert pins[str(files[3])]=='758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad'
    put('launch.json',{'input_SHA256':pins,'affinity':proc.cpu_affinity(),'native_jobs':0})
    print('LOAD_ACTUAL_R299_CACHE',flush=True)
    h=pickle.loads(files[0].read_bytes());groups=pickle.loads(files[1].read_bytes());domains=h['domains_normalized']
    ref={};root_ids={}
    for domain,(net,r,p) in ROOTS.items():
        gg=[q for q in groups[net] if any(v['kind']=='pad' and v['ref']==r and str(v['pin'])==p for v in q)]
        assert len(gg)==1
        root_ids[domain]={'net':net,'ref':r,'pin':p}
        for ly in ('In1.Cu','In4.Cu'):
            ss=[v['shape'] for v in gg[0] if v['kind']=='fill' and v['layer']==ly]
            ref[domain,ly]=(ss,STRtree(ss))
    pads={p['uuid']:p for p in h['pads']};via_by={v['uuid']:v for v in h['vias']}
    netxml=ET.parse(files[7]).getroot();pin_types={norm(n.get('name')):{v.get('pintype','') for v in n.findall('node')} for n in netxml.find('nets')}
    candidates=[];census=[]
    for net,gg in groups.items():
        domain=domains.get(net)
        required={i for i,q in enumerate(gg) if any(r['kind']=='pad' and r.get('pin') for r in q)}
        if len(required)<2:continue
        why=[]
        if domain not in ROOTS:why.append('domain_reference_not_in_this_bounded_pass')
        if any(t.startswith('power_') for t in pin_types.get(net,set())):why.append('source_power_pin_requires_current_route_qualification')
        if not net or net in {v[0] for v in ROOTS.values()} or any(t in net.upper() for t in ('GND','24V','3V3','5V','1V2','POWER','_SUPPLY','VCC')):why.append('power_or_ground_or_unnamed_excluded')
        if why:census.append({'net':net,'required_groups':len(required),'excluded':why});continue
        ports=collections.defaultdict(list)
        for gi in required:
            for r in gg[gi]:
                ly=r['layer']
                if ly not in LAYERS:continue
                if (r['kind']=='track' and not r['source'].get('m')) or (r['kind']=='pad' and pads[r['uuid']]['smd']):
                    ports[ly].append({'group':gi,'uuid':r['uuid'],'kind':r['kind'],'shape':r['shape'],'ref':r.get('ref'),'pin':r.get('pin')})
        count=0
        for ly,pp in ports.items():
            tree=STRtree([q['shape'] for q in pp]);edges=collections.defaultdict(list)
            for i,p in enumerate(pp):
                x0,y0,x1,y1=p['shape'].bounds
                for j in tree.query(box(x0-16,y0-16,x1+16,y1+16)):
                    j=int(j);q=pp[j]
                    if i>=j or p['group']==q['group']:continue
                    length=p['shape'].distance(q['shape'])
                    if not .000002<length<=16:continue
                    pa,pb=nearest_points(p['shape'],q['shape'])
                    aa=[round(pa.x,6),round(pa.y,6)];bb=[round(pb.x,6),round(pb.y,6)]
                    edge=tuple(sorted((p['group'],q['group'])))
                    edges[edge].append((length,{**p,'at':aa},{**q,'at':bb}))
            for edge,ps in edges.items():
                # Diverse existing entry points; avoid all 8 candidates being
                # almost-coincident endpoints of one old track fanout.
                picked=[];seen_locations=set()
                for length,p,q in sorted(ps,key=lambda x:x[0]):
                    loc=(tuple(round(v,2) for v in p['at']),tuple(round(v,2) for v in q['at']))
                    if loc in seen_locations:continue
                    seen_locations.add(loc);picked.append((length,p,q))
                    if len(picked)>=16:break
                for length,p,q in picked:candidates.append({'net':net,'domain':domain,'layer':ly,'span':length,'edge':edge,'a':p,'b':q});count+=1
        census.append({'net':net,'domain':domain,'required_groups':len(required),'endpoint_candidates':count,'same_layer_entry_ports':sum(len(v) for v in ports.values())})
    candidates.sort(key=lambda c:(c['span'],c['net'],c['layer']))
    put('remaining-group-census.json',census)
    print('CANDIDATES',len(candidates),'unresolved_nets',len(census),flush=True)
    # Build actual geometry spatial indices only; no connectivity graph.
    records={ly:[] for ly in K.LAYERS};holes=[]
    def add(uid,net,kind,ly,s,local=0.,error=0.):
        if not s.is_empty:records[ly].append({'uuid':uid,'net':norm(net),'kind':kind,'shape':s,'local':local,'error':error})
    for p in h['pads']:
        for ly,ps in p['layers'].items():
            for s in L.poly(ps):add(p['uuid'],p['net'],'pad',ly,s,error=.005)
        for s in L.poly(p.get('hole') or []):holes.append({'uuid':p['uuid'],'shape':s,'error':.005})
    for t in h['tracks']:
        if t.get('m'):s=L.body(t)
        else:s=outer(LineString([t['a'],t['b']]),t['w']/2)
        add(t['uuid'],t['net'],'track',t['layer'],s)
    for v in h['vias']:
        s=outer(Point(v['x'],v['y']),v['d']/2)
        for ly in v['flashed']:add(v['uuid'],v['net'],'via',ly,s)
        holes.append({'uuid':v['uuid'],'shape':outer(Point(v['x'],v['y']),v['drill']/2),'error':0.})
    for z in h['zones']:
        for ly,ps in z['fills'].items():
            for s in L.poly(ps):add(z['uuid'],z['net'],'actual_filled_zone',ly,s,float(z['clearance_mm']))
    for s in h['shapes']:
        for p in L.poly(s['poly']):add(s['uuid'],s['net'],'Cu_graphic',s['layer'],p)
    old=json.loads(files[6].read_text())['copper'];current=json.loads(files[4].read_text())['copper'];peer=[]
    removed=set(old)-set(current)
    for ly in records:records[ly]=[r for r in records[ly] if r['uuid'] not in removed]
    for uid,r in current.items():
        if uid in old and r==old[uid]:continue
        if r['kind']=='segment':
            a=[v/1e6 for v in r['start_IU']];b=[v/1e6 for v in r['end_IU']];s=outer(LineString([a,b]),r['width_IU']/2e6)
            add(uid,r['raw_net'],'frozen_current_peer_track',r['layer'],s);peer.append((norm(r['raw_net']),r['layer'],s))
        elif r['kind']=='via':
            s=outer(Point([v/1e6 for v in r['at_IU']]),max(r['diameters_IU'].values())/2e6)
            for ly in K.LAYERS:add(uid,r['raw_net'],'frozen_current_peer_via',ly,s)
            holes.append({'uuid':uid,'shape':outer(Point([v/1e6 for v in r['at_IU']]),r['drill_IU']/2e6),'error':0.})
        else:raise ValueError('Unhandled current peer '+r['kind'])
    # The two earlier GPU track proposals remain hard peers, without credit.
    gpu=HERE/'gpu-existing-In3-ports-r1/source-bound-track-nominees.json';pins[str(gpu)]=sha(gpu)
    for c in json.loads(gpu.read_text()):
        for t in c['tracks']:add(t['uuid'],t['net'],'prospective_GPU_peer','In3.Cu',body([t['a'],t['b']]))
    trees={ly:STRtree([r['shape'] for r in rr]) for ly,rr in records.items()};ht=STRtree([r['shape'] for r in holes])
    reserve,exemptions=K.A.reservations();pins.update(K.A.READS)
    hard={ly:[] for ly in LAYERS}
    for rows,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
        for r in rows:
            if not isreserve and not r.get('no_tracks'):continue
            for ly in set(r['layers'])&set(LAYERS):
                for s in L.poly(r['outline']):hard[ly].append({'name':r.get('name',r.get('uuid')),'shape':s,'exempt':exemptions.get(r.get('name',''),set()) if isreserve else set()})
    board=unary_union(L.poly(h['outline'])).buffer(-.525)
    selected=[];attempts=[];parents={};caps={};reasons=collections.Counter()
    def find(key):
        parents.setdefault(key,key)
        while parents[key]!=key:parents[key]=parents[parents[key]];key=parents[key]
        return key
    def ground(domain,ly,window):
        ss,tree=ref[domain,ly]
        return unary_union([ss[int(i)].intersection(window) for i in tree.query(window)])
    # Honor explicit native DRU track-disallow area rules as well as native
    # no-track flags and the inherited conservative reserved-area envelope.
    dru=files[9].read_text()
    for condition in re.findall(r'\(condition "([^"\n]*)"\)\s*\(constraint disallow track via zone\)',dru):
        names=re.findall(r"A\.intersectsArea\('([^']+)'\)",condition)
        if not names:raise ValueError('Unhandled native track disallow condition')
        ex={norm(s) for s in re.findall(r"A\.NetName != '([^']+)'",condition)}
        for area in h['rule_areas']:
            if area.get('name') not in names:continue
            for ly in set(area['layers'])&set(LAYERS):
                for s in L.poly(area['outline']):hard[ly].append({'name':area['name'],'shape':s,'exempt':ex})
    gpu_trials=0
    print('SPATIAL_INDICES_READY',sum(map(len,records.values())),'Cu rows',flush=True)
    for ci,c in enumerate(candidates):
        net,ly=c['net'],c['layer'];ga,gb=c['edge'];aa,bb=c['a'],c['b'];a,b=aa['at'],bb['at']
        if find((net,ga))==find((net,gb)):continue
        roi=box(min(a[0],b[0])-1.2,min(a[1],b[1])-1.2,max(a[0],b[0])+1.2,max(a[1],b[1])+1.2)
        foreign=[]
        for i in trees[ly].query(roi):
            r=records[ly][int(i)]
            if r['net']==net:continue
            gap=.15 if domains.get(r['net'])==c['domain'] else .6
            foreign.append((r,max(gap,r['local'])+.025+r['error']))
        ownvia={uid for uid,v in via_by.items() if norm(v['net'])==net and any(math.dist((v['x'],v['y']),p)<.000002 for p in (a,b))}
        ownpad={p['uuid'] for p in (aa,bb) if p['kind']=='pad'}
        drill=[holes[int(i)] for i in ht.query(roi) if holes[int(i)]['uuid'] not in ownvia|ownpad]
        refs=ground(c['domain'],REF_LAYER[ly],roi)
        localrules=[r for r in hard[ly] if net not in r['exempt'] and r['shape'].intersects(roi)]
        chosen=None;failcounts=collections.Counter();proposals=list(paths(a,b))
        # CUDA proposals use the exact conservative vector free domain, then
        # every rounded segment is rechecked below. No raster result is proof.
        if gpu_trials<64:
            cuts=[outer(r['shape'].intersection(roi),.1+gap) for r,gap in foreign]
            cuts.extend(outer(q['shape'],.375+q['error']) for q in drill)
            cuts.extend(outer(r['shape'],.125) for r in localrules)
            for cc in selected:
                if cc['layer']==ly and cc['net']!=net:cuts.append(outer(cc['shape'],.275 if domains.get(cc['net'])==c['domain'] else .725))
            free=roi.intersection(board.buffer(-.10001)).intersection(refs.buffer(-.10001)).difference(unary_union(cuts))
            if free.covers(Point(a)) and free.covers(Point(b)):
                p,gpuinfo=GPU.cuda_route(free,a,b,roi,.05);gpu_trials+=1
                if p:proposals.append([[round(x,6),round(y,6)] for x,y in p])
        for path in proposals:
            s=body(path);fails=[]
            if not board.covers(s):fails.append('board_edge')
            if s.intersection(aa['shape']).area<.000001 or s.intersection(bb['shape']).area<.000001:fails.append('finite_actual_endpoint_contact')
            for r,gap in foreign:
                if s.distance(r['shape'])<gap:fails.append('foreign_'+r['kind']);break
            for h0 in drill:
                if s.distance(h0['shape'])<.275+h0['error']:fails.append('unrelated_drill');break
            if any(s.distance(r['shape'])<.025 for r in localrules):fails.append('rule')
            for cc in selected:
                if cc['layer']==ly and cc['net']!=net:
                    gap=.175 if domains.get(cc['net'])==c['domain'] else .625
                    if s.distance(cc['shape'])<gap:fails.append('selected_peer');break
            if not s.difference(refs).is_empty:fails.append('actual_source_reference_gap')
            if not fails:
                same=unary_union([p for n,l,p in peer if n==net and l==ly and p.intersects(roi)])
                if s.difference(same).area<.000001:fails.append('already_current_peer_Cu')
            if fails:failcounts.update(set(fails));continue
            chosen=(path,s);break
        reasons.update(failcounts)
        row={'candidate_index':ci,'net':net,'domain':c['domain'],'layer':ly,'actual_required_group_edge':list(c['edge']),'span_mm':c['span'],
             'endpoints':[{k:v for k,v in e.items() if k!='shape'} for e in (aa,bb)],'bounded_attempt_failure_counts':dict(failcounts),'PASS':chosen is not None}
        if chosen:
            path,s=chosen;row.update(path=path,length_mm=LineString(path).length,actual_source_reference={'root':root_ids[c['domain']],'actual_layer':REF_LAYER[ly],'full_body_covered':True},
                                    finite_actual_endpoint_contact_mm2=[s.intersection(e['shape']).area for e in (aa,bb)],body=info(s))
            tracks=[]
            for j,(p,q) in enumerate(zip(path,path[1:])):
                uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'R299-broad-existing-layer-bridge:'+str(ci)+':'+str(j)))
                assert uid not in current
                t={'uuid':uid,'net':next(p['net'] for p in h['pads'] if norm(p['net'])==net),'layer':ly,'w':.2,'a':p,'b':q};tracks.append(t)
            row['tracks']=tracks;selected.append({**row,'shape':s});parents[find((net,ga))]=find((net,gb))
            print('SELECT',len(selected),net,ly,round(row['length_mm'],3),flush=True)
        attempts.append(row)
        if ci%200==0:
            put('progress.json',{'candidate_index':ci,'total_candidates':len(candidates),'selected':len(selected),'elapsed_seconds':time.monotonic()-t0})
    put('bounded-bridge-attempts.json',attempts)
    packets=[]
    for r in selected:
        ops=[]
        for t in r['tracks']:
            f=OUT/(t['uuid']+'.add-segment-fragment');f.write_bytes(native(t));ops.append({'action':'add_exact_segment','UUID':t['uuid'],'file':str(f),'SHA256':sha(f)})
        wf=OUT/('candidate-'+str(r['candidate_index'])+'-body.wkb');wf.write_bytes(r['shape'].wkb)
        packets.append({k:v for k,v in r.items() if k!='shape'}|{'operations':ops,'body_WKB_file':str(wf),'body_WKB_file_SHA256':sha(wf)})
    for module in list(sys.modules.values()):
        f=Path(getattr(module,'__file__',''))
        if f.is_file() and f.suffix=='.py' and str(ROOT).lower() in str(f.resolve()).lower():pins[str(f.resolve())]=sha(f)
    report={'status':'SHORT_ACTUAL_CACHED_GROUP_EXISTING_LAYER_BRIDGES_HOST_SCREEN_NATIVE_AFTER_OPEN','actual_R299_parent_unfilled_SHA256':'7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2',
            'frozen_current_peer_SHA256':pins[str(files[3])],'screened_endpoint_pairs':len(attempts),'bounded_candidate_pairs':len(candidates),'selected_nonredundant_bridges':len(selected),
            'selected_nets':len({r['net'] for r in selected}),'new_tracks':sum(len(r['tracks']) for r in selected),'packets':packets,'bounded_failure_counts':dict(reasons),
            'strict_actual_source_full_body_reference_no_caps_or_fill_carves':True,'inherited_same_layer_endpoint_entries_only':True,'new_vias':0,'removed_Cu':0,'new_or_changed_planes':0,'CUDA_trials':gpu_trials,'CUDA_GPU':GPU.torch.cuda.get_device_name(0),
            'all_input_SHA256':pins,'inputs_unchanged':all(sha(Path(f))==v for f,v in pins.items()),'native_jobs':0,'native_full_after_source_parity_oldrefs_current_SI':'OPEN_REQUIRED',
            'CPU_affinity':proc.cpu_affinity(),'numeric_threads':2,'PCB_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-t0}
    put('receipt.json',report);print(json.dumps({k:report[k] for k in ('selected_nonredundant_bridges','selected_nets','new_tracks','inputs_unchanged','elapsed_seconds')}),flush=True)

if __name__=='__main__':main()
