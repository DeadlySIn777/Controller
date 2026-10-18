"""Actual physical regulated-field load/source census on frozen R25 geometry."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
import contact_layout as C
import fast_contacts as F
from inventory import sha
P=Path(__file__).resolve().parent;OUT=P/'field-supply-census-r38'
def main():
 assert not OUT.exists();OUT.mkdir();bp=P/'local-and-b5-return-audit-r25';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());targets=[('A3V3','U11017','1'),('B3V3','U11018','1'),('B_DO3V3','U11038','1'),('FIELD5','U11017','5'),('B5PRE','L19001','2'),('B_DO_PG','U11038','6')];rows=[]
 for label,ref,pin in targets:
  p0=next(q for q in g['pads'] if(q['ref'],q['num'])==(ref,pin));net=C.norm(p0['net']);groups=F.graph(g,net);ports=[(ref,pin)]
  if label=='FIELD5':ports=[(q['ref'],q['num']) for q in g['pads'] if q['ref'].startswith('L110') and C.norm(q['net'])==net]
  rootkeys={q['uuid'] for q in g['pads'] if(q['ref'],q['num']) in ports};items=[]
  for i,xs in enumerate(groups):
   pp=[C.identity(q) for q in xs if q['kind']=='pad' and q.get('pin')];named={(q['ref'],q['pin'],q['uuid']) for q in pp};rooted=any(q['uuid'] in rootkeys for q in pp)
   if named:items.append({'physical_group_index':i,'source_port_present':rooted,'named_physical_pads':pp,'all_distinct_physical_contact_keys':sorted({(q['kind'],q['uuid'],q['layer']) for q in xs if q['kind']!='fill'}),'fill_component_count':sum(q['kind']=='fill' for q in xs)})
  rows.append({'label':label,'raw_net':p0['net'],'source_port_candidates':ports,'source_is_connector_power_root':False,'named_groups':len(items),'unrooted_named_groups':sum(not q['source_port_present'] for q in items),'groups':items});print(label,p0['net'],ports,'groups',len(items),'unrooted',rows[-1]['unrooted_named_groups'],flush=True)
 (OUT/'receipt.json').write_text(json.dumps({'verdict':'REGULATED_SUPPLY_CENSUS_COMPLETION_PENDING','rows':rows,'R25_receipt_sha256':sha(bp/'receipt.json'),'R25_geometry_sha256':sha(bp/'geometry.pkl'),'true_external_power_roots':['J11003.1/.2','J11005.1/.2'],'r32_rejected_and_r36_pending_excluded':True,'parent_protected24_and_SBC_new_CORE_omitted':True,'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
