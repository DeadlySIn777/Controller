"""Bind independent joint checks and exact witness supplement without waivers."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={
 'actual_joint':('U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r255/receipt.json','144ec25c899ef9f54397c0fe914920799e58475cb35cb2770f1f9583244d8b5b'),
 'actual_planes_and_unselected':('joint-R253-two-new-FG-planes-true-foreign-and-untouched-physics-r260/receipt.json','414810b17827b02d3e922867948328019abc5921eff76d0a2a09fa1d29640ff6'),
 'exact_current_witness':('U10003-old-reference-exact-all-source-rational-arrangement-r257/receipt.json','f79930e3323c62ebc7fc1f1c43a8f9ad7872739cb297e7dc88dbc620d9265a7f'),
 'exact_witness_source_binding':('U10003-all-source-exact-bbox-reference-witness-binding-r256/receipt.json','70a2588587fa20ac4f825ede677f3da5579ec6aa3dfce9c65686ebb9bb836353')}
r={};pins={}
for name,(path,digest)in checks.items():
 p=H/path;assert sha(p)==digest;r[name]=json.loads(p.read_bytes());pins[str(p.resolve())]=digest
m=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert sha(m)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440';g,h,b,q,c=pickle.loads(m.read_bytes());pins[str(m.resolve())]=sha(m)
a=r['actual_joint'];assert a['after_SHA256']==sha(m)
assert all(a[k]==0 for k in('geometry_errors','old_relationship_losses','old_direct_contact_losses','prior_source_keys_lost','new_body_reference_failures'));assert a['strict_old_routed_reference_failures']==1
assert all(x['ordinary_window_pass']and x['both_annuli_pass']for x in a['returns'])
assert r['actual_planes_and_unselected']['status']=='SCOPED_NEW_PLANES_AND_UNTOUCHED_PHYSICS_PASS_NATIVE_OPEN'
assert r['exact_current_witness']['literal_loss_classification_count']==0 and r['exact_current_witness']['witness_sha256']=='d303bde81af60cb3e7e74fd742bc249c278876fcf5d656526ac39de350eff06a'
binding=r['exact_witness_source_binding'];assert binding['inputs_sha256'][str(m.resolve())]==sha(m);assert r['exact_current_witness']['source_receipt_sha256']==checks['exact_witness_source_binding'][1]
fail=H/'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r255/strict-original-routed-reference-failures.json';raw=json.loads(fail.read_bytes());assert len(raw)==1 and raw[0]['uuid']=='3aabe7ec-baf5-4304-ac89-079b0a62e545'and raw[0]['literal_direct_formula_loss']['WKB_SHA256']==r['exact_current_witness']['witness_sha256'];pins[str(fail.resolve())]=sha(fail)
gp=H/'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r255/fresh-actual-drilled-affected-groups.pkl';assert sha(gp)==a['fresh_groups_SHA256'];groups=pickle.loads(gp.read_bytes());pins[str(gp.resolve())]=sha(gp)
fg=K.root(groups['/motherboard_motors/FIELD_GND'][1],'J11003','2');lg=K.root(groups['/LOGIC_GND'][1],'J11001','2');host=next(xs for xs in groups['/motherboard_do/DOA_SDI_HOST'][1]if any(x['kind']=='pad'and(x['ref'],str(x['pin']))==('U13004','31')for x in xs))
sourceproof=[]
for net,root,selectors in[('/motherboard_motors/FIELD_GND',fg,[('U10003','9')]),('/LOGIC_GND',lg,[('R10007','2')]),('/motherboard_do/DOA_SDI_HOST',host,[('R10007','1'),('U10003','3')])]:
 for ref,pin in selectors:
  pad=next(p for p in h['pads']if(p['ref'],str(p['num']))==(ref,pin));kk=K.keys(root);yes=any(k[0]=='pad'and k[1]==pad['uuid']for k in kk);assert yes,(net,ref,pin);sourceproof.append({'net':net,'ref':ref,'pin':pin,'UUID':pad['uuid'],'actual_source_group_key_present':yes})
op=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/full-sparse-operation.pkl';d=pickle.loads(op.read_bytes());assert (len(d['new_tracks']),len(d['new_vias']),len(d['removed_original_tracks']),len(d['replaced_only_two_new_FG_planes']))==(13,4,6,2);pins[str(op.resolve())]=sha(op)
out=H/'U10003-HOST-joint-current-scoped-independent-evidence-r261';assert not out.exists();out.mkdir();result={'status':'CURRENT_JOINT_HOST_FIELD_GEOMETRIC_INCREMENTAL_SCOPE_WITH_EXACT_WITNESS_SUPPLEMENT_PASS_NATIVE_OPEN','model_SHA256':sha(m),'sparse_operation_SHA256':sha(op),'all_input_SHA256':pins,'source_targets':sourceproof,'true_geometry_checks':a['geometry_checks'],'old_direct_contacts':a['old_direct_contacts'],'all_old_relationship_source_and_direct_contact_losses':0,'new_and_restored_CLK_fullbody_reference_remaining_gaps':0,'ordinary_return_pairs_both_actual_planes_and_saved_window':4,'both_moved_R10007_SMD_bodies_actual_J1_In4_supported':True,'literal_raw_old_reference_failure_count_retained':1,'specific_exact_current_all_source_arrangement_classification_real_loss_count':0,'literal_raw_failure_files_or_flags_modified':False,'raw_precision_native_integer_owned_edge_splice':'OPEN; no hidden global resnap','exact_native_Cu_locked_flags_FP_pose_collector_actual_all6_flashes_native_fill_DRC':'OPEN','full_source_current_power_signed_mesh_barrel_SI_thermal_manufacturing':'OPEN','all_inherited_DIC_CORE_R5051_original_native_and_prior_r06_failures':'RETAINED','native_jobs':0,'adopted':False,'manufacturing_ready':False};(out/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R261_SCOPED',sha(out/'receipt.json'),flush=True)
