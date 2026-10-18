"""Freeze exact Q0/DIC/DI6 sparse replay authority against full R157.

No board emission, selected fill, whole-model overlay or adoption. Root's
later all-net clone must compose the current CORE/field peers independently
and retain every failed/open gate and original native required mask.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'Q0-DIC-DI6-exact-R157-minimal-sparse-native-replay-manifest-r588'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or s==v;pins[str(p.resolve())]=s;return p
 qf=pin(H/'Q0-two-SMD-shielding-scoped-supplement-r536/minimal-exact-shielded-Q0-current-supplement.json','85d262e256dcd04e637b73492e5fe7ec063b6590757962f1a2d0395546857f63');q536=json.loads(qf.read_bytes());qbase=pin(q536['extends_exact_R512_sparse_native_copper_pose_recipe']['file'],'e807261a930a03002a681fcc4d3c3f522841796f8f091eb3cb9f646c53ba9ba8');q512=json.loads(qbase.read_bytes());qledger=pin(q512['native_discrete_operations_file'],q512['native_discrete_operations_sha256']);qops=json.loads(qledger.read_bytes());df=pin(H/'DIC-policy-coupled-exact-sparse-host-scope-supplement-r566/minimal-exact-DIC-coupled-host-supplement.json','1422c2032032dbd19427486795963924c7a1bdfe72d7a9c998ea3322986de04e');dic=json.loads(df.read_bytes());dif=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/receipt.json','a4e9c25f6f63bf24077a6deb13f3021f17137da2ae733fe560174ba08f083dfd');di=json.loads(dif.read_bytes());dip=pin(di['sparse_operation_file'],di['sparse_operation_SHA256']);diop=pickle.loads(dip.read_bytes());host=pin(di['model_file'],'cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(host.read_bytes());nf=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb');nativebytes=nf.read_bytes();iv=K.C.inventory(nativebytes);before=iv[3];cu=iv[4];ef=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(ef.read_bytes());adds={};retires={};authority={}
 def add(uid,ch,owner,reason):
  if uid in adds:assert adds[uid]==ch
  adds[uid]=ch;authority.setdefault(uid,[]).append({'owner':owner,'reason':reason})
 def retire(uid,ch,owner,reason):
  assert before[uid]==ch and nativebytes.count(ch)==1
  if uid in retires:assert retires[uid]==ch
  retires[uid]=ch;authority.setdefault(uid,[]).append({'owner':owner,'reason':reason})
 for row in qops:
  f=pin(row['exact_chunk_file'],row['exact_chunk_sha256']);ch=f.read_bytes()
  if row['action']=='remove':retire(row['uuid'],ch,'Q0_R512','exact_four_original_native_track_removal')
  else:assert row['action']=='add';add(row['uuid'],ch,'Q0_R512','exact_new_native_chunk_with_declared_locked_metadata')
 for row in dic['exact_retire_current_native_chunks']:
  f=pin(row['file'],row['SHA256']);retire(row['UUID'],f.read_bytes(),'DIC_R566','two_exact_original_locked_G0_and_only_owned_unaccepted_DIC_trial_items')
 for row in dic['exact_new_chunks']:
  f=pin(row['file'],row['SHA256']);add(row['UUID'],f.read_bytes(),'DIC_R566','compliant_pair_and_locked_G0_replacement')
 for uid,ch in diop['exact_new_chunks'].items():assert uid not in before;add(uid,ch,'DI6_R578','twelve_new_only_discrete_items_no_original_ripup')
 identity.assert_chunks(adds);parsed={uid:K.A.G.parse(uid,ch,{})for uid,ch in adds.items()};hby={x['uuid']:x for x in h['tracks']+h['vias']};allow=set(retires);nativeonly=set(cu)-set(hby);newhost=set(hby)-set(cu);changed=[];unbound=[];arcs={t['uuid']:t for t in h['tracks']if t.get('m')is not None}
 def semantic_same(p,x):
  if K.L.norm(p['net'])!=K.L.norm(x['net']):return False
  if p['kind']=='via':return tuple(p['at'])==(x['x'],x['y'])and(p['d'],p['drill'])==(x['d'],x['drill'])
  if p['kind']=='segment':return(p['layer'],p['w'],tuple(p['a']),tuple(p['b']))==(x['layer'],x['w'],tuple(x['a']),tuple(x['b']))
  return p['kind']=='arc'and p==arcs[p['uuid']]
 for uid in sorted(nativeonly):
  if uid not in retires:unbound.append({'UUID':uid,'kind':'NATIVE_ONLY_MISSING_IN_HOST_NO_EXACT_RETIRE_AUTHORITY'})
 for uid in sorted(newhost):
  if uid not in adds:unbound.append({'UUID':uid,'kind':'NEW_HOST_ITEM_NO_EXACT_ADD_AUTHORITY'})
 for uid in sorted(set(cu)&set(hby)):
  p=K.A.G.parse(uid,cu[uid],arcs)
  if not semantic_same(p,hby[uid]):
   changed.append(uid)
   if uid not in adds or uid not in retires:unbound.append({'UUID':uid,'kind':'SAME_UUID_NATIVE_CU_REPLACEMENT_WITHOUT_EXACT_BEFORE_AND_AFTER_AUTHORITY'})
 for uid,p in parsed.items():assert uid in hby and semantic_same(p,hby[uid]),('manifest new chunk differs actual current model',uid)
 put(OUT/'all-current-host-vs-exact-R157-native-Cu-authority-diff.json',{'current_host_SHA256':sha(host),'native_source_SHA256':sha(nf),'native_only_UUIDs':sorted(nativeonly),'new_host_UUIDs':sorted(newhost),'same_UUID_changed_Cu_UUIDs':changed,'unbound_differences':unbound});assert not unbound,'No stale whole model or unbound source changes permitted'
 operations=[]
 for uid in sorted(set(adds)|set(retires)):
  row={'UUID':uid,'authorities':authority[uid],'action':'replace'if uid in adds and uid in retires else'add'if uid in adds else'remove'}
  if uid in retires:f=OUT/(uid+'-exact-before-R157.chunk');f.write_bytes(retires[uid]);row['before']={'file':str(f.resolve()),'SHA256':sha(f)}
  if uid in adds:f=OUT/(uid+'-exact-after.chunk');f.write_bytes(adds[uid]);row['after']={'file':str(f.resolve()),'SHA256':sha(f)};row['actual_native_NEW_all6_flash_required']=parsed[uid]['kind']=='via'
  operations.append(row)
 pose=q512['footprint_replacements'];pose=[pose]if isinstance(pose,dict)else pose;assert len(pose)==1
 for p in pose:
  bf=pin(p['exact_before_chunk_file'],p['exact_before_chunk_sha256']);af=pin(p['exact_after_chunk_file'],p['exact_after_chunk_sha256']);assert before[p['UUID']]==bf.read_bytes()and p['ref']=='R10016';assert p['candidate_root_at_mm']==[229.96,166.662]
 proof=[]
 for f,v in((H/'DI6-current-frozen-independent-plane-key-closure-r582/receipt.json','1c58cecfcd0b31a0ea7c536121005197c8f012c02479ea4d6f79d27c63305a58'),(H/'DI6-actual-full-R157-target-source-mask-void-binding-r586/receipt.json','4800d7dfb440aac7f2f23f38636b284127c1aa88a09cfaee1c81a167fa5e040b'),(H/'DIC-policy-coupled-actual-current-independent-r562/receipt.json','ae47a082e0813041706a153fcfc6fc1f2c4e2de101f55e8580be3c1a104cb776'),(H/'DIC-R562-literal-subtraction-scope-arrangement-r564/receipt.json','561a7ecc4be07e2c45ad4461d1ba587e02ad4ea2ee434d0d859390b0ccdbc6a7')):
  f=pin(f,v);proof.append({'file':str(f.resolve()),'SHA256':sha(f)})
 readsets=(H/'Q0-two-SMD-shielding-scoped-supplement-r536/frozen-read-set.json',H/'DIC-policy-coupled-exact-sparse-host-scope-supplement-r566/frozen-read-set.json')
 for f in readsets:
  if f.exists():pin(f)
 manifest={'schema':'Q0-DIC-DI6-minimal-exact-R157-sparse-replay-manifest-r588','verdict':'SPARSE_REPLAY_AUTHORITY_AND_INCREMENTAL_HOST_SCOPES_FROZEN_ALL_NET_NATIVE_CURRENT_PEER_GATES_OPEN','exact_full_all_net_R157_native_parent':{'file':str(nf.resolve()),'SHA256':sha(nf)},'reference_host_only_never_wholemodel_overlay':{'file':str(host.resolve()),'SHA256':sha(host)},'exact_discrete_operations':operations,'exact_R10016_only_native_pose_replacement':pose,'original_Q0_SENSE_chunks_unused_flags_and_mandatory_F_B_masks_retained_new_In2_native_flash_required':q512['exact_old_SENSE_native_chunks_and_flags_retained_with_new_actual_In2_flash_obligations'],'replay_dependency_order':[{'role':'Q0_original_Cu_pose_and_sparse_negative_roles_fill','file':str(qbase.resolve()),'SHA256':sha(qbase)},{'role':'Q0_new_FG637_shield_and_only_new_FA7ef_negative_scope_plus_final_host_proof','file':str(qf.resolve()),'SHA256':sha(qf)},{'role':'DIC_only_retired_unaccepted55ab_preDIC_primitive_replay_then_exact_NEW_cuts_and_compliant_locked_G0_DIC_items','file':str(df.resolve()),'SHA256':sha(df)},{'role':'DI6_exact_new_items_and_only_current_native_family_cuts_no_owned_role_change','file':str(dif.resolve()),'SHA256':sha(dif)}],'independent_actual_incremental_and_full_native_BEFORE_target_proofs':proof,'full_current_owned_roles_must_come_from_later_combined_CORE_field_head_with_exact_constituent_sparse_replay':True,'never_copy_whole_q_host_model_or_old_actual_filled_array_or_credit_selected_blank_foreign_cache':True,'unchanged_original_native_zone_outlines_source_rules_project_FP_except_named_R10016':True,'all_required_old_native_masks_original_flags_retained_no_forcing':True,'all_current_true_all6_caps_holes_SMD_source_direct_strict_oldref_newbody_currentpeer_checks_mandatory_after_late_combination':True,'native_diagnostic_method':'One combined ALL-NET refill after CORE repair; bind actual original masks/source/allCu/declared actual zone settings then uncapped original_r06_r07_R155_R157_native guards and full CLI DRC. No selected native trial.','current_R157_original_full_CLI_must_remain_uninterrupted':True,'all_failed_open_gates_retained':['R15722 original native mask failures','R36828 strict oldrefs and later field raw refinements','CORE93 and DCbody/current/thermal/full loop qualification','R7 raw new body gap/ROOT42/extra planner failures','Q0 old B terminal raw failures and full signed FA current/source/thermal','DIC raw R562 subtraction witnesses separately exact-supported R564; all old trial policy failures','DI6 old R14.836 pair and original matched native remoteMOTION210nm failure; new AFTER complete native neighbor/source/SI pending'],'native_launch_authorized_by_this_manifest':False,'native_jobs':0,'full_board_gate_pass':False,'adopted':False,'manufacturing_ready':False}
 put(OUT/'minimal-exact-Q0-DIC-DI6-native-replay-manifest.json',manifest);pin(Path(__file__));put(OUT/'frozen-read-set.json',pins);put(OUT/'receipt.json',{'verdict':manifest['verdict'],'manifest_SHA256':sha(OUT/'minimal-exact-Q0-DIC-DI6-native-replay-manifest.json'),'exact_R157_source_SHA256':sha(nf),'host_model_SHA256':sha(host),'operation_count':len(operations),'Q0_DIC_DI6_dependency_profiles_and_all_raw_failures_retained':True,'native_inventory_unbound_count':len(unbound),'native_jobs':0,'adopted':False,'board_written':False,'elapsed_seconds':time.monotonic()-st});print('R588_COMPLETE',sha(OUT/'receipt.json'),sha(OUT/'minimal-exact-Q0-DIC-DI6-native-replay-manifest.json'),len(operations),flush=True)
if __name__=='__main__':main()
