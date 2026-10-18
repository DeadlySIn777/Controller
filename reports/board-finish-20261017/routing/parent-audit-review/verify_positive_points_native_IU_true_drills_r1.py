"""Separate literal binary64 certificates from exact native IU point geometry.

No raw failure is cleared. Native filled rings use exact integral nanometres;
straight-track capsules and circular drills are tested by integer arithmetic.
Oval drills use a conservative exact enclosing circle and stay unresolved if hit.
"""
import os,sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,collections
from pathlib import Path
from fractions import Fraction as Q
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
B=OLD/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
OUT=HERE/'native-IU-true-drill-positive-point-review-r1'
DRILLS=HERE/'read-only-native-drill-IU-r1'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
norm=lambda n:n.replace('{slash}','/')
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def iu(v):
    u=round(v*10**6);assert v==u/10**6,('Native 1nm identity required',v,u);return u
def ring(raw):
    r=[(iu(x),iu(y))for x,y in raw]
    if r[0]!=r[-1]:r.append(r[0])
    return (r,(min(x for x,y in r),min(y for x,y in r),max(x for x,y in r),max(y for x,y in r)))
def inbounds(point,b):
    x,y=point;return b[0]*x.denominator<=x.numerator<=b[2]*x.denominator and b[1]*y.denominator<=y.numerator<=b[3]*y.denominator
def ringloc(point,prepared):
    r,bounds=prepared
    if not inbounds(point,bounds):return 'EXTERIOR'
    x,y=point;xn,xd=x.numerator,x.denominator;yn,yd=y.numerator,y.denominator;inside=False
    for a,b in zip(r,r[1:]):
        if not min(a[1],b[1])*yd<=yn<=max(a[1],b[1])*yd:continue
        side=(b[0]-a[0])*(yn-a[1]*yd)*xd-(b[1]-a[1])*(xn-a[0]*xd)*yd
        if side==0 and min(a[0],b[0])*xd<=xn<=max(a[0],b[0])*xd:return 'BOUNDARY'
        if(a[1]*yd>yn)!=(b[1]*yd>yn):
            if(side>0 and b[1]>a[1])or(side<0 and b[1]<a[1]):inside=not inside
    return 'INTERIOR'if inside else'EXTERIOR'
def polyloc(point,rings):
    outer=ringloc(point,rings[0])
    if outer!='INTERIOR':return outer
    boundary=False
    for r in rings[1:]:
        h=ringloc(point,r)
        if h=='INTERIOR':return 'EXTERIOR'
        boundary|=h=='BOUNDARY'
    return 'BOUNDARY'if boundary else'INTERIOR'
def fill_index(model):
    index=collections.defaultdict(list)
    for z in model['zones']:
        net=norm(z['net'])
        if net not in('/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'):continue
        for ly,records in z['fills'].items():
            if ly not in('In1.Cu','In4.Cu'):continue
            for i,(outer,holes)in enumerate(records):
                rs=[ring(outer),*[ring(r)for r in holes]]
                index[net,ly].append((z['uuid'],i,rs))
    return index
def fillloc(point,rows):
    hits=[]
    for uid,i,rings in rows:
        if not inbounds(point,rings[0][1]):continue
        loc=polyloc(point,rings)
        if loc!='EXTERIOR':hits.append({'zone_UUID':uid,'native_record':i,'location':loc})
    return hits
def trackloc(point,t):
    if t.get('m'):return 'ARC_ANALYTIC_GEOMETRY_OPEN'
    a=tuple(Q(iu(v))for v in t['a']);b=tuple(Q(iu(v))for v in t['b']);r=Q(iu(t['w']),2)
    d=(b[0]-a[0],b[1]-a[1]);ap=(point[0]-a[0],point[1]-a[1]);dd=d[0]**2+d[1]**2;dot=ap[0]*d[0]+ap[1]*d[1]
    if dd==0 or dot<=0:distance=ap[0]**2+ap[1]**2
    elif dot>=dd:distance=(point[0]-b[0])**2+(point[1]-b[1])**2
    else:distance=(d[0]*ap[1]-d[1]*ap[0])**2/dd
    return 'INTERIOR'if distance<r*r else'BOUNDARY'if distance==r*r else'EXTERIOR'
def holes_index(document):
    out=[]
    for v in document['vias']:out.append(('via',v['UUID'],*v['at_IU'],v['drill_IU'],True))
    for v in document['pads']:
        diameter=max(v['drill_IU']);circle=v['drill_shape_enum']==v['round_drill_enum']and v['drill_IU'][0]==v['drill_IU'][1]
        out.append(('pad',v['UUID'],*v['at_IU'],diameter,circle))
    return out
def drillloc(point,holes):
    x,y=point;xn,xd=x.numerator,x.denominator;yn,yd=y.numerator,y.denominator;hits=[]
    for kind,uid,cx,cy,diameter,circle in holes:
        dx=xn-cx*xd
        if abs(dx)*2>diameter*xd:continue
        dy=yn-cy*yd
        if abs(dy)*2>diameter*yd:continue
        excess=4*(dx*dx*yd*yd+dy*dy*xd*xd)-diameter*diameter*xd*xd*yd*yd
        if excess>0:continue
        hits.append({'kind':kind,'UUID':uid,'location':'BOUNDARY'if circle and excess==0 else'INTERIOR'if circle else'OVAL_EXACT_ENCLOSING_CIRCLE_HIT_UNRESOLVED','squared_radius_excess_native_IU2':str(Q(excess,4*xd*xd*yd*yd))})
    return hits
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    modelpaths={'before':B/'actual-full-R157-before-model.pkl','after':P/'actual-combined-full-after-model.pkl'}
    models={side:pickle.loads(f.read_bytes())for side,f in modelpaths.items()};indices={side:fill_index(h)for side,h in models.items()}
    drilldocs={side:json.loads((DRILLS/(side+'-native-holes.json')).read_bytes())for side in models}
    for side,h in models.items():
        observed={v['UUID']:v for v in drilldocs[side]['vias']};assert set(observed)=={v['uuid']for v in h['vias']}
        for v in h['vias']:
            assert observed[v['uuid']]['at_IU']==[iu(v['x']),iu(v['y'])]and observed[v['uuid']]['drill_IU']==iu(v['drill'])
        pads={v['uuid']:v for v in h['pads']}
        for p in drilldocs[side]['pads']:assert p['at_IU']==[iu(pads[p['UUID']]['x']),iu(pads[p['UUID']]['y'])]
    holes={side:holes_index(document)for side,document in drilldocs.items()}
    bindings=HERE/'actual-source-witness-inputs-r2/old-reference-witness-source-binding.json';bound={r['track_UUID']:r for r in json.loads(bindings.read_bytes())}
    first=HERE/'exact-literal-source-classification-r1/all-classifications.json';second=HERE/'exact-literal-source-classification-r2/all-classifications.json'
    documents={str(f):sha(f)for f in(first,second)};rawrows={r['track_UUID']:r for f in(first,second)for r in json.loads(f.read_bytes())}
    tracks={t['uuid']:t for t in models['before']['tracks']};reports=[];counts=collections.Counter()
    for uid,row in rawrows.items():
        r=bound[uid];assert row['raw_witness_SHA256']==r['witness_SHA256'];components=[]
        for comp in row['components']:
            cert=comp.get('exact_interior_witness')
            if not cert:continue
            point=tuple(Q(v)*10**6 for v in cert['point_exact']);body=trackloc(point,tracks[uid]);locations={side:fillloc(point,indices[side][r['root'][0],r['reference_layer']])for side in models};dh={side:drillloc(point,holes[side])for side in models}
            beforeinside=any(q['location']=='INTERIOR'for q in locations['before']);afterabsent=not locations['after'];allclear=not any(dh.values())
            if body!='INTERIOR':status='EXACT_TRUE_TRACK_BODY_POINT_NOT_INTERIOR_PHYSICAL_LOSS_CERTIFICATE_OPEN'
            elif not allclear:status='EXACT_DRILL_OR_OVAL_BOUND_HIT_POINT_PHYSICAL_LOSS_CERTIFICATE_OPEN'
            elif beforeinside and afterabsent:status='CERTIFIED_NATIVE_IU_POSITIVE_AREA_FILL_WITHDRAWAL_TRUE_BODY_POINT_CLEAR_OF_EVERY_DRILL'
            elif beforeinside and locations['after']:status='NATIVE_GROUND_FILL_PRESENT_AT_LITERAL_GAP_POINT_SOURCE_ROOT_OR_OVERLAY_CLASSIFICATION_OPEN'
            else:status='NATIVE_BEFORE_FILL_POINT_NOT_INTERIOR_PHYSICAL_LOSS_CERTIFICATE_OPEN'
            counts[status]+=1;components.append({'component':comp['component'],'classification':status,'point_exact_mm':cert['point_exact'],'point_mm_approx':[float(q/10**6)for q in point],'exact_true_track_capsule_location':body,'native_IU_fill_locations':locations,'every_native_drill_test_hits':dh,'raw_parent_failure_held':True})
        if components:reports.append({'track_UUID':uid,'raw_net':r['raw_net'],'reference_root':r['root'],'reference_layer':r['reference_layer'],'components':components})
        if len(reports)%20==0:put('progress.json',reports)
    put('all-point-classifications.json',reports)
    put('receipt.json',{'status':'EXACT_NATIVE_IU_TRUE_BODY_CIRCULAR_DRILL_POINT_CERTIFICATES_RAW_GATES_HELD','counts':dict(counts),'tracks_with_positive_literal_certificates_in_snapshot':len(reports),'raw_tracks_in_literal_snapshot':len(rawrows),'complete472_raw_tracks':len(rawrows)==472,'all472_raw_parent_failures_retained':True,'exact_native_fill_vertices_asserted_on1nm_grid':True,'exact_integer_arithmetic_in_native_IU_for_filled_ring_winding':True,'exact_rational_true_straight_track_capsule_and_circle_drill_predicates':True,'oval_hits_unresolved_enclosing_circle_exclusion_only':True,'source_binding':'Parent actual drilled J1/J3/J5 source piece certificate retained; native point presence is local, no global current or analytic graph qualification','no_cap_or_reference_policy_added':True,'native_Fill_calls':0,'native_Save_calls':0,'adopted':False,'input_SHA256':{**{str(f):sha(f)for f in(Path(__file__),bindings,*modelpaths.values(),DRILLS/'receipt.json',DRILLS/'before-native-holes.json',DRILLS/'after-native-holes.json')},**documents},'elapsed_seconds':time.monotonic()-st})
    print('EXACT_NATIVE_IU_POINTS',dict(counts),'tracks',len(reports),flush=True)
if __name__=='__main__':main()
