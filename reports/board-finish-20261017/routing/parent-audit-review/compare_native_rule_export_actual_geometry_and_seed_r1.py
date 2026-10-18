"""Bind independently reloaded native rules to actual export, separately seed."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time
from pathlib import Path
from decimal import Decimal
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
GEOMETRY=PROJECT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/native-full/actual-full-refill-geometry.json'
NATIVE=HERE/'read-only-native-R299-rule-areas-r2/exact-native-rule-areas.json'
MODEL=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-model.pkl'
OUT=HERE/'native-rule-actual-export-seed-binding-r1'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def iu(v):
    q=Decimal(str(v))*10**6;assert q==q.to_integral_value();return int(q)
def ring(raw,scale):
    pts=[tuple(iu(v)if scale else int(v)for v in p)for p in raw]
    if pts[0]==pts[-1]:pts.pop()
    assert len(pts)>=3
    low=min(pts);candidates=[]
    for seq in(pts,list(reversed(pts))):
        candidates.extend(tuple(seq[i:]+seq[:i])for i,p in enumerate(seq)if p==low)
    return min(candidates)
def nativepoly(z):return tuple(sorted((ring(r['outer_IU'],False),tuple(sorted(ring(h,False)for h in r['holes_IU'])))for r in z['outlines']))
def geometrypoly(z):return tuple(sorted((ring(r[0],True),tuple(sorted(ring(h,True)for h in r[1:])))for r in z['outline']))
def seedpoly(z):return tuple(sorted((ring(r[0],True),tuple(sorted(ring(h,True)for h in r[1])))for r in z['outline']))
def compare(left,right,source):
    differences=[]
    for uid in sorted(set(left)&set(right)):
        a,b=left[uid],right[uid];diff={}
        keys=[('name','name'),('layers','layers'),('GetDoNotAllowTracks','no_tracks'),('GetDoNotAllowVias','no_vias'),('GetDoNotAllowPads','no_pads'),('GetDoNotAllowFootprints','no_footprints'),('GetDoNotAllowZoneFills','no_fill'if source=='actual_export'else'no_zones')]
        for ak,bk in keys:
            x,y=a[ak],b[bk]
            if ak=='layers':x,y=sorted(x),sorted(y)
            if x!=y:diff[ak]={'native_API':x,source:y}
        pa,pb=nativepoly(a),geometrypoly(b)if source=='actual_export'else seedpoly(b)
        if pa!=pb:diff['exact_IU_ring_coordinates']={'native_API':pa,source:pb}
        if source=='actual_export':
            owner=None if a['owner']['kind']=='board'else a['owner']['ref']
            if owner!=b.get('footprint'):diff['owner']={'native_API':owner,source:b.get('footprint')}
        if diff:differences.append({'UUID':uid,'differences':diff})
    return {'native_API_inventory':len(left),'comparison_inventory':len(right),'native_API_only':sorted(left.keys()-right.keys()),'comparison_only':sorted(right.keys()-left.keys()),'differences':differences}
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    native={r['UUID']:r for r in json.loads(NATIVE.read_bytes())};actual={r['uuid']:r for r in json.loads(GEOMETRY.read_bytes())['rule_areas']};seed={r['uuid']:r for r in pickle.loads(MODEL.read_bytes())['rule_areas']}
    a=compare(native,actual,'actual_export');b=compare(native,seed,'seed_model')
    put('actual-native-geometry-vs-independent-API.json',a);put('inherited-seed-model-vs-independent-API.json',b)
    complete=not(a['native_API_only']or a['comparison_only']or a['differences'])
    put('receipt.json',{'status':'WHOLE_ACTUAL_NATIVE_RULE_EXPORT_INDEPENDENT_API_EXACTLY_BOUND'if complete else'ACTUAL_NATIVE_RULE_EXPORT_API_DIFFERENCES_HELD','actual_export_exact_native_rule_inventory_flags_owners_and_IU_rings':complete,'actual_rule_count':len(native),'seed_rule_count':len(seed),'seed_native_only_rules':b['native_API_only'],'seed_only_rules':b['comparison_only'],'seed_rule_differences':len(b['differences']),'native_coordinate_units':'integer1nm with exact decimal IU conversion; ring start and winding canonical only','rule_or_copper_geometry_changed':False,'native_Fill_calls':0,'native_Save_calls':0,'all_parent_no_fill_and_old_reference_failures_held':True,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),NATIVE,GEOMETRY,MODEL)},'elapsed_seconds':time.monotonic()-st})
    print('RULE_API_BINDING',complete,'actual',len(native),'seed',len(seed),'seed_differences',len(b['differences']),flush=True)
if __name__=='__main__':main()
