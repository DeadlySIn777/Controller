"""Materialize exact R98 primitive additions and conservative actual-fill cuts only."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for folder in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/folder))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import complete_geometry_r2 as G
import restore_SAFE_generated_precision_states_r168 as PS
from audit_field_io3_crossings_r15e import losses
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(sh):return hashlib.sha256(sh.wkb).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref,pin='2'):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)for q in xs))
def named(xs):return{q['uuid']for q in xs if q['kind']=='pad'and q['pin']}
def bounded_remove(before,cutter):
 raw=before.wkb;before=set_precision(before,1e-6,mode='pointwise');assert raw==before.wkb
 after=set_precision(before.difference(cutter),1e-6,mode='pointwise');rounding=[]
 for attempt in range(5):
  gain=after.difference(before)
  if gain.is_empty:break
  local=N.bounded_buffer(gain,.000003);rounding.append({'attempt':attempt,'local_gain_WKB_sha256':digest(gain),'local_gain_mm2':gain.area,'local_only_inward_cut_sha256':digest(local),'reserve_mm':.000003});after=set_precision(after.difference(local),1e-6,mode='pointwise')
 assert after.difference(before).is_empty,'remove-only generated role gained copper after local nm correction'
 assert not after.is_empty
 return after,rounding
def main():
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';mp=parent/'model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';packet=H/'CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert sha(packet/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd';g,h,b,z,before=pickle.loads(mp.read_bytes());replay=PS.restore_bound_generated_precision_states(b,z);route_rows=pickle.loads((packet/'proposed-route-and-zone.pkl').read_bytes());d=pickle.loads((packet/'proposed-discrete.pkl').read_bytes());assert len(route_rows)==1 and len(d['vias'])==2 and not d['tracks'];route=route_rows[0];core=route['zone'];assert core['uuid']=='b0453302-df03-561f-9bc4-0560bc66658a'and core['net']=='/CORE_1V2'and core['layer']=='In2.Cu';assert digest(core['shape'])=='4b5675bccc5a299d38f996843162681d4f227b6c194ae3d65194d4b00a823e74';raw='/CORE_1V2';out=H/'CORE-In2-owned-notch-materialized-source-proposal-r100';assert not out.exists();out.mkdir();put(out/'parent-generated-role-replay.json',replay)
 pins={str(p.resolve()):sha(p)for p in [mp,parent/'receipt.json',packet/'receipt.json',packet/'proposed-route-and-zone.pkl',packet/'proposed-discrete.pkl',Path(PS.__file__),Path(N.__file__),Path(G.__file__)]};assert not{v['uuid']for v in d['vias']}&{v['uuid']for v in h['vias']};new_h=copy.deepcopy(h);new_h['vias']+=copy.deepcopy(d['vias']);qscope={'e2fe644a-2849-5c69-8ebb-d1e94909cd4c','6b1d4fb8-c0e5-531b-acf4-26ef99b34597'};assert qscope<={q['uuid']for q in z};owned=[];rolecuts=[]
 for q in z+[core]:
  result=copy.deepcopy(q);physical_cuts=[];outline_cuts=[]
  if q['uuid']in qscope:
   assert q['layer']=='In2.Cu';clear=max(G.gap(new_h,q['net'],raw),float(q.get('clearance_mm',.15)))+.025+.000100;cut=N.bounded_buffer(core['shape'],clear);physical_cuts.append(cut);outline_cuts.append(cut)
  for via in d['vias']:
   if C.norm(q['net'])==raw:cut=N.bounded_disk(via,via['drill']/2);physical_cuts.append(cut)
   else:
    clear=max(G.gap(new_h,q['net'],raw),float(q.get('clearance_mm',.15)))+.025+.000100;radius=max(via['drill']/2+.275+.000100,via['d']/2+clear);cut=N.bounded_disk(via,radius);physical_cuts.append(cut);outline_cuts.append(cut)
  for role,cuts in [('shape',physical_cuts),('zone_outline_shape',outline_cuts)]:
   previous=result[role];relevant=[cut for cut in cuts if cut.intersects(previous)]
   if not relevant:continue
   cutter=unary_union(relevant);updated,rounding=bounded_remove(previous,cutter)
   if updated.wkb==previous.wkb:continue
   result[role]=updated;rolecuts.append({'UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'role':role,'before_WKB_sha256':digest(previous),'after_WKB_sha256':digest(updated),'removed_mm2':previous.difference(updated).area,'added_mm2':0.,'only_NEW_OWNED_role':True,'only_exact_CORE_pair_antipads_same_net_drills_or_declared_two_In2_notches':True,'local_only_nm_gain_corrections':rounding})
  owned.append(result)
 put(out/'owned-remove-only-role-cuts.json',rolecuts);print('R100_OWNED_REMOVE_ONLY',len(rolecuts),flush=True)
 # Original zone definitions/settings stay exactly h; actual filled copper is
 # the already projected immutable R83 baseline minus only NEW primitives.
 # Shrinking existing owned roles never credits reclaimed native filled Cu.
 oldactual={q['uuid']:q for q in before['zones']};native=[];actualcuts=[];guardrows=[];cutcache={}
 for definition in h['zones']:
  prior=oldactual[definition['uuid']];row=copy.deepcopy(definition);row['fills']={}
  for layer,records in prior['fills'].items():
   baseline=unary_union(C.poly(records));remaining=set_precision(baseline,0);assert remaining.wkb==baseline.wkb;clear=max(G.gap(new_h,definition['net'],raw),float(definition['clearance_mm']))+.025+.000100;cuts=[]
   for via in d['vias']:
    if C.norm(definition['net'])==raw:radius=via['drill']/2;kind='same-net-new-ordinary-drill-void'
    else:radius=max(via['drill']/2+.275+.000100,via['d']/2+clear);kind='new-ordinary-foreign-Cu-and-drill-antipad'
    key=('via',via['uuid'],radius)
    if key not in cutcache:cutcache[key]=N.bounded_disk(via,radius)
    cuts.append((kind,via['uuid'],cutcache[key]))
   if layer==core['layer']and C.norm(definition['net'])!=raw:
    key=('newCOREzone',clear)
    if key not in cutcache:cutcache[key]=N.bounded_buffer(core['shape'],clear)
    cuts.append(('new-CORE-In2-feed-foreign-Cu-antipad',core['uuid'],cutcache[key]))
   for kind,uid,cut in cuts:
    if not cut.intersects(baseline):continue
    cut_zero=set_precision(cut,0);assert cut_zero.wkb==cut.wkb;previous=remaining;remaining=remaining.difference(cut_zero);actualcuts.append({'native_zone_UUID':definition['uuid'],'raw_net':definition['net'],'layer':layer,'only_added_primitive_UUID':uid,'kind':kind,'generated_cut_WKB_sha256':digest(cut),'removed_actual_native_fill_mm2':previous.difference(remaining).area,'native_original_definition_and_existing_guard_cuts_unchanged':True})
   assert remaining.difference(baseline).area<=1e-12,'floating actual-fill subtraction gained copper';row['fills'][layer]=G.records(remaining)
   reconstructed=unary_union(C.poly(row['fills'][layer]));assert reconstructed.equals(remaining),'coordinate record adapter changed actual fill'
   if not remaining.is_empty:
    for via in d['vias']:
     if C.norm(definition['net'])==raw:continue
     actual=remaining.distance(Point(via['x'],via['y']))-via['d']/2;required=clear-.000100;guardrows.append({'native_zone_UUID':definition['uuid'],'layer':layer,'foreign_UUID':via['uuid'],'required_gap_mm':required,'actual_gap_mm':actual,'PASS':actual>=required})
    if layer==core['layer']and C.norm(definition['net'])!=raw:actual=remaining.distance(core['shape']);required=clear-.000100;guardrows.append({'native_zone_UUID':definition['uuid'],'layer':layer,'foreign_UUID':core['uuid'],'required_gap_mm':required,'actual_gap_mm':actual,'PASS':actual>=required})
  native.append(row)
 for q in owned:native.append({'uuid':q['uuid'],'net':q['net'],'priority':int(q.get('priority',124)),'clearance_mm':float(q.get('clearance_mm',.15)),'min_thickness_mm':float(q.get('min_thickness_mm',.15)),'pad_connect_mode':q.get('pad_connect_mode','FULL_SOLID'),'island_removal_mode':int(q.get('island_removal_mode',1)),'thermal_gap_mm':float(q.get('thermal_gap_mm',.15)),'thermal_bridge_width_mm':float(q.get('thermal_bridge_width_mm',.3)),'fills':{q['layer']:G.records(q['shape'])},'prospective_not_native':True})
 current={**new_h,'zones':native};put(out/'only-added-primitives-native-actual-fill-cuts.json',actualcuts);put(out/'actual-native-fill-vs-new-primitive-guards.json',guardrows);guarderrors=[q for q in guardrows if not q['PASS']];put(out/'actual-native-fill-vs-new-primitive-guard-errors.json',guarderrors);print('R100_NATIVE_DELTA',len(actualcuts),len(guardrows),len(guarderrors),flush=True)
 precision=[]
 for q in owned:
  for role in ('shape','zone_outline_shape'):
   value=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==value;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in owned);b['CORE_R100_only_added_ordinary_native_actual_fill_projection']={'baseline_model_sha256':sha(mp),'route_receipt_sha256':sha(packet/'receipt.json'),'old_native_zone_definitions_unchanged':True,'new_ordinary_vias':[v['uuid']for v in d['vias']],'new_owned_CORE_In2_UUID':core['uuid'],'strict_original104_PDN_and_all_raw_failed_reference_ledgers_unchanged':True,'all_full_current_return_source_native_qualification':'OPEN'};(out/'model.pkl').write_bytes(pickle.dumps((g,new_h,b,owned,current),protocol=5));(out/'proposed-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5));(out/'proposed-new-CORE-zone.pkl').write_bytes(pickle.dumps([next(q for q in owned if q['uuid']==core['uuid'])],protocol=5));(out/'owned-role-updates.pkl').write_bytes(pickle.dumps([q for q in owned if q['uuid']in{r['UUID']for r in rolecuts}],protocol=5));put(out/'generated-precision-state-ledger.json',precision)
 head=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(head/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';oldgroups=pickle.loads((head/'groups.pkl').read_bytes());newgroups={};contacts=[]
 for net in ['/CORE_1V2',*sorted(n for n in oldgroups if n!='/CORE_1V2')]:
  now=F.graph(current,net);newgroups[net]=now;bad=losses(oldgroups[net],now);contacts.append({'net':net,'old_R214_relationship_losses':bad});put(out/'contact-checkpoint.json',contacts)
  if net=='/CORE_1V2':joined=named(root(now,'L2001'));print('R100_CORE_SOURCE_NAMED_PADS',len(joined),'old_rel_losses',len(bad),flush=True)
  if bad:print('R100_CONTACT_LOSS',net,len(bad),flush=True)
 sources=[]
 for net,ref,pin in [('/CORE_1V2','L2001','2'),('/IO_3V3','R18001','2'),('/mc_local_power/CORE_5V','R11022','2'),('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]:
  oldroot=root(oldgroups[net],ref,pin);newroot=root(newgroups[net],ref,pin);lost=F.discrete_keys(oldroot)-F.discrete_keys(newroot);sources.append({'net':net,'actual_source':ref+'.'+pin,'prior_source_keys_lost':[list(k)for k in sorted(lost)],'before_named_pads':len(named(oldroot)),'after_named_pads':len(named(newroot))});print('R100_SOURCE',net,len(lost),len(named(newroot)),flush=True)
 (out/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));put(out/'source-rows.json',sources);assert all(sha(p)==value for p,value in pins.items());put(out/'input-bytes.json',pins);ok=not guarderrors and not any(q['old_R214_relationship_losses']for q in contacts)and not any(q['prior_source_keys_lost']for q in sources);put(out/'receipt.json',{'verdict':'CORE_ORDINARY_IN2_FEED_SOURCE_CONTACT_NEW_NATIVE_GUARD_POSITIVE_FULL_GATES_OPEN'if ok else'CORE_ORDINARY_IN2_FEED_MATERIALIZATION_REPAIR_REQUIRED','model_sha256':sha(out/'model.pkl'),'parent_R83_model_sha256':sha(mp),'prior_positive_R214_model_sha256':sha(head/'model.pkl'),'route_receipt_sha256':sha(packet/'receipt.json'),'new_ordinary_vias':2,'new_owned_CORE_In2_zone':core['uuid'],'remove_only_owned_roles':len(rolecuts),'native_actual_fill_only_new_added_primitive_cuts':len(actualcuts),'new_primitive_actual_native_guard_checks':len(guardrows),'new_primitive_actual_native_guard_errors':len(guarderrors),'checked_old_contact_nets':len(contacts),'contacts_sha256':sha(out/'contact-checkpoint.json'),'sources':sources,'full_FAG_4_58442937244A_four_RTN_constraints_CORE_0_8A_IO3_2A_mesh_drop_return_refs_direct_layercontacts_true_caps_all6_actual_native_DRC':'OPEN','original104_PDN_proposal_and_known_raw_original_reference_FAIL_retained':True,'no_old_source_pad_pose_track_barrel_native_outline_or_settings_edits':True,'native_jobs':0,'board_written':False,'adopted':False});print('R100_CONSTRUCTIVE_SOURCE_CONTACT_RESULT',ok,sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
