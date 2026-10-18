"""Independently bind actual native zone-disallow rule on current FA body."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,re,time,hashlib
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
R9=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl'
D9=H.parent/'SAFE-exploratory-native-trial-r9/measure/copy/board.kicad_dru'
D155=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
DRC=H.parent/'R9-failed-flash-native-DRC-diagnostic-r113/drc.json'
O=H/'R155-protected-FA-TMR4WI-U14619-native-rule-attribution-r473'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
def rule(path):
 raw=path.read_text(encoding='utf-8');m=re.search(r'\(rule "P1v2 TMR4WI U14619 keepout: no unrelated copper under converter"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow track via zone\)\)',raw);assert m,path
 return m.group(0),m.group(1)
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 _,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);uid='7ef3cb5e-2f4f-5533-8b6b-1734bc6c6348'
 # Resolve the frozen full UUID from its uniquely named prefix.
 matches=[x for x in q if x['uuid'].startswith('7ef3cb5e')];assert len(matches)==1;x=matches[0];uid=x['uuid'];ars=[a for a in h['rule_areas']if 'TMR4WI_KEEPOUT_U14619' in str(a)];assert len(ars)==1;area=ars[0];body=unary_union(L.poly(area['outline']));assert x['layer']in area['layers']
 oldrule,cond=rule(D9);newrule,newcond=rule(D155);assert oldrule==newrule
 exemptions=re.findall(r"A.NetName != '([^']*)'",cond);actual=x['net'];assert actual not in exemptions
 hits={}
 for role in ('shape','zone_outline_shape'):
  hit=x[role].intersection(body);f=O/(uid+'-'+role+'-actual-rule-area-intersection.wkb');f.write_bytes(hit.wkb);hits[role]={**ds(hit),'witness_file':str(f.resolve()),'witness_file_sha256':sha(f),'native_error_point_distance_mm':x[role].distance(Point(213.146113,49.93998))}
 _,_,_,oldq,_=pickle.loads(R9.read_bytes());old=next(y for y in oldq if y['uuid']==uid);same={r:old[r].wkb==x[r].wkb for r in('shape','zone_outline_shape')}
 error=next(e for e in json.loads(DRC.read_text(encoding='utf-8'))['violations']if e['type']=='items_not_allowed');put(O/'exact-native-rule.txt',oldrule)
 result={'status':'CURRENT_FA_NATIVE_TMR4WI_KEEP_OUT_VIOLATION_REPAIR_REQUIRED'if any(not v['empty']for v in hits.values())else'NO_CURRENT_BODY_OUTLINE_INTERSECTION_WITH_EXACT_NATIVE_KEEP_OUT','current_R155_model_sha256':sha(M),'R9_host_SAFE_model_sha256':sha(R9),'UUID':uid,'raw_net':actual,'layer':x['layer'],'R9_current_exact_role_WKB_equality':same,'native_rule_file_R9':str(D9.resolve()),'native_rule_file_current':str(D155.resolve()),'exact_same_native_rule_bytes':oldrule==newrule,'native_rule_condition':cond,'native_rule_constraint':'disallow track via zone','native_raw_net_exemptions':exemptions,'zone_has_no_memberOfFootprint_exemption':True,'rule_applies_to_current_raw_net':True,'native_rule_area_record':area,'role_intersections':hits,'R113_exact_native_error':error,'R113_drc_sha256':sha(DRC),'outline_and_physical_both_checked':True,'no_current_geometry_or_rule_change':True,'no_native_job_or_adoption':True,'elapsed_seconds':time.monotonic()-start};put(O/'receipt.json',result);print(json.dumps({'status':result['status'],'receipt_sha256':sha(O/'receipt.json'),'same':same,'hits':hits}),flush=True)
if __name__=='__main__':main()
