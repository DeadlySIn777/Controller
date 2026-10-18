"""Freeze exact sparse bytes only; no board/native/current acceptance."""
from pathlib import Path
import sys,json,pickle,hashlib,re,copy,uuid
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'Q0-R426-exact-native-owned-operation-r428';assert not out.exists();out.mkdir()
nomdir=H/'Q0-SENSE-In2-Q0-In3-coupled-r426';rp=nomdir/'receipt.json';assert sha(rp)=='e95a83e0dfa2c45dcbb392c693e36ae62c28846bbfc31118c68ae5711c3af272';r=json.loads(rp.read_bytes());assert all(r['results'].values());nom=pickle.loads((nomdir/'sparse-nomination.pkl').read_bytes());nt=nom['tracks'];assert len(nt)==20 and all(t['a']!=t['b']for t in nt);assert len(nom['new_vias'])==7 and len(nom['deleted_tracks'])==3
model=Path(r['input_model_file'])if'in put_model_file'in r else P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)==r['model_sha256']=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes());source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)==r['source_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';sourcebytes=source.read_bytes();iv=K.C.inventory(sourcebytes);identity=K.A.N.SourceNets(sourcebytes);adds={};deletes={};operations=[];nv=[];roles={}
for t in nt:
 ch=(nomdir/(t['uuid']+'.segment-chunk')).read_bytes();parsed=K.A.G.parse(t['uuid'],ch,{});assert(parsed['net'],parsed['layer'],parsed['a'],parsed['b'],parsed['w'])==(K.L.norm(t['net']),t['layer'],t['a'],t['b'],t['w']);assert t['uuid']not in iv[3];adds[t['uuid']]=ch
for v in nom['new_vias']:
 uid,ch=SERIAL.serial_via(identity,K.L.norm(v['net']),[v['x'],v['y']]);assert uid not in iv[3]and uid not in adds;roles[v['uuid']]=uid;nv.append({**v,'uuid':uid,'role':v['uuid'],'net':identity.raw(v['net'])});adds[uid]=ch;assert not any(x in ch for x in(b'remove_unused_layers',b'keep_end_layers',b'zone_layer_connections'))
for uid in nom['deleted_tracks']:
 ch=(nomdir/(uid+'.exact-owned-delete-chunk')).read_bytes();assert iv[3][uid]==ch and sourcebytes.count(ch)==1;deletes[uid]=ch
fps=[(uid,ch)for uid,ch in iv[3].items()if K.C.pcbtext.chunk_kind(ch)=='footprint'and re.search(rb'\(property\s+"Reference"\s+"R10016"',ch)];assert len(fps)==1;fpuid,fpbefore=fps[0];oldast=K.Q.parse(fpbefore.decode());oldat=K.Q.child(oldast,'at');assert[float(x)for x in oldat[1:3]]==[230.36,167.162];match=re.search(rb'\(at\s+[^()]+\)',fpbefore);assert match and K.Q.parse(match.group().decode())==oldat
fpafter=fpbefore[:match.start()]+b'(at 229.86 166.662'+(b' '+b' '.join(str(x).encode()for x in oldat[3:])if len(oldat)>3 else b'')+b')'+fpbefore[match.end():];newast=K.Q.parse(fpafter.decode());assert[float(x)for x in K.Q.child(newast,'at')[1:3]]==[229.86,166.662];reverted=copy.deepcopy(newast);at=K.Q.child(reverted,'at');at[:]=oldat;assert reverted==oldast;assert sourcebytes.count(fpbefore)==1
fpbp=out/'R10016.exact-before-footprint-chunk';fpap=out/'R10016.exact-translated-footprint-chunk';fpbp.write_bytes(fpbefore);fpap.write_bytes(fpafter)
for action,bank in [('remove',deletes),('add',adds)]:
 for uid,ch in sorted(bank.items()):
  p=out/(action+'-'+uid+'.native-chunk');p.write_bytes(ch);operations.append({'action':action,'uuid':uid,'chunk_kind':K.C.pcbtext.chunk_kind(ch),'exact_chunk_file':str(p),'exact_chunk_sha256':sha(p),'source_original_occurrences':sourcebytes.count(ch)if action=='remove'else 0})
identity.assert_chunks(adds);put(out/'exact-sparse-discrete-operation-ledger.json',operations);put(out/'new-ordinary-via-role-native-identity-map.json',roles)
pairrows=json.loads((nomdir/'all-five-paired-source-return-nominations.json').read_bytes());assert len(pairrows)==6 and all(.90<=x['spacing_mm']<=1.0 and x['after_local_source_contact_nomination_pass']for x in pairrows)
for row in pairrows:
 row['signal']=roles.get(row['signal'],row['signal']);row['return']=roles.get(row['return'],row['return'])
put(out/'six-exact-paired-source-return-nominations.json',pairrows)
packet={'tracks':nt,'vias':nv,'exact_deleted_track_UUIDs':nom['deleted_tracks'],'R10016_FP_UUID':fpuid,'R10016_translation_mm':[-.5,-.5],'exact_FP_before_file':str(fpbp),'exact_FP_before_sha256':sha(fpbp),'exact_FP_after_file':str(fpap),'exact_FP_after_sha256':sha(fpap),'original_SENSE_via_UUID':'5a4b7757-ae7c-470d-81fe-abcec92e0f06','original_SENSE_required_actual_annuli':['F.Cu','B.Cu'],'original_SENSE_natural_new_used_annuli':['In2.Cu'],'original_SENSE_unused_layer_flags_unchanged':True,'new_ordinary_required_native_actual_annuli':list(K.LAYERS),'raw_all_before_native_source_current_reference_failures_preserved':True}
pp=out/'exact-owned-discrete-and-pose-nomination.pkl';pp.write_bytes(pickle.dumps(packet,protocol=5))
result={'verdict':'EXACT_SPARSE_NATIVE_BYTES_FROZEN_FULL_INDEPENDENT_GATES_OPEN','R426_nomination_receipt_sha256':sha(rp),'input_current_model_file':str(model),'input_current_model_sha256':sha(model),'source_native_parent_file':str(source),'source_native_parent_sha256':sha(source),'exact_discrete_operation_file':str(out/'exact-sparse-discrete-operation-ledger.json'),'exact_discrete_operation_sha256':sha(out/'exact-sparse-discrete-operation-ledger.json'),'exact_packet_file':str(pp),'exact_packet_sha256':sha(pp),'new_track_count':20,'new_ordinary_via_count':7,'exact_original_track_deletes':3,'exact_FP_replacements':1,'all_FP_local_AST_except_global_at_exact':True,'all_new_raw_tokens_exact_no_normalization_collisions':True,'new_tracks_have_no_zero_axis':True,'ordinary7_must_native_flash_all6':True,'old_SENSE_F_B_plus_NEW_In2_must_naturally_flash_flags_unchanged':True,'all_current_source_contacts_ref_planner_current_r06_r07_native_pose_parity_fullfill_DRC_SI_and_new_pad_body':'OPEN','model_or_q_or_rules_or_board_written':False,'native_jobs':0,'adopted':False,'manufacturing_ready':False};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'packet_sha256':sha(pp),'via_roles':roles,'FP_UUID':fpuid}),flush=True)
