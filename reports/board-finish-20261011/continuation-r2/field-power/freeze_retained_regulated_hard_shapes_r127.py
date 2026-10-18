"""Freeze four retained REG body nominees without waiting for full projection."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'regulated-four-retained-hard-snapshot-r127';DROP={'c70aed70-d8e0-5712-8468-097b177d3c8a','e7367999-5e27-5c2f-a1c8-628b55d61bcd'}
def main():
 assert not O.exists();O.mkdir();src=H/'regulated-source-contact-reference-audit-r116';p=src/'proposed-zones.pkl';assert sha(p)=='3069a86cc9a1c1e7d192bede4285a697e78f878932f84ae7458c62f931c54dab';zones=pickle.loads(p.read_bytes());keep=[q for q in zones if q['uuid'] not in DROP];assert len(keep)==4 and {q['uuid'] for q in zones if q['uuid'] in DROP}==DROP;(O/'proposed-zones.pkl').write_bytes(pickle.dumps(keep,protocol=5));d=H/'regulated-quantized-inner-source-feeds-r114/proposed-discrete.pkl';assert sha(d)=='9651216efa39c190b8731162251cb4b68f6313f1b12c62f5eab45d2a452c891b';(O/'proposed-discrete.pkl').write_bytes(d.read_bytes());receipt={'verdict':'EXACT_FOUR_RETAINED_BODY_HARD_SNAPSHOT_ONLY','source_six_zone_pickle_sha256':sha(p),'failed_full_scope_receipt_sha256':sha(src/'receipt.json'),'retained_zone_sha256':sha(O/'proposed-zones.pkl'),'retained_discrete_sha256':sha(O/'proposed-discrete.pkl'),'zones':[{'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer']} for q in keep],'withdrawn_only_failed_new_In1_UUIDs':sorted(DROP),'via_count':3,'segment_count':6,'all_objects_unchanged_subset':True,'new_source_root_OR_contact_ref_current_native_credit':False,'requires_fresh_full_projection_corrected_returns_and_root_spines':True,'board_written':False,'native_jobs':0};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(sha(O/'receipt.json'));print(receipt['retained_zone_sha256'])
if __name__=='__main__':main()
