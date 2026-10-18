"""Find a no-new-hole FA bridge between existing In3 track interiors.

Actual R299 source-rooted FG floor and all native foreign Cu stay hard; R157 historical coverage remains a separate diagnostic.
No endpoint caps or arbitrary reference exemptions are used.
"""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,runpy,time,math,gc,collections,heapq
from pathlib import Path
import numpy as np
from shapely import from_wkb,contains_xy
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union
from scipy.spatial import cKDTree
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';B=ROOT/'reports/board-finish-20261011/continuation-r2/field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763';STAGE=ROOT/'reports/board-finish-20261017/combined-route-stage-r4';OUT=H/'FA-existing-In3-full-source-component-route-r7';T=runpy.run_path(str(H/'triage_reference_current_causal_geometry_r1.py'));norm=T['norm']
OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;NET='/motherboard_power_entry/FA_SHDN_CONTACT';GROUND='/motherboard_motors/FIELD_GND';ANCHOR_TRACKS=['1f10d7d8-3a00-47cf-8498-260c300495d6','77153d84-aaa7-4785-a9ff-7369bf089759'];CHAIN=ROOT/'reports/board-finish-20261017/power-review/field5-current-continuation/complete-existing-FA-via-to-via-F-chain-r14/receipt.json'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 t=time.monotonic();assert not OUT.exists();OUT.mkdir();mf=P/'actual-combined-full-after-model.pkl';h=pickle.loads(mf.read_bytes());chain=json.loads(CHAIN.read_bytes());assert len(chain['exact_retirement_operations'])==38;retire={r['UUID']if 'UUID'in r else r['uuid']for r in chain['exact_retirement_operations']}
 floors=[];pins={str(f):sha(f)for f in(Path(__file__),mf,CHAIN,STAGE/'all-copper-expected.json')}
 for label,f in(('R157',B/'actual-full-R157-before-all-net-groups.pkl'),('R299',P/'actual-combined-full-after-all-net-groups.pkl')):
  gs=pickle.loads(f.read_bytes());g=K.root(gs[GROUND],'J11003','2');floor=unary_union([r['shape']for r in g if r['kind']=='fill'and r['layer']=='In4.Cu']);floors.append(floor);(OUT/(label+'-actual-source-FG-In4-floor.wkb')).write_bytes(floor.wkb);pins[str(f)]=sha(f);del gs;gc.collect()
 ex=json.loads((STAGE/'all-copper-expected.json').read_bytes())['copper'];tracks=[r for r in h['tracks']if r['uuid']in ex and r['uuid']not in retire];vias=[r for r in h['vias']if r['uuid']in ex];ids={r['uuid']for r in tracks+vias}|retire
 for uid,r in ex.items():
  if uid in ids:continue
  if r['kind']=='segment':tracks.append({'uuid':uid,'net':r['raw_net'],'layer':r['layer'],'a':[v/1e6 for v in r['start_IU']],'b':[v/1e6 for v in r['end_IU']],'w':r['width_IU']/1e6})
  elif r['kind']=='via':vias.append({'uuid':uid,'net':r['raw_net'],'x':r['at_IU'][0]/1e6,'y':r['at_IU'][1]/1e6,'d':max(r['diameters_IU'].values())/1e6,'drill':r['drill_IU']/1e6,'flashed':list(r['diameters_IU'])})
  else:raise AssertionError(('Unhandled new copper',uid,r['kind']))
 h={**h,'tracks':tracks,'vias':vias};npth=json.loads(T['NPTH'].read_bytes());nocu={r['UUID']for r in npth if r['IsNPTHWithNoCopper']and not any(l['CanFlashLayer']or l['FlashLayer']for l in r['layer_observations'])};rec,_=T['build'](h,nocu)
 # Include every otherwise omitted Cu graphic and conservative full-arc disk.
 omitted=[]
 for q in h['shapes']:
  for sh in T['polys'](q['poly']):rec[q['layer']].append({'shape':sh,'kind':'graphic','UUID':q['uuid'],'raw_net':q['net'],'radius':0,'data':q});omitted.append(('graphic',q['uuid'],q['layer'],list(sh.bounds)))
 for q in h['tracks']:
  if not q.get('m'):continue
  sh=L.body(q);rec[q['layer']].append({'shape':sh,'kind':'arc_native_cached_body','UUID':q['uuid'],'raw_net':q['net'],'radius':0,'data':q});omitted.append(('arc',q['uuid'],q['layer'],list(sh.bounds)))
 domain=h['domains_normalized'][NET];req=lambda net:.175 if h['domains_normalized'].get(norm(net))==domain else .625
 region=box(275,136,328,173);barriers=[];ledger=[]
 for r in rec['In3.Cu']:
  if norm(r['raw_net'])==NET or not region.buffer(1).intersects(r['shape']):continue
  clearance=max(req(r['raw_net']),float(r['data'].get('clearance_mm',0))+.025);mesh=.005 if r['kind']in('pad','arc_native_cached_body')else 0
  barriers.append(r['shape'].buffer(r['radius']+.1+clearance+mesh+.0001,quad_segs=64));ledger.append({'UUID':r['UUID'],'kind':r['kind'],'raw_net':r['raw_net'],'guarded_gap_mm':clearance,'pad_or_arc_mesh_bound_mm':mesh})
 holes=[]
 for v in vias:
  if norm(v['net'])!=NET:holes.append((v['uuid'],Point(v['x'],v['y']),v['drill']/2))
 for q in h['pads']:
  if norm(q['net'])!=NET:holes.extend((q['uuid'],sh,0)for sh in T['polys'](q.get('hole')or[]))
 for uid,sh,radius in holes:
  if region.buffer(2).intersects(sh):barriers.append(sh.buffer(radius+.1+.275+.005+.0001,quad_segs=64))
 rules=json.loads(T['RULES'].read_bytes())
 for r in rules:
  if not r['GetDoNotAllowTracks']or'In3.Cu'not in r['layers']:continue
  for poly in r['outlines']:
   sh=Polygon([(x/1e6,y/1e6)for x,y in poly['outer_IU']], [[(x/1e6,y/1e6)for x,y in ring]for ring in poly['holes_IU']])
   if region.intersects(sh):barriers.append(sh.buffer(.1251,quad_segs=64));ledger.append({'UUID':r['UUID'],'kind':'actual109_no_track_rule','name':r['name'],'guarded_gap_mm':.025})
 reservation,exempt=K.A.reservations()
 for r in reservation['keepouts']:
  if NET in exempt.get(r['name'],set())or'In3.Cu'not in r['layers']:continue
  for sh in L.poly(r['outline']):
   if region.intersects(sh):barriers.append(sh.buffer(.1251,quad_segs=64));ledger.append({'kind':'frozen_reserved_area','name':r['name']})
 outline=unary_union(L.poly(h['outline'])).buffer(-.6251);ref=floors[1];free=region.intersection(outline).intersection(ref.buffer(-.1001)).difference(unary_union(barriers));(OUT/'search-only-free-centerline-area.wkb').write_bytes(free.wkb);put('hard-obstacle-ledger.json',ledger);put('complete-arc-and-Cu-graphic-census.json',omitted)
 anchorrows=[];anchorpoints=[]
 for uid in ANCHOR_TRACKS:
  track=next(q for q in tracks if q['uuid']==uid);axis=LineString([track['a'],track['b']]);options=[]
  for i in range(1,40):
   pt=axis.interpolate(i/40,normalized=True);q=(round(pt.x,6),round(pt.y,6))
   if free.contains(Point(q)):options.append(q)
  anchorrows.append({'retained_existing_In3_track':track,'qualified_search_anchor_count':len(options),'points_mm':options});anchorpoints.append(options)
 put('retained-In3-anchor-options.json',anchorrows)
 if not all(anchorpoints):
  put('receipt.json',{'status':'HELD_NO_START_OR_TARGET_ON_COMPLETE_HARD_CU_AND_ACTUAL_R299_SOURCE_FLOOR','anchor_options':anchorrows,'no_own_cap_or_reference_exception_added':True,'all_native_current_reference_gates':'OPEN_REQUIRED','input_SHA256':pins});print('FA_ROUTE_HELD_NO_ANCHOR',flush=True);return
 pitch=.025;nx=2121;ny=1481;xs=275+np.arange(nx)*pitch;ys=136+np.arange(ny)*pitch;xx,yy=np.meshgrid(xs,ys);safe=free.buffer(-.018);mask=contains_xy(safe,xx,yy).ravel();ids=np.flatnonzero(mask);points=np.column_stack((xx.ravel()[ids],yy.ravel()[ids]));tree=cKDTree(points);del xx,yy
 endpoints=[]
 for options in anchorpoints:
  usable={}
  for q in options:
   _,near=tree.query(q,k=min(64,len(ids)))
   for ni in np.atleast_1d(near):
    ni=int(ni)
    if free.contains(LineString([q,tuple(points[ni])])):usable.setdefault(int(ids[ni]),q);break
  endpoints.append(usable)
 assert all(endpoints),'No source-floor/grid connectors'
 prev=np.full(nx*ny,-2,dtype=np.int32);queue=collections.deque(endpoints[0]);targets=set(endpoints[1])
 for i in queue:prev[i]=-1
 found=None
 while queue:
  i=queue.popleft()
  if i in targets:found=i;break
  for j in(i-1 if i%nx else-1,i+1 if i%nx<nx-1 else-1,i-nx,i+nx):
   if 0<=j<len(prev)and mask[j]and prev[j]==-2:prev[j]=i;queue.append(j)
 if found is None:
  put('receipt.json',{'status':'HELD_NO_COMPLETE_HARD_CU_AND_ACTUAL_R299_SOURCE_FLOOR_GRID_PATH','visited_nodes':int(np.count_nonzero(prev!=-2)),'free_grid_nodes':len(ids),'anchor_counts':[len(r)for r in endpoints],'all_native_current_reference_gates':'OPEN_REQUIRED','input_SHA256':pins});print('FA_ROUTE_HELD_DISCONNECTED',flush=True);return
 chain=[];i=found
 while i!=-1:chain.append(i);i=int(prev[i])
 chain.reverse();path=[endpoints[0][chain[0]]]+[(round(float(xs[i%nx]),6),round(float(ys[i//nx]),6))for i in chain]+[endpoints[1][found]];simplified=[path[0]];i=0
 while i<len(path)-1:
  j=min(i+1000,len(path)-1)
  while j>i+1 and not free.contains(LineString([path[i],path[j]])):j-=1
  simplified.append(path[j]);i=j
 path=simplified;axis=LineString(path);(OUT/'proposed-native-IU-polyline-axis.wkb').write_bytes(axis.wkb);put('proposed-native-IU-polyline.json',{'points_mm':path,'new_width_mm':.2,'all_points_exactly_serializable_native_IU':True,'native_vias_or_layer_entries_added':0})
 failures=[];checks=[]
 for i,(a,b)in enumerate(zip(path,path[1:])):
  line=LineString([a,b]);outward=line.buffer(.100002/math.cos(math.pi/(4*512)),quad_segs=512)
  for label,floor in zip(('actual_R157_source_FG','actual_R299_source_FG'),floors):
   loss=outward.difference(floor);checks.append({'segment':i,'kind':label,'source_rooted_full_outward_round_cap_shadow_covered':loss.is_empty,'raw_loss_area_mm2':loss.area})
   if label=='actual_R299_source_FG'and not loss.is_empty:failures.append(checks[-1])
  for r in rec['In3.Cu']:
   if norm(r['raw_net'])==NET or not line.envelope.buffer(1).intersects(r['shape'].envelope):continue
   mesh=.005 if r['kind']in('pad','arc_native_cached_body')else 0;gap=line.distance(r['shape'])-r['radius']-.1-mesh;need=max(req(r['raw_net']),float(r['data'].get('clearance_mm',0))+.025)
   if gap<need:failures.append({'segment':i,'kind':'true_new_trace_to_actual_foreign_'+r['kind'],'UUID':r['UUID'],'gap_mm':gap,'required_mm':need})
 put('full-outward-body-actual-source-floor-and-Cu-checks.json',checks);put('full-outward-body-failures.json',failures)
 put('receipt.json',{'status':'NO_NEW_HOLE_FA_IN3_NATIVE_GRID_ROUTE_HOST_FULL_BODY_REFERENCE_AND_CU_PRECHECK_PASS'if not failures else'HELD_NEW_FA_IN3_ROUTE_HAS_EXPLICIT_GEOMETRY_FAILURES','path_mm':path,'width_mm':.2,'length_mm':axis.length,'new_segments':len(path)-1,'new_vias_or_layer_entries':0,'retained_original_In3_tracks':ANCHOR_TRACKS,'retired_original_F_track_count':38,'actual_R299_named_source_FG_In4_full_new_outward_body_covered':not failures,'own_caps_or_reference_exemptions_added':False,'original_vias_retained_literal_inherited_port_gaps_not_redrawn':True,'all_native_actual_source_partitions_contacts_masks_allbank_oldrefs_newbody_current_IR_minwidth_thermal':'OPEN_REQUIRED','input_SHA256':pins,'elapsed_seconds':time.monotonic()-t,'native_jobs':0,'adopted':False});print('FA_IN3_ROUTE_RESULT',len(path),'points',len(failures),'failures',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
