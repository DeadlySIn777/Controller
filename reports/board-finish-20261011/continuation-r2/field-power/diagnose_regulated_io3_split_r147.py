"""Exact existing IO3 split and related six-feed old-fill cutter ledger."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'regulated-io3-split-diagnosis-r147'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'paired-regional-six-regulated-full-contact-audit-r142';old=pickle.loads((base/'ROOT_R22-regional-model.pkl').read_bytes());new=pickle.loads((base/'REG_R130-regional-model.pkl').read_bytes());og=pickle.loads((base/'ROOT_R22-regional-groups.pkl').read_bytes())['/IO_3V3'];ng=pickle.loads((base/'REG_R130-regional-groups.pkl').read_bytes())['/IO_3V3'];bad=next(q for q in json.loads((base/'contact-rows.json').read_text()) if q['net']=='/IO_3V3')['regional_R22_old_discrete_losses'];assert len(bad)==1;affected=bad[0]['new_partitions'];small=min(affected,key=lambda k:len(affected[k]));keys={tuple(k) for k in affected[small]};members=[q for q in ng[int(small)] if (q['kind'],q['uuid']) in keys];rows=[{'kind':q['kind'],'uuid':q['uuid'],'ref':q.get('ref'),'pin':q.get('pin'),'layer':q['layer'],'bounds':list(q['shape'].bounds)} for q in members];write(O/'split-member-rows.json',rows)
 oldzones={q['uuid']:q for q in old[4]['zones']};zdelta=[];sources=pickle.loads((H/'safe-root22-regulated-source-contact-audit-r130/six-corrected-REG-zones.pkl').read_bytes());cutrows=json.loads((base/'REG_R130-regional-retreats.json').read_text());cutmap={(q['zone_uuid'],q['layer']):q for q in cutrows};region=unary_union([q['shape'] for q in ng[int(small)]])
 for q in new[4]['zones']:
  if C.norm(q['net'])!='/IO_3V3' or q['uuid'] not in oldzones:continue
  for l,records in q['fills'].items():
   a=unary_union(C.poly(oldzones[q['uuid']]['fills'].get(l,[])));b=unary_union(C.poly(records));lost=a.difference(b)
   if lost.is_empty:continue
   related=[{'uuid':p['uuid'],'net':p['net'],'layer':p['layer'],'shape_bounds':list(p['shape'].bounds),'shape_to_loss_mm':p['shape'].distance(lost)} for p in sources if p['layer']==l and p['shape'].distance(lost)<.8]
   zdelta.append({'old_zone_uuid':q['uuid'],'layer':l,'lost_area_mm2':lost.area,'lost_bounds':list(lost.bounds),'lost_distance_to_detached_contacts_mm':lost.distance(region),'new_REG_related':related,'cutters':cutmap.get((q['uuid'],l),{}).get('cutters',[])})
 write(O/'IO3-old-fill-loss-and-cutter-rows.json',zdelta);write(O/'receipt.json',{'verdict':'DIAGNOSTIC_EXACT_IO3_SPLIT_NO_WAIVER','paired_R142_receipt_sha256':sha(base/'receipt.json'),'old_group':bad[0]['old_group'],'old_discrete_count':bad[0]['old_discrete_count'],'new_retained_partitions':{k:len(v) for k,v in affected.items()},'detached_partition':small,'split_members_sha256':sha(O/'split-member-rows.json'),'fill_loss_rows_sha256':sha(O/'IO3-old-fill-loss-and-cutter-rows.json'),'no_original_definition_or_copper_change':True});print('R147',sha(O/'receipt.json'),'members',json.dumps(rows), 'deltas',json.dumps([{k:v for k,v in r.items() if k!='cutters'} for r in zdelta]),flush=True)
if __name__=='__main__':main()
