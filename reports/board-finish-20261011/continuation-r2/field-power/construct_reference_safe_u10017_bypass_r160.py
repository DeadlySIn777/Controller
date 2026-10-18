"""Rebuild only the protected source bypass around exact retained references."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,pickle,json
from pathlib import Path
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;BASE=H/'u10017-reference-safe-bypass-search-base-r160';assert not BASE.exists();BASE.mkdir();parent=H/'u10017-coupled-vdd-strong-source-bypass-base-r154';g,h,b,z,c=pickle.loads((parent/'model.pkl').read_bytes());b=copy.deepcopy(b);maskpath=H/'regulated-indexed-reference-wall-repair-base-r123/reference-masks.pkl';masks=pickle.loads(maskpath.read_bytes());rows=[]
for (net,layer),shape in masks.items():
 clear=max([float(q['clearance_mm']) for q in h['zones'] if C.norm(q['net'])==net and layer in q['fills']]+[.15]);rows.append({'uuid':'RETAINED_OLD_SOURCE_REFERENCE_'+net+'_'+layer,'net':net,'layer':layer,'shape':shape,'clearance_mm':clear})
b['field_regulated_search_hard_nominees']['planes']+=rows;(BASE/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));(BASE/'receipt.json').write_text(json.dumps({'model_sha256':sha(BASE/'model.pkl'),'parent_sha256':sha(parent/'model.pkl'),'required_old_reference_masks_sha256':sha(maskpath),'mask_rows':[{'net':q['net'],'layer':q['layer'],'native_clearance_mm':q['clearance_mm']} for q in rows],'scope':'CONSTRUCTION_ONLY_OLD_REFERENCE_HARD_REROUTE_NO_PRIOR_FAIL_WAIVER'},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'u10017-reference-safe-source-bypass-nominee-r160';BASE=HERE/'u10017-reference-safe-bypass-search-base-r160'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']", "INNER=['In2.Cu','In3.Cu','In1.Cu','In4.Cu']")
s=s.replace("for bank,net,ref,pin,policy in PORTS:", "for bank,net,ref,pin,policy in [('FBVS','/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17',2.003)]:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and q.get('ref')=='U10017' for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):", "for margin in(8.,25.,60.):\n    for width in(1.,.75):")
s=s.replace('for d0,h0 in((.6,.3),(.5,.2)):', 'for d0,h0 in((.8,.4),(.6,.3)):')
s=s.replace('for width in(.25,.2):', 'for width in(.3,.25):')
s=s.replace('controller-regulated-r76/', 'controller-u10017-reference-safe-bypass-r160/')
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)", "construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
