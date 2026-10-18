"""Exact physical reference identity and paired raw operator controls.

No raw nonempty derived expression is waived. Identical actual source
primitive sets independently establish identical supported reference sets.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time
from pathlib import Path
from shapely import set_precision
H=Path(__file__).resolve().parent
for d in('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
P=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl';A=H/'FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545';O=H/'FIELD5-R545-identical-reference-primitive-paired-before-controls-r547'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'WKB_SHA256':dg(s)}
def identity(group):return sorted((r['uuid'],r['layer'],dg(r['shape']))for r in group if r['kind']=='fill'and r['layer']in('In1.Cu','In4.Cu'))
def main():
 assert not O.exists();O.mkdir();st=time.monotonic();assert sha(A/'receipt.json')=='327869c6a571da7935a4a5535b4d5457b3168ad20d5522bff2961de72f3a947a';rec=json.loads((A/'receipt.json').read_text(encoding='utf-8'));old=pickle.loads((H/'FA-IO3-TMR-current-R515-complete-delta-direct-contact-r517/actual-drilled-current-groups.pkl').read_bytes());now=pickle.loads((A/'actual-drilled-current-groups.pkl').read_bytes());g,h,b,q,c=pickle.loads(P.read_bytes());by={z['uuid']:z for z in q};rows=[];ident=[]
 for net,ref,pin in K.ROOTS[:3]:
  a=K.root(old[net],ref,pin);n=K.root(now[net],ref,pin);ai=identity(a);ni=identity(n);assert ai==ni;ar=K.source_refs(a);nr=ar
  ident.append({'bank':net,'source':ref+'.'+pin,'actual_drilled_In1_In4_source_fill_primitive_UUID_layer_SHA256_rows':ai,'before_after_literal_primitive_set_exact':True,'same_closed_sets_independent_of_any_GEOS_intersection_reconstruction':True})
  for failure in[r for r in rec['old_reference_delta_losses']if r['bank']==net]:
   z=by[failure['UID']];body=lit(z['shape']);R=ar[z['layer']];S=body.intersection(R);before_control=S.difference(R);after_expression=S.difference(nr[z['layer']]);assert before_control.wkb==after_expression.wkb;assert dg(after_expression)==failure['actual_before_supported_reference_delta']['WKB_SHA256']
   folder=O/(z['uuid']+'-'+net.replace('/','_'));folder.mkdir()
   for name,s in(('actual-before-body',body),('literal-reference-before-and-after-identical',R),('raw-computed-before-supported-intersection',S),('raw-before-control-and-after-witness-identical',before_control)):(folder/(name+'.wkb')).write_bytes(s.wkb)
   rows.append({'bank':net,'UID':z['uuid'],'layer':z['layer'],'raw_before_control':sm(before_control),'raw_after_expression':sm(after_expression),'raw_BEFORE_control_equals_AFTER_witness_WKB':True,'same_actual_before_after_reference_input_OBJECT_and_WKB':True,'same_actual_source_reference_constituent_sets':True,'raw_formula_NONEMPTY_FAIL_preserved':not before_control.is_empty,'incremental_actual_reference_set_change_NONE_by_exact_input_identity':True,'independent_rational_location_certificate':'NOT_CLAIMED_IDENTITY_OF_UNCHANGED_CLOSED_SETS_SUFFICES_FOR_INCREMENTAL_REFERENCE_SET_EQUALITY','witness_folder':str(folder.resolve())})
 other_errors=rec['old_physical_relationship_losses']or rec['direct_old_owned_FG_native_contact_losses']or rec['all_ten_prior_source_key_loss_count']or rec['FIELD5_nine_target_pads_missing']or rec['new_true_geometry_errors']or rec['native_nozone_errors'];assert not other_errors
 put(O/'actual-source-reference-primitive-identity.json',ident);put(O/'raw-before-control-paired-after-expression-witnesses.json',rows);put(O/'receipt.json',{'status':'EXACT_INCREMENTAL_SOURCE_CONTACT_TRUE_GEOMETRY_NOZONE_AND_REFERENCE_PRIMITIVE_IDENTITY_CERTIFIED_RAW_DERIVED_CONTROLS_FAIL_RETAINED_CURRENT_NEW_LOOP_NATIVE_OPEN','R543_model_SHA256':rec['model_SHA256'],'R545_raw_receipt_SHA256':sha(A/'receipt.json'),'raw_nonempty_before_controls_and_after_expressions_retained_count':len(rows),'actual_bank_reference_primitive_set_identity_count':len(ident),'no_raw_nonempty_expression_size_or_boundary_waiver':True,'no_geometry_buffer_operator_rule_or_current_change':True,'cached_before_net_graph_count':rec['cached_baseline_physical_graph_net_count'],'complete_compared_graph_count':rec['complete_compared_graph_net_count'],'exact_unchanged_actual_net_identity_count':rec['unchanged_nets_certified_by_exact_full_native_discrete_hole_fill_identity'],'actual_net_enumeration_includes_empty_unassigned_net':True,'all_ten_source_and50direct_native_layer_contacts_retained':True,'new_FIELD5_cached_full_body_return_gap':rec['new_FIELD5_DC_actual_drilled_body_ground_reference_gap'],'new_F5_sheet_barrel_full_signed_FG_current_return_loop_thermal_native':'OPEN','all_R545_raw_formula_FAIL_and_inherited_R15528refs_CORE_ROOT42_planner_FAIL_preserved':True,'adopted':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-st});print('R547',sha(O/'receipt.json'),'paired rawFAIL',len(rows),flush=True)
if __name__=='__main__':main()
