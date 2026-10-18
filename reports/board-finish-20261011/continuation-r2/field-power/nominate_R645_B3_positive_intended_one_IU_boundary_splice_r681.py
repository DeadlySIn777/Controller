"""Keep every old native vertex; insert the required physical vertex as a positive splice."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,copy
from pathlib import Path
from shapely.geometry import Polygon,MultiPolygon
from shapely import set_precision
H=Path(__file__).resolve().parent
P=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/only-four-current-member-to-qualified-direction-union-operation-candidates.pkl'
OUT=H/'R645-B3-positive-intended-one-native-IU-boundary-splice-nomination-r681'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def coords(s):return [([[int(round(x*1e6)),int(round(y*1e6))]for x,y in p.exterior.coords],[[[int(round(x*1e6)),int(round(y*1e6))]for x,y in r.coords]for r in p.interiors])for p in(s.geoms if s.geom_type=='MultiPolygon'else[s])]
assert not OUT.exists();OUT.mkdir();assert sha(P)=='6fa00a4fa7f7cce7025d7574b28a6f2b26e7820d63b124df6bdcdaa1f974b766'
old=pickle.loads(P.read_bytes())[1]['new_q'];assert old['uuid']=='f595cb04-2945-5e6a-9b86-f7c7c6e1b0c1'
intent=zero(old['zone_outline_shape']);physical=zero(old['shape']);tokens=coords(intent);newtokens=copy.deepcopy(tokens);loc=[]
for pi,(outer,holes)in enumerate(tokens):
 for ri,ring in enumerate([outer,*holes]):
  for vi,xy in enumerate(ring[:-1]):
   if xy==[85304972,125334335]:loc.append((pi,ri,vi))
assert len(loc)==1;pi,ri,vi=loc[0];oldring=[tokens[pi][0],*tokens[pi][1]][ri];rr=[newtokens[pi][0],*newtokens[pi][1]][ri]
inserted=[85304971,125334335];rr.insert(vi+1,inserted)
pp=[Polygon([(x/1e6,y/1e6)for x,y in outer],[[(x/1e6,y/1e6)for x,y in r]for r in holes])for outer,holes in newtokens]
candidate=pp[0]if len(pp)==1 else MultiPolygon(pp);lost=intent.difference(candidate);excess=physical.difference(candidate);gain=candidate.difference(intent)
retained=copy.deepcopy(newtokens);[retained[pi][0],*retained[pi][1]][ri].pop(vi+1);assert retained==tokens
triangle=Polygon([(x/1e6,y/1e6)for x,y in [oldring[vi],inserted,oldring[vi+1]]])
literal_extra_outside_declared_triangle=gain.difference(triangle);literal_missing_declared_triangle=triangle.difference(gain)
tag=set_precision(candidate,1e-6,mode='pointwise');assert tag.wkb==candidate.wkb
for name,s in [('literal_old_intended_loss',lost),('literal_physical_outside_proposed_intent',excess),('explicit_added_intended_triangle',gain),('declared_exact_three_native_vertex_triangle',triangle),('added_outside_declared_triangle',literal_extra_outside_declared_triangle),('triangle_missing_from_added',literal_missing_declared_triangle)]: (OUT/(name+'.wkb')).write_bytes(s.wkb)
status='POSITIVE_NATIVE_INTENDED_SPLICE_NOMINEE_PHYSICAL_UNCHANGED_GUARDS_OPEN'if candidate.is_valid and lost.is_empty and excess.is_empty and not gain.is_empty and literal_extra_outside_declared_triangle.is_empty and literal_missing_declared_triangle.is_empty else 'REJECTED_LITERAL_SPLICE_NOMINEE'
new={**old,'zone_outline_shape':tag};assert new['shape'].wkb==old['shape'].wkb
f=OUT/'only-owned-B3-intended-one-native-IU-positive-splice-NOT_MODEL.pkl';f.write_bytes(pickle.dumps({'exact_before_q':old,'exact_after_q_NOT_ADOPTED':new,'all_old_native_vertex_tokens_retained_exact_order':True,'only_inserted_native_vertex':[pi,ri,vi+1,inserted],'explicit_added_intended_geometry':gain,'declared_exact_triangle':triangle,'actual_physical_role_UNCHANGED':True,'actual_current_filled_arrays_NOT_TOUCHED':True},protocol=5))
put(OUT/'receipt.json',{'status':status,'parent_sparse_packet_SHA256':sha(P),'owner_UUID':old['uuid'],'raw_net':old['net'],'layer':old['layer'],'intended_before_SHA256':hs(intent),'intended_after_proposed_SHA256':hs(candidate),'physical_before_after_identical_SHA256':hs(physical),'all_old_native_vertex_tokens_retained_exact_order':True,'only_inserted_native_vertex':[pi,ri,vi+1,inserted],'old_intended_loss':ds(lost),'physical_outside_proposed_intent':ds(excess),'explicit_positive_intended_addition':ds(gain),'declared_triangle_exact_integer_vertices':[oldring[vi],inserted,oldring[vi+1]],'added_outside_declared_triangle':ds(literal_extra_outside_declared_triangle),'declared_triangle_missing_from_added':ds(literal_missing_declared_triangle),'candidate_valid':candidate.is_valid,'nominee_packet_SHA256':sha(f),'actual_current_physical_fills_header_holes_and_native_original_UNCHANGED':True,'true_foreign_native_guard_profile_intent_interzone_native_source_current_qualification':'OPEN','raw_R655_R677_and_x_only_negative_nominee_preserved':True,'model_written':False,'native_jobs':0,'adopted':False})
print('R681_COMPLETE',status,sha(OUT/'receipt.json'),'gain',gain.area,'lost',lost.area,'excess',excess.area,flush=True)
