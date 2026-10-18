"""Freeze the exact six-track/one-via/resistor-pose nominee; no board adoption."""
import hashlib,json,pickle,re,copy,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
OUT=H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r234';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rp=H/'R10007-joint-B-F-real-source-and-ordinary-return-route-nomination-r233/receipt.json';assert sha(rp)=='04a007e57d15456796e3d7b5ad1a18d2417e08649de24124e3d5a6ddf6685afe';r=json.loads(rp.read_bytes());n=r['nominee'];assert n and len(n['new_tracks'])==6
source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=K.C.inventory(raw);identity=K.A.N.SourceNets(raw)
fmt=lambda x:format(x,'.9f').rstrip('0').rstrip('.')
adds={};tracks=[]
for old in n['new_tracks']:
 t={**old,'net':identity.raw(old['net'])};assert t['uuid']not in iv[3] and t['w']==.2 and t['a']!=t['b']
 ch=('\t(segment\n\t\t(start '+fmt(t['a'][0])+' '+fmt(t['a'][1])+')\n\t\t(end '+fmt(t['b'][0])+' '+fmt(t['b'][1])+')\n\t\t(width .2)\n\t\t(layer "'+t['layer']+'")\n\t\t(net "'+t['net']+'")\n\t\t(uuid "'+t['uuid']+'")\n\t)\n').encode()
 p=K.A.G.parse(t['uuid'],ch,{});assert(p['net'],p['layer'],p['a'],p['b'],p['w'])==(K.L.norm(t['net']),t['layer'],t['a'],t['b'],t['w']);adds[t['uuid']]=ch;tracks.append(t)
 port=n['ordinary_HOST_port'];uid,ch=SERIAL.serial_via(identity,K.L.norm(tracks[1]['net']),port['signal_xy_mm']);assert uid not in iv[3] and uid not in adds;adds[uid]=ch
 assert_not_used=(b'remove_unused_layers',b'keep_end_layers',b'zone_layer_connections');assert not any(x in ch for x in assert_not_used)
 identity.assert_chunks(adds)
 via={'uuid':uid,'net':identity.raw(tracks[1]['net']),'x':port['signal_xy_mm'][0],'y':port['signal_xy_mm'][1],'d':.5,'drill':.2,'span':list(K.LAYERS),'flashed':list(K.LAYERS),'prospective_not_native':True,'mask_provenance':'NEW_ORDINARY_REQUIRES_FRESH_NATIVE_ALL6'}
 fps=[(u,c)for u,c in iv[3].items()if K.C.pcbtext.chunk_kind(c)=='footprint'and re.search(rb'\(property\s+"Reference"\s+"R10007"',c)];assert len(fps)==1;fpuid,before=fps[0];oldast=K.Q.parse(before.decode());oldat=K.Q.child(oldast,'at');oldpose=[float(x)for x in oldat[1:]]
 if len(oldpose)==2:oldpose.append(0.)
 assert oldpose[:2]==[218.,145.217];newpose=[207.5,141.717,(oldpose[2]+180)%360];match=re.search(rb'\(at\s+[^()]+\)',before);assert match and K.Q.parse(match.group().decode())==oldat
 after=before[:match.start()]+('(at '+' '.join(fmt(x)for x in newpose)+')').encode()+before[match.end():];newast=K.Q.parse(after.decode());revert=copy.deepcopy(newast);K.Q.child(revert,'at')[:]=oldat;assert revert==oldast
 fbp=OUT/'R10007.exact-before-footprint-chunk';fap=OUT/'R10007.exact-rigid-after-footprint-chunk';fbp.write_bytes(before);fap.write_bytes(after);ops=[]
 for u,c in adds.items():
  p=OUT/(u+'.native-chunk');p.write_bytes(c);ops.append({'action':'add','uuid':u,'kind':K.C.pcbtext.chunk_kind(c),'file':str(p.resolve()),'sha256':sha(p)})
 (OUT/'exact-operation-ledger.json').write_text(json.dumps(ops,indent=1)+'\n')
 packet={'tracks':tracks,'vias':[via],'original_native_Cu_deletes':[],'FP_UUID':fpuid,'ref':'R10007','original_root_mm_deg':oldpose,'target_root_mm_deg':newpose,'model_rigid_pose_degrees_dx_dy':n['pose']['pose'],'exact_FP_before_file':str(fbp.resolve()),'exact_FP_before_sha256':sha(fbp),'exact_FP_after_file':str(fap.resolve()),'exact_FP_after_sha256':sha(fap),'source_terminal_UUID':r['existing_actual_HOST_source_terminal_UUID'],'source_terminal_all6_native_masks_unchanged':True,'source_terminal_exact_own_cap_mm':.575,'new_signal_exact_own_cap_mm':.525,'existing_ground_return_UUID':port['existing_return_UUID'],'signal_return_distance_mm':port['actual_pair_mm'],'native_pose_masks_actual_source_contact_reference_joint_FG_gates':'OPEN; root native pose collector must be extended only for this frozen separately attested operation','nine_FG_CLK_FLT_unadopted_body_withdrawal_only_FOR_NOMINATION':r['withdrawn_only_nine_unadopted_tracks'],'manufacturing_ready':False}
 pp=OUT/'exact-discrete-and-rigid-pose-packet.pkl';pp.write_bytes(pickle.dumps(packet,protocol=5))
 receipt={'verdict':'EXACT_NATIVE_R10007_HOST_PACKET_FROZEN_POSE_MASK_SOURCE_REFERENCE_JOINT_NATIVE_GATES_OPEN','nominee_sha256':sha(rp),'native_source_sha256':sha(source),'model_before_sha256':r['model_sha256'],'packet_sha256':sha(pp),'operation_ledger_sha256':sha(OUT/'exact-operation-ledger.json'),'new_tracks':6,'new_ordinary_vias':1,'native_Cu_deletes':0,'FP_replacements':1,'all_native_local_FP_AST_fields_source_raw_net_and_pad_UUIDs_exact':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False}
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R234_EXACT_PACKET',sha(pp),'RECEIPT',sha(OUT/'receipt.json'),flush=True)
