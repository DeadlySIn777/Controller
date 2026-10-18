"""Explicit owned positive corners; restore only prior exact owned member fills."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time,copy,re,traceback
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import restore_field_current_mixed_precision_states_r366 as MS
M=H/'R543-four-unions-bound-exact-line-owned-scopes-r631/model.pkl'
R=H/'R543-two-ground-union-explicit-outward-corner-addition-nominees-r639'
O=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r641'
D=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 x=set_precision(s,0);assert x.wkb==s.wkb;return x
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(name,s):
 f=O/(name+'.wkb');f.write_bytes(s.wkb);return {'file':str(f),'file_SHA256':sha(f),**ds(s)}
def main():
 assert not O.exists();O.mkdir();st=time.monotonic();assert sha(M)=='8dacfdb44f609ecbd3fcfb9280aac624eca7d03e3bf6d50ada3dbe3ac230887a';assert sha(R/'receipt.json')=='378d700d88e78f0fb63e2d98c3ae5e03a962778e6a7a407cdf09f6e98b30e765'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);beforeq={a['uuid']:a for a in q};beforez={a['uuid']:a for a in c['zones']};plans=pickle.loads((R/'only-four-exact-member-raw-integer-union-candidates-NOT_MODEL.pkl').read_bytes());fp=M.parent/'only-four-current-member-to-inward-union-and-local-current-record-operations.pkl';assert sha(fp)=='64d4ab1f883da3becc6b23fb5e23121b6b5ae68563549578f41d833f78952822';prior=pickle.loads(fp.read_bytes());changed={};cz={};rows=[];ops=[];fullops=copy.deepcopy(prior)
 for i in (2,3):
  pl=plans[i];p=prior[i];uid=p['new_q']['uuid'];old=beforeq[uid];assert old==p['new_q'];new=copy.deepcopy(old);roleproof=[]
  for role in ('shape','zone_outline_shape'):
   candidate=zero(pl['raw_integer_proposed_q_NOT_ADOPTED'][role]);literal=unary_union([zero(a[role])for a in p['exact_before_q']]);gain=candidate.difference(literal);loss=literal.difference(candidate);assert loss.is_empty,('literal old owned copper lost',i,role,ds(loss));added=candidate.difference(zero(old[role]));assert not added.is_empty
   tag=set_precision(candidate,1e-6,mode='pointwise');assert tag.wkb==candidate.wkb;new[role]=tag
   roleproof.append({'role':role,'failed_R631_before_SHA256':hs(old[role]),'exact_R543_member_union_SHA256':hs(literal),'new_SHA256':hs(candidate),'explicit_added_Cu_over_R543':save(f'cluster-{i}-{role}-declared-positive-wedges',gain),'explicit_added_Cu_over_failed_R631':save(f'cluster-{i}-{role}-restored-previous-negative-plus-new-corners',added),'old_literal_R543_union_loss_EMPTY':True,'only_new_intersection_vertices_relocated':True,'exact_outward_Fraction_ledger_file':str(R/f'cluster-{i}-{role}-exact-new-intersection-inward-ledger.json'),'exact_outward_Fraction_ledger_SHA256':sha(R/f'cluster-{i}-{role}-exact-new-intersection-inward-ledger.json')})
  ly=new['layer'];oldzone=beforez[uid];newzone=copy.deepcopy(oldzone);records=[];recordproof=[]
  for op in p['actual_current_record_operations']:
   records+=copy.deepcopy(op['before_records']);recordproof.append({'member_UUID':op['old_UUID'],'exact_R631_after_records':op['after_records'],'exact_reversible_R543_before_records':op['before_records'],'restoring_only_own_R631_integer_wedge_withdrawals':True,'no_new_added_corner_fill_credit':True})
  assert oldzone['fills'][ly]==[record for op in p['actual_current_record_operations']for record in op['after_records']];newzone['fills']={ly:records};changed[uid]=new;cz[uid]=newzone
  ops.append({'UUID':uid,'exact_before_q':old,'exact_after_q':new,'exact_before_actual_zone':oldzone,'exact_after_actual_zone':newzone,'role_proofs':roleproof,'only_old_owned_member_array_restore_operations':recordproof});rows.append({'index':i,'UUID':uid,'raw_net':new['net'],'layer':ly,'role_proofs':roleproof,'all_prior_ground_member_filled_record_tokens_restored_exactly':True,'physical_added_corner_area_NOT_credited_as_filled_native_Cu':True})
  fullops[i]['new_q']=new;fullops[i]['new_actual_zone']=newzone
  for op in fullops[i]['actual_current_record_operations']:op['after_records']=copy.deepcopy(op['before_records']);op['R631_failed_owned_negative_operation_reversed_exactly']=True
 finalq=[changed.get(a['uuid'],a)for a in q];actual={**c,'zones':[cz.get(a['uuid'],a)for a in c['zones']]};assert{k:v for k,v in actual.items()if k!='zones'}=={k:v for k,v in c.items()if k!='zones'}
 for a in finalq:
  if a['uuid']not in changed:assert a==beforeq[a['uuid']]
 for a in actual['zones']:
  if a['uuid']not in changed:assert a==beforez[a['uuid']]
 # Screen ONLY the explicitly new Cu additions; full inherited margins remain separate.
 rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'];checks=[];errors=[]
 for op in ops:
  new=op['exact_after_q'];net=L.norm(new['net']);ly=new['layer'];baseline=unary_union([zero(a['shape'])for a in prior[next(i for i in(2,3)if prior[i]['new_q']['uuid']==new['uuid'])]['exact_before_q']]);gain=zero(new['shape']).difference(baseline);nativegap=lambda foreign:.15 if dom[L.norm(foreign)]==dom[net]else .6
  for j in trees[ly].query(gain.buffer(.85),predicate='intersects'):
   r=rec[ly][int(j)]
   if L.norm(r['net'])==net:continue
   if r['kind']=='via':v=r['source'];distance=Point(v['x'],v['y']).distance(gain)-v['d']/2
   elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];distance=LineString([t['a'],t['b']]).distance(gain)-t['w']/2
   else:distance=zero(r['shape']).distance(gain)
   row={'new_union_UUID':new['uuid'],'kind':'explicit_positive_corner_to_true_'+r['kind'],'foreign_UUID':r['uuid'],'foreign_raw_net':r['net'],'actual_gap_mm':distance,'native_required_mm':nativegap(r['net']),'planner_required_mm':nativegap(r['net'])+.025};checks.append(row)
   if distance<row['planner_required_mm']:errors.append(row)
  for z in actual['zones']:
   if L.norm(z['net'])==net or ly not in z['fills']:continue
   body=unary_union(L.poly(z['fills'][ly]));distance=body.distance(gain)
   if body.is_empty or distance>.85:continue
   required=max(float(z['clearance_mm']),nativegap(z['net']),float(new['clearance_mm']))+.025;row={'new_union_UUID':new['uuid'],'kind':'explicit_positive_corner_to_actual_foreign_fill','foreign_UUID':z['uuid'],'foreign_raw_net':z['net'],'actual_gap_mm':distance,'planner_required_mm':required};checks.append(row)
   if distance<required:errors.append(row)
  for z in finalq:
   if z['layer']!=ly or L.norm(z['net'])==net:continue
   for role in ('shape','zone_outline_shape'):
    distance=zero(z[role]).distance(gain)
    if distance>.85:continue
    required=max(float(z['clearance_mm']),nativegap(z['net']),float(new['clearance_mm']))+.025;row={'new_union_UUID':new['uuid'],'kind':'explicit_positive_corner_to_owned_foreign_'+role,'foreign_UUID':z['uuid'],'foreign_raw_net':z['net'],'actual_gap_mm':distance,'planner_required_mm':required};checks.append(row)
    if distance<required:errors.append(row)
 rules=[]
 for name,cond,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',D.read_text(encoding='utf-8')):
  if 'zone'not in what.split():continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",cond);assert len(names)==1;area=next(a for a in h['rule_areas']if a.get('name')==names[0]);rules.append((name,area,re.findall(r"A.NetName != '([^']+)'",cond)))
 rules.extend((a.get('name',a['uuid']),a,[])for a in h['rule_areas']if a.get('no_zones'));nozone=[]
 for new in changed.values():
  for name,area,exempt in rules:
   if new['layer']not in area['layers']or new['net']in exempt:continue
   ar=unary_union(L.poly(area['outline']))
   for role in ('shape','zone_outline_shape'):
    hit=zero(new[role]).intersection(ar)
    if not hit.is_empty:nozone.append({'UUID':new['uuid'],'role':role,'rule':name,**ds(hit)})
 put(O/'explicit-positive-corner-true-foreign-copper-and-peer-checks.json',checks);put(O/'explicit-positive-corner-guard-errors.json',errors);put(O/'two-ground-whole-role-native-nozone-errors.json',nozone)
 b=copy.deepcopy(b);b['restored_generated_grid_UUIDs']=sorted(a['uuid']for a in finalq);b['generated_precision_state_ledger']=[{'new_generated_UUID':a['uuid'],'role':role,'grid_mm':0 if(a['uuid'],role)in MS.ZERO else1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hs(a[role])}for a in finalq for role in ('shape','zone_outline_shape')];ledger=O/'two-explicit-ground-positive-corner-and-exact-member-fill-restoration-ledger.json';put(ledger,rows);b['owned_ground_positive_corner_repair_r641']={'failed_R631_model_SHA256':sha(M),'failed_R635_receipt_SHA256':sha(H/'four-minimal-owned-unions-actual-all-drill-source-contact-reference-r635/receipt.json'),'ledger_file':str(ledger),'ledger_SHA256':sha(ledger),'explicit_added_Cu_NOT_negative_only':True,'actual_corner_fill_source_credit':False,'full_source_reference_native_current':'OPEN'};MS.restore_bound_field_current_precision_states(b,finalq)
 pk=O/'only-two-owned-ground-positive-corners-and-exact-old-member-filled-array-restoration.pkl';pk.write_bytes(pickle.dumps(ops,protocol=5));allpk=O/'only-four-current-member-to-qualified-direction-union-operation-candidates.pkl';allpk.write_bytes(pickle.dumps(fullops,protocol=5));mp=O/'model.pkl';mp.write_bytes(pickle.dumps((g,h,b,finalq,actual),protocol=5))
 put(O/'receipt.json',{'status':'DECLARED_TWO_GROUND_CORNER_ADDITIONS_GUARD_REPAIR_REQUIRED'if errors or nozone else'DECLARED_TWO_GROUND_CORNER_ADDITIONS_TRUE_GUARD_NOZONE_PASS_SOURCE_REFERENCE_NATIVE_CURRENT_OPEN','parent_failed_R631_model_SHA256':sha(M),'model_SHA256':sha(mp),'sparse_packet_SHA256':sha(pk),'complete_four_cluster_packet_SHA256':sha(allpk),'ledger_SHA256':sha(ledger),'true_new_corner_guard_check_count':len(checks),'true_new_corner_guard_errors':errors,'whole_ground_role_nozone_errors':nozone,'all_other_q_current_arrays_original_native_Cu_FP_holes_outlines_sources_rules_exact':True,'no_fabricated_fill_credit_for_declared_added_corner_Cu':True,'raw_R631_R635_reference_FAILs_AND_inherited_B3_outside_intent_FAIL_kept':True,'full_current_source_reference_native':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R641',sha(O/'receipt.json'),'model',sha(mp),'newGuardErrors',len(errors),'nozone',len(nozone),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'status':'CONSTRUCTOR_FAILURE_NO_QUALIFICATION','traceback':traceback.format_exc()})
  raise
