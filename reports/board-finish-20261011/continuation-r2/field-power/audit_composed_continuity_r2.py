"""Audit every retained pad relationship affected by prospective fill voids."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from contact_layout import HERE,load,norm
from power_groups import graph
from inventory import sha
OUT=HERE/'composed-field-continuity-r2'
def main():
 assert not OUT.exists();OUT.mkdir();old,b=load();r=json.loads((HERE/'composed-field-geometry-r3/receipt.json').read_text(encoding='utf-8'));gpath=HERE/'composed-field-geometry-r3/geometry.pkl';assert sha(gpath)==r['geometry_sha256'];new=pickle.loads(gpath.read_bytes());source=json.loads((HERE/'combined-power-source-r3-hierarchy/receipt.json').read_text(encoding='utf-8'));exclude={(x['ref'],x['pin']) for x in source['pin_net_changes']};nets=sorted({norm(x['net_raw']) for x in r['prospective_foreign_clearance_voids']});rows=[]
 for net in nets:
  a=graph(old,net);bb=graph(new,net);membership={};newgroups=[]
  for i,group in enumerate(bb):
   pads={(x['ref'],x['pin'],x['uuid']) for x in group if x['kind']=='pad' and x['pin']};newgroups.append(pads)
   for pad in pads:assert pad not in membership;membership[pad]=i
  losses=[];checked=0
  for i,group in enumerate(a):
   pads={(x['ref'],x['pin'],x['uuid']) for x in group if x['kind']=='pad' and x['pin'] and (x['ref'],x['pin']) not in exclude}
   if len(pads)<2:continue
   partitions={}
   for pad in pads:partitions.setdefault(membership.get(pad,'MISSING'),[]).append(list(pad))
   checked+=1
   if len(partitions)!=1 or 'MISSING' in partitions:losses.append({'old_group':i,'old_retained_pad_count':len(pads),'new_partitions':{str(k):sorted(v) for k,v in partitions.items()}})
  rows.append({'canonical_net':net,'verdict':'PASS' if not losses else 'REPAIR_REQUIRED','old_pad_groups':sum(any(x['kind']=='pad' for x in group) for group in a),'new_pad_groups':sum(bool(pads) for pads in newgroups),'old_retained_multi_pad_groups_checked':checked,'lost_retained_group_relationships':losses});print(net,rows[-1]['verdict'],'lostgroups',len(losses),flush=True);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 result={'verdict':'PASS' if all(x['verdict']=='PASS' for x in rows) else 'REPAIR_REQUIRED','rows':rows,'exact_14_intentionally_moved_pads_excluded':sorted([list(x) for x in exclude]),'original_binding':b,'prospective_geometry_sha256':sha(gpath),'composed_receipt_sha256':sha(HERE/'composed-field-geometry-r3/receipt.json'),'native_filled_evidence':False,'native_jobs':0,'board_written':False,'scope':'Every distinct physical old named-pad UUID relationship on every net whose filled copper is explicitly voided; isolated one-pad islands are not manufactured connections.'};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':result['verdict'],'receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
