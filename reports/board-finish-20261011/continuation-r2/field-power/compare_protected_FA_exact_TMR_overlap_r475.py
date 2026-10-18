"""Supplement current/R9 native-rule witness; no geometry or native changes."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
from inventory import sha
O=H/'R155-R9-protected-FA-native-TMR-exact-overlap-comparison-r475';O.mkdir(exist_ok=False)
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';OLD=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl'
_,h,b,q,c=pickle.loads(M.read_bytes());_,_,_,pq,_=pickle.loads(OLD.read_bytes());ar=next(a for a in h['rule_areas']if a.get('name')=='TMR4WI_KEEPOUT_U14619');area=unary_union(L.poly(ar['outline']));cur=next(x for x in q if x['uuid'].startswith('7ef3cb5e'));prior=next(x for x in pq if x['uuid']==cur['uuid']);rows={}
def dg(sh):return hashlib.sha256(sh.wkb).hexdigest()
def ds(sh):return {'empty':sh.is_empty,'type':sh.geom_type,'area_mm2':sh.area,'length_mm':sh.length,'bounds_mm':None if sh.is_empty else list(sh.bounds),'WKB_sha256':dg(sh)}
for role in ('shape','zone_outline_shape'):
 a=prior[role].intersection(area);z=cur[role].intersection(area);f=O/(role+'-R9-literal-overlap.wkb');f.write_bytes(a.wkb);nf=O/(role+'-R155-literal-overlap.wkb');nf.write_bytes(z.wkb);rows[role]={'old_R9':ds(a),'current_R155':ds(z),'exact_WKB_same':a.wkb==z.wkb,'old_minus_current':ds(a.difference(z)),'current_minus_old':ds(z.difference(a)),'old_full_role_sha256':dg(prior[role]),'current_full_role_sha256':dg(cur[role]),'old_file':str(f.resolve()),'current_file':str(nf.resolve())}
r={'status':'R9_AND_CURRENT_PROTECTED_FA_ACTUAL_RULE_AREA_OVERLAP_FAIL_PRESERVED','current_model_sha256':sha(M),'R9_host_model_sha256':sha(OLD),'raw_net':cur['net'],'UUID':cur['uuid'],'native_rule_area_name':ar['name'],'native_area_record':ar,'area_WKB_sha256':dg(area),'roles':rows,'native_DRC_item_position_not_assumed_local_violation_coordinate':True,'no_model_geometry_coordinate_or_rule_change':True,'native_jobs':0,'adopted':False};(O/'receipt.json').write_text(json.dumps(r,indent=1),encoding='utf-8');print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'roles':rows}),flush=True)
