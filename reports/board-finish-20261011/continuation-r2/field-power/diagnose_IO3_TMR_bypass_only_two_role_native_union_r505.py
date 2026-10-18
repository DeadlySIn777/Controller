"""Literal minimal two-member same-settings union diagnostic; no model."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'));sys.path.insert(0,str(H.parent/'coupled-recovery'))
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'IO3-R14045-new-only-existing-barrel-TMR-materialization-r501/model.pkl'
O=H/'IO3-TMR-bypass-minimal-two-member-native-union-diagnostic-r505'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def summary(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'sha256':dg(s)}
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(M)=='4085476528750a14f77b9d9c78a75c10914522a82932b38991f35241b7c77bd3'
 g,h,b,qs,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,qs);old=next(x for x in qs if x['uuid'].startswith('4f297f78'));add=qs[-1]
 settings=('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm');assert all(old[x]==add[x]for x in settings)
 rows=[];packet={}
 for role in ('shape','zone_outline_shape'):
  a=lit(old[role]);n=lit(add[role]);raw=unary_union([a,n]);canonical=set_precision(raw,1e-6,mode='valid_output')
  retained_loss=a.difference(lit(canonical));additional_loss=n.difference(lit(canonical));extra_gain=lit(canonical).difference(a).difference(n)
  for label,sh in [('raw_union',raw),('native_nm_union',canonical),('old_retained_loss',retained_loss),('new_addition_loss',additional_loss),('gain_outside_authorized_addition',extra_gain)]:(O/(role+'-'+label+'.wkb')).write_bytes(sh.wkb)
  rows.append({'role':role,'old_sha256':dg(a),'new_addition_sha256':dg(n),'raw_union_sha256':dg(raw),'native_nm_union_sha256':dg(canonical),'old_retained_loss':summary(retained_loss),'new_addition_loss':summary(additional_loss),'gain_outside_authorized_addition':summary(extra_gain),'old_loss_EMPTY':retained_loss.is_empty,'gain_outside_addition_EMPTY':extra_gain.is_empty})
  packet[role]=canonical
 (O/'only-two-role-union-candidate.pkl').write_bytes(pickle.dumps(packet,protocol=5))
 (O/'receipt.json').write_text(json.dumps({'status':'LITERAL_MINIMAL_UNION_PROOF_PASS_SOURCE_NATIVE_CURRENT_OPEN'if all(r['old_loss_EMPTY']and r['gain_outside_addition_EMPTY']for r in rows)else'LITERAL_MINIMAL_UNION_REQUIRES_REPAIR_NO_MODEL','model_sha256':sha(M),'only_members':[old['uuid'],add['uuid']],'same_all_nine_settings_exact':True,'rows':rows,'no_model_or_native_export':True,'no_precision_or_remote_change_adopted':True,'elapsed_seconds':time.monotonic()-started},indent=1)+'\n',encoding='utf-8');print('R505 receipt',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
