"""Local actual-native cause census for the two largest retained power gaps."""
import os,sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,runpy,time
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
B=OLD/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
for d in (OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L
ns=runpy.run_path(str(HERE/'classify_literal_R763_witnesses_r1.py'));X=ns['X'];loc=ns['location'];prep=ns['prepare']
INPUT=HERE/'actual-source-witness-inputs-r1';OUT=HERE/'CORE24V-actual-fill-cause-and-native-IU-r1'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()

def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    after=pickle.loads((P/'actual-combined-full-after-model.pkl').read_bytes());before=pickle.loads((B/'actual-full-R157-before-model.pkl').read_bytes())
    binding=INPUT/'old-reference-witness-source-binding.json';rows=[r for r in json.loads(binding.read_bytes())if r['track_UUID']in('942659fe-dca8-4a36-af79-d5a05f611887','028ef3d3-2b43-440e-a40f-06eeffe3d727')]
    records=[]
    for v in after['vias']:records.append(('via',v['uuid'],v['net'],Point(v['x'],v['y']),v['d']/2))
    for t in after['tracks']:
        if t['layer']=='In1.Cu':records.append(('track',t['uuid'],t['net'],LineString([t['a'],t['b']])if not t.get('m')else L.body(t),t['w']/2 if not t.get('m')else 0))
    for pad in after['pads']:
        for shape in L.poly(pad['layers'].get('In1.Cu',[])):records.append(('pad',pad['uuid'],pad['net'],shape,0))
    fill=[]
    for z in after['zones']:
        if L.norm(z['net'])=='/LOGIC_GND':continue
        for sh in L.poly(z['fills'].get('In1.Cu',[])):
            if sh.intersects(box(258,65,267,74)):fill.append((z,sh))
    out=[]
    for row in rows:
        witness=from_wkb(Path(row['witness_file']).read_bytes());body=from_wkb(Path(row['body_file']).read_bytes())
        pieces={}
        for side in ('before','after'):
            pieces[side]=[from_wkb(Path(r['file']).read_bytes())for r in row['individual_source_pieces']if r['side']==side]
        prepared={side:[prep(X.read_polys(shape))for shape in values]for side,values in pieces.items()};bodyprep=prep(X.read_polys(body))
        components=[]
        for i,part in enumerate(sorted(ns['parts'](witness),key=lambda s:s.area,reverse=True)):
            rp=part.representative_point();point=X.point((rp.x,rp.y));wp=prep(X.read_polys(part))
            locations={'witness':loc(point,wp),'body':loc(point,bodyprep),'before':[loc(point,s)for s in prepared['before']],'after':[loc(point,s)for s in prepared['after']]}
            pos=locations['witness']=='INTERIOR'and locations['body']=='INTERIOR'and'INTERIOR'in locations['before']and all(x=='EXTERIOR'for x in locations['after'])
            nearest=sorted([{'kind':kind,'UUID':u,'raw_net':n,'true_nominal_point_to_Cu_gap_mm':rp.distance(shape)-rad}for kind,u,n,shape,rad in records if L.norm(n)!='/LOGIC_GND' and shape.distance(rp)-rad<1.1],key=lambda r:r['true_nominal_point_to_Cu_gap_mm'])[:8]
            foreign=sorted([{'zone_UUID':z['uuid'],'raw_net':z['net'],'clearance_mm':z['clearance_mm'],'priority':z['priority'],'gap_mm':rp.distance(sh)}for z,sh in fill],key=lambda r:r['gap_mm'])[:4]
            ap=unary_union(pieces['after']);near=nearest_points(rp,ap)[1]
            components.append({'component':i,'raw_area_mm2':part.area,'raw_bounds_mm':list(part.bounds),'point_exact':[str(x)for x in point],'point_mm':[rp.x,rp.y],'literal_binary64_source_locations':locations,'literal_positive_area_loss_certified':pos,'point_distance_to_actual_after_source_mm':rp.distance(ap),'nearest_actual_after_source_point_mm':[near.x,near.y],'nearest_foreign_actual_In1_discrete_Cu':nearest,'nearest_foreign_actual_In1_fills':foreign})
        out.append({'track_UUID':row['track_UUID'],'raw_net':row['raw_net'],'layer':row['layer'],'components':components})
    z='58c55cd5-98e6-4467-88e3-146ceeee361a';bz=next(r for r in before['zones']if r['uuid']==z);az=next(r for r in after['zones']if r['uuid']==z)
    exact={'zone_UUID':z,'same_native_intended_outline':bz['outline']==az['outline'],'same_all_native_non_fill_settings':all(bz[k]==az[k]for k in bz if k not in('outline','fills'))}
    changed=[];oldvia={v['uuid']:v for v in before['vias']};oldtrack={t['uuid']:t for t in before['tracks']}
    for v in after['vias']:
        if v!=oldvia.get(v['uuid']) and 257<v['x']<268 and 64<v['y']<75:changed.append(v)
    for t in after['tracks']:
        if t!=oldtrack.get(t['uuid'])and t['layer']=='In1.Cu'and LineString([t['a'],t['b']]).intersects(box(257,64,268,75)):changed.append(t)
    put('two-CORE24V-big-gap-actual-source-and-foreign-Cu-diagnosis.json',out)
    put('receipt.json',{'status':'CORE24V_LARGE_LITERAL_GAPS_LOCAL_CAUSE_CENSUS_NO_REPAIR_OR_WAIVER','source_zone_native_identity':exact,'local_new_or_changed_actual_In1_Cu':changed,'power_not_signal_identity_preserved':True,'no_own_caps':True,'native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),binding,B/'actual-full-R157-before-model.pkl',P/'actual-combined-full-after-model.pkl')},'elapsed_seconds':time.monotonic()-st})
    print('CORE24_DIAG_COMPLETE',len(out),flush=True)

if __name__=='__main__':main()
