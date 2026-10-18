"""Preserve r2 writer diagnostics; bind exact controlled policy in fresh r3."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
p=HERE/'audit_ao1_positive_operation_r2.py';t=p.read_text()
t=t.replace("out=HERE/'ao1-positive-independent-operation-r2.json'","out=HERE/'ao1-positive-independent-operation-r3.json'")
t=t.replace("'schema':'ao1-independent-positive-operation-r2'","'schema':'ao1-independent-positive-operation-r3'")
t=t.replace("'new_parsed_items':parsed", "'new_parsed_items':{u:{k:v for k,v in z.items() if k!='shape'} for u,z in parsed.items()},'derived_shape_WKB_sha256':{u:C.sha(z['shape'].wkb) for u,z in parsed.items() if 'shape' in z}")
needle="    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)"
replacement=needle+"""
    policies={S.norm(n):r for n,r in json.loads(A.read(S.CONTROLLED))['nets'].items()}
    if policies.get(SDI,{}).get('class')!='NONE':raise ValueError('Exact frozen SDI policy is not ordinary NONE')"""
assert needle in t;t=t.replace(needle,replacement)
t=t.replace("'raw_net_identity':{n:identity.raw(n) for n in (VREF,SDI,COM)}", "'raw_net_identity':{n:identity.raw(n) for n in (VREF,SDI,COM)},'exact_frozen_SDI_controlled_policy':policies[SDI],'SCLK_all_source_chunks_unchanged':True")
t=t.replace("    out.write_text(json.dumps(report,indent=1)+'\\n');print(json.dumps(","    print(json.dumps({'prewrite_counts':{'clearance':len(errors),'pads':len(losses),'contacts':len(contacts),'fill':len(fillerrors),'references':len(referrors),'returns':len(returnerrors)}}),flush=True)\n    out.write_text(json.dumps(report,indent=1)+'\\n');print(json.dumps(")
q=HERE/'audit_ao1_positive_operation_r3.py'
if q.exists():raise ValueError('Fresh r3 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-positive-operation-r2-failed-diagnostic.json').write_text(json.dumps({'verdict':'AUDIT_COMPLETED_CALCULATIONS_BUT_WRITER_FAILED_NO_RESULT_CREDIT','script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reason':'Shared parser includes derived Shapely Polygon in parsed dictionaries; writer rejected it','preserved_script':str(p.resolve()),'corrected_separate':str(q.resolve())},indent=1)+'\n')
print('r3 syntax PASS; r2 preserved')
