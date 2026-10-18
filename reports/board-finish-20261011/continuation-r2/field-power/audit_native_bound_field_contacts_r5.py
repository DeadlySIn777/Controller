"""Complete native-bound field contact check with independent SBC local-clearance projection."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
HERE=Path(__file__).resolve().parent;path=HERE/'audit_logic_repairs_r1.py';text=path.read_text()
text=text.replace("OUT=HERE/'logic-return-contact-audit-r1'","OUT=HERE/'native-bound-field-contact-audit-r5'")
text=text.replace('import complete_geometry_r2 as G','import complete_geometry_r2 as G\nimport native_clearance_projection_r1 as M\nimport zone_projection_r1 as N')
text=text.replace("bp=HERE/'coupled-logic-base-r1'","bp=HERE/'native-bound-field-base-r5'")
needle="adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());before=m['projected'];"
new="""adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());fp=HERE/'field-contact-repair-r2-raw';fr=json.loads((fp/'receipt.json').read_text());assert sha(fp/'proposed-zones.pkl')==fr['proposal_sha256'];sp=HERE/'b5-contact-repair-r3-frozen';sr=json.loads((sp/'receipt.json').read_text());assert sha(sp/'proposed-zones.pkl')==sr['proposal_sha256'];cb=HERE/'owned-field-zones-native-r3';cr=json.loads((cb/'receipt.json').read_text());assert sha(cb/'proposed-zones.pkl')==cr['proposal_sha256'];adds=pickle.loads((cb/'proposed-zones.pkl').read_bytes());owned={q['uuid'] for q in adds};m['new_zones']=[q for q in m['new_zones'] if q['uuid'] not in owned];allzones=m['new_zones']+adds
    collisions=[]
    for i,a in enumerate(allzones):
        for b in allzones[i+1:]:
            if a['layer']!=b['layer'] or C.norm(a['net'])==C.norm(b['net']):continue
            gap=.15 if m['discrete']['domains_normalized'][C.norm(a['net'])]==m['discrete']['domains_normalized'][C.norm(b['net'])] else .6
            if a['shape'].distance(b['shape'])<gap+.024:collisions.append({'a':a['uuid'],'b':b['uuid'],'distance_mm':a['shape'].distance(b['shape']),'required_mm':gap+.024})
    assert not collisions,collisions
    minimum_rows=M.minimum_web_screen(allzones);(OUT/'minimum-web-screen.json').write_text(json.dumps(minimum_rows,indent=1)+'\\n');before=m['projected'];"""
assert needle in text;text=text.replace(needle,new)
text=text.replace("after,retreats=G.projected(","after,retreats=N.projected(")
text=text.replace("'repair_receipt_sha256':sha(rp/'receipt.json'),", "'repair_receipt_sha256':sha(rp/'receipt.json'),'field_repair_receipt_sha256':sha(fp/'receipt.json'),'b5_repair_receipt_sha256':sha(sp/'receipt.json'),'native_bound_owned_shape_receipt_sha256':sha(cb/'receipt.json'),'all_new_plane_mutual_clearance':'PASS','projection_method':'Max(domain clearance, original explicit local zone clearance, new0.15)+0.025mm for changed discrete Cu and new planes; no native fill claim','minimum_web_screen_sha256':sha(OUT/'minimum-web-screen.json'),'native_discrete_sha256':br['native_discrete_sha256'],")
exec(compile(text,str(path),'exec'))
