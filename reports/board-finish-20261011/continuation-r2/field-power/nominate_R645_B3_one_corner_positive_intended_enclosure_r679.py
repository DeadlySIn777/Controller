"""One owned intended corner nomination; no physical/model/native mutation."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,itertools,copy
from pathlib import Path
from fractions import Fraction
from shapely.geometry import Polygon,MultiPolygon
from shapely import set_precision
H=Path(__file__).resolve().parent
P=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/only-four-current-member-to-qualified-direction-union-operation-candidates.pkl'
OUT=H/'R645-B3-one-native-IU-positive-intended-corner-enclosure-nomination-r679'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def coords(s):return [([[int(round(x*1e6)),int(round(y*1e6))]for x,y in p.exterior.coords],[[[int(round(x*1e6)),int(round(y*1e6))]for x,y in r.coords]for r in p.interiors])for p in(s.geoms if s.geom_type=='MultiPolygon'else[s])]
def cross(a,b,c):return(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
assert not OUT.exists();OUT.mkdir();assert sha(P)=='6fa00a4fa7f7cce7025d7574b28a6f2b26e7820d63b124df6bdcdaa1f974b766';old=pickle.loads(P.read_bytes())[1]['new_q'];assert old['uuid']=='f595cb04-2945-5e6a-9b86-f7c7c6e1b0c1';intent=zero(old['zone_outline_shape']);physical=zero(old['shape']);assert not physical.difference(intent).is_empty
tokens=coords(intent);loc=[]
for pi,(outer,holes)in enumerate(tokens):
 for ri,ring in enumerate([outer,*holes]):
  for vi,xy in enumerate(ring[:-1]):
   if xy==[85304972,125334335]:loc.append((pi,ri,vi))
assert len(loc)==1;pi,ri,vi=loc[0];ring=[tokens[pi][0],*tokens[pi][1]][ri];prev=ring[vi-1];vertex=ring[vi];nxt=ring[vi+1];orientation=sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(ring,ring[1:]));assert orientation!=0;material_inside_side=(1 if orientation>0 else-1)*(1 if ri==0 else-1);attempts=[];accepted=[]
for dx,dy in itertools.product((-1,0,1),repeat=2):
 if not(dx or dy):continue
 at=[vertex[0]+dx,vertex[1]+dy];newtokens=copy.deepcopy(tokens);rr=[newtokens[pi][0],*newtokens[pi][1]][ri];rr[vi]=at
 if vi==0:rr[-1]=list(at)
 pp=[Polygon([(x/1e6,y/1e6)for x,y in outer],[[(x/1e6,y/1e6)for x,y in r]for r in holes])for outer,holes in newtokens];candidate=pp[0]if len(pp)==1 else MultiPolygon(pp)
 if not candidate.is_valid:attempts.append({'dx_IU':dx,'dy_IU':dy,'valid':False});continue
 lost=intent.difference(candidate);excess=physical.difference(candidate);gain=candidate.difference(intent);side_in=material_inside_side*cross(prev,vertex,at);side_out=material_inside_side*cross(vertex,nxt,at);row={'dx_IU':dx,'dy_IU':dy,'valid':True,'literal_old_intended_NOT_retained':ds(lost),'literal_physical_outside_candidate':ds(excess),'explicit_positive_intended_geometry':ds(gain),'exact_integer_incoming_outward_halfplane_product':side_in,'exact_integer_outgoing_outward_halfplane_product':side_out,'two_controlling_halfplanes_outward_or_tangent':side_in<=0 and side_out<=0};attempts.append(row)
 if lost.is_empty and excess.is_empty and not gain.is_empty and row['two_controlling_halfplanes_outward_or_tangent']:
  tag=set_precision(candidate,1e-6,mode='pointwise');assert tag.wkb==candidate.wkb;new={**old,'zone_outline_shape':tag};assert new['shape'].wkb==old['shape'].wkb;accepted.append((new,newtokens,row,gain))
put(OUT/'all-eight-one-IU-corner-choices-and-literal-halfplane-ledgers.json',attempts);assert accepted,('no minimal positive candidate',attempts);new,newtokens,row,gain=min(accepted,key=lambda x:x[2]['explicit_positive_intended_geometry']['area_mm2']);diff=[(p,r,v,a,b)for p,((outer,holes),(nouter,nholes))in enumerate(zip(tokens,newtokens))for r,(aa,bb)in enumerate(zip([outer,*holes],[nouter,*nholes]))for v,(a,b)in enumerate(zip(aa,bb))if a!=b];assert len(diff)==1,(diff,pi,ri,vi);f=OUT/'only-one-owned-B3-intended-corner-positive-proposal-NOT_MODEL.pkl';f.write_bytes(pickle.dumps({'exact_before_q':old,'exact_after_q_NOT_ADOPTED':new,'all_other_vertex_tokens_exact':True,'only_changed_native_IU_vertex':diff,'explicit_added_intended_geometry':gain,'actual_physical_role_UNCHANGED':True,'actual_current_filled_arrays_NOT_TOUCHED':True},protocol=5));(OUT/'explicit-positive-intended-added-Cu-native-effect-OPEN.wkb').write_bytes(gain.wkb)
put(OUT/'receipt.json',{'status':'ONE_IU_POSITIVE_INTENDED_CORNER_ENCLOSURE_NOMINEE_PHYSICAL_ROLE_UNCHANGED_ALL_GUARDS_NATIVE_OPEN','parent_sparse_packet_SHA256':sha(P),'raw_R655_R677_inherited_enclosure_FAIL_preserved':True,'owner_UUID':old['uuid'],'raw_net':old['net'],'layer':old['layer'],'intended_before_SHA256':hs(intent),'intended_proposed_SHA256':hs(new['zone_outline_shape']),'physical_before_after_identical_SHA256':hs(physical),'changed_vertex_native_IU':diff,'all_other_actual_native_vertex_tokens_exact':True,'exact_incoming_and_outgoing_halfplane_proof':row,'explicit_positive_intended_copper_NOT_a_waiver':ds(gain),'literal_original_intended_loss_EMPTY':True,'literal_physical_outside_intended_candidate_EMPTY':True,'nominee_packet_SHA256':sha(f),'actual_current_fill_source_body_oldcontacts_rules_PROFILES_UNTOUCHED':True,'true_foreign_Cu_guard_source_REFERENCE_native_current_loop_thermal':'OPEN; only a nomination, no native or fullmodel authority','native_jobs':0,'model_written':False,'adopted':False});print('R679_COMPLETE',sha(OUT/'receipt.json'),'added',gain.area,'delta',[row['dx_IU'],row['dy_IU']],flush=True)
