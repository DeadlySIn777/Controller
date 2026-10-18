"""Rebuild only FIELD5's failed owned In2 feed around literal retained IO3 Cu."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,copy
from pathlib import Path
from shapely import from_wkb,set_precision
from inventory import sha
import contact_layout as C
H=Path(__file__).resolve().parent;BASE=H/'field5-exact-IO3-preserving-search-base-r169';assert not BASE.exists();BASE.mkdir()
parent=H/'field5-alternate-search-base-r149';g,h,b,z,c=pickle.loads((parent/'model.pkl').read_bytes());b=copy.deepcopy(b);hard=b['field_regulated_search_hard_nominees'];bindings=[]
mask=H/'exact-original-IO3-preservation-spine-r167/exact-old-IO3-retained-spine-mask.wkb';assert sha(mask)=='b4e5255d1fbabc272aa86981ed162e1b82aa14b9a42ac8bc08494631d309134f';hard['planes'].append({'uuid':'EXACT_OLD_SOURCE_IO3_SPINE_R167','net':'/IO_3V3','layer':'In2.Cu','shape':from_wkb(mask.read_bytes()),'clearance_mm':.15});bindings.append({'file':str(mask.resolve()),'sha256':sha(mask),'scope':'Literal old Cu preservation mask; no new IO3 conductor credit'})
for path,expected in [(H.parent/'logic-two-reference-safe-return-restoration-r42/proposed-zones.pkl','6dade25d3aced12036dcd56ef8bbec590f5bd721ec47bd83435cd3ad2186b114'),(H.parent/'sbc-power/IO3-bounded-owned-CORE-notch-reroute-r164/proposed-replacement-zones.pkl','8422aa284097d54fe99568673318b8563a925d4bf9603f487718f52e67d6a76b'),(H/'u17-u10017-reference-safe-incremental-audit-r162/new-owned-zones.pkl',None)]:
 if expected:assert sha(path)==expected
 hard['planes']+=pickle.loads(path.read_bytes());bindings.append({'file':str(path.resolve()),'sha256':sha(path),'scope':'Later exact hard nomination; no automatic source/contact credit'})
dpath=H/'u17-u10017-reference-safe-incremental-audit-r162/proposed-discrete.pkl';d=pickle.loads(dpath.read_bytes());hard['discrete']['tracks']+=d['tracks'];hard['discrete']['vias']+=d['vias'];bindings.append({'file':str(dpath.resolve()),'sha256':sha(dpath)})
mp=H/'regulated-indexed-reference-wall-repair-base-r123/reference-masks.pkl';masks=pickle.loads(mp.read_bytes())
for (net,layer),shape in masks.items():
 clear=max([float(q['clearance_mm']) for q in h['zones'] if C.norm(q['net'])==net and layer in q['fills']]+[.15]);hard['planes'].append({'uuid':'RETAINED_OLD_SOURCE_REFERENCE_'+net+'_'+layer,'net':net,'layer':layer,'shape':shape,'clearance_mm':clear})
bindings.append({'file':str(mp.resolve()),'sha256':sha(mp),'scope':'All retained old outer source-reference bodies hard'})
# Restore exactly the documented d5 GEOS construction tag; physical WKB is unchanged.
for q in z:
 if q['uuid']=='d5e1a664-0428-5fe4-aaa9-7887f79adfe7':
  before=q['shape'].wkb;q['shape']=set_precision(q['shape'],1e-6,mode='pointwise');assert before==q['shape'].wkb
  if 'zone_outline_shape' in q:q['zone_outline_shape']=set_precision(q['zone_outline_shape'],1e-6,mode='pointwise')
(BASE/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));(BASE/'receipt.json').write_text(json.dumps({'verdict':'SEARCH_ONLY_BAD_8B_WITHDRAWN_ALL_LATER_HARD_AND_LITERAL_IO3_PRESERVED','model_sha256':sha(BASE/'model.pkl'),'parent_model_sha256':sha(parent/'model.pkl'),'hard_bindings':bindings,'restore_ded2_from_ROOT22_is_search_only_original_new_return_then_replay_final_cutters':True,'candidate_old_fills_inherited_SEARCH_ONLY':True},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'field5-exact-IO3-preserving-alternate-r169';BASE=HERE/'field5-exact-IO3-preserving-search-base-r169'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']", "INNER=['In2.Cu']")
s=s.replace('for bank,net,ref,pin,policy in PORTS:', "for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='FIELD5']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11071','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace('for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):', 'for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):')
s=s.replace('native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)', 'construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)')
old="for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):";assert s.count(old)==1;s=s.replace(old,'for a in []: # existing actual source/target barrel contacts only')
s=s.replace('controller-regulated-r76/','controller-field5-exact-IO3-preserving-r169/').replace('.read_text()',".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
