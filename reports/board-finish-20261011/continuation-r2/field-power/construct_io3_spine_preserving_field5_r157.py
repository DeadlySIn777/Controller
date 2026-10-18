"""Preserve a concrete existing IO3 corridor while rebuilding owned FIELD5."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_declared_settings_projection_r58 as P
BASE=H/'field5-IO3-spine-preserving-search-base-r157'
assert not BASE.exists();BASE.mkdir()
r142=H/'paired-regional-six-regulated-full-contact-audit-r142';old=pickle.loads((r142/'ROOT_R22-regional-groups.pkl').read_bytes())['/IO_3V3'];new=pickle.loads((r142/'REG_R130-regional-groups.pkl').read_bytes())['/IO_3V3'];A=unary_union([q['shape'] for q in old[0] if q['kind']=='fill' and q['layer']=='In2.Cu']);start=unary_union([q['shape'] for q in new[5] if q['layer']=='In2.Cu']);end=unary_union([q['shape'] for q in new[0] if q['layer']=='In2.Cu']);aa,bb=nearest_points(start,end);answer=None
for width in (.3,.25,.2):
 free=A.buffer(-width/2-.00002)
 parts=[free] if free.geom_type=='Polygon' else [q for q in getattr(free,'geoms',[]) if q.geom_type=='Polygon']
 for part in sorted(parts,key=lambda q:-q.area):
  a=part.intersection(start);b=part.intersection(end)
  if a.is_empty or b.is_empty:continue
  pa,pb=nearest_points(a,b);line=LineString([pa,pb]);body=P.bounded_buffer(line,width/2)
  if not A.covers(body):
   try:points,search=T.route(part,tuple(pa.coords[0]),tuple(pb.coords[0]))
   except (AssertionError,ValueError):continue
   line=LineString([[round(x,6),round(y,6)] for x,y in points]);body=P.bounded_buffer(line,width/2)
  if A.covers(body) and body.intersection(start).area>1e-8 and body.intersection(end).area>1e-8:answer=(line,body,width);break
 if answer:break
assert answer is not None
line,body,width=answer;(BASE/'exact-old-IO3-retained-spine-mask.wkb').write_bytes(body.wkb)
g,h,b,z,candidate=pickle.loads((H/'field5-alternate-search-base-r149/model.pkl').read_bytes());b=copy.deepcopy(b);b['field_regulated_search_hard_nominees']['planes'] += [{'uuid':'EXACT_OLD_IO3_RETAINED_SPINE_MASK_R157','net':'/IO_3V3','layer':'In2.Cu','shape':body,'clearance_mm':.15}];(BASE/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,candidate),protocol=5));(BASE/'receipt.json').write_text(json.dumps({'verdict':'SEARCH_ONLY_ORIGINAL_IO3_CONDUCTOR_PRESERVATION_MASK','model_sha256':sha(BASE/'model.pkl'),'R142_receipt_sha256':sha(r142/'receipt.json'),'mask_sha256':sha(BASE/'exact-old-IO3-retained-spine-mask.wkb'),'mask_bounds_mm':list(body.bounds),'mask_points_mm':list(line.coords),'length_mm':line.length,'physical_width_mm':width,'complete_body_literal_original_source_IO3_fill_coverage':True,'actual_new_IO3_Cu_added':False,'this_mask_is_a_hard_retained_Cu_constraint_not_new_zone_credit':True},indent=1)+'\n',encoding='utf-8');print('R157 retained IO3 mask',list(body.bounds),line.length,width,flush=True)
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'field5-IO3-spine-preserving-alternate-r157';BASE=HERE/'field5-IO3-spine-preserving-search-base-r157'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']", "INNER=['In2.Cu']")
s=s.replace("for bank,net,ref,pin,policy in PORTS:", "for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='FIELD5']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11071','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):", "for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):")
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)", "construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
oldloop="for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):"
assert s.count(oldloop)==1;s=s.replace(oldloop,'for a in []: # existing plated contacts only')
s=s.replace('controller-regulated-r76/','controller-IO3-spine-preserving-field5-r157/')
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
