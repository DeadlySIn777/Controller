"""Exact bounded ordinary LG-return proposals for three new In3 entries.

Host geometry only. The immutable actual R299 fills remain hard obstacles;
current composed-peer Cu is separately rebound from its exact native ledger.
"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='2'
from pathlib import Path
import collections, hashlib, json, math, pickle, re, sys, time, uuid
import psutil
proc=psutil.Process(); proc.cpu_affinity(list(range(16,28))); proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import shapely
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely import STRtree

ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
CACHE=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
CURRENT=ROOT/'reports/board-finish-20261017/combined-route-stage-r1'
OUT=HERE/'paired-returns-prospective-antipads-r1'
BASE=OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb'
for d in (OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'): sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K; L=N.L; norm=L.norm
LG='/LOGIC_GND'; GUARD=.025; PAD_ERROR=.005
TARGETS=[('DIR10_DEST','2375b24c-2ef4-4289-a726-c5ef84b84f11'),
         ('DIR10_SOURCE','962ffd3a-8436-4a45-bfc0-9f7aa24e2a42'),
         ('MOTOR_TX_GATE_B_SOURCE','9074b648-652f-40dd-a304-1d19e982955e')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v): (OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def outer(s,r):
    return shapely.set_precision(s.buffer((r+.000002)/math.cos(math.pi/256),quad_segs=64),.000001)
def lower_ring(c,rv,rh):
    return Point(c).buffer(rv-.000002,quad_segs=256).difference(outer(Point(c),rh))
def summary(s):
    return {'area_mm2':s.area,'bounds':list(s.bounds) if not s.is_empty else None,'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def parse(txt):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+',txt); st=[]; root=None
    for t in tokens:
        if t=='(':
            v=[]
            if st: st[-1].append(v)
            else:root=v
            st.append(v)
        elif t==')': st.pop()
        else: st[-1].append(json.loads(t) if t.startswith('"') else t)
    assert not st
    return root
def field(tree,name,default=None):
    a=[r[1:] for r in tree if isinstance(r,list) and r and r[0]==name]
    assert len(a)<=1
    return a[0] if a else default
def chunk_at(txt,start):
    depth=0; quote=False; esc=False
    for end in range(start,len(txt)):
        c=txt[end]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':quote=False
        elif c=='"':quote=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return txt[start:end+1]
    raise ValueError('unclosed')
def local_pad_rules(txt,pads):
    fps={}; answer={}
    for p in pads:
        uid=p['uuid']; i=txt.index('"'+uid+'"')
        start=txt.rfind('\n\t(footprint ',0,i)+2
        assert start>1
        if start not in fps: fps[start]=parse(chunk_at(txt,start))
        fp=fps[start]; pp=[r for r in fp if isinstance(r,list) and r and r[0]=='pad' and field(r,'uuid')==[uid]]
        assert len(pp)==1
        pp=pp[0]
        def inherited(key):
            v=field(pp,key)
            if v is None or float(v[0])==0: v=field(fp,key)
            return float(v[0]) if v else 0.
        size=[float(v) for v in field(pp,'size')]
        mask=inherited('solder_mask_margin')
        paste=inherited('solder_paste_margin')
        ratio=inherited('solder_paste_margin_ratio')
        # Full dimension times positive ratio is a conservative upper bound
        # even if the native definition applies the ratio per full opening.
        expansion=max(0.,mask,paste+max(size)*max(0.,ratio))
        answer[uid]={'mask_mm':mask,'paste_mm':paste,'paste_ratio':ratio,'opening_expansion_upper_mm':expansion,
                     'local_clearance_mm':max(0.,inherited('clearance')),'pad_size_mm':size,
                     'native_footprint_chunk_SHA256':hashlib.sha256(chunk_at(txt,start).encode()).hexdigest()}
    return answer

def main():
    assert not OUT.exists();OUT.mkdir()
    t0=time.monotonic()
    files=[CACHE/'actual-combined-full-after-model.pkl',CACHE/'actual-combined-full-after-all-net-groups.pkl',
           CACHE/'actual-graph-cache-receipt.json',BASE,CURRENT/'native/board.kicad_pcb',
           CURRENT/'all-copper-expected.json',CURRENT/'construction-receipt.json',
           OLD/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json',
           HERE/'gpu-existing-In3-native-packet-r1/exact-additive-native-track-manifest.json',Path(__file__)]
    pins={str(f):sha(f) for f in files}
    assert pins[str(files[0])]=='c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806'
    assert pins[str(files[1])]=='c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd'
    assert pins[str(BASE)]=='6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632'
    assert pins[str(CURRENT/'native/board.kicad_pcb')]=='758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad'
    put('launch.json',{'input_SHA256':pins,'CPU_affinity':proc.cpu_affinity(),'new_board_written':False})
    print('LOAD_ACTUAL_SOURCE',flush=True)
    h=pickle.loads(files[0].read_bytes()); groups=pickle.loads(files[1].read_bytes())
    roots=[q for q in groups[LG] if any(r['kind']=='pad' and r.get('ref')=='J11001' and str(r.get('pin'))=='2' for r in q)]
    assert len(roots)==1
    root=roots[0]; del groups
    vias={v['uuid']:v for v in h['vias']}; targets=[]
    for name,uid in TARGETS:
        v=vias[uid]; targets.append({'name':name,'signal_via_UUID':uid,'at_mm':[v['x'],v['y']],'signal_net':norm(v['net'])})
    roi=unary_union([box(q['at_mm'][0]-2.1,q['at_mm'][1]-2.1,q['at_mm'][0]+2.1,q['at_mm'][1]+2.1) for q in targets])
    source={ly:unary_union([r['shape'].intersection(roi) for r in root if r['kind']=='fill' and r['layer']==ly and r['shape'].intersects(roi)]) for ly in ('In1.Cu','In4.Cu')}
    del root
    localpads=[p for p in h['pads'] if roi.distance(Point(p['x'],p['y']))<2]
    txt=BASE.read_bytes().decode()
    pad_rules=local_pad_rules(txt,localpads); del txt
    put('local-pad-opening-rules.json',pad_rules)
    records=[]; holes=[]; smd=[]
    def add(uid,net,kind,ly,shape,local=0.,error=0.):
        if not shape.is_empty and shape.intersects(roi):
            records.append({'uuid':uid,'net':norm(net),'kind':kind,'layer':ly,'shape':shape.intersection(roi),
                            'clearance':max(.15 if h['domains_normalized'].get(norm(net))=='DOM_LOGIC' else .6,local)+GUARD+error})
    for p in localpads:
        rules=pad_rules[p['uuid']]
        for ly,polys in p['layers'].items():
            for s in L.poly(polys):
                add(p['uuid'],p['net'],'pad',ly,s,rules['local_clearance_mm'],PAD_ERROR)
                if ly in ('F.Cu','B.Cu') and (p['smd'] or p['ref'].startswith('J')) and s.intersects(roi):
                    smd.append({'uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':ly,'shape':s,'expansion':rules['opening_expansion_upper_mm']})
        for s in L.poly(p.get('hole') or []):
            if s.intersects(roi):holes.append({'uuid':p['uuid'],'kind':'pad_drill','shape':s,'error':PAD_ERROR})
    for v in h['vias']:
        if roi.distance(Point(v['x'],v['y']))>1:continue
        c=Point(v['x'],v['y']); shape=outer(c,v['d']/2)
        for ly in v['flashed']:add(v['uuid'],v['net'],'actual_flashed_via',ly,shape)
        holes.append({'uuid':v['uuid'],'kind':'via_drill','shape':outer(c,v['drill']/2),'error':0.})
    for t in h['tracks']:
        if roi.distance(LineString([t['a'],t['b']]))>t['w']/2+.001:continue
        assert 'm' not in t,'Unhandled arc'
        add(t['uuid'],t['net'],'segment',t['layer'],outer(LineString([t['a'],t['b']]),t['w']/2))
    for z in h['zones']:
        for ly,ps in z['fills'].items():
            for s in L.poly(ps):add(z['uuid'],z['net'],'actual_filled_zone',ly,s,float(z.get('clearance_mm',.15)))
    for s in h['shapes']:
        for p in L.poly(s['poly']):add(s['uuid'],s['net'],'Cu_graphic',s['layer'],p)
    # Rebind current source changes. No added/changed physical primitive may
    # enter these windows. Metadata-equivalent pad angles are separately proved.
    old=json.loads(files[7].read_text())['copper']; current=json.loads(files[5].read_text())['copper']
    changed=[]
    for uid in sorted(set(old)|set(current)):
        a=old.get(uid); b=current.get(uid)
        if a==b:continue
        for state,r in (('old',a),('current',b)):
            if not r:continue
            if r['kind']=='segment':s=outer(LineString([[v/1e6 for v in r['start_IU']],[v/1e6 for v in r['end_IU']]]),r['width_IU']/2e6)
            elif r['kind']=='via':s=outer(Point([v/1e6 for v in r['at_IU']]),max(r['diameters_IU'].values())/2e6)
            else:raise ValueError('Unhandled peer '+r['kind'])
            assert roi.distance(s)>1.0,(uid,state,'Current peer in local return region')
            changed.append({'UUID':uid,'state':state,'kind':r['kind'],'bounds_mm':list(s.bounds),'distance_to_any_ROI_mm':roi.distance(s)})
    put('current-composed-peer-rebind.json',{'actual_current_SHA256':pins[str(CURRENT/'native/board.kicad_pcb')],'changed_primitive_states':changed,'all_outside_local_windows_by_mm':1.0})
    gpu=json.loads(files[8].read_text())
    for packet in gpu['packets']:
        for op in packet['operations']:
            f=Path(op['file']); assert sha(f)==op['SHA256']; pins[str(f)]=sha(f)
            tree=parse(f.read_text()); a=[float(v) for v in field(tree,'start')];b=[float(v) for v in field(tree,'end')]
            add(op['UUID'],packet['net'],'prospective_GPU_track','In3.Cu',outer(LineString([a,b]),.1))
    reserve,exemptions=K.A.reservations(); rules=[]
    for rows,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
        for r in rows:
            if not isreserve and not r.get('no_vias'):continue
            if isreserve and LG in exemptions.get(r.get('name',''),set()):continue
            for s in L.poly(r['outline']):
                if s.intersects(roi):rules.append({'name':r.get('name',r.get('uuid')),'shape':s,'layers':r['layers']})
    pins.update(K.A.READS)
    foreign=[r for r in records if r['net']!=LG]
    print('LOCAL_EXACT_RECORDS',len(records),'foreign',len(foreign),'holes',len(holes),'outer_pads',len(smd),flush=True)
    board=unary_union(L.poly(h['outline'])); results=[]; nominees=[]
    for target in targets:
        c=Point(target['at_mm']); window=box(c.x-1.001,c.y-1.001,c.x+1.001,c.y+1.001)
        # Strict upper bound and included lower bound survive native nm rounding.
        annulus=c.buffer(.999995,quad_segs=512).difference(outer(c,.900005))
        for diameter,drill in ((.6,.3),(.5,.2)):
            rv,rh=diameter/2,drill/2
            local=[r for r in foreign if r['shape'].distance(window)<rv+r['clearance']]
            cuts=[outer(r['shape'].intersection(window.buffer(1.1)),rv+r['clearance']) for r in local if r['kind']!='actual_filled_zone']
            hh=[q for q in holes if q['shape'].distance(window)<rh+.25+GUARD+q['error']]
            cuts.extend(outer(q['shape'],rh+.25+GUARD+q['error']) for q in hh)
            outerpads=[q for q in smd if q['shape'].distance(window)<rv+.1+q['expansion']+GUARD+PAD_ERROR]
            cuts.extend(outer(q['shape'],rv+.1+q['expansion']+GUARD+PAD_ERROR) for q in outerpads)
            cuts.extend(outer(r['shape'],rv+GUARD) for r in rules if r['shape'].distance(window)<rv+GUARD)
            legal=annulus.intersection(board.buffer(-(.5+rv+GUARD))).difference(unary_union(cuts))
            both_full=legal.intersection(source['In1.Cu'].buffer(-(rv+.00001))).intersection(source['In4.Cu'].buffer(-(rv+.00001)))
            entry={'target':target,'via_diameter_mm':diameter,'drill_mm':drill,'exact_center_region':summary(legal),'full_disc_actual_J1_In1_In4_support_center_region':summary(both_full),'all_foreign_Cu_records_considered':len(local),'holes_considered':len(hh),'ordinary_outer_pad_records_considered':len(outerpads)}
            centers=[]
            for region,full in ((both_full,True),(legal,False)):
                if region.is_empty:continue
                parts=list(region.geoms) if hasattr(region,'geoms') else [region]
                for pp in sorted(parts,key=lambda x:-x.area)[:20]:
                    centers.append((pp.representative_point(),full))
                for angle in range(720):
                    p=Point(c.x+.95*math.cos(angle*math.pi/360),c.y+.95*math.sin(angle*math.pi/360))
                    if region.covers(p):centers.append((p,full))
                if full and centers:break
            checked=[]
            for p,full in centers:
                at=[round(p.x,6),round(p.y,6)];p=Point(at);distance=p.distance(c)
                if not .9<=distance<1.:continue
                if not legal.covers(p):continue
                ring=lower_ring(at,rv,rh)
                contacts={ly:ring.intersection(s).area for ly,s in source.items()}
                if min(contacts.values())<.002:continue
                failures=[]
                body=outer(p,rv);hole=outer(p,rh)
                for r in local:
                    if r['kind']=='actual_filled_zone':continue
                    gap=body.distance(r['shape'])
                    if gap+1e-9<r['clearance']:failures.append({'kind':'foreign_Cu','UUID':r['uuid'],'layer':r['layer'],'gap_mm':gap,'required_mm':r['clearance']})
                for q in hh:
                    if hole.distance(q['shape'])+1e-9<.25+GUARD+q['error']:failures.append({'kind':'hole','UUID':q['uuid']})
                for q in outerpads:
                    if body.distance(q['shape'])+1e-9<.1+q['expansion']+GUARD+PAD_ERROR:failures.append({'kind':'outer_pad','UUID':q['uuid']})
                for r in rules:
                    if body.distance(r['shape'])+1e-9<GUARD:failures.append({'kind':'rule','name':r['name']})
                if failures:continue
                checked.append({'at_mm':at,'signal_to_return_center_distance_mm':distance,'full_disc_support':full,'actual_J1_root_annulus_contact_lower_mm2':contacts,
                                'lower_annulus_area_mm2':ring.area,'minimum_foreign_Cu_excess_mm':min((body.distance(r['shape'])-r['clearance'] for r in local),default=None),
                                'minimum_drill_gap_excess_mm':min((hole.distance(q['shape'])-.25-GUARD-q['error'] for q in hh),default=None),
                                'prospective_foreign_fill_antipads':[{'zone_UUID':r['uuid'],'net':r['net'],'layer':r['layer'],'antipad_radius_with_guard_mm':rv+r['clearance'],'old_actual_fill_removed_upper_mm2':r['shape'].intersection(outer(p,rv+r['clearance'])).area} for r in local if r['kind']=='actual_filled_zone' and r['shape'].intersects(outer(p,rv+r['clearance']))]})
            checked.sort(key=lambda p:(not p['full_disc_support'],-min(p['actual_J1_root_annulus_contact_lower_mm2'].values()),-min(p['minimum_foreign_Cu_excess_mm'] or 9,p['minimum_drill_gap_excess_mm'] or 9)))
            entry['passing_unique_centers']=len({tuple(q['at_mm']) for q in checked});entry['best_centers']=checked[:8]
            if not checked:
                # Conservative per-obstacle coverage explains a bounded miss.
                why=[]
                for r in local:
                    hit=annulus.intersection(outer(r['shape'],rv+r['clearance']))
                    if hit.area>0:why.append({'kind':r['kind'],'UUID':r['uuid'],'net':r['net'],'layer':r['layer'],'excluded_center_area_mm2':hit.area,'clearance_with_guard_mm':r['clearance']})
                entry['largest_foreign_Cu_exclusions']=sorted(why,key=lambda q:-q['excluded_center_area_mm2'])[:12]
            else:
                best=checked[0]; uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-currentR299-ordinary-LG-return:'+target['signal_via_UUID']+':'+str(best['at_mm'])+':'+str(diameter)))
                nominees.append({'signal':target,'return_UUID':uid,'net':LG,'diameter_mm':diameter,'drill_mm':drill,**best})
            results.append(entry)
            print(target['name'],diameter,'free',round(legal.area,8),'root_full',round(both_full.area,8),'sites',len(checked),flush=True)
            if checked:break
    for p in (HERE/'gpu_existing_port_routes.py',HERE/'freeze_gpu_track_nominees.py'):pins[str(p)]=sha(p)
    # Imported helpers are pinned for THIS replay, not a retroactive certificate.
    for module in list(sys.modules.values()):
        f=Path(getattr(module,'__file__',''))
        if f.is_file() and f.suffix=='.py' and str(ROOT).lower() in str(f.resolve()).lower():pins[str(f.resolve())]=sha(f)
    report={'status':'DIAGNOSTIC_PROSPECTIVE_ANTIPADS_NOT_STRICT_SITES_NO_ADOPTION','results':results,'diagnostic_centers_only_not_nominees':nominees,
            'all_input_SHA256':pins,'inputs_unchanged':all(sha(Path(f))==v for f,v in pins.items()),'actual_current_peer_SHA256':pins[str(CURRENT/'native/board.kicad_pcb')],
            'guard_mm':GUARD,'ordinary_via_outer_pad_landing':'outer Cu gap >= .10 + conservative actual mask/paste expansion + .005 pad polygon error + .025 guard',
            'all_current_actual_foreign_fills_hard':False,'foreign_fill_carve_requires_full_exact_old_relationship_reference_audit':True,'reference_root':'actual unique full-R299 /LOGIC_GND group containing J11001.2; In1/In4 actual fills only',
            'forced_layer_flashes':False,'expanded_owned_signal_caps':False,'native_flashes':'OPEN_REQUIRED','native_full_after':'OPEN_REQUIRED',
            'old_reference_and_new_return_current_SI':'OPEN_REQUIRED','PCB_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-t0}
    put('receipt.json',report)
    print(json.dumps({'nominees':len(nominees),'inputs_unchanged':report['inputs_unchanged'],'elapsed_seconds':report['elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
