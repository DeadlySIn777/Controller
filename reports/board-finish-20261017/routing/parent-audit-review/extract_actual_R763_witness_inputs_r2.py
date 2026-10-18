"""Pin exhaustive local source pieces for independent literal gap review."""
import os, sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,time,gc
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import box
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
B=OLD/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
for folder in (OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(folder))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;OUT=HERE/'actual-source-witness-inputs-r2'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()

def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir()
    before=pickle.loads((B/'actual-full-R157-before-model.pkl').read_bytes());after=pickle.loads((P/'actual-combined-full-after-model.pkl').read_bytes())
    tracks={t['uuid']:t for t in before['tracks']};roots=K.ROOTS[:3]
    domain_to_root={before['domains_normalized'][net]:(net,ref,pin) for net,ref,pin in roots}
    witnesses=[]
    for f in sorted(P.glob('oldref-*.wkb')):
        uid=f.stem[len('oldref-'):];t=tracks[uid];g=from_wkb(f.read_bytes());root=domain_to_root[before['domains_normalized'][L.norm(t['net'])]]
        body=K.A.shape({'kind':'segment',**t}) if not t.get('m') else L.body(t)
        bp=OUT/('track-body-'+uid+'.wkb');bp.write_bytes(body.wkb)
        witnesses.append({'track_UUID':uid,'raw_net':t['net'],'layer':t['layer'],'reference_layer':K.MAP[t['layer']],'root':list(root),'witness_file':str(f),'witness_SHA256':sha(f),'raw_type':g.geom_type,'raw_area_mm2':g.area,'raw_length_mm':g.length,'bounds_mm':list(g.bounds),'body_file':str(bp),'body_SHA256':sha(bp),'individual_source_pieces':[]})
    assert len(witnesses)==472, 'Final exhaustive parent bank witness count changed'
    graphfiles={'before':B/'actual-full-R157-before-all-net-groups.pkl','after':P/'actual-combined-full-after-all-net-groups.pkl'}
    for side,gf in graphfiles.items():
        groups=pickle.loads(gf.read_bytes());indices={}
        for net,ref,pin in roots:
            source=K.root(groups[net],ref,pin)
            for ly in ('In1.Cu','In4.Cu'):
                rows=[r for r in source if r['kind']=='fill' and r['layer']==ly]
                indices[net,ly]=(rows,STRtree([r['shape'] for r in rows]))
        for wi,w in enumerate(witnesses):
            rows,tree=indices[w['root'][0],w['reference_layer']];env=box(*w['bounds_mm'])
            # STRtree bounds are generated directly from literal input vertices;
            # an explicit envelope census is retained for every omitted piece.
            local=set(int(j) for j in tree.query(env));omitted=0
            for j,r in enumerate(rows):
                rb=r['shape'].bounds;b=w['bounds_mm']
                disjoint=rb[2]<b[0] or rb[0]>b[2] or rb[3]<b[1] or rb[1]>b[3]
                if j not in local:assert disjoint;omitted+=1
                else:
                    h=hashlib.sha256(r['shape'].wkb).hexdigest();f=OUT/('source-piece-'+side+'-'+h+'.wkb')
                    if not f.exists():f.write_bytes(r['shape'].wkb)
                    w['individual_source_pieces'].append({'side':side,'zone_UUID':r['uuid'],'layer':r['layer'],'file':str(f),'SHA256':h,'bounds_mm':list(rb)})
            w[side+'_source_piece_census']={'all_source_pieces':len(rows),'relevant_pieces':len(local),'omitted_exact_envelope_disjoint_pieces':omitted}
        print('EXTRACT_SOURCE',side,len(witnesses),flush=True)
        del groups,indices;gc.collect()
    # Exact native-IU fill arrays and via dimensions for the two direct losses.
    direct=json.loads((P/'all-old-direct-native-fill-contacts.json').read_bytes());loss=[r for r in direct if not r['ANY_same_raw_actual_fill_touch_retained']]
    directrows=[]
    for row in loss:
        uid=row['key'][1];net=row['net'];ly=row['key'][2];bvia=next(v for v in before['vias']if v['uuid']==uid);avia=next(v for v in after['vias']if v['uuid']==uid)
        assert bvia==avia
        source=[]
        for side,m in (('before',before),('after',after)):
            for z in m['zones']:
                if L.norm(z['net'])!=net:continue
                for shape in L.poly(z['fills'].get(ly,[])):
                    if shape.distance(box(bvia['x']-.31,bvia['y']-.31,bvia['x']+.31,bvia['y']+.31))>.001:continue
                    f=OUT/('direct-'+side+'-'+uid+'-'+z['uuid']+'-'+hashlib.sha256(shape.wkb).hexdigest()+'.wkb');f.write_bytes(shape.wkb)
                    source.append({'side':side,'zone_UUID':z['uuid'],'file':str(f),'SHA256':sha(f)})
        directrows.append({'parent_row':row,'unchanged_via':bvia,'individual_same_net_native_fill_polygons':source})
    put('old-reference-witness-source-binding.json',witnesses);put('two-direct-loss-native-inputs.json',directrows)
    pins=[Path(__file__),P/'actual-graph-cache-receipt.json',B/'prepare-receipt.json',P/'all-old-direct-native-fill-contacts.json',B/'actual-full-R157-before-model.pkl',P/'actual-combined-full-after-model.pkl',*graphfiles.values()]
    put('receipt.json',{'status':'LITERAL_SOURCE_WITNESS_INPUTS_PINNED_NO_CLASSIFICATION_OR_WAIVER','oldref_count':len(witnesses),'direct_loss_count':len(loss),'all_omitted_source_pieces_exact_vertex_envelope_disjoint':True,'new_own_caps':0,'input_SHA256':{str(f):sha(f) for f in pins},'native_jobs':0,'geometry_modified':False,'adopted':False,'elapsed_seconds':time.monotonic()-started})
    print('EXTRACT_COMPLETE',len(witnesses),len(loss),flush=True)

if __name__=='__main__':main()
