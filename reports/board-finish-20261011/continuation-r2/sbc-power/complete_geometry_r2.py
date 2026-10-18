"""Quantized, cross-agent power/control model; no native fill or board save."""
import copy,json,hashlib
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
import combined_overlay_r2 as B
L=B.L;p=B.p
def records(sh):return [[list(q.exterior.coords),[list(x.coords) for x in q.interiors]] for q in p.hubs.components(sh)]
def model(final_frozen=False,with_field=False,coupled_revision='r5',new_root_base=False,allow_prior_geometry=False):
    joint=json.loads((L.OUT/'joint-power-planes-r3.json').read_text());bulk=json.loads((L.OUT/'C94-bulk-feeds-r3.json').read_text())
    field_returns=[]
    if with_field:
        import field_overlay_r4 as F
        g,h,tail,binding,field_returns=F.model(new_root_base)
    else:g,h,tail,binding=B.model(new_root_base)
    newv=joint['new_CORE_bank_vias']+bulk['new_vias'];assert len({q['uuid'] for q in newv})==len(newv)
    assert not {q['uuid'] for q in newv}&{q['uuid'] for q in h['vias']};h={**h,'vias':h['vias']+newv}
    paths=[('SBC-local-F',p.NET,'F.Cu',joint['SBC_F_bus']['geometry_file'])]
    paths += [('CORE-'+q['name']+'-F',L.stage.caps.CORE,'F.Cu',q['geometry_file']) for q in joint['CORE_F_fanouts']]
    paths += [('C94-'+q['pad']+'-F',q['net_raw'],'F.Cu',q['geometry_file']) for q in bulk['C94_F_arms']]
    paths += [('CORE-main-In2',L.stage.caps.CORE,'In2.Cu',bulk['CORE_In2_complete_plane']['geometry_file'])]
    fingers=json.loads((L.OUT/'IO3-restoration-fingers-r4.json').read_text())['restoration_fingers']
    paths += [('IO3-finger-'+str(i),'/IO_3V3','In2.Cu',q['body_file']) for i,q in enumerate(fingers)]
    zones=[]
    for label,net,layer,file in paths:
        path=Path(file);sh=set_precision(from_wkb(path.read_bytes()),1e-6)
        zones.append({'uuid':'prospective-'+label,'label':label,'net':net,'layer':layer,'shape':sh,'geometry_file':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    zones+=field_returns
    if final_frozen:
        receiptpath=L.OUT/('coupled-power-geometry-frozen-'+coupled_revision if with_field else 'full-power-geometry-frozen-r4')/'receipt.json';receipt=json.loads(receiptpath.read_text())
        if not allow_prior_geometry:assert receipt['combined_parent_binding']['parent_board_sha256']==binding['parent_board_sha256']
        else:binding={**binding,'prior_proposal_geometry_parent_sha256':receipt['combined_parent_binding']['parent_board_sha256'],'prior_proposal_geometry_receipt_file':str(receiptpath.resolve()),'prior_proposal_geometry_receipt_sha256':hashlib.sha256(receiptpath.read_bytes()).hexdigest(),'rebinding_requires_fresh_independent_and_native_checks':True}
        zones=[]
        for row in receipt['zones']:
            path=Path(row['geometry_file']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
            zones.append({**row,'net':row['net_raw'],'shape':from_wkb(path.read_bytes())})
    return g,h,tail,binding,zones
def gap(h,a,b):return .15 if h['domains_normalized'].get(p.norm(a))==h['domains_normalized'].get(p.norm(b)) else .6
def foreign_discrete(h,net,layer,newonly=None):
    """Physical Cu and drill envelope only; returns provenance for every cut."""
    out=[]
    for t in h['tracks']:
        if t['layer']==layer and p.norm(t['net'])!=p.norm(net) and (newonly is None or t['uuid'] in newonly):out.append((t['uuid'],p.base.body(t).buffer(gap(h,net,t['net'])+.025)))
    for v in h['vias']:
        if (newonly is None or v['uuid'] in newonly) and p.norm(v['net'])!=p.norm(net):
            radius=v['drill']/2+.25+.025
            if layer in v['flashed']:radius=max(radius,v['d']/2+gap(h,net,v['net'])+.025)
            out.append((v['uuid'],Point(v['x'],v['y']).buffer(radius)))
    for q in h['pads']:
        if p.norm(q['net'])!=p.norm(net) and (newonly is None or q['uuid'] in newonly):
            for sh in p.base.polygons(q['layers'].get(layer,[])):out.append((q['uuid'],sh.buffer(gap(h,net,q['net'])+.025)))
    return out
def projected(g,h,zones):
    """Projected repour, retaining every original zone's provenance."""
    old={q['uuid'] for k in ('tracks','vias','pads') for q in g[k]}
    new={q['uuid'] for k in ('tracks','vias','pads') for q in h[k] if q['uuid'] not in old}
    changed_refs={'U11012','C11061','C11062','C11063','C15001','C15002','R11049','C11068'}
    new|={q['uuid'] for q in h['pads'] if q['ref'] in changed_refs}
    oldpads={q['uuid']:q for q in g['pads']}
    new|={q['uuid'] for q in h['pads'] if q['uuid'] in oldpads and q!=oldpads[q['uuid']]}
    oldtracks={q['uuid']:q for q in g['tracks']}
    new|={q['uuid'] for q in h['tracks'] if q['uuid'] in oldtracks and q!=oldtracks[q['uuid']]}
    oldvias={q['uuid']:q for q in g['vias']}
    new|={q['uuid'] for q in h['vias'] if q['uuid'] in oldvias and q!=oldvias[q['uuid']]}
    cache={};ledger=[];zz=[]
    def cutters(net,layer):
        key=(net,layer)
        if key not in cache:
            rows=foreign_discrete(h,net,layer,new)
            rows += [(q['uuid'],q['shape'].buffer(gap(h,net,q['net'])+.025)) for q in zones if q['layer']==layer and p.norm(q['net'])!=p.norm(net)]
            cache[key]=rows,unary_union([s for _,s in rows])
        return cache[key]
    for z in h['zones']:
        row=copy.deepcopy(z);row['fills']={}
        for layer,rs in z['fills'].items():
            polys=p.base.polygons(rs);rows,cut=cutters(z['net'],layer);original=unary_union(polys);remaining=original.difference(cut)
            row['fills'][layer]=records(remaining)
            delta=original.difference(remaining)
            if not delta.is_empty:ledger.append({'zone_uuid':z['uuid'],'net_raw':z['net'],'layer':layer,'removed_Cu_area_mm2':delta.area,'cutters':[uid for uid,s in rows if s.intersects(original)]})
        zz.append(row)
    for q in zones:zz.append({'uuid':q['uuid'],'net':q['net'],'fills':{q['layer']:records(q['shape'])}})
    return {**h,'zones':zz},ledger
if __name__=='__main__':
    g,h,tail,binding,z=model();print('COMPLETE_MODEL',len(h['pads']),len(h['tracks']),len(h['vias']),len(z))
