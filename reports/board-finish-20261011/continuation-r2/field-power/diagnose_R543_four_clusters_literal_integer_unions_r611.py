"""Only current four same-nine-settings clusters; freeze raw union witnesses.

No current filled arrays or native files are edited. The literal roles are
compared with proposed integer unions before any negative repair or model.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,hashlib,time,copy,uuid
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
OUT=H/'R543-four-native-overlap-clusters-literal-integer-union-diagnostic-r611'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 r=set_precision(s,0);assert r.wkb==s.wkb;return r
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 rp=H/'eight-native-overlap-plan-exact-R543-source-head-recensus-r601/receipt.json';assert sha(rp)=='4667e4a3af868d7a3093714187da7292466638682978b04be541ad0980d0dcbb'
 mp=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl';assert sha(mp)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416'
 pk=rp.parent/'only-current-cluster-constituents-and-provisional-unions-NOT_REPLACEMENT.pkl';assert sha(pk)=='2524ab3468f28891793ba30b709dc5cc806bf19a5d91f548ea6326b68b5ed17b'
 packet=pickle.loads(pk.read_bytes());g,h,b,qs,c=pickle.loads(mp.read_bytes());by={q['uuid']:q for q in qs};rows=[];results=[]
 for i,p in enumerate(packet):
  members=p['exact_R543_constituent_q_rows'];uids=[q['uuid']for q in members]
  for q in members:
   current=by[q['uuid']];assert current.keys()==q.keys()
   assert all(current[k].wkb==q[k].wkb if k in('shape','zone_outline_shape')else current[k]==q[k]for k in current)
  q=copy.deepcopy(members[0]);q['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R543-only-overlap-cluster/'+ '|'.join(sorted(uids))));q['label']='Exact current same-settings union '+q['uuid'];q['constituent_proposal_UUIDs']=sorted({uid for a in members for uid in [a['uuid']]+a.get('constituent_proposal_UUIDs',[])})
  role_rows=[]
  for role in ('shape','zone_outline_shape'):
   before=[zero(a[role])for a in members];literal=unary_union(before)
   after=set_precision(literal,1e-6,mode='valid_output');actual=zero(after)
   gain=actual.difference(literal);loss=literal.difference(actual)
   seams=unary_union([a.boundary.intersection(d.boundary)for j,a in enumerate(before)for d in before[j+1:]])
   for name,body in [('literal_before_union',literal),('integer_proposed',actual),('raw_positive_gain',gain),('raw_negative_loss',loss),('exact_member_boundary_crossings',seams)]:
    f=OUT/(f'cluster-{i}-{role}-{name}.wkb');f.write_bytes(body.wkb)
   rr={'role':role,'literal_member_WKBs':{a['uuid']:hs(a[role])for a in members},'actual_before_literal_union':ds(literal),'proposed_integer_union':ds(actual),'literal_raw_gain':ds(gain),'literal_raw_loss':ds(loss),'member_boundary_crossings':ds(seams),'proposed_integer_grid_mm':get_precision(after),'unchanged_current_filled_arrays':True,'no_scope_or_small_area_waiver':True};role_rows.append(rr);q[role]=after
  q.pop('integer_nm_physical_rings',None);q.pop('integer_nm_outline_rings',None)
  results.append({'cluster':p['plan'],'exact_before_members':members,'raw_integer_proposed_q_NOT_ADOPTED':q,'role_rows':role_rows});rows.append({'index':i,'members':uids,'raw_net':q['net'],'layer':q['layer'],'roles':role_rows,'all_nine_setting_authority':p['plan']['nine_setting_owner_authority']})
 outpk=OUT/'only-four-exact-member-raw-integer-union-candidates-NOT_MODEL.pkl';outpk.write_bytes(pickle.dumps(results,protocol=5));put(OUT/'four-cluster-literal-role-deltas.json',rows)
 failed=any(not rr['literal_raw_gain']['empty']or not rr['literal_raw_loss']['empty']for row in rows for rr in row['roles'])
 put(OUT/'receipt.json',{'status':'RAW_INTEGER_UNION_ROLE_DIFFERENCES_REPAIR_REQUIRED_NO_MODEL'if failed else'FOUR_INTEGER_UNIONS_LITERAL_ROLE_COPPER_IDENTICAL_CURRENT_CONTACT_PROOF_OPEN','R543_before_model_SHA256':sha(mp),'R601_exact_plan_SHA256':sha(rp),'packet_SHA256':sha(outpk),'clusters':rows,'all_actual_filled_native_discrete_source_rules_FP_original_outlines_UNCHANGED':True,'raw_eight_native_overlap_errors_preserved':True,'R543_reference_current_loop_native_failures_preserved':True,'native_jobs':0,'model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R611',sha(OUT/'receipt.json'),'rawdifference',failed,flush=True)
if __name__=='__main__':main()
