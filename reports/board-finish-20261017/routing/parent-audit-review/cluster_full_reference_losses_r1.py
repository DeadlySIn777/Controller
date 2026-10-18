"""Full 472-loss descriptive census; never turns a size class into a pass."""
import os,sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,re,collections,time
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2';P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;OUT=HERE/'full-472-reference-loss-census-r1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def kind(net):
    n=L.norm(net)
    if re.search(r'GND|(?:^|_)0V(?:_|$)|_COM(?:_|$)',n):return 'ground_or_return_named'
    if re.search(r'24V|12V|5V|3V3|1V2|VCC|VDD',n):return 'power_rail_named'
    if re.search(r'SPI|SCLK|MOSI|MISO|SDI|SDO|CLOCK|CLK|STEP|DIR\d|ENC\d|MIPI|USB|HDMI|ETH',n):return 'clock_serial_motion_or_highspeed_named'
    return 'other_signal_speed_unqualified'
def components(s):
    if s.is_empty:return[]
    if s.geom_type in('Polygon','LineString','Point'):return[s]
    return[p for g in s.geoms for p in components(g)]
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    parent=P/'three-bank-strict-old-routed-body-reference.json';banks=json.loads(parent.read_bytes());assert sum(len(b['losses'])for b in banks)==472
    model=P/'actual-combined-full-after-model.pkl';h=pickle.loads(model.read_bytes());fill={ly:[]for ly in K.LAYERS}
    for z in h['zones']:
        for ly,records in z['fills'].items():
            fill[ly].extend({'UUID':z['uuid'],'raw_net':z['net'],'local_clearance_mm':z['clearance_mm'],'priority':z['priority'],'shape':s}for s in L.poly(records))
    trees={ly:STRtree([r['shape']for r in rs])for ly,rs in fill.items()}
    partialfile=HERE/'exact-literal-source-classification-r1/progress.json';partial=json.loads(partialfile.read_bytes())if partialfile.exists()else[];exact={r['track_UUID']:r for r in partial}
    rows=[];causes=collections.defaultdict(list);functions=collections.Counter();sourcecounts={}
    for bank in banks:
        ground=bank['ground'];sourcecounts[ground]={'eligible_retained_tracks':bank['eligible_retained_track_count'],'raw_failures':len(bank['losses'])}
        for r in bank['losses']:
            w=r['literal_actual_before_supported_body_not_supported_after'];f=Path(w['file']);assert sha(f)==w['WKB_SHA256'];shape=from_wkb(f.read_bytes());parts=components(shape);largest=max(parts,key=lambda s:(s.area,s.length));point=largest.representative_point();inner=K.MAP[r['layer']];near=[]
            for j in trees[inner].query(point.buffer(1.0),predicate='intersects'):
                z=fill[inner][int(j)]
                if L.norm(z['raw_net'])==ground:continue
                required=.15 if h['domains_normalized'].get(L.norm(z['raw_net']))==h['domains_normalized'][ground]else .6
                required=max(required,z['local_clearance_mm']);distance=point.distance(z['shape'])
                near.append({k:z[k]for k in('UUID','raw_net','local_clearance_mm','priority')}|{'distance_mm':distance,'native_required_mm':required,'strict_old_body_point_inside_current_foreign_clearance':distance<required})
            near.sort(key=lambda r:r['distance_mm']);c=near[0]if near else None
            category=kind(r['raw_net']);functions[category]+=1
            cause='current_foreign_filled_clearance_conflict:'+c['UUID']if c and c['strict_old_body_point_inside_current_foreign_clearance']else'no_foreign_fill_clearance_cause_at_selected_point_numeric_or_other_cause_open'
            er=exact.get(r['track_UUID']);exacts=[]if er is None else[c['classification']for c in er['components']]
            row={'ground_source_net':ground,'source_anchor':next(ref+'.'+pin for net,ref,pin in K.ROOTS[:3]if net==ground),'track_UUID':r['track_UUID'],'raw_net':r['raw_net'],'layer':r['layer'],'reference_layer':inner,'descriptive_function_class':category,'function_class_is_not_electrical_policy_or_rate_qualification':True,'raw_area_mm2':shape.area,'raw_length_mm':shape.length,'raw_geometry_type':shape.geom_type,'raw_component_count':len(parts),'bounds_mm':list(shape.bounds),'selected_point_mm':[point.x,point.y],'nearest_current_foreign_native_fills':near[:3],'cause_group':cause,'partial_exact_binary64_component_classes':exacts,'exact_native_IU_true_circle_followup':'OPEN; binary64 drilled-overlay certificate is distinct','raw_file':str(f),'raw_SHA256':sha(f)}
            rows.append(row);causes[ground+'|'+cause].append(row)
    clusters=[]
    for label,rs in causes.items():
        clusters.append({'source_and_cause':label,'tracks':len(rs),'sum_raw_area_mm2':sum(r['raw_area_mm2']for r in rs),'maximum_raw_area_mm2':max(r['raw_area_mm2']for r in rs),'descriptive_function_counts':dict(collections.Counter(r['descriptive_function_class']for r in rs)),'top_tracks_by_raw_area':[{'UUID':r['track_UUID'],'net':r['raw_net'],'area_mm2':r['raw_area_mm2']}for r in sorted(rs,key=lambda r:r['raw_area_mm2'],reverse=True)[:8]]})
    clusters.sort(key=lambda c:c['sum_raw_area_mm2'],reverse=True)
    put('all-472-raw-reference-losses-classified-descriptively.json',rows);put('source-cause-functional-clusters.json',clusters)
    put('receipt.json',{'status':'FULL472_RAW_SOURCE_CAUSE_FUNCTIONAL_CENSUS_NO_GATE_WAIVER','source_bank_counts':sourcecounts,'descriptive_function_counts':dict(functions),'cause_clusters':len(clusters),'partial_exact_snapshot_tracks':len(partial),'all_raw_loss_files_SHA256_checked':True,'area_and_length_used_only_for_ordering_not_acceptance':True,'native_IU_and_true_circle_numeric_classification_separate_open':True,'every_raw_parent_failure_retained':True,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),parent,model)},'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st})
    print('FULL472_CENSUS_COMPLETE',len(clusters),flush=True)
if __name__=='__main__':main()
