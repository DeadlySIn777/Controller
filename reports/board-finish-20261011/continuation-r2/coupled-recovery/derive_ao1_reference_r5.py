"""Correct paired native target and reject disconnected referenced cases exactly."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;p=HERE/'ao1_reference_coupled_r3.py';t=p.read_text()
t=t.replace("OUT=HERE/'ao1-reference-coupled-r3.json'","OUT=HERE/'ao1-reference-coupled-r5.json'")
t=t.replace('U14636.7#0','C14643.1#0')
t=t.replace('for vat in vsite[:6]:','for vat in vsite[:12]:')
t=t.replace("removed=set(recipe['deletes']);withdrawn=set(recipe['restores'])","removed=set(recipe['deletes']);withdrawn=set(recipe['restores'])\n    lost=json.loads(A.read(HERE/'conflict-graph.json'))['lost_route_rows']\n    relation=next(r for r in lost if r['net']==VREF)['native_lost_relationships'][0]['r06_pad_relationship']\n    if set(relation)!={'C14643.1#0','U14626.9#0'}:raise ValueError('Exact native lost VREF relation differs')")
needle="    attempts=[];success=None;S.STEP=.025"
replacement="""    diagnostic['actual_initial_full_reference_F_components']={}
    for net,start in ((VREF,vstart),(SDI,sstart)):
        comp=containing(strict[net,'F.Cu'],start)
        path=HERE/('ao1-r5-initial-'+net.rsplit('/',1)[-1]+'.wkb');path.write_bytes(comp.wkb)
        diagnostic['actual_initial_full_reference_F_components'][net]={'area_mm2':comp.area,'bounds_mm':list(comp.bounds),'WKB_path':str(path.resolve()),'WKB_sha256':C.sha(comp.wkb)}
    attempts=[];success=None;S.STEP=.025"""
assert needle in t;t=t.replace(needle,replacement)
needle="                starts=[p for p in starts if shape.covers(Point(p))];goals=[p for p in goals if shape.covers(Point(p))]"
replacement=needle+"""
                pieces=P.K.D.components(shape)
                shared=[p for p in pieces if any(p.covers(Point(a)) for a in starts) and any(p.covers(Point(b)) for b in goals)]
                if not shared:
                    source_parts=[p for p in pieces if any(p.covers(Point(a)) for a in starts)]
                    attempt['failures'].append({'net':net,'layer':layer,'reason':'Exact continuous own-transition/reference/free components disconnected','source_component_areas_mm2':[p.area for p in source_parts],'source_component_bounds_mm':[list(p.bounds) for p in source_parts],'own_transition_mm':signals[net][1]})
                    break
                shape=unary_union(shared)
"""
assert needle in t;t=t.replace(needle,replacement)
t=t.replace("'component_diagnostic':diagnostic","'component_diagnostic':diagnostic,'exact_original_recovered_relation':relation")
q=HERE/'ao1_reference_coupled_r5.py'
if q.exists():raise ValueError('Fresh paired r5 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-reference-r5-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'changes':['Exact C14643.1/U14626.9 original native target','Save full-reference source components before new signal cuts','Reject exact disconnected per-case source/target polygon components before finite Astar, preserving only legitimate path-own transition exception'],'board_emitted':False},indent=1)+'\n')
print('Correct paired native-target r5 syntax PASS')
