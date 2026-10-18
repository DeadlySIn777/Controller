"""Exact rational witness classification; retain every raw parent failure."""
import os,sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,time
from pathlib import Path
from fractions import Fraction as Q
from shapely import from_wkb
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
sys.path.insert(0,str(OLD))
import audit_FIELD5_R453_literal_rational_line_membership_r189 as X
INPUT=HERE/'actual-source-witness-inputs-r1';OUT=HERE/'exact-literal-source-classification-r1'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()

def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def bbox(r):return (min(p[0]for p in r),min(p[1]for p in r),max(p[0]for p in r),max(p[1]for p in r))
def prepare(polys):return [[(r,bbox(r))for r in rings]for rings in polys]
def location(p,polys):
    boundary=False
    for rings in polys:
        r,b=rings[0]
        if not b[0]<=p[0]<=b[2]or not b[1]<=p[1]<=b[3]:continue
        outer=X.ring_location(p,r)
        if outer=='EXTERIOR':continue
        if outer=='BOUNDARY':boundary=True;continue
        holeboundary=False;inhole=False
        for r,b in rings[1:]:
            if not b[0]<=p[0]<=b[2]or not b[1]<=p[1]<=b[3]:continue
            h=X.ring_location(p,r)
            if h=='INTERIOR':inhole=True;break
            if h=='BOUNDARY':holeboundary=True
        if inhole:continue
        if holeboundary:boundary=True;continue
        return 'INTERIOR'
    return 'BOUNDARY'if boundary else'EXTERIOR'
def parts(s):
    if s.is_empty:return[]
    return [s]if s.geom_type=='Polygon'else [p for g in s.geoms for p in parts(g)]
def edges(polys):return [(a,b)for rings in polys for r in rings for a,b in zip(r,r[1:])if a!=b]
def boundhit(a,b,lo,hi):return not(max(a[0],b[0])<lo[0]or min(a[0],b[0])>hi[0]or max(a[1],b[1])<lo[1]or min(a[1],b[1])>hi[1])

def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    binding=INPUT/'old-reference-witness-source-binding.json';rows=json.loads(binding.read_bytes());cache={};reports=[]
    for wi,row in enumerate(rows):
        wp=Path(row['witness_file']);assert sha(wp)==row['witness_SHA256'];w=from_wkb(wp.read_bytes())
        bp=Path(row['body_file']);assert sha(bp)==row['body_SHA256'];body=X.read_polys(from_wkb(bp.read_bytes()))
        rawlocal={'body':body};local={'body':prepare(body)};inputs=[]
        for r in row['individual_source_pieces']:
            path=Path(r['file']);assert sha(path)==r['SHA256']
            if r['SHA256']not in cache:cache[r['SHA256']]=X.read_polys(from_wkb(path.read_bytes()))
            key=r['side']+'_'+r['zone_UUID']+'_'+r['SHA256'];rawlocal[key]=cache[r['SHA256']];local[key]=prepare(rawlocal[key]);inputs.append(r)
        sourceedges=[e for k,ps in rawlocal.items()for e in edges(ps)]
        components=[]
        for ci,part in enumerate(parts(w)):
            witness=X.read_polys(part);rawlocal['witness']=witness;local['witness']=prepare(witness)
            def classify(p):
                loc={k:location(p,ps)for k,ps in local.items()}
                before=any(v!='EXTERIOR'for k,v in loc.items()if k.startswith('before_'))
                after=any(v!='EXTERIOR'for k,v in loc.items()if k.startswith('after_'))
                hit=loc['witness']!='EXTERIOR'and loc['body']!='EXTERIOR'and before and not after
                positive=hit and loc['witness']=='INTERIOR'and loc['body']=='INTERIOR'and any(v=='INTERIOR'for k,v in loc.items()if k.startswith('before_'))
                return hit,positive,loc
            coords=witness[0][0][:-1];rp=part.representative_point();candidates=[X.point((rp.x,rp.y))]
            if coords:
                candidates.append(tuple(sum(p[k]for p in coords)/len(coords)for k in(0,1)))
                candidates.extend(tuple((coords[0][k]+coords[j][k]+coords[j+1][k])/3 for k in(0,1))for j in range(1,min(len(coords)-1,128)))
            certificate=None
            for point in candidates:
                hit,positive,loc=classify(point)
                if positive:
                    certificate={'point_exact':[str(x)for x in point],'point_mm_approx':[float(x)for x in point],'locations':loc};break
            if certificate:
                components.append({'component':ci,'classification':'CERTIFIED_REAL_POSITIVE_AREA_SOURCE_REFERENCE_LOSS','exact_interior_witness':certificate});continue
            # Exhaustive planar arrangement for unresolved/degenerate witnesses.
            allcoords=[p for rings in witness for ring in rings for p in ring]
            lo=tuple(min(p[k]for p in allcoords)for k in(0,1));hi=tuple(max(p[k]for p in allcoords)for k in(0,1))
            boundaries=edges(witness)+[e for e in sourceedges if boundhit(*e,lo,hi)]
            if len(boundaries)>300:
                components.append({'component':ci,'classification':'UNRESOLVED_BOUNDED_EXACT_ARRANGEMENT_EDGE_COUNT','edges':len(boundaries)});continue
            splitps={'all_boundaries':[[[a,b,a]]for a,b in boundaries]};seen=set();bad=[];counts={'vertices':0,'midpoints':0,'adjacent_faces':0}
            def check(point,kind):
                if point in seen:return
                seen.add(point);counts[kind]+=1;hit,positive,loc=classify(point)
                if hit:bad.append({'kind':kind,'positive_area':positive,'point_exact':[str(x)for x in point],'point_mm_approx':[float(x)for x in point],'locations':loc})
            for a,b in boundaries:
                ts=X.split_parameters(a,b,splitps)
                for t in ts:check(X.along(a,b,t),'vertices')
                for t,u in zip(ts,ts[1:]):
                    if t==u:continue
                    middle=X.along(a,b,(t+u)/2);check(middle,'midpoints');delta=X.sub(b,a);normal=(-delta[1],delta[0]);scale=max(abs(x)for x in normal)
                    for sign in(-1,1):
                        end=(middle[0]+sign*normal[0]/scale/1000,middle[1]+sign*normal[1]/scale/1000)
                        xs=X.split_parameters(middle,end,splitps);positive=[x for x in xs if x>0];step=min(positive)/2 if positive else Q(1)
                        check(X.along(middle,end,step),'adjacent_faces')
            components.append({'component':ci,'classification':'CERTIFIED_REAL_CLOSED_SOURCE_REFERENCE_LOSS'if bad else'EXACT_ARRANGEMENT_RAW_GE0S_WITNESS_HAS_NO_BODY_AND_BEFORE_OUTSIDE_AFTER_POINTS','edges':len(boundaries),'sample_counts':counts,'literal_loss_count':len(bad),'literal_loss_witnesses_first8':bad[:8]})
        report={'track_UUID':row['track_UUID'],'raw_net':row['raw_net'],'layer':row['layer'],'root':row['root'],'raw_witness_area_mm2':row['raw_area_mm2'],'raw_witness_file':row['witness_file'],'raw_witness_SHA256':row['witness_SHA256'],'literal_input_source_pieces':inputs,'components':components,'raw_failure_preserved':True,'own_caps_added':0}
        reports.append(report);put('progress.json',reports)
        print('EXACT_OLDREF',wi,row['track_UUID'],{c:sum(r['classification']==c for r in components)for c in {r['classification']for r in components}},flush=True)
    counts={}
    for row in reports:
        for r in row['components']:counts[r['classification']]=counts.get(r['classification'],0)+1
    put('all-classifications.json',reports)
    put('receipt.json',{'status':'EXACT_BINARY64_SOURCE_WITNESS_CLASSIFICATION_COMPLETE_RAW_FAILURES_RETAINED','counts':counts,'witness_tracks':len(reports),'literal_vertex_envelope_coverage_binding_SHA256':sha(INPUT/'receipt.json'),'input_SHA256':{str(f):sha(f)for f in(Path(__file__),Path(X.__file__),binding)},'exact_rational_GEOS_witness_body_individual_BEFORE_AFTER_source_vertices':True,'positive_area_classification_requires_exact_INTERIOR_witness_body_and_BEFORE_and_EXTERIOR_all_AFTER':True,'no_area_or_length_tolerance_no_shape_or_precision_change':True,'raw_parent_failures_preserved':True,'no_own_cap_or_new_native_fill':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st})
    print('EXACT_COMPLETE',counts,flush=True)

if __name__=='__main__':main()
