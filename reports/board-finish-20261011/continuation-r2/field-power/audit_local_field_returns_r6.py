"""Independently project the25 local field returns and check every affected net."""
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
OUT=HERE/'local-field-return-contact-audit-r6'
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
    assert not OUT.exists();OUT.mkdir();bp=HERE/'native-bound-field-contact-audit-r5';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];before=pickle.loads((bp/'geometry.pkl').read_bytes());oldgroups=pickle.loads((bp/'groups.pkl').read_bytes());nm=pickle.loads((HERE/'native-bound-field-base-r5/model.pkl').read_bytes());frozen=pickle.loads((HERE/'full-field-zone-recipe-r2/proposed-zones.pkl').read_bytes());ids={q['uuid'] for q in frozen};rp=HERE/'source-rooted-local-field-returns-r6';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-zones.pkl')==rr['proposal_sha256'];adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());planes=[q for q in nm['new_zones'] if q['uuid'] not in ids]+frozen+adds;collisions=[]
    for i,a in enumerate(planes):
        for b in planes[i+1:]:
            if a['layer']!=b['layer'] or C.norm(a['net'])==C.norm(b['net']):continue
            gap=.15 if nm['discrete']['domains_normalized'][C.norm(a['net'])]==nm['discrete']['domains_normalized'][C.norm(b['net'])] else .6
            distance=a['shape'].distance(b['shape'])
            if distance<gap+.024:collisions.append({'a':a['uuid'],'b':b['uuid'],'distance_mm':distance,'required_mm':gap+.024})
    after,retreats=N.projected(nm['old'],nm['discrete'],planes);oldZ={q['uuid']:q for q in before['zones']};changed=[]
    for z in after['zones']:
        if z['uuid'] not in oldZ:continue
        for l,rs in z['fills'].items():
            a=unary_union(C.poly(oldZ[z['uuid']]['fills'].get(l,[])));b=unary_union(C.poly(rs));delta=a.difference(b)
            assert b.difference(a).area<1e-8
            if delta.area>1e-8:changed.append({'uuid':z['uuid'],'layer':l,'net_raw':z['net'],'additional_retreat_area_mm2':delta.area})
    nets=sorted({C.norm(q['net_raw']) for q in changed}|{'/LOGIC_GND','/motherboard_do/FIELD_B_0V','/motherboard_motors/FIELD_GND'});rows=[];newgroups={}
    for net in nets:
        a=oldgroups.get(net)
        if a is None:a=graph(before,net)
        b=graph(after,net);newgroups[net]=b;lost=losses(a,b);row={'net':net,'verdict':'PASS' if not lost else 'REPAIR_REQUIRED','lost_old_discrete_relationships':lost,'old_groups':len(a),'new_groups':len(b)};rows.append(row);print(net,row['verdict'],'lossgroups',len(lost),flush=True);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
    sources=[]
    for net,root in [('/motherboard_do/FIELD_B_0V','J11005'),('/motherboard_motors/FIELD_GND','J11003')]:
        gs=newgroups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(root,'2') for q in xs));pads={q['uuid'] for q in gs[ri] if q['kind']=='pad' and q['pin']};sources.append({'net':net,'source_root':root+'.2','root_group':ri,'actual_named_physical_pads_source_joined':len(pads),'still_unrooted_named_pad_groups':[i for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]})
    (OUT/'geometry.pkl').write_bytes(pickle.dumps(after,protocol=5));(OUT/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));receipt={'verdict':'PASS_CONTACTS_CURRENT_NATIVE_PENDING' if not collisions and all(q['verdict']=='PASS' for q in rows) else 'MUTUAL_REPAIR_REQUIRED','all_foreign_new_plane_clearance_collisions':collisions,'rows':rows,'field_source_status':sources,'additional_old_fill_retreats':changed,'complete_prospective_retreats':retreats,'geometry_sha256':sha(OUT/'geometry.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'base_contact_receipt_sha256':sha(bp/'receipt.json'),'local25_receipt_sha256':sha(rp/'receipt.json'),'exact_native_discrete_sha256':br['native_discrete_sha256'],'latest_CM_holes_composed':True,'final_SBC_IO3_r15_not_yet_composed':True,'new_holes':0,'native_jobs':0,'board_written':False,'full_signed_current_and_native_fill_gates':'OPEN'};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
