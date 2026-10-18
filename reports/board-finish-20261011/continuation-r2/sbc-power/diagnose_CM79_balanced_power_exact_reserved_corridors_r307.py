"""Exact frozen/native rule areas on the local full1.25 CORE5 detour."""
import hashlib,json,pickle,sys,time
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-balanced-fullwidth-power-exact-frozen-reservation-authority-r307'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def buf(s,r):a=Z.bounded_buffer(s,r);z=set_precision(a,0);assert z.wkb==a.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');oldbody=buf(LineString([old['a'],old['b']]),.625);reserve,exempt=A.reservations();rows=[]
 for y in(202.705,202.715,202.725):
  axis=LineString([(116.0,y),(120.1,y)]);body=buf(axis,.625);novel=body.difference(oldbody);rr=[]
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if'F.Cu'not in rule['layers']or(not ex and not rule.get('no_tracks')):continue
    allowed=ex and L.norm(old['net'])in exempt.get(rule['name'],set())
    for sh in L.poly(rule['outline']):
     if body.distance(sh)>.02501:continue
     rr.append({'kind':'frozen_reservation'if ex else'native_no_tracks','name':rule.get('name'),'UUID':rule.get('uuid'),'exact_CORE5_existing_exemption':bool(allowed),'declared_exempt_normalized_nets':sorted(exempt.get(rule['name'],set()))if ex else[],'full_new_body_rule_overlap_mm2':body.intersection(sh).area,'true_novel_body_rule_overlap_mm2':novel.intersection(sh).area,'true_novel_body_rule_gap_mm':novel.distance(sh),'rule_shape_bounds_mm':sh.bounds,'full_original_body_rule_overlap_mm2':oldbody.intersection(sh).area,'no_exception_or_threshold_modified':True})
  rows.append({'exact_axis_y_mm':y,'fullwidth_mm':1.25,'rule_rows':rr});put(O/'local-fullwidth-true-novel-rule-authority.json',rows)
 put(O/'receipt.json',{'verdict':'READ_ONLY_EXACT_LOCAL_FULLWIDTH_POWER_FROZEN_RULE_AUTHORITY','R289_failed_diagnostic_model_sha256':sha(mp),'exact_original_power_raw_net':old['net'],'rows':rows,'source_rule_read_hashes':A.READS,'model_native_board_rules_or_geometry_changed':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R307_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
