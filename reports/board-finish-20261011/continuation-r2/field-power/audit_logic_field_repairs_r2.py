"""Mutual full contact proof after all four actual field-ground endpoint repairs."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
HERE=Path(__file__).resolve().parent;path=HERE/'audit_logic_repairs_r1.py';text=path.read_text()
text=text.replace("OUT=HERE/'logic-return-contact-audit-r1'","OUT=HERE/'logic-field-mutual-contact-audit-r2'")
needle="adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());before=m['projected'];"
new="""adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());fp=HERE/'field-contact-repair-r2-raw';fr=json.loads((fp/'receipt.json').read_text());assert sha(fp/'proposed-zones.pkl')==fr['proposal_sha256'];fieldadd=pickle.loads((fp/'proposed-zones.pkl').read_bytes());adds+=fieldadd
    # Audit actual mutual shapes independently, including all four field repairs.
    foreign_collisions=[]
    for i,a in enumerate(m['new_zones']+adds):
        for b in (m['new_zones']+adds)[i+1:]:
            if a['layer']!=b['layer'] or C.norm(a['net'])==C.norm(b['net']):continue
            gap=.15 if m['projected']['domains_normalized'][C.norm(a['net'])]==m['projected']['domains_normalized'][C.norm(b['net'])] else .6
            if a['shape'].distance(b['shape'])<gap+.024:foreign_collisions.append({'a':a['uuid'],'b':b['uuid'],'distance_mm':a['shape'].distance(b['shape']),'required_mm':gap+.024})
    assert not foreign_collisions,foreign_collisions
    before=m['projected'];"""
assert needle in text;text=text.replace(needle,new)
text=text.replace("'repair_receipt_sha256':sha(rp/'receipt.json'),", "'repair_receipt_sha256':sha(rp/'receipt.json'),'field_repair_receipt_sha256':sha(fp/'receipt.json'),'all_new_field_CORE_GND_plane_mutual_clearance_screen':'PASS',")
exec(compile(text,str(path),'exec'))
