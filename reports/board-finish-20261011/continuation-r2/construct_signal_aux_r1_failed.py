"""Reconcile one exact ordinary route with the independently audited AUX repair.

Only immutable byte-level copper operations are supported. This does not adopt
the candidate or substitute for native refill, connectivity or electrical gates.
"""
import collections,hashlib,json,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
S,C=F.S,F.C
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
HERE=F.HERE;OUT=HERE/'signal-aux-r1';READS={}
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();READS[str(p)]=hashlib.sha256(raw).hexdigest();return raw
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;read(Path(__file__))
    audit=json.loads(read(HERE/'coupled-recovery/aux-exact-audit-r3.json'))
    recipe=json.loads(read(HERE/'coupled-recovery/aux-power-escape-r2.json'))
    route=json.loads(read(HERE/'ordinary-routes-r1/result.json'))
    source=read(F.SOURCE);aux=read(HERE/'coupled-recovery/aux-power-escape-r2-host-only.kicad_pcb')
    if C.sha(source)!=audit['source_sha256'] or C.sha(aux)!=audit['candidate_sha256']:raise ValueError('Frozen board mismatch')
    for p,h in recipe['read_files_sha256'].items():
        if C.sha(read(p))!=h:raise ValueError('AUX construction dependency changed '+p)
    if audit['pad_relationship_failures'] or audit['clearance_errors'] or audit['surviving_physical_contact_failures']:raise ValueError('AUX host audit failed')
    before,current=C.inventory(source),C.inventory(aux)
    if before[0]!=current[0] or before[2]!=current[2] or before[5]!=current[5]:raise ValueError('Unchanged physical definitions required')
    paths=[(r['net'],p) for r in route['results'] for p in r['paths']]
    if len(paths)!=1:raise ValueError('Expected one frozen ordinary route')
    net,path=paths[0]
    if S.norm(net)!='/motherboard_safety_sensor/DIC_SENSOR_SCL' or path['layer']!='F.Cu' or path['new_vias']:raise ValueError('Unexpected signal route')
    g=F.geometry();arcs={t['uuid']:t for t in g['tracks'] if t.get('kind')=='arc'}
    g['tracks']=[]
    for uid,ch in current[4].items():
        kind=C.pcbtext.chunk_kind(ch)
        if kind=='segment':g['tracks'].append({'uuid':uid,'net':S.overlay_tool.netname(ch),'a':S.overlay_tool.numbers(ch,'start'),'b':S.overlay_tool.numbers(ch,'end'),'w':S.overlay_tool.scalar(ch,'width'),'layer':C.pcbtext.chunk_layer(ch)})
        elif kind=='arc':g['tracks'].append(arcs[uid])
    # The restored original DVDT via is outside this F signal window. Retain its
    # original physical annuli explicitly; current annuli stay freshly native.
    vm={v['uuid']:v for v in g['vias']}
    old=json.loads(read(S.overlay_tool.base.GEOM));oldvm={v['uuid']:v for v in old['vias']}
    g['vias']=[dict(vm.get(uid,oldvm.get(uid)),flashed=vm.get(uid,oldvm.get(uid))['flashed']) for uid,ch in current[4].items() if C.pcbtext.chunk_kind(ch)=='via']
    reserved=json.loads(read(F.C06/'alternate-r07/reserved-r07.json'));import re
    ex={}
    for line in read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    Model=F.exact_model_class();model=Model(g,reserved,ex)
    layer=path['layer'];points=path['points_mm'];errors=[];nearest=collections.defaultdict(lambda:float('inf'))
    for index,(a,b) in enumerate(zip(points,points[1:])):
        body=LineString([a,b]).buffer(.1,resolution=128)
        for i in model.trees[layer].query(body.buffer(.75),predicate='intersects'):
            r=model.records[layer][i]
            if r.get('net')==S.norm(net):continue
            req=.25 if r['kind']=='hole' else .15 if r.get('domain')=='DOM_LOGIC' else .6
            gap=body.distance(r['shape']);nearest[r['kind']]=min(nearest[r['kind']],gap)
            if gap<req+.010-1e-9:errors.append({'segment':index,'obstacle':r['uuid'],'kind':r['kind'],'gap_mm':gap,'required_with_geometry_guard_mm':req+.010})
        for r in model.hard[layer]:
            if S.norm(net) not in r['exempt'] and body.intersects(r['shape'].buffer(.010)):errors.append({'segment':index,'hard_area':r['name']})
    ref='In1.Cu';fill=unary_union([r['shape'] for r in model.records[ref] if r['kind']=='fill' and r['net']=='/LOGIC_GND'])
    conductive=unary_union([fill]+[r['shape'] for r in model.records[ref] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][ref]))
    pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms);rooted=fill.intersection(unary_union([p for p in pieces if p.intersects(anchor)]))
    body=LineString(points).buffer(.1,resolution=128);uncovered=body.difference(rooted);center_uncovered=LineString(points).difference(rooted)
    # Full body reference coverage is required for this path, beyond the original
    # exploratory centreline screen. An antipad exception is not needed here.
    if uncovered.area>1e-8:errors.append({'reference_body_uncovered_mm2':uncovered.area,'reference_centerline_uncovered_mm':center_uncovered.length})
    added=[];chunks=[]
    for a,b in zip(points,points[1:]):
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-continuation-r2/DIC_SENSOR_SCL/'+repr((a,b,.2))))
        f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
        chunk=(f'\t(segment\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "{S.norm(net)}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
        if uid in current[3]:raise ValueError('UUID collision')
        chunks.append(chunk);added.append({'uuid':uid,'chunk_sha256':C.sha(chunk)})
    candidate=current[0]+b''.join(current[1])+b''.join(chunks)+current[2]
    inv=C.inventory(candidate)
    if inv[5]!=current[5] or any(inv[3].get(u)!=ch for u,ch in current[3].items()):raise ValueError('Retained AUX items changed')
    F.READS.update(S.READS);READS.update(F.READS)
    for p,h in READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Input changed '+p)
    report={'schema':'signal-aux-construction-r1','verdict':'HOST_READY_NATIVE_OPEN' if not errors else 'HOST_AUDIT_FAIL','source_sha256':C.sha(source),'aux_sha256':C.sha(aux),'candidate_sha256':C.sha(candidate),'new_signal_items':added,'geometry_errors':errors,'nearest_gap_by_kind_mm':dict(nearest),'signal_reference':{'plane':ref,'source_pad':'J11001.2#0','body_uncovered_mm2':uncovered.area,'centerline_uncovered_mm':center_uncovered.length},'source_paths':paths,'removed_source_items':audit['deleted_items'],'restored_original_items':audit['restored_original_items'],'aux_new_items':audit['new_items'],'inputs':READS,'native_drc':False,'adopted':False,'manufacturing_ready':False}
    (OUT/'construction.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    if not errors:(OUT/'signal-aux-host-only.kicad_pcb').write_bytes(candidate)
    print(json.dumps({k:report[k] for k in ('verdict','candidate_sha256','geometry_errors','signal_reference')}),flush=True)
if __name__=='__main__':main()
