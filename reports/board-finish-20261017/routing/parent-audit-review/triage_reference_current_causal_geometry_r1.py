"""Locate current material causes for all certified native withdrawal points.

Distances here are causal triage, not acceptance predicates or gap tolerances.
Every raw failure remains held. Native non-conductive NPTHs stay drill objects.
"""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,math,collections,importlib.util
from pathlib import Path
from fractions import Fraction as Q
from shapely.geometry import Point,LineString,Polygon,box
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
B=PROJECT/'reports/board-finish-20261011/continuation-r2/field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
POINTS=HERE/'native-IU-point-source-cause-functional-clusters-r1/all-true-native-point-components.json'
NPTH=HERE/'actual-project-epsilon-NPTH-cloned-deflation-r2/all-actual-native-NPTH-conductor-and-layer-observations.json'
RULES=HERE/'read-only-native-R299-rule-areas-r2/exact-native-rule-areas.json'
OUT=HERE/'all433-current-causal-geometry-triage-r1'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
norm=lambda n:n.replace('{slash}','/')
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def polys(records):return [Polygon(outer,holes)for outer,holes in records]
def state(row,kind):
    if kind=='via':return tuple((k,json.dumps(row.get(k),sort_keys=True))for k in('net','x','y','d','drill','flashed'))
    if kind=='track':return tuple((k,json.dumps(row.get(k),sort_keys=True))for k in('net','layer','a','b','w','m'))
    if kind=='pad':return tuple((k,json.dumps(row.get(k),sort_keys=True))for k in('net','x','y','layers'))
def build(model,no_copper):
    records=collections.defaultdict(list)
    def add(ly,shape,kind,item,radius=0):records[ly].append({'shape':shape,'kind':kind,'UUID':item['uuid'],'raw_net':item['net'],'radius':radius,'data':item})
    for t in model['tracks']:
        if t.get('m'):continue
        add(t['layer'],LineString([t['a'],t['b']]),'track',t,t['w']/2)
    for v in model['vias']:
        for ly in v['flashed']:add(ly,Point(v['x'],v['y']),'via',v,v['d']/2)
    for p in model['pads']:
        if p['uuid']in no_copper:continue
        for ly,rs in p['layers'].items():
            for sh in polys(rs):add(ly,sh,'pad',p)
    for z in model['zones']:
        for ly,rs in z['fills'].items():
            for sh in polys(rs):add(ly,sh,'fill',z)
    return records,{ly:STRtree([r['shape']for r in rs])for ly,rs in records.items()}
def sourcekeys(groups,ground):
    ref,pin={'/LOGIC_GND':('J11001','2'),'/motherboard_motors/FIELD_GND':('J11003','2'),'/motherboard_do/FIELD_B_0V':('J11005','2')}[ground]
    root=next(gr for gr in groups[ground]if any(r['kind']=='pad'and(r['ref'],str(r['pin']))==(ref,pin)for r in gr))
    return {(r['kind'],r['uuid'],r['layer'])for r in root if r['kind']!='fill'}
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    beforefile=B/'actual-full-R157-before-model.pkl';afterfile=P/'actual-combined-full-after-model.pkl'
    before=pickle.loads(beforefile.read_bytes());after=pickle.loads(afterfile.read_bytes());points=json.loads(POINTS.read_bytes())
    npth=json.loads(NPTH.read_bytes());no_copper={r['UUID']for r in npth if r['IsNPTHWithNoCopper']and not any(l['CanFlashLayer']or l['FlashLayer']for l in r['layer_observations'])}
    rec,trees=build(after,no_copper);oldrec,oldtrees=build(before,no_copper)
    oldobjects={kind:{r['uuid']:r for r in before[k]}for kind,k in(('via','vias'),('track','tracks'),('pad','pads'),('fill','zones'))}
    byold=collections.defaultdict(list)
    for ly,rows in oldrec.items():
        for r in rows:byold[r['kind'],r['UUID'],ly].append(r)
    groupfile=P/'actual-combined-full-after-all-net-groups.pkl';groups=pickle.loads(groupfile.read_bytes());keys={g:sourcekeys(groups,g)for g in('/LOGIC_GND','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V')};del groups
    rules=json.loads(RULES.read_bytes());rule_rows=[]
    for r in rules:
        if r['GetDoNotAllowZoneFills']:
            for p in r['outlines']:
                sh=Polygon([[v/1e6 for v in xy]for xy in p['outer_IU']],[[[v/1e6 for v in xy]for xy in ring]for ring in p['holes_IU']]);rule_rows.append((r,sh))
    # Exact native point-to-rule membership; all quantitative proximity below is triage.
    helper=HERE/'verify_positive_points_native_IU_true_drills_r1.py';spec=importlib.util.spec_from_file_location('native_IU_predicates_for_causal_triage',helper);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
    prepared={r['UUID']:[[A.ring([(x/1e6,y/1e6)for x,y in p['outer_IU']]),*[A.ring([(x/1e6,y/1e6)for x,y in ring])for ring in p['holes_IU']]]for p in r['outlines']]for r in rules if r['GetDoNotAllowZoneFills']}
    zb={z['uuid']:z for z in before['zones']};za={z['uuid']:z for z in after['zones']};results=[];clusters=collections.defaultdict(list)
    max_radius=max([v['d']/2 for v in after['vias']]+[t['w']/2 for t in after['tracks']]);search=1+max_radius
    for index,row in enumerate(points):
        exact=tuple(Q(v)for v in row['exact_native_point']);q=Point(*[float(v)for v in exact]);ly=row['reference_layer'];ground=row['reference_root'][0];domain=after['domains_normalized'][ground]
        ownclear=max([float(zb[u]['clearance_mm'])for u in row['before_native_source_zone_UUIDs']]);neighbors={};sameground=[]
        for i in trees[ly].query(box(q.x-search,q.y-search,q.x+search,q.y+search)):
            r=rec[ly][int(i)];net=norm(r['raw_net']);gap=q.distance(r['shape'])-r['radius']
            if net==ground:
                if r['kind']=='via'and(r['kind'],r['UUID'],ly)in keys[ground]and gap<=0:
                    v=r['data'];d=math.hypot(q.x-v['x'],q.y-v['y'])
                    if d>v['drill']/2:sameground.append({'UUID':r['UUID'],'raw_net':r['raw_net'],'actual_source_rooted_layer_key':True,'point_inside_nominal_annulus':True,'reference_scope_not_credited':True})
                continue
            required=max(ownclear,.15 if after['domains_normalized'].get(net)==domain else .6,float(r['data'].get('clearance_mm',0)))
            if gap>required+.05:continue
            key=(r['kind'],r['UUID']);old=oldobjects[r['kind']].get(r['UUID']);oldlocal=byold.get((r['kind'],r['UUID'],ly),[])
            oldgap=min((q.distance(x['shape'])-x['radius']for x in oldlocal),default=None)
            if r['kind']=='fill':
                change='NEW_NATIVE_ZONE'if old is None else'CHANGED_NATIVE_ZONE_INTENT_OR_PROFILE'if any(old.get(k)!=r['data'].get(k)for k in set(old)|set(r['data'])if k!='fills')else'UNCHANGED_NATIVE_ZONE_INTENT_REFILLED'
            else:change='NEW_DISCRETE'if old is None else'CHANGED_DISCRETE'if state(old,r['kind'])!=state(r['data'],r['kind'])else'UNCHANGED_DISCRETE'
            candidate={'kind':r['kind'],'UUID':r['UUID'],'raw_net':r['raw_net'],'current_nominal_point_to_Cu_gap_mm':gap,'declared_nominal_clearance_mm':required,'before_same_object_nearest_Cu_gap_mm':oldgap,'current_change':change,'inside_nominal_clearance_by_float_triage':gap<required,'before_inside_nominal_clearance_by_float_triage':oldgap is not None and oldgap<required,'triage_not_acceptance':True}
            if key not in neighbors or gap<neighbors[key]['current_nominal_point_to_Cu_gap_mm']:neighbors[key]=candidate
        candidates=sorted(neighbors.values(),key=lambda r:r['current_nominal_point_to_Cu_gap_mm']-r['declared_nominal_clearance_mm'])
        rulehits=[]
        for rule,sh in rule_rows:
            if ly not in rule['layers']or not sh.envelope.intersects(q):continue
            pointIU=tuple(v*1e6 for v in exact);locs=[A.polyloc(pointIU,rs)for rs in prepared[rule['UUID']]]
            if any(s!='EXTERIOR'for s in locs):rulehits.append({'UUID':rule['UUID'],'name':rule['name'],'exact_point_locations':locs,'physical_keepout_scope_held':True})
        blocking=[r for r in candidates if r['inside_nominal_clearance_by_float_triage']]
        if blocking:category='NOMINAL_FOREIGN_CU_CANDIDATE:'+blocking[0]['current_change']+':'+blocking[0]['kind']+':'+blocking[0]['UUID']
        elif rulehits:category='EXACT_UNCHANGED_PHYSICAL_NO_FILL_POINT_INTERSECTION:'+rulehits[0]['UUID']
        elif sameground:category='CURRENT_SOURCE_GROUND_ANNULUS_AT_WITHDRAWN_FILL_POINT_SCOPE_HELD'
        else:category='NO_CURRENT_NOMINAL_FOREIGN_CU_OR_NO_FILL_POINT_CAUSE_IDENTIFIED'
        result={**row,'cause_category':category,'nearest_current_foreign_Cu_candidates':candidates[:8],'actual_source_ground_annulus_points_uncredited':sameground,'exact_native_no_fill_point_hits':rulehits,'all_parent_failures_held':True};results.append(result);clusters[category].append(row)
        if index%100==0:put('progress.json',{'completed_components':index,'total_components':len(points),'clusters':{k:len(v)for k,v in clusters.items()}})
    put('all-native-withdrawal-point-current-causal-triage.json',results)
    summaries=[]
    for cause,items in clusters.items():
        summaries.append({'cause':cause,'components':len(items),'tracks':len({r['track_UUID']for r in items}),'functional_track_counts':{f:len({r['track_UUID']for r in items if r['descriptive_function_class']==f})for f in sorted({r['descriptive_function_class']for r in items})},'raw_component_area_sum_for_ordering_only':sum(r['raw_component_area_mm2_for_ordering_only']for r in items),'priority_clock_serial_motion_or_highspeed':sorted({r['track_UUID']for r in items if r['descriptive_function_class']=='clock_serial_motion_or_highspeed_named'})})
    put('causal-clusters.json',sorted(summaries,key=lambda r:(-r['functional_track_counts'].get('clock_serial_motion_or_highspeed_named',0),-r['raw_component_area_sum_for_ordering_only'])))
    put('receipt.json',{'status':'ALL433_CURRENT_CAUSAL_TRIAGE_NOT_REFERENCE_OR_GEOMETRY_ACCEPTANCE','components':len(results),'unique_tracks':len({r['track_UUID']for r in results}),'clusters':len(clusters),'only_native_API_proven_NPTHWithNoCopper_and_no_flash_excluded_as_electrical_Cu':sorted(no_copper),'NPTH_drill_voids_and_washer_mechanical_roles_preserved':True,'float_gaps_used_only_to_rank_and_identify_causal_candidates':'Exact guarded candidate proof required before any repair is composable','all_raw_parent_failures_and_physical_current_scopes_held':True,'no_own_caps_added':True,'native_jobs':0,'candidate_or_source_changed':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),POINTS,NPTH,RULES,beforefile,afterfile,groupfile,helper)},'elapsed_seconds':time.monotonic()-st})
    print('CAUSAL_TRIAGE_COMPLETE',len(results),len(clusters),flush=True)
if __name__=='__main__':main()
