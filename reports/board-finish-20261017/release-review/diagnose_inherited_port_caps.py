"""Cheap geometric triage only, never qualifies owned aperture coverage."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='2'
from pathlib import Path
import hashlib,json,pickle,sys,math
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import search_same_layer_body_bridges as B
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
HERE=Path(__file__).resolve().parent;OUT=HERE/'inherited-port-cap-diagnostic-r1';OUT.mkdir()
f=B.CACHE/'actual-combined-full-after-model.pkl';g=B.CACHE/'actual-combined-full-after-all-net-groups.pkl'
h=pickle.loads(f.read_bytes());groups=pickle.loads(g.read_bytes())
attempts=HERE/'short-same-layer-body-bridges-r2/bounded-bridge-attempts.json'
rows=json.loads(attempts.read_text());refs={};rr={}
for d,(net,ref,pin) in B.ROOTS.items():
    root=next(q for q in groups[net] if any(r['kind']=='pad' and r['ref']==ref and str(r['pin'])==pin for r in q))
    for ly in ('In1.Cu','In4.Cu'):
        ss=[r['shape'] for r in root if r['kind']=='fill' and r['layer']==ly];refs[d,ly]=(ss,STRtree(ss))
for n,gg in groups.items():
    for gi,q in enumerate(gg):
        for r in q:
            if r['kind']=='track':rr[n,gi,r['layer'],r['uuid']]=r
vias=h['vias'];vt=STRtree([Point(v['x'],v['y']) for v in vias]);result=[]
for row in rows:
    ends=row['endpoints'];net=row['net'];ly=row['layer'];a,b=[e['at'] for e in ends]
    roi=box(min(a[0],b[0])-1.2,min(a[1],b[1])-1.2,max(a[0],b[0])+1.2,max(a[1],b[1])+1.2)
    ss,tree=refs[row['domain'],B.REF_LAYER[ly]];ref=unary_union([ss[int(i)].intersection(roi) for i in tree.query(roi)])
    caps=[];owners=[]
    for e in ends:
        if e['kind']!='track':continue
        old=rr[net,e['group'],ly,e['uuid']]
        for i in vt.query(Point(e['at']).buffer(.65)):
            v=vias[int(i)]
            if B.norm(v['net'])!=net or ly not in v['flashed']:continue
            c=Point(v['x'],v['y']);ring=c.buffer(v['d']/2,quad_segs=128).difference(B.outer(c,v['drill']/2))
            area=old['shape'].intersection(ring).area
            if area>.000001:
                caps.append(c.buffer(v['d']/2+.275,quad_segs=256));owners.append({'signal_UUID':v['uuid'],'old_track_UUID':e['uuid'],'finite_existing_same_layer_contact_mm2':area,'radius_mm':v['d']/2+.275})
    if not caps:continue
    test=unary_union([ref,*caps]);best=None
    for path in B.paths(a,b):
        body=B.body(path);gap=body.difference(test)
        if gap.is_empty:best={'path':path,'raw_reference_gap_mm2':body.difference(ref).area};break
    if best:result.append({'candidate_index':row['candidate_index'],'net':net,'layer':ly,'span_mm':row['span_mm'],'owners':owners,**best,'this_is_only_diagnostic_unclipped_caps':True})
report={'status':'DIAGNOSTIC_ONLY_UNCLIPPED_OWNER_CAPS_NOT_A_CLEARANCE_OR_REFERENCE_PASS','diagnostic_geometric_opportunities':result,
        'input_SHA256':{str(p):B.sha(p) for p in (f,g,attempts,Path(__file__),Path(B.__file__))}}
(OUT/'receipt.json').write_text(json.dumps(report,indent=1)+'\n')
print(json.dumps({'opportunities':len(result),'nets':sorted({r['net'] for r in result})}))
