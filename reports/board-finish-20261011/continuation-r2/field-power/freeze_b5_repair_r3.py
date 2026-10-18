"""Freeze only the first proven repair; it already joins both mandatory split groups."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from inventory import sha
HERE=Path(__file__).resolve().parent;OUT=HERE/'b5-contact-repair-r3-frozen';assert not OUT.exists();OUT.mkdir()
rp=HERE/'b5-contact-repair-r2';r=json.loads((rp/'receipt.json').read_text());assert sha(rp/'receipt.json')=='ad85afa8f9f126a1ce989ec190045308ad0da23bfa07be504ff1698beebafd27';assert sha(rp/'proposed-zones.pkl')==r['proposal_sha256'];zz=pickle.loads((rp/'proposed-zones.pkl').read_bytes());q=r['rows'][0]['repair'];assert {0,1,3}.issubset({x['group'] for x in q['contacted_groups']});assert zz[0]['uuid']==q['uuid'];assert zz[0]['net']=='/motherboard_safety_sensor{slash}FIELD_B_5V_PRE'
(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps([zz[0]],protocol=5));q=dict(q);q['current_allocation_status']='COMPLETE_B5PRE_NORMAL_RESERVATION_0.132585384615_A_ROUTING_POLICY_0.14_A';q['conditional_sheet_only_drop_at_routing_target_V']=q['legacy_uniform_core_sheet_R60C_upper_bound_ohm']*.14;q['barrel_contact_full_mesh_temperature_and_switching_qualification']=False
receipt={'verdict':'ONE_EXACT_RAW_B5PRE_REPAIR_RESTORES_BOTH_REQUIRED_PARTITIONS_MUTUAL_GATE_PENDING','construction_receipt_sha256':sha(rp/'receipt.json'),'proposal_sha256':sha(OUT/'proposed-zones.pkl'),'rows':[{'repair':q}],'redundant_second_constructed_finger_excluded':True,'first_failed_constructor_preserved':'b5-contact-repair-r1/receipt.json','first_failure_explanation':'Raw NET used in normalized lookup comparison incorrectly blocked same-net Cu. No-path was a constructor error, not geometric impossibility. Corrected r2 retains exact raw serialization while using lookupNET for comparisons.','native_jobs':0,'board_written':False,'source_complete_model_sha256':sha(HERE/'normal-model-r3.json')};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'))
