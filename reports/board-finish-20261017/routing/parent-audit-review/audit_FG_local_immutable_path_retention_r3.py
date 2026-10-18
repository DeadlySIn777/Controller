"""Prove retained FG contacts via an existing cut-free path, never projected fills.

The only geometric witness is a line strictly inside immutable cached physical
Cu and the proposed owned intent. It is not new Cu, a route, or native AFTER.
"""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,collections,runpy,gc,math
from pathlib import Path
import numpy as np
from shapely import from_wkb,contains_xy
from shapely.geometry import LineString,Point
from shapely.strtree import STRtree
from shapely.prepared import prep
from scipy.spatial import cKDTree
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;X=runpy.run_path(str(H/'classify_literal_R763_witnesses_r2.py'));Q=X['Q'];EX=X['X']
PACK=H/'owned-FG-negative-four-conflicts-intent-only-r4';OUT=H/'FG-local-immutable-path-retention-r3';UID='ff5ffe1e-111b-5951-957a-dfd8894ca90c';NET='/motherboard_motors/FIELD_GND'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 t=time.monotonic();assert not OUT.exists();OUT.mkdir();gf=P/'actual-combined-full-after-all-net-groups.pkl';graphs=pickle.loads(gf.read_bytes());old=graphs[NET];g=next(r for r in old if len(K.keys(r))==808);del graphs;gc.collect();assert len(K.keys(g))==808
 mainfill=next(r for r in g if r['kind']=='fill'and r['uuid']==UID and r['layer']=='In1.Cu'and r['shape'].area>100);source=mainfill['shape'];intentfile=PACK/'guard-600001-after-intended.wkb';intent=from_wkb(intentfile.read_bytes())
 # Replay ONLY immutable cached graph rows. No source model/shape is reconstructed.
 retained=[r for r in g if not(r['kind']=='fill'and r['uuid']==UID)];uf=K.A.S.UF();bylayer=collections.defaultdict(list)
 for r in retained:uf.find(r['key']);bylayer[r['layer']].append(r)
 for layer,rows in bylayer.items():
  tree=STRtree([r['shape']for r in rows])
  for i,r in enumerate(rows):
   for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
    if int(j)>i and r['shape'].distance(rows[int(j)]['shape'])<=.000002:uf.join(r['key'],rows[int(j)]['key'])
 groups=collections.defaultdict(list)
 for r in retained:groups[uf.find(r['key'])].append(r)
 branches=list(groups.values());assert len(branches)==2 and set().union(*(K.keys(r)for r in branches))==K.keys(g)
 contact=[]
 for gi,rows in enumerate(branches):
  candidates=[]
  for r in rows:
   if r['layer']!='In1.Cu'or not source.envelope.intersects(r['shape'].envelope):continue
   overlap=source.intersection(r['shape'])
   for part in K.RF.parts(overlap):
    if part.geom_type!='Polygon'or part.area<=0:continue
    q=part.representative_point()
    if source.contains(q)and intent.contains(q)and r['shape'].contains(q):candidates.append({'point':(q.x,q.y),'row':r,'overlap_area':part.area})
  assert candidates,('No finite current contact inside retained intent',gi);contact.append(candidates)
 put('immutable-branch-census.json',{'old_retained_layer_keys':808,'unchanged_cached_record_count':len(retained),'branches':[{'keys':len(K.keys(rs)),'records':len(rs),'finite_contact_candidates':len(cs),'key_inventory':[list(k)for k in sorted(K.keys(rs))]}for rs,cs in zip(branches,contact)],'source_piece_WKB_SHA256':hashlib.sha256(source.wkb).hexdigest(),'source_piece_bounds_mm':list(source.bounds),'source_piece_area_mm2':source.area,'scope':'Existing immutable rows and old contact convention2nm; no new edge uses this tolerance'})
 # All boolean erosion/intersection below is SEARCH ONLY. It is never a fill,
 # graph authority or replacement geometry; every final segment is exact-checked.
 support=source.intersection(intent);candidates=[]
 for a in contact[0]:
  for b in contact[1]:candidates.append((math.dist(a['point'],b['point']),a,b))
 candidates.sort(key=lambda r:r[0]);chosen=None;path=None
 for dist,a,b in candidates[:128]:
  line=LineString([a['point'],b['point']])
  if source.contains(line)and intent.contains(line):chosen=(a,b);path=[a['point'],b['point']];break
 if path is None:
  pitch=.05;margin=.045;safe=support.buffer(-margin);x0,y0,x1,y1=support.bounds
  nx=math.ceil((x1-x0)/pitch)+1;ny=math.ceil((y1-y0)/pitch)+1;xs=x0+np.arange(nx)*pitch;ys=y0+np.arange(ny)*pitch
  xx,yy=np.meshgrid(xs,ys);free=contains_xy(safe,xx,yy).ravel();ids=np.flatnonzero(free);assert len(ids)>0;points=np.column_stack((xx.ravel()[ids],yy.ravel()[ids]));tree=cKDTree(points);del xx,yy
  endpoints=[]
  for cs in contact:
   options={}
   for c in cs:
    distance,near=tree.query(c['point'],k=min(32,len(ids)))
    for ni in np.atleast_1d(near):
     ni=int(ni);line=LineString([c['point'],tuple(points[ni])])
     if source.contains(line)and intent.contains(line):options.setdefault(int(ids[ni]),c);break
   assert options,'No interior grid connector to immutable contact';endpoints.append(options)
  prev=np.full(nx*ny,-2,dtype=np.int32);queue=collections.deque(endpoints[0]);targets=set(endpoints[1])
  for i in queue:prev[i]=-1
  found=None
  while queue:
   i=queue.popleft()
   if i in targets:found=i;break
   for j in(i-1 if i%nx else-1,i+1 if i%nx<nx-1 else-1,i-nx,i+nx):
    if 0<=j<len(prev)and free[j]and prev[j]==-2:prev[j]=i;queue.append(j)
  assert found is not None,'No retained current Cu grid path; no graph-retention pass'
  chain=[];i=found
  while i!=-1:chain.append(i);i=int(prev[i])
  chain.reverse();chosen=(endpoints[0][chain[0]],endpoints[1][found]);path=[chosen[0]['point']]+[(float(xs[i%nx]),float(ys[i//nx]))for i in chain]+[chosen[1]['point']]
  # Greedy visibility simplification remains a search; exact checks follow.
  simplified=[path[0]];i=0
  while i<len(path)-1:
   j=min(len(path)-1,i+1000)
   while j>i+1:
    line=LineString([path[i],path[j]])
    if source.contains(line)and intent.contains(line):break
    j-=1
   simplified.append(path[j]);i=j
  path=simplified
 put('search-path-proposal.json',{'points_mm':path,'endpoint_keys':[list(c['row']['key'])for c in chosen],'source_piece_immutable_WKB_SHA256':hashlib.sha256(source.wkb).hexdigest(),'all_search_booleans_not_actual_or_accepted_geometry':True})
 # Exhaustive literal Fraction path split; strict INTERIOR at all endpoints,
 # boundary breakpoints and every open interval midpoint proves a finite-width
 # existing current Cu path, without silently cutting any remote source region.
 rawpolys={'immutable_current_physical_piece':EX.read_polys(source),'owned_negative_intent_after':EX.read_polys(intent)};prepared={k:X['prepare'](v)for k,v in rawpolys.items()};cert=[]
 for i,(aa,bb)in enumerate(zip(path,path[1:])):
  a=EX.point(aa);b=EX.point(bb)
  if a==b:continue
  ts=EX.split_parameters(a,b,rawpolys);checks=[]
  for q in ts+[(q+r)/2 for q,r in zip(ts,ts[1:])if q!=r]:
   point=EX.along(a,b,q);loc={k:X['location'](point,p)for k,p in prepared.items()};assert all(v=='INTERIOR'for v in loc.values()),('Exact retained path failed',i,str(q),loc)
   checks.append({'parameter':str(q),'point_exact_mm':[str(v)for v in point],'locations':loc})
  cert.append({'segment':i,'a_exact_mm':[str(v)for v in a],'b_exact_mm':[str(v)for v in b],'checks':checks})
 endpointproof=[]
 for c in chosen:
  q=EX.point(c['point']);body=EX.read_polys(c['row']['shape']);loc=EX.location(q,body);assert loc=='INTERIOR';endpointproof.append({'key':list(c['row']['key']),'layer_key':[c['row']['kind'],c['row']['uuid'],c['row']['layer']],'exact_contact_point_mm':[str(v)for v in q],'exact_immutable_contact_body_location':loc,'immutable_contact_body_WKB_SHA256':hashlib.sha256(c['row']['shape'].wkb).hexdigest()})
 put('exact-interior-immutable-Cu-path-and-positive-endpoint-proof.json',{'strict_interior_segments':cert,'positive_contact_endpoints':endpointproof,'interpretation':'Continuous compact interior path gives strictly positive existing Cu support. It does not establish any required current/minwidth or native-after fill.'})
 prior=H/'FG-In1-conservative-whole-record-retention-r1/receipt.json';priorrow=json.loads(prior.read_bytes())['trials'][0];assert not priorrow['old_FIELD_GND_In1_source_layer_key_losses']and not priorrow['old_FIELD_GND_In1_direct_fill_contact_losses']
 put('receipt.json',{'status':'CONDITIONAL_LOCAL_FG808_IMMUTABLE_CURRENT_GRAPH_PATH_RETENTION_PASS_NOT_NATIVE_AFTER_CURRENT_REFERENCE_PASS','old_retained_physical_layer_keys':808,'all808_keys_in_the_two_literal_unchanged_branches':True,'unchanged_cached_graph_branches_joined_by_exact_interior_existing_Cu_path':True,'source_keys_and_old_direct_contacts_already_retained_in_stronger_record_absence_check':True,'source_and_direct_contact_receipt_SHA256':sha(prior),'no_new_Cu_or_owned_ground_cap_or_source_reference_authority':True,'no_modified_projected_fill_or_whole_record_removal_accepted_as_candidate':True,'authority':'Only immutable R299 cached drilled physical rows and exact proposed same-zone intent; witness path is existing Cu support, not an emitted trace or fabricated fill','conditional_scope':'For local removal confined to original current source piece outside the retained after-intent; any real native refill can alter more and must requalify all groups/contacts/references/current','native_CPP_actual_all9source_contacts_all_old_reference_minwidth_IR_thermal_barrel_and_bank_gates':'OPEN_REQUIRED','all_parent_reference_failures_held':True,'native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),gf,intentfile,PACK/'receipt.json',prior,Path(EX.__file__),H/'classify_literal_R763_witnesses_r2.py')},'elapsed_seconds':time.monotonic()-t})
 print('FG_LOCAL_IMMUTABLE_PATH_PASS',len(path),'points',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
