"""Actual selected source gains against the pinned full native foreign fills."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,time
from pathlib import Path
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as R
K=N.K;L=N.L;O=N.O;sha=N.sha
OUT=H/'R275-actual-source-gains-versus-full-before-native-foreign-filled-Cu-r279'
AP=H/'R275-actual-selected-native-five-net-source-body-reference-audit-r278'
BP=H/'R275-actual-R157-fresh-five-net-BEFORE-cache-r277'
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();N.assert_R157_actual_before()
 receipt=json.loads((AP/'receipt.json').read_bytes());af=AP/'actual-five-net-after-model.pkl';ag=AP/'actual-five-net-all-drilled-after-groups.pkl';assert sha(af)==receipt['after_actual_model_SHA256']and sha(ag)==receipt['after_actual_groups_SHA256']
 after=pickle.loads(af.read_bytes());groups=pickle.loads(ag.read_bytes());assert sha(BP/'receipt.json')==receipt['input_SHA256'][str((BP/'receipt.json').resolve())];br=json.loads((BP/'receipt.json').read_bytes());bf=BP/'actual-R157-five-affected-net-groups.pkl';assert sha(bf)==br['groups_SHA256'];old=pickle.loads(bf.read_bytes());native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());ctx=K.hole_context(after);dom=after['domains_normalized']
 by={ly:[]for ly in K.LAYERS}
 for z in native['zones']:
  if z.get('rule_area'):continue
  for ly,rs in z['fills'].items():
   for shape in L.poly(O.polys(rs)):
    if shape.is_empty:continue
    actual=shape.difference(unary_union([ctx[0][int(i)]for i in ctx[1].query(shape,predicate='intersects')]))
    if not actual.is_empty:by[ly].append({'uuid':z['uuid'],'net':L.norm(z['net']),'local_mm':float(z['clearance_mm']),'shape':actual})
 trees={ly:STRtree([r['shape']for r in rows])for ly,rows in by.items()};rows=[];bad=[];deltas=[];coverage=[];owners={z['uuid']:z for z in after['zones']}
 for net,ref,pin in (K.ROOTS[0],K.ROOTS[1],K.ROOTS[5]):
  ar=K.root(groups[net],ref,pin);orr=K.root(old[net],ref,pin)
  for ly in K.LAYERS:
   ab=unary_union([r['shape']for r in ar if r['kind']=='fill'and r['layer']==ly]);ob=unary_union([r['shape']for r in orr if r['kind']=='fill'and r['layer']==ly]);gain=ab.difference(ob);deltas.append({'net':net,'layer':ly,'actual_source_gain':R.shapeinfo(gain)})
   if gain.is_empty:continue
   (OUT/(net.rsplit('/',1)[-1]+'-'+ly+'-actual-source-gain.wkb')).write_bytes(gain.wkb)
   own_shapes={}
   for r in ar:
    if r['kind']=='fill'and r['layer']==ly:own_shapes.setdefault(r['uuid'],[]).append(r['shape'])
   attributed=[]
   for owner_uuid,shapes in own_shapes.items():
    owner_gain=unary_union(shapes).intersection(gain)
    if owner_gain.is_empty:continue
    attributed.append(owner_gain)
    owner_local=float(owners[owner_uuid]['clearance_mm']);query_guard=max([.6,owner_local]+[r['local_mm']for r in by[ly]])
    for i in trees[ly].query(owner_gain.buffer(query_guard+.000001),predicate='intersects'):
     other=by[ly][int(i)]
     if other['net']==net:continue
     required=max(owner_local,other['local_mm'],.15 if dom[net]==dom[other['net']]else .6);assert required<=query_guard;distance=owner_gain.distance(other['shape']);intersection=owner_gain.intersection(other['shape'])
     row={'source_net':net,'layer':ly,'actual_source_owner_zone_UUID':owner_uuid,'actual_source_owner_native_clearance_mm':owner_local,'foreign_native_zone_UUID':other['uuid'],'foreign_net':other['net'],'foreign_original_native_clearance_mm':other['local_mm'],'true_physical_required_mm':required,'bounded_query_guard_mm':query_guard,'actual_SOURCE_gain_to_original_native_foreign_Cu_mm':distance,'literal_foreign_intersection':R.shapeinfo(intersection),'pass':distance>=required and intersection.is_empty};rows.append(row)
     if not row['pass']:
      bad.append(row)
      if not intersection.is_empty:(OUT/(net.rsplit('/',1)[-1]+'-'+ly+'-'+owner_uuid+'-'+other['uuid']+'-gain-foreign-intersection.wkb')).write_bytes(intersection.wkb)
   union=unary_union(attributed);missing=gain.difference(union);excess=union.difference(gain);coverage.append({'net':net,'layer':ly,'literal_unattributed_source_gain':R.shapeinfo(missing),'literal_attributed_gain_outside_aggregate':R.shapeinfo(excess),'zero_area_portions_NOT_waived':True,'pass':missing.is_empty and excess.is_empty})
   if not missing.is_empty:(OUT/(net.rsplit('/',1)[-1]+'-'+ly+'-unattributed-source-gain.wkb')).write_bytes(missing.wkb)
   if not excess.is_empty:(OUT/(net.rsplit('/',1)[-1]+'-'+ly+'-attributed-gain-outside-aggregate.wkb')).write_bytes(excess.wkb)
   put('checkpoint.json',{'net':net,'layer':ly,'checks':len(rows),'failures':len(bad)});print('R279_GAIN',net,ly,'checks',len(rows),'failures',len(bad),flush=True)
 put('all-actual-source-gain-deltas.json',deltas);put('all-original-full-native-foreign-fill-guards.json',rows);put('all-literal-guard-failures.json',bad);put('exact-aggregate-source-gain-owner-coverage.json',coverage);coveragebad=sum(not r['pass']for r in coverage)
 status='R275_ACTUAL_SELECTED_SOURCE_GAIN_NATIVE_FOREIGN_FILL_CONFLICT_OR_OWNER_COVERAGE_HELD'if bad or coveragebad else ('R275_GAIN_GUARDS_SCOPED_PASS_PARENT_SOURCE_CONTACT_REFERENCE_HELD'if any(receipt['counts'].values())else'R275_ACTUAL_SELECTED_SOURCE_GAIN_FULL_BEFORE_FOREIGN_FILL_SCOPED_PASS_CURRENT_OPEN')
 put('receipt.json',{'status':status,'parent_R278_status':receipt['status'],'parent_R278_counts':receipt['counts'],'parent_source_contact_reference_failures_NOT_waived':True,'actual_root_after_receipt_SHA256':sha(AP/'receipt.json'),'actual_full_native_BEFORE_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'actual_after_model_SHA256':sha(af),'actual_after_groups_SHA256':sha(ag),'actual_foreign_filled_Cu_body_count':sum(len(rs)for rs in by.values()),'source_gain_layers':len(deltas),'true_guard_checks':len(rows),'failures':len(bad),'literal_owner_coverage_failures':coveragebad,'all_source_gains_actual_FlashLayer_and_ALL_drill_group_bound':True,'source_gains_not_current_capacity':True,'full_after_foreign_refill_source_preservation':'OPEN_MUST_REFILL_ALL_NETS; original full native foreign bodies retained as hard BEFORE comparison','literal_formula_threshold':0,'same_domain_mm':.15,'cross_domain_mm':.6,'old_native_local_clearance_if_larger_applies':True,'native_DRC_current_SI_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R279_COMPLETE',sha(OUT/'receipt.json'),'failures',len(bad),'owner_coverage',coveragebad,flush=True)
if __name__=='__main__':main()
