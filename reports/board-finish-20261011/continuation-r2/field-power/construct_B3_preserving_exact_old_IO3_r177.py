"""Replace only failed owned C5 B3 feed; immutable actual SAFE/REG context."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import from_wkb,set_precision
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent
B=H/'B3-exact-IO3-preserving-search-base-r177';assert not B.exists();B.mkdir()
R=H/'SAFE-regulated-u17-u10017-paired-regional-audit-r171';assert sha(R/'model.pkl')=='01870275e31f88e4fdb5b08a7395c940047f83d2be0649a069c96ba76568e7ef'
g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());c=copy.deepcopy(c);b=copy.deepcopy(b)
failed='c5ba529f-a864-5662-be39-9d5cf864ee62';assert sum(q['uuid']==failed for q in z)==1
z=[q for q in z if q['uuid']!=failed];c['zones']=[q for q in c['zones'] if q['uuid']!=failed]
hard={'planes':[],'discrete':{'vias':[],'tracks':[]}}
bindings=[]
mask=H/'exact-original-IO3-preservation-spine-r167/exact-old-IO3-retained-spine-mask.wkb';assert sha(mask)=='b4e5255d1fbabc272aa86981ed162e1b82aa14b9a42ac8bc08494631d309134f'
hard['planes'].append({'uuid':'EXACT_OLD_SOURCE_IO3_SPINE_R167','net':'/IO_3V3','layer':'In2.Cu','shape':from_wkb(mask.read_bytes()),'clearance_mm':.15})
bindings.append({'file':str(mask.resolve()),'sha256':sha(mask),'scope':'Literal old conductive relationship; no new IO3 continuity credit'})
for path,expected in [(H.parent/'sbc-power/original-IO3-r172-positive-snapshot-4/proposed-zones.pkl','9fbe57d1d4a5d6999e4500ab091480ad7e34afe47a1fa9b35d457c2f165937fd'),(H.parent/'SAFE-logic-four-return-restoration-r55/proposed-zones.pkl','b0e3766d17138741ae1f4ab6d2a574e55da6634734b03bec93d6a6abb891e065')]:
 assert sha(path)==expected;hard['planes']+=pickle.loads(path.read_bytes());bindings.append({'file':str(path.resolve()),'sha256':sha(path),'scope':'Later actual peer proposal hard only'})
mp=H/'regulated-indexed-reference-wall-repair-base-r123/reference-masks.pkl'
for (net,layer),shape in pickle.loads(mp.read_bytes()).items():
 clear=max([float(q['clearance_mm']) for q in h['zones'] if C.norm(q['net'])==net and layer in q['fills']]+[.15]);hard['planes'].append({'uuid':'RETAINED_OLD_SOURCE_REFERENCE_'+net+'_'+layer,'net':net,'layer':layer,'shape':shape,'clearance_mm':clear})
bindings.append({'file':str(mp.resolve()),'sha256':sha(mp),'scope':'Retained old source-ground outer-reference masks'})
# R171 derived all-role state tags are restored without altering coordinates.
for q in z:
 for role in ('shape','zone_outline_shape'):
  raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==raw
b['field_regulated_search_hard_nominees']=hard
(B/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5))
(B/'receipt.json').write_text(json.dumps({'verdict':'SEARCH_ONLY_C5_WITHDRAWN_LATEST_R171_CONTEXT_ALL_PEERS_HARD','model_sha256':sha(B/'model.pkl'),'parent_model_sha256':sha(R/'model.pkl'),'withdrawn_owned_plane_UUID':failed,'hard_bindings':bindings,'all_prior_contacts_sources_references_full76_are_mandatory_after_construction':True,'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'B3-exact-IO3-preserving-alternate-r177';BASE=HERE/'B3-exact-IO3-preserving-search-base-r177'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']","INNER=['In2.Cu','In1.Cu','In4.Cu','In3.Cu']")
s=s.replace('for bank,net,ref,pin,policy in PORTS:',"for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='B3V3']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'","xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('U19008','10') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace('for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):','for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):')
s=s.replace('native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)','construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)')
old="for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):";assert s.count(old)==1;s=s.replace(old,'for a in []: # existing actual target/source barrels only')
s=s.replace('controller-regulated-r76/','controller-B3-exact-old-IO3-r177/').replace('.read_text()',".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
