"""Exact 13-track/4-via/6-delete sparse native patch; no board emitted."""
import hashlib,json,pickle,re,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-HOST-joint-exact-native-Cu-and-attested-pose-packet-r263';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
scope=H/'U10003-HOST-joint-current-scoped-independent-evidence-r261/receipt.json';assert sha(scope)=='95ddd9b21a3650f0a5efd941bcae67b3708fff7cb81524b9cec3e3fbfb2b1be1';r=json.loads(scope.read_bytes());assert r['status']=='CURRENT_JOINT_HOST_FIELD_GEOMETRIC_INCREMENTAL_SCOPE_WITH_EXACT_WITNESS_SUPPLEMENT_PASS_NATIVE_OPEN'
source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=K.C.inventory(raw);identity=K.A.N.SourceNets(raw)
opfile=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/full-sparse-operation.pkl';assert sha(opfile)==r['sparse_operation_SHA256'];d=pickle.loads(opfile.read_bytes());deleted={};adds={};locked=[];operations=[]
for t in d['removed_original_tracks']:
 uid=t['uuid'];ch=iv[3][uid];p=K.A.G.parse(uid,ch,{})
 assert(p['kind'],p['net'],p['layer'],p['w'],list(p['a']),list(p['b']))==('segment',K.L.norm(t['net']),t['layer'],t['w'],list(t['a']),list(t['b']))
 deleted[uid]=ch
 if re.search(rb'\(locked\s+yes\)',ch):locked.append(uid)
assert len(deleted)==6 and len(d['new_tracks'])==13 and len(d['new_vias'])==4
fmt=lambda x:format(x,'.9f').rstrip('0').rstrip('.')
locknet={K.L.norm(t['net'])for t in d['removed_original_tracks']if t['uuid']in locked}
for t in d['new_tracks']:
 uid=t['uuid'];assert uid not in iv[3]and uid not in adds and t['w']==.2
 net=identity.raw(K.L.norm(t['net']));lock='\t\t(locked yes)\n'if K.L.norm(net)in locknet else''
 ch=('\t(segment\n\t\t(start '+fmt(t['a'][0])+' '+fmt(t['a'][1])+')\n\t\t(end '+fmt(t['b'][0])+' '+fmt(t['b'][1])+')\n\t\t(width .2)\n\t\t(layer "'+t['layer']+'")\n'+lock+'\t\t(net "'+net+'")\n\t\t(uuid "'+uid+'")\n\t)\n').encode();p=K.A.G.parse(uid,ch,{})
 assert(p['net'],p['layer'],p['w'],list(p['a']),list(p['b']))==(K.L.norm(net),t['layer'],.2,list(t['a']),list(t['b']));adds[uid]=ch
for v in d['new_vias']:
 uid=v['uuid'];assert uid not in iv[3]and uid not in adds and(v['d'],v['drill'])==(.5,.2);net=identity.raw(K.L.norm(v['net']))
 ch=('\t(via\n\t\t(at '+fmt(v['x'])+' '+fmt(v['y'])+')\n\t\t(size .5)\n\t\t(drill .2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "'+net+'")\n\t\t(uuid "'+uid+'")\n\t)\n').encode();p=K.A.G.parse(uid,ch,{})
 assert(p['kind'],p['net'],p['d'],p['drill'],list(p['at']))==('via',K.L.norm(net),.5,.2,[v['x'],v['y']]);assert not any(token in ch for token in(b'remove_unused_layers',b'keep_end_layers',b'zone_layer_connections'));adds[uid]=ch
identity.assert_chunks(adds)
hp=H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';assert sha(hp)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402';host=pickle.loads(hp.read_bytes());fpbefore=Path(host['exact_FP_before_file']);fpafter=Path(host['exact_FP_after_file']);assert sha(fpbefore)==host['exact_FP_before_sha256']and sha(fpafter)==host['exact_FP_after_sha256'];assert iv[3][host['FP_UUID']]==fpbefore.read_bytes()
for action,chunks in(('remove',deleted),('add',adds)):
 for uid,ch in chunks.items():
  p=OUT/(action+'-'+uid+'.native-chunk');p.write_bytes(ch);operations.append({'action':action,'uuid':uid,'kind':K.C.pcbtext.chunk_kind(ch),'file':str(p.resolve()),'SHA256':sha(p),'locked_yes':bool(re.search(rb'\(locked\s+yes\)',ch))})
for name,p in [('before',fpbefore),('after',fpafter)]:
 copy=OUT/('R10007-'+name+'.native-footprint-chunk');copy.write_bytes(p.read_bytes())
operations.append({'action':'replace_footprint_root_pose_only','uuid':host['FP_UUID'],'ref':'R10007','before_file':str((OUT/'R10007-before.native-footprint-chunk').resolve()),'before_SHA256':sha(fpbefore),'after_file':str((OUT/'R10007-after.native-footprint-chunk').resolve()),'after_SHA256':sha(fpafter),'target_root_mm_deg':host['target_root_mm_deg'],'all_other_local_AST_exact':True,'native_pose_attestation':'R237 actual B pad masks; final current both bodies/source R260/R261'})
ledger=OUT/'exact-native-discrete-and-pose-operation.json';ledger.write_text(json.dumps(operations,indent=1)+'\n')
result={'status':'EXACT_NATIVE_JOINT_CU_POSE_PATCH_FROZEN_OWNED_ROLE_INTEGER_REPLAY_AND_API_OPEN','scope_receipt_SHA256':sha(scope),'model_SHA256':r['model_SHA256'],'source_native_SHA256':sha(source),'operation_ledger_SHA256':sha(ledger),'new_tracks':13,'new_ordinary_vias':4,'original_track_deletes':6,'all_deleted_source_native_chunks_bound_exact':True,'locked_original_track_UUIDs':locked,'replacement_net_locking_policy':'every replacement segment on a deleted locked net remains locked; no unrelated old flags changed','new_via_all6_default_then_actual_afterfill_required':True,'original_CLOCK_UUID_retained_without_new_chunk':'06f5b2a7-dc39-4a5d-9309-5badd13a2347','FP_root_pose_replacements':1,'two_NEW_FG_intended_planes_and_foreign_negative_cutters':'OPEN separate exact native integer emitter/replay; no stale whole-model overlay','native_API_old_masks_all_source_DRCorigin_current_SI':'OPEN','native_jobs':0,'PCB_emitted':False,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R263_NATIVE_CU_PACKET',sha(OUT/'receipt.json'),'LOCKED_OLD',locked,flush=True)
