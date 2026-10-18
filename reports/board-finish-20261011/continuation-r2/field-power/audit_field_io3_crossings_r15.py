"""Independent complete field/LOGIC contact audit of exact SBC r15 crossing model."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from collections import defaultdict
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
from fast_contacts import graph,discrete_keys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
OUT=HERE/'field-io3-crossing-contact-audit-r15'
def losses(a,b):
    mm={q:i for i,xs in enumerate(b) for q in discrete_keys(xs)};result=[]
    for i,xs in enumerate(a):
        keys=discrete_keys(xs)
        if len(keys)<2:continue
        parts=defaultdict(list)
        for q in keys:parts[str(mm.get(q,'MISSING'))].append(list(q))
        if len(parts)>1 or 'MISSING' in parts:result.append({'old_group':i,'old_discrete_count':len(keys),'new_partitions':dict(parts)})
    return result
def main():
    assert not OUT.exists();OUT.mkdir();rp=HERE.parent/'sbc-power/io3-field-crossings-r15';rr=json.loads((rp/'receipt.json').read_text());cache=rp/'model.pkl';old,discrete,binding,zones,saved=pickle.loads(cache.read_bytes());bp=HERE/'native-bound-field-contact-audit-r5';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];before=pickle.loads((bp/'geometry.pkl').read_bytes());priorgroups=pickle.loads((bp/'groups.pkl').read_bytes());nm=pickle.loads((HERE/'native-bound-field-base-r5/model.pkl').read_bytes())
    for kind in ('pads','tracks','vias'):
        assert {q['uuid']:q for q in discrete[kind]}=={q['uuid']:q for q in nm['discrete'][kind]},('discrete mismatch',kind)
    frozen=pickle.loads((HERE/'full-field-zone-recipe-r2/proposed-zones.pkl').read_bytes());byid={q['uuid']:q for q in zones};carves={q['uuid']:q for q in rr['field_In2_exact_delta']};fieldrows=[]
    for q in frozen:
        new=byid[q['uuid']];removed=q['shape'].difference(new['shape']);added=new['shape'].difference(q['shape']);assert added.area<1e-8
        if removed.area>1e-8:
            assert q['uuid'] in carves and q['layer']=='In2.Cu';c=carves[q['uuid']];assert sha(c['removed_file'])==c['removed_file_sha256'];assert abs(removed.area-c['removed_area_mm2'])<1e-7
        fieldrows.append({'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'frozen_shape_unchanged':removed.area<1e-8 and added.area<1e-8,'removed_area_mm2':removed.area,'no_added_shape_area_mm2':added.area})
    after,cuts=N.projected(old,discrete,zones);saveZ={q['uuid']:q for q in saved['zones']};projectiondiff=[]
    for z in after['zones']:
        s=saveZ[z['uuid']]
        for l,rs in z['fills'].items():
            d=unary_union(C.poly(rs)).symmetric_difference(unary_union(C.poly(s['fills'].get(l,[])))).area
            if d>1e-8:projectiondiff.append({'uuid':z['uuid'],'layer':l,'area_mm2':d})
    assert not projectiondiff,projectiondiff;oldZ={q['uuid']:q for q in before['zones']};changed=[]
    for z in after['zones']:
        if z['uuid'] not in oldZ:continue
        for l,rs in z['fills'].items():
            a=unary_union(C.poly(oldZ[z['uuid']]['fills'].get(l,[])));b=unary_union(C.poly(rs));difference=a.symmetric_difference(b)
            if difference.area>1e-8:changed.append({'uuid':z['uuid'],'layer':l,'net_raw':z['net'],'lost_area_mm2':a.difference(b).area,'restored_fill_area_mm2':b.difference(a).area})
    nets=sorted(set(priorgroups)|{C.norm(q['net_raw']) for q in changed}|{'/LOGIC_GND','/motherboard_do/FIELD_B_0V','/motherboard_motors/FIELD_GND'});rows=[];allgroups={}
    for net in nets:
        a=priorgroups.get(net)
        if a is None:a=graph(before,net)
        b=graph(after,net);allgroups[net]=b;lost=losses(a,b);row={'net':net,'verdict':'PASS' if not lost else 'REPAIR_REQUIRED','old_groups':len(a),'new_groups':len(b),'lost_old_discrete_relationships':lost};rows.append(row);print(net,row['verdict'],'lossgroups',len(lost),flush=True);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
    source=[]
    for net,root in [('/LOGIC_GND','J11001'),('/motherboard_do/FIELD_B_0V','J11005'),('/motherboard_motors/FIELD_GND','J11003')]:
        gs=allgroups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(root,'2') for q in xs));oldri=next(i for i,xs in enumerate(priorgroups[net]) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(root,'2') for q in xs));oldkeys=discrete_keys(priorgroups[net][oldri]);newkeys=discrete_keys(gs[ri]);missing=sorted(oldkeys-newkeys);source.append({'net':net,'actual_source':root+'.2','source_group':ri,'rooted_named_physical_pads':len({q['uuid'] for q in gs[ri] if q['kind']=='pad' and q['pin']}),'prior_source_rooted_physical_Cu_not_in_new_source_group':[list(q) for q in missing],'unrooted_named_pad_groups':[i for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]})
    (OUT/'geometry.pkl').write_bytes(pickle.dumps(after,protocol=5));(OUT/'groups.pkl').write_bytes(pickle.dumps(allgroups,protocol=5));receipt={'verdict':'PASS_RETAINED_CONTACTS_CURRENT_NATIVE_PENDING' if all(q['verdict']=='PASS' for q in rows) and not any(q['prior_source_rooted_physical_Cu_not_in_new_source_group'] for q in source) else 'RETAINED_CONTACT_REPAIR_REQUIRED','rows':rows,'actual_source_root_status':source,'frozen38_owned_shapes_delta':fieldrows,'exact_discrete_unchanged':True,'independent_projection_matches_saved_r15':True,'input_r15_cache_sha256':sha(cache),'input_r15_receipt_sha256':sha(rp/'receipt.json'),'prior_field_contact_receipt_sha256':sha(bp/'receipt.json'),'native_discrete_sha256':br['native_discrete_sha256'],'geometry_sha256':sha(OUT/'geometry.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'prospective_original_fill_deltas':changed,'complete_original_fill_retreats':cuts,'local25_and_later_dogbones_not_composed':True,'new_holes':0,'native_jobs':0,'board_written':False,'full_signed_current_redistribution_native_fill_and_thermal_gates':'OPEN'};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
