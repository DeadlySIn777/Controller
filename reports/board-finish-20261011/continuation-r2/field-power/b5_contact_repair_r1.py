"""Restore B5PRE's two newly separated local load/cap groups to real L19001.2."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
HERE=Path(__file__).resolve().parent;path=HERE/'field_contact_repair_r1.py';text=path.read_text()
text=text.replace("OUT=HERE/'field-contact-repair-r1'","OUT=HERE/'b5-contact-repair-r1'")
text=text.replace("base=HERE/'logic-return-contact-audit-r1'","base=HERE/'logic-field-mutual-contact-audit-r2'")
text=text.replace("zones=mm['new_zones']+pickle.loads((HERE/'logic-return-repair-r2/proposed-zones.pkl').read_bytes());", "zones=mm['new_zones']+pickle.loads((HERE/'logic-return-repair-r2/proposed-zones.pkl').read_bytes())+pickle.loads((HERE/'field-contact-repair-r2-raw/proposed-zones.pkl').read_bytes());")
text=text.replace("[('FAG','/motherboard_motors/FIELD_GND','J11003',[0]),('FBG','/motherboard_do/FIELD_B_0V','J11005',[4,5,15])]","[('B5PRE','/motherboard_safety_sensor/FIELD_B_5V_PRE','L19001',[1,3])]")
# Resolve raw spelling once from the actual source pad; never serialize lookup aliases.
text=text.replace("dom=h['domains_normalized'][NET];groups=allgroups[NET];", "lookupNET=NET;dom=h['domains_normalized'][NET];groups=allgroups[NET];NET=next(q['net'] for q in groups[0] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2'));assert '/motherboard_safety_sensor{slash}FIELD_B_5V_PRE'==NET;")
# Underlying constructor compares normalized lookups, while emission keeps raw NET.
text=text.replace("C.norm(q['net'])==NET","C.norm(q['net'])==lookupNET")
text=text.replace("C.norm(t['net'])!=NET","C.norm(t['net'])!=lookupNET")
text=text.replace("C.norm(v['net'])==NET","C.norm(v['net'])==lookupNET")
text=text.replace("C.norm(p['net'])!=NET","C.norm(p['net'])!=lookupNET")
text=text.replace("C.norm(z['net'])!=NET","C.norm(z['net'])!=lookupNET")
text=text.replace("'native_jobs':0};adds.append", "'native_jobs':0,'normal_complete_B5PRE_load_A':0.132585384615,'proposed_routing_target_A':0.14,'conditional_R_model':'35um nominal copper at 60C; sheet only, source/load contacts and thermal qualification open'};adds.append")
text=text.replace("'controller-field-lost-contact-r1-'", "'controller-b5pre-lost-contact-r1-'")
exec(compile(text,str(path),'exec'))
