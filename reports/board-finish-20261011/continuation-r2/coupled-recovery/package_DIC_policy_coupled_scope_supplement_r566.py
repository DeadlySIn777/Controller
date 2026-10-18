"""Freeze sparse policy-compliant DIC/G0FAULT delta and exact scopes.

This packet is independent host evidence for root's later composition and
native diagnostic. It never grants adoption or hides inherited failures.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DIC-policy-coupled-exact-sparse-host-scope-supplement-r566'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
 audit=pin(H/'DIC-policy-coupled-actual-current-independent-r562/receipt.json','ae47a082e0813041706a153fcfc6fc1f2c4e2de101f55e8580be3c1a104cb776');a=json.loads(audit.read_bytes());rat=pin(H/'DIC-R562-literal-subtraction-scope-arrangement-r564/receipt.json','561a7ecc4be07e2c45ad4461d1ba587e02ad4ea2ee434d0d859390b0ccdbc6a7');r=json.loads(rat.read_bytes());assert r['literal_outside_scope_count']==0 and len(r['raw_R562_six_GE0S_failures_retained'])==6
 for key in('actual_old_relationship_losses','actual_old_direct_same_zone_contact_losses','true_all6_geometry_errors','strict_raw_old_reference_losses','new_body_reference_errors'):assert a[key]==[]
 assert a['prior_ten_source_layer_key_loss_count']==0 and a['actual_r06_DIC_pad_relationship_joined']and a['signal_layer_legs']==3
 assert all(z['policy_and_host_source_pair_pass']and .9<=z['distance_mm']<=1 for z in a['all_three_hard_policy_pairs'])
 cr=pin(H/'DIC-retired-cutter-policy-coupled-current-r556/receipt.json','cc71df8c96290d7a689af22213dc72b248df85f0f139c0833e314ab8b1b9204b');c=json.loads(cr.read_bytes());mp=pin(c['model_file'],'95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5');opfile=pin(c['sparse_discrete_and_current_fill_delta_file'],'7743366078b088048050f4c04c036961d5d0a2ac7b9225ee3f09fc67d5cef8a0');op=pickle.loads(opfile.read_bytes())
 beforefile=pin(H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl','97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14');g,h,b,q,c0=pickle.loads(beforefile.read_bytes());byitem={x['uuid']:x for x in h['tracks']+h['vias']}
 source=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');native=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb');sv=K.C.inventory(source.read_bytes())[3];nv=K.C.inventory(native.read_bytes())[3];new=op['exact_new_chunks'];retired=set(op['retired_current_NEW_track_UUIDs']);viaids={v['uuid']for v in op['changed_only_NEW_vias']};nativeold=set(op['native_deleted_chunks']);assert len(retired)==8 and len(viaids)==3 and len(nativeold)==2 and retired.isdisjoint(sv)and viaids.isdisjoint(sv)
 oldrows=[]
 for uid in sorted(nativeold|retired|viaids):
  chunk=nv[uid];assert native.read_bytes().count(chunk)==1
  item=byitem[uid];parsed=K.A.G.parse(uid,chunk,{})
  assert K.L.norm(parsed['net'])==K.L.norm(item['net'])
  if parsed['kind']=='segment':assert parsed['layer']==item['layer']and parsed['w']==item['w']and tuple(parsed['a'])==tuple(item['a'])and tuple(parsed['b'])==tuple(item['b'])
  else:assert parsed['kind']=='via'and tuple(parsed['at'])==(item['x'],item['y'])and(parsed['d'],parsed['drill'])==(item['d'],item['drill'])
  if uid in nativeold:assert chunk==sv[uid]==op['native_deleted_chunks'][uid]and b'(locked yes)'in chunk
  f=OUT/(uid+'-exact-current-R157-retire.chunk');f.write_bytes(chunk);pin(f);oldrows.append({'UUID':uid,'file':str(f.resolve()),'SHA256':sha(f),'original_eedf_native':uid in nativeold,'unaccepted_recipe_owned_DIC_trial_only':uid not in nativeold,'replacement_same_UUID':uid in new,'exact_geometry_matches_R526':True,'original_locked_yes_preserved_if_replaced':uid in nativeold})
 newrows=[]
 for uid,ch in sorted(new.items()):
  assert uid not in sv;f=OUT/(uid+'-exact-new.chunk');f.write_bytes(ch);pin(f);p=K.A.G.parse(uid,ch,{});newrows.append({'UUID':uid,'file':str(f.resolve()),'SHA256':sha(f),'kind':p['kind'],'raw_serialized_net':p['net'],'ordinary_all6_API_required':p['kind']=='via','locked_yes':b'(locked yes)'in ch})
 freeze=pin(H/'Q0-two-SMD-shielding-scoped-supplement-r536/minimal-exact-shielded-Q0-current-supplement.json','85d262e256dcd04e637b73492e5fe7ec063b6590757962f1a2d0395546857f63')
 # Exhaustive files from independently frozen inputs/outputs remain hashed.
 for rr in(a,r,c):
  for key in('input_SHA256','inputs_SHA256','output_SHA256'):
   for f,v in rr.get(key,{}).items():pin(f,v)
 rsfile=pin(H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/receipt.json','0fb06aad596ba3efad377852b8ee38ddd26f95530a629434ceb443254e440e4e');rs=json.loads(rsfile.read_bytes())
 for key in('input_SHA256','output_SHA256'):
  for f,v in rs.get(key,{}).items():pin(f,v)
 recipe={'schema':'exact-DIC-policy-coupled-host-incremental-scope-supplement-r566','verdict':'HOST_INCREMENTAL_CONTACT_SOURCE_TRUE_GEOMETRY_STRICT_OLD_REF_AND_NEW_BODY_PASS_WITH_EXACT_SCOPE_CERTIFICATE_NATIVE_CURRENT_OPEN','constructor_receipt':{'file':str(cr.resolve()),'SHA256':sha(cr)},'current_model':{'file':str(mp.resolve()),'SHA256':sha(mp)},'sparse_delta':{'file':str(opfile.resolve()),'SHA256':sha(opfile)},'required_previous_Q0_sparse_scope':{'file':str(freeze.resolve()),'SHA256':sha(freeze)},'current_R157_native_exact_retirement_source':{'file':str(native.resolve()),'SHA256':sha(native)},'exact_retire_current_native_chunks':oldrows,'exact_new_chunks':newrows,'owned_native_deletes_count':2,'only_unaccepted_DIC_track_retirements':8,'only_unaccepted_DIC_via_replacements':3,'original_DIC_four_native_deletes_and_all_required_original_via_masks_unchanged':True,'strict_RAW_R562_scope_FAIL_preserved':a['raw_extra_negative_outside_scoped_cuts_or_declared_local_reserves'],'separate_exact_rational_scope_certificate':{'file':str(rat.resolve()),'SHA256':sha(rat),'literal_outside_scope_count':0},'independent_actual_contact_source_geometry_reference_receipt':{'file':str(audit.resolve()),'SHA256':sha(audit)},'actual_old_relationship_net_scopes':a['full_old_relationship_net_count'],'all_three_saved_window_pairs':a['all_three_hard_policy_pairs'],'independent_actual_DIC_original_pad_join':True,'source_return_identity_own_scope_before_clipped_only':True,'no_generic_disk_credit_or_same_plane_window_waiver':True,'exact_all_q49_roles98_native_settings_and_FP_headers_rules_source_retained':True,'retired_NEW55ab_source_cache_replay_must_use_only_pinned_PRE_DIC_primitives_and_owned_cutter':{'file':str(rsfile.resolve()),'SHA256':sha(rsfile)},'actual_current_fill_delta_must_replay_per_record_only_no_stale_q_or_model_overlay':True,'all_inherited_CORE93_R36828_R7_ROOT42_planner_current_native_failures_preserved':True,'native_API_actual_all6_masks_source_partitions_all_baselines_fullDRC_SI_current_minfeature':'OPEN; root owns fresh exact composition and all native jobs','host_complete_board_gate_pass':False,'production_gate_pass':False,'adopted':False,'manufacturing_ready':False,'native_jobs':0}
 put(OUT/'minimal-exact-DIC-coupled-host-supplement.json',recipe);put(OUT/'frozen-read-set.json',pins);put(OUT/'receipt.json',{'verdict':recipe['verdict'],'recipe_SHA256':sha(OUT/'minimal-exact-DIC-coupled-host-supplement.json'),'model_SHA256':sha(mp),'sparse_delta_SHA256':sha(opfile),'frozen_read_set_SHA256':sha(OUT/'frozen-read-set.json'),'exact_retire_rows':len(oldrows),'new_tracks':10,'NEW_via_replacements':3,'no_source_board_project_or_flags_written':True,'adopted':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-st});print('R566_COMPLETE',sha(OUT/'receipt.json'),sha(OUT/'minimal-exact-DIC-coupled-host-supplement.json'),len(pins),flush=True)
if __name__=='__main__':main()
