"""Frozen R171 failure attribution; no changed candidate or routing claim."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely import from_wkb
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'sbc-power'))
import regional_guarded_declared_projection_r140 as P
O=H/'SAFE-IO3-exact-split-attribution-r176';assert not O.exists();O.mkdir()
R=H/'SAFE-regulated-u17-u10017-paired-regional-audit-r171'
old=pickle.loads((R/'baseline-regional-groups.pkl').read_bytes())['/IO_3V3']
new=pickle.loads((R/'groups.pkl').read_bytes())['/IO_3V3']
g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes())
base=pickle.loads((R/'baseline-regional-model.pkl').read_bytes())[-1]
loss=next(q for q in json.loads((R/'contact-rows.json').read_text(encoding='utf-8')) if q['net']=='/IO_3V3')['baseline_retained_relationship_losses'][0]
stats=[]
for index,keys in loss['new_partitions'].items():
 xs=new[int(index)];refs={}
 for q in xs:
  if q['kind']=='pad':refs.setdefault(q['ref'],set()).add(q['pin'])
 stats.append({'new_group':int(index),'retained_old_discrete_keys':len(keys),'all_discrete_keys':len(F.discrete_keys(xs)),'all_named_pads':sum(q['kind']=='pad' for q in xs),'bounds':list(unary_union([q['shape'] for q in xs]).bounds),'named_refs':{k:sorted(v) for k,v in sorted(refs.items())},'fills':[{'uuid':q['uuid'],'layer':q['layer'],'contour':q['contour'],'area':q['shape'].area,'bounds':list(q['shape'].bounds)} for q in xs if q['kind']=='fill']})
mask=from_wkb((H/'exact-original-IO3-preservation-spine-r167/exact-old-IO3-retained-spine-mask.wkb').read_bytes())
oldz={q['uuid']:q for q in base['zones'] if C.norm(q['net'])=='/IO_3V3'}
newz={q['uuid']:q for q in c['zones'] if C.norm(q['net'])=='/IO_3V3'}
cuts=[]
for uid,q in oldz.items():
 for layer,rs in q['fills'].items():
  a=unary_union(C.poly(rs));bb=unary_union(C.poly(newz[uid]['fills'][layer]));removed=a.difference(bb)
  if removed.area<1e-12:continue
  fp=O/(uid+'-'+layer+'.removed.wkb');fp.write_bytes(removed.wkb)
  causes=[]
  for candidate in z:
   if candidate['layer']!=layer or C.norm(candidate['net'])=='/IO_3V3':continue
   guard=max(float(q.get('clearance_mm',.15)),float(candidate.get('clearance_mm',.15)),.15)+.025
   cutter=P.bounded_buffer(candidate['shape'],guard)
   intersection=removed.intersection(cutter)
   if intersection.area>1e-10:causes.append({'uuid':candidate['uuid'],'net':candidate['net'],'guard':guard,'intersects_removed_area_mm2':intersection.area,'mask_clearance_mm':candidate['shape'].distance(mask) if layer=='In2.Cu' else None,'mask_removed_mm2':intersection.intersection(mask).area if layer=='In2.Cu' else None})
  cuts.append({'old_zone':uid,'layer':layer,'native_clearance':q.get('clearance_mm'),'removed_mm2':removed.area,'mask_removed_mm2':removed.intersection(mask).area if layer=='In2.Cu' else None,'file':str(fp),'file_sha256':sha(fp),'new_owned_causes':causes})
coverage=[]
for label,model in [('baseline',base),('candidate',c)]:
 fills=unary_union([s for q in model['zones'] if C.norm(q['net'])=='/IO_3V3' for s in C.poly(q['fills'].get('In2.Cu',[]))])
 coverage.append({'scope':label,'mask_uncovered_mm2':mask.difference(fills).area,'covers_mask':fills.covers(mask)})
result={'verdict':'DIAGNOSTIC_NO_ADOPTION','R171_model_sha256':sha(R/'model.pkl'),'retained_IO3_partitions':stats,'literal_mask_coverage':coverage,'old_IO3_changed_fill_cuts':cuts,'native_jobs':0,'board_written':False}
(O/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'partitions':[{k:r[k] for k in ('new_group','retained_old_discrete_keys','bounds','named_refs')} for r in stats],'mask_coverage':coverage,'cuts':[{'zone':r['old_zone'],'layer':r['layer'],'clearance':r['native_clearance'],'removed':r['removed_mm2'],'mask_removed':r['mask_removed_mm2'],'causes':r['new_owned_causes']} for r in cuts],'receipt_sha256':sha(O/'receipt.json')},indent=1),flush=True)
