"""Current immutable fill minus new Cu/drill guards; complete health restored."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy
from pathlib import Path
from shapely import set_precision
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from inventory import sha
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import guarded_declared_settings_projection_r58 as N
import complete_geometry_r2 as G
import restore_SAFE_generated_precision_states_r168 as PS
import physical_reference_losses_r1 as REF
B=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';R=H/'U11025-joint-health-return-legal-face-construction-r344';O=H/'U11025-actual-current-fill-materialized-source-proof-r346';FG='/motherboard_motors/FIELD_GND'
def write(f,v):f.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def digest(s):return sha_bytes(s.wkb)
def sha_bytes(v):
 import hashlib
 return hashlib.sha256(v).hexdigest()
def root(gs,ref,pin='2'):return next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs))
def parts(sh):return [q for q in ([sh] if sh.geom_type=='Polygon' else getattr(sh,'geoms',[])) if q.geom_type=='Polygon' and not q.is_empty]
def records(sh):return [[list(q.exterior.coords),[list(r.coords) for r in q.interiors]] for q in parts(sh)]
def main():
 assert not O.exists();O.mkdir();g,oh,ob,oz,bc=pickle.loads((B/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(ob,oz);_,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(b,z);d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());assert len(d['vias'])==1 and len(d['tracks'])==6;deleted=json.loads((R/'exact-owned-old-track-rows.json').read_text());deletedids={q['uuid'] for q in deleted};v=d['vias'][0];nativeids={q['uuid'] for q in h['zones']};cache={};ledger=[];nativeguards=[]
 def cuts(net,local,layer,physical=True):
  out=[]
  for via in d['vias']:
   if net==via['net']:
    if physical:radius=via['drill']/2
    else:continue
    kind='own_new_ordinary_physical_drill_void'
   else:
    clear=max(G.gap(h,net,via['net']),float(local))+.025+.000100;radius=max(via['drill']/2+.275+.000100,via['d']/2+clear);kind='new_ordinary_foreign_Cu_drill_antipad'
   key=('via',via['uuid'],radius)
   if key not in cache:cache[key]=N.bounded_disk(via,radius)
   out.append((kind,via['uuid'],set_precision(cache[key],0)))
  for t in d['tracks']:
   if t['layer']!=layer or t['net']==net:continue
   clear=max(G.gap(h,net,t['net']),float(local))+.025+.000100;radius=t['w']/2+clear;key=('track',t['uuid'],radius)
   if key not in cache:cache[key]=N.bounded_buffer(LineString([t['a'],t['b']]),radius)
   out.append(('new_F_track_foreign_Cu_guard',t['uuid'],set_precision(cache[key],0)))
  return out
 owned=[]
 for q in z:
  nq=copy.deepcopy(q)
  for role in ('shape','zone_outline_shape'):
   before=q[role];applicable=[row for row in cuts(q['net'],q.get('clearance_mm',.15),q['layer'],role=='shape') if row[2].intersects(before)]
   if not applicable:continue
   zero=set_precision(before,0);cut=unary_union([row[2] for row in applicable]);after=set_precision(zero.difference(cut),1e-6,mode='pointwise');roundings=[]
   for iteration in range(16):
    gain=set_precision(after,0).difference(zero)
    if gain.is_empty:break
    reserve=N.bounded_buffer(gain,.000100);after=set_precision(set_precision(after,0).difference(set_precision(reserve,0)),1e-6,mode='pointwise');roundings.append({'iteration':iteration,'literal_gain_SHA256':digest(gain),'literal_gain_mm2':gain.area,'only_local_new_negative_reserve_SHA256':digest(reserve),'reserve_mm':.000100})
   assert set_precision(after,0).difference(zero).is_empty,('owned physical/intended gained',q['uuid'],role);assert not after.is_empty;nq[role]=after;cutfile=O/(q['uuid']+'-'+role+'-only-added-primitives-cut.wkb');cutfile.write_bytes(cut.wkb);ledger.append({'owned_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'role':role,'before_SHA256':digest(before),'after_SHA256':digest(after),'only_removed_mm2':zero.difference(set_precision(after,0)).area,'added_mm2':0,'cut_file':str(cutfile.resolve()),'cut_SHA256':sha(cutfile),'local_integer_gain_corrections':roundings,'own_drill_void_only_physical_not_intended':True})
  owned.append(nq)
 actual=[];fillledger=[]
 for before in bc['zones']:
  if before['uuid'] not in nativeids:continue
  nq=copy.deepcopy(before)
  for layer,recs in before['fills'].items():
   applicable=cuts(before['net'],before.get('clearance_mm',.15),layer,True);newrecords=[]
   for idx,(rec,shape) in enumerate(zip(recs,C.poly(recs))):
    zero=set_precision(shape,0);local=[row for row in applicable if row[2].intersects(zero)]
    if not local:newrecords.append(copy.deepcopy(rec));continue
    cut=unary_union([row[2] for row in local]);after=zero.difference(cut);after=after.intersection(zero);newrecords+=records(after);again=unary_union(C.poly(records(after)));assert again.difference(zero).is_empty,('native actual gained',before['uuid'],layer,idx);fillledger.append({'native_UUID':before['uuid'],'raw_net':before['net'],'layer':layer,'record':idx,'before_SHA256':digest(shape),'after_SHA256':digest(again),'only_added_primitive_UUIDs':[row[1] for row in local],'removed_mm2':zero.difference(again).area,'added_mm2':0,'all_no_cut_original_arrays_exact':True})
   nq['fills'][layer]=newrecords
  actual.append(nq)
 # Apply exact role withdrawals to the existing owned actual filled records;
 # untouched arrays stay exact, and no old source filled copper is reclaimed.
 om={q['uuid']:q for q in oz};am={q['uuid']:q for q in bc['zones']};ownedmap={q['uuid']:q for q in owned}
 for q in owned:
  before=am[q['uuid']];nq=copy.deepcopy(before);layer=q['layer'];withdrawal=set_precision(om[q['uuid']]['shape'],0).difference(set_precision(q['shape'],0));newrecords=[]
  for idx,(rec,shape) in enumerate(zip(before['fills'][layer],C.poly(before['fills'][layer]))):
   zero=set_precision(shape,0)
   if withdrawal.is_empty or not withdrawal.intersects(zero):newrecords.append(copy.deepcopy(rec));continue
   after=zero.difference(withdrawal).intersection(zero);newrecords+=records(after);again=unary_union(C.poly(records(after)));assert again.difference(zero).is_empty,('owned actual filled gain',q['uuid'],idx);fillledger.append({'owned_UUID':q['uuid'],'raw_net':q['net'],'layer':layer,'record':idx,'before_SHA256':digest(shape),'after_SHA256':digest(again),'exact_role_withdrawal_SHA256':digest(withdrawal),'removed_mm2':zero.difference(again).area,'added_mm2':0,'all_no_cut_original_arrays_exact':True})
  nq['fills'][layer]=newrecords;actual.append(nq)
 current={**h,'zones':actual};write(O/'only-added-owned-role-delta-ledger.json',ledger);write(O/'immutable-before-filled-record-minus-new-primitives-ledger.json',fillledger);print('R346 roles',len(ledger),'filled records',len(fillledger),flush=True)
 states=[]
 for q in owned:
  for role in ('shape','zone_outline_shape'):states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest(q[role]),'exact_WKB_unchanged':True})
 b=copy.deepcopy(b);b['generated_precision_state_ledger']=states;b['U11025_exact_health_return_owned_delta']={'prior_ROOT112_model_SHA256':sha(B/'model.pkl'),'R344_discrete_SHA256':sha(R/'proposed-discrete.pkl'),'exact_original_health_delete_UUIDs':sorted(deletedids),'new_ordinary_via_UUID':v['uuid'],'full_current_native_allseverity':'OPEN'}
 oldgroups=pickle.loads((B/'groups.pkl').read_bytes());newgroups={};contactrows=[]
 for net in [FG,*sorted(n for n in oldgroups if n!=FG)]:
  now=F.graph(current,net);newgroups[net]=now;bad=losses(oldgroups[net],now);contactrows.append({'net':net,'old_ROOT112_contact_losses':bad});write(O/'all-original-zone-net-contact-checkpoint.json',contactrows)
  if net==FG:rr=root(now,'J11003');print('R346 FG source pads',sum(q['kind']=='pad' for q in rr),'U25 rooted',any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11025','2') for q in rr),flush=True)
  if bad:print('R346 CONTACT FAIL',net,len(bad),flush=True)
 health=next(q['net'] for q in d['tracks'] if q['net']!=v['net']);oldhealth=F.graph(bc,health);newhealth=F.graph(current,health);trimmed=[[q for q in group if q['uuid'] not in deletedids] for group in oldhealth];trimmed=[q for q in trimmed if q];healthlosses=losses(trimmed,newhealth);write(O/'literal-health-all-retained-relationship-check.json',{'net':health,'exact_owned_old_deletes':sorted(deletedids),'retained_health_losses':healthlosses,'old_groups':len(oldhealth),'new_groups':len(newhealth)})
 sources=[]
 for net,ref,pin in [('/CORE_1V2','L2001','2'),('/IO_3V3','R18001','2'),('/mc_local_power/CORE_5V','R11022','2'),('/LOGIC_GND','J11001','2'),(FG,'J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]:
  a,bb=root(oldgroups[net],ref,pin),root(newgroups[net],ref,pin);missing=F.discrete_keys(a)-F.discrete_keys(bb);sources.append({'net':net,'root':ref+'.'+pin,'prior_source_keys_lost':[list(k) for k in sorted(missing)]})
 references=[];eligible={**bc,'tracks':[t for t in bc['tracks'] if t['uuid'] not in deletedids]}
 for net,ref in [(FG,'J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/LOGIC_GND','J11001')]:
  aa,bb=root(oldgroups[net],ref),root(newgroups[net],ref);a_refs={out:unary_union([q['shape'] for q in aa if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};b_refs={out:unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,proof=REF.audit(eligible,a_refs,b_refs,net);references.append({'net':net,'strict_old_ref_losses':bad,'full_formula_proof':proof});print('R346 old refs',net,len(bad),flush=True)
 fg=root(newgroups[FG],'J11003');newref=unary_union([q['shape'] for q in fg if q['kind']=='fill' and q['layer']=='In1.Cu']);newbodyrefs=[{'UUID':t['uuid'],'health_reference_gap_mm2':LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=256).difference(newref).area} for t in d['tracks'] if t['net']==health];u25=any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11025','2') for q in fg);ok=u25 and not healthlosses and not any(q['old_ROOT112_contact_losses'] for q in contactrows) and not any(q['prior_source_keys_lost'] for q in sources) and not any(q['strict_old_ref_losses'] for q in references) and all(q['health_reference_gap_mm2']<=1e-9 for q in newbodyrefs)
 write(O/'source-and-required-reference-ledger.json',{'sources':sources,'old_references':references,'new_health_full_J3_In1_references':newbodyrefs,'U11025_2_J3_rooted':u25});(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,owned,current),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));(O/'owned-role-updates.pkl').write_bytes(pickle.dumps([q for q in owned if q['uuid'] in {row['owned_UUID'] for row in ledger}],protocol=5));write(O/'generated-precision-state-ledger.json',states);rec={'verdict':'U11025_COMPLETE_COUPLED_HEALTH_GROUND_SOURCE_CONTACT_OLDREF_PASS_FULL_NATIVE_CURRENT_OPEN' if ok else 'U11025_COUPLED_MATERIALIZATION_REJECTED_SOURCE_CONTACT_OR_REF','parent_ROOT112_model_SHA256':sha(B/'model.pkl'),'R344_nomination_receipt_SHA256':sha(R/'receipt.json'),'model_SHA256':sha(O/'model.pkl'),'groups_SHA256':sha(O/'groups.pkl'),'only_added_owned_role_deltas':len(ledger),'only_added_primitive_current_filled_record_deltas':len(fillledger),'all_original_zone_nets_checked':len(contactrows),'old_contact_losses':sum(len(q['old_ROOT112_contact_losses']) for q in contactrows),'health_retained_relationship_losses':healthlosses,'prior_source_keys_lost':sum(len(q['prior_source_keys_lost']) for q in sources),'strict_old_reference_losses':sum(len(q['strict_old_ref_losses']) for q in references),'U11025_2_J11003_2_source_connected':u25,'all_new_health_full_reference_gaps':newbodyrefs,'ground_planning_current_A':.001,'native_full_true_copper_holes_current_thermal_DRC_gate':'OPEN','no_old_native_outline_or_settings_or_source_node_changed':True,'native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'PASS':ok}),flush=True)
if __name__=='__main__':main()
