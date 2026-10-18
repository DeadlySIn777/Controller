"""Preserve the first diagnostic and make a corrected isolated auditor."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
p=HERE/'audit_ao1_positive_operation_r1.py';t=p.read_text()
t=t.replace('def rooted_reference(model,masks):','def rooted_reference(model,masks,raw_com):')
t=t.replace("if anchor['net']!=COM:","if anchor['net']!=raw_com:")
t=t.replace('refs,witness,guf,groundrows=rooted_reference(candidate,masks)','refs,witness,guf,groundrows=rooted_reference(candidate,masks,identity.raw(COM))')
t=t.replace("out=HERE/'ao1-positive-independent-operation-r1.json'","out=HERE/'ao1-positive-independent-operation-r2.json'")
t=t.replace("'schema':'ao1-independent-positive-operation-r1'","'schema':'ao1-independent-positive-operation-r2'")
needle='    gaps=zone_gaps(now);refchecks=[]'
replacement="""    retained_transitions=[]
    for v in candidate.g['vias']:
        if v['uuid'] in parsed or v['net'] not in (VREF,SDI):continue
        contacted=[u for u,z in parsed.items() if z['kind']=='segment' and z['net']==v['net'] and z['layer'] in source_masks.get(v['uuid'],set()) and A.shape(z).intersects(Point(v['x'],v['y']).buffer(v['d']/2,resolution=128))]
        if contacted:retained_transitions.append(dict(v,contacted_added_or_restored_segments=contacted))
    signals+=retained_transitions
    gaps=zone_gaps(now);refchecks=[]"""
assert needle in t;t=t.replace(needle,replacement)
q=HERE/'audit_ao1_positive_operation_r2.py'
if q.exists():raise ValueError('Fresh isolated r2 required')
q.write_text(t);compile(t,str(q),'exec')
failure=HERE/'ao1-positive-operation-r1-failed-diagnostic.json'
failure.write_text(json.dumps({'verdict':'AUDIT_STOPPED_BEFORE_REFERENCE_RESULT','script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reason':'Pad raw token compared to normalized graph label; no proof or board emitted','preserved_script':str(p.resolve()),'correction_separate':str(q.resolve())},indent=1)+'\n')
print('r2 syntax PASS; r1 preserved')
