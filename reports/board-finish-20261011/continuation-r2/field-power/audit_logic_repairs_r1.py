"""Independent complete repour projection and retained physical-contact gates."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from collections import defaultdict
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
from fast_contacts import graph,discrete_keys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import complete_geometry_r2 as G
OUT=HERE/'logic-return-contact-audit-r1'
def relation_losses(a,b):
    mm={q:i for i,xs in enumerate(b) for q in discrete_keys(xs)};loss=[]
    for i,xs in enumerate(a):
        keys=discrete_keys(xs)
        if len(keys)<2:continue
        parts=defaultdict(list)
        for q in keys:parts[str(mm.get(q,'MISSING'))].append(list(q))
        if len(parts)>1 or 'MISSING' in parts:loss.append({'prior_group':i,'retained_discrete_count':len(keys),'new_partitions':{k:sorted(v) for k,v in parts.items()}})
    return loss
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'coupled-logic-base-r1';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')==br['model_sha256'];m=pickle.loads((bp/'model.pkl').read_bytes());rp=HERE/'logic-return-repair-r2';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-zones.pkl')==rr['proposal_sha256'];adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());before=m['projected'];after,retreats=G.projected(m['old'],m['discrete'],m['new_zones']+adds);oldZ={z['uuid']:z for z in before['zones']};changed=[]
    for z in after['zones']:
        if z['uuid'] not in oldZ:continue
        for l,rs in z['fills'].items():
            aa=unary_union(C.poly(oldZ[z['uuid']]['fills'].get(l,[])));bb=unary_union(C.poly(rs));delta=aa.difference(bb)
            assert bb.difference(aa).area<1e-8,('projection manufactured original Cu',z['uuid'],l)
            if delta.area>1e-8:changed.append({'uuid':z['uuid'],'layer':l,'net_raw':z['net'],'additional_retreat_area_mm2':delta.area})
    print('projection',len(adds),'GND additions',len(changed),'additional old fill layer retreats',flush=True)
    nets=sorted({C.norm(q['net_raw']) for q in changed}|{'/LOGIC_GND'});rows=[];allgroups={}
    for net in nets:
        if net=='/LOGIC_GND':a=pickle.loads((bp/'groups.pkl').read_bytes())['new_groups']
        else:a=graph(before,net)
        b=graph(after,net);allgroups[net]=b;losses=relation_losses(a,b);r={'net':net,'verdict':'PASS' if not losses else 'REPAIR_REQUIRED','prior_groups':len(a),'new_groups':len(b),'lost_retained_discrete_group_relationships':losses};rows.append(r);print(net,r['verdict'],'lossgroups',len(losses),flush=True);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
    oldlogic=pickle.loads((bp/'groups.pkl').read_bytes())['old_groups'];newlogic=allgroups['/LOGIC_GND'];newmapping={q:i for i,xs in enumerate(newlogic) for q in discrete_keys(xs)};oldkeys=discrete_keys(oldlogic[0]);retained={q for q in oldkeys if q in newmapping};partitions=defaultdict(list)
    for q in retained:partitions[str(newmapping[q])].append(list(q))
    assert len(partitions)==1,('old main LOGIC physical Cu not repaired',[(k,len(v)) for k,v in partitions.items()]);source=next(i for i,xs in enumerate(newlogic) if any(q['kind']=='pad' and q['ref']=='J11001' and q['pin']=='2' for q in xs));restoredgroup=int(next(iter(partitions)));assert source==restoredgroup;rootedpads={(q['ref'],q['pin'],q['uuid']) for q in newlogic[source] if q['kind']=='pad' and q['pin']};raw=pickle.dumps(after,protocol=5);(OUT/'geometry.pkl').write_bytes(raw);raw=pickle.dumps(allgroups,protocol=5);(OUT/'groups.pkl').write_bytes(raw)
    receipt={'verdict':'PASS_CONTACTS_CURRENT_AND_NATIVE_PENDING' if all(q['verdict']=='PASS' for q in rows) else 'FOREIGN_CONTACT_REPAIR_REQUIRED','rows':rows,'base_receipt_sha256':sha(bp/'receipt.json'),'repair_receipt_sha256':sha(rp/'receipt.json'),'geometry_sha256':sha(OUT/'geometry.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'additional_old_fill_retreats':changed,'full_combined_retreat_ledger':retreats,'old_LOGIC_main_retained_discrete_items_rejoined':len(retained),'old_LOGIC_named_pad_count_rejoined':len({(q['ref'],q['pin'],q['uuid']) for q in oldlogic[0] if q['kind']=='pad' and q['pin']}),'actual_J11001_source_rooted_physical_named_pads':len(rootedpads),'source_root_group':source,'all_old_retained_LOGIC_main_item_joins_restored':True,'new_holes':0,'native_filled_evidence':False,'native_jobs':0,'board_written':False,'still_unrooted_load_groups_present':True,'root_latest_CM_holes_not_yet_composed':True};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'verdict':receipt['verdict'],'restored_old_items':len(retained),'rooted_pads':len(rootedpads),'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
