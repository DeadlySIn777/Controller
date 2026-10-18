"""Freeze only two source-screened short nominees, without native adoption."""
import sys,json,pickle,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;sha=N.sha
OUT=H/'short-ESD-ground-and-watchdog-exact-current-native-add-only-r310'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir()
 source=H/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb'
 assert sha(source)=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
 packet=H/'current-R753-short-logic-no-hole-surface-construction-r307/ONLY_NEW-short-surface-physical-nominees-NOT_MODEL.pkl'
 assert sha(packet)=='ad00b11785d328664c575c90a895f0495eafffdf8681851f780808d5d81fee9d'
 triage=H/'R307-short-surface-actual-native-BEFORE-source-and-width-triage-r308/triage.json';rows={r['index']:r for r in json.loads(triage.read_bytes())}
 selected=[r for r in pickle.loads(packet.read_bytes())if r['index']in(1,13)];assert len(selected)==2
 assert {r['normalized_net']for r in selected}=={'/LOGIC_GND','/watchdog_conditioning/WD_M_CWD'}
 raw=source.read_bytes();iv=K.C.inventory(raw);identity=K.A.N.SourceNets(raw);adds={};ops=[]
 fmt=lambda x:format(x,'.9f').rstrip('0').rstrip('.')
 for r in selected:
  check=rows[r['index']];assert not check['historical_table_width_deficit_requires_rejection_or_new_authoritative_local_load_IR_proof']
  assert check['raw_source_LG_full_body_reference_gap']['EMPTY']
  if r['normalized_net']=='/LOGIC_GND':assert not check['real_BEFORE_J1_same_surface_contact']['EMPTY']
  for t in r['tracks']:
   uid=t['uuid'];assert uid not in iv[3]and uid not in adds and t['w']==.2 and not t['locked'];net=identity.raw(K.L.norm(t['net']));assert net==t['net']
   chunk=('\t(segment\n\t\t(start '+fmt(t['a'][0])+' '+fmt(t['a'][1])+')\n\t\t(end '+fmt(t['b'][0])+' '+fmt(t['b'][1])+')\n\t\t(width .2)\n\t\t(layer "'+t['layer']+'")\n\t\t(net "'+net+'")\n\t\t(uuid "'+uid+'")\n\t)\n').encode()
   parsed=K.A.G.parse(uid,chunk,{})
   assert(parsed['net'],parsed['layer'],parsed['w'],list(parsed['a']),list(parsed['b']))==(K.L.norm(net),t['layer'],.2,list(t['a']),list(t['b']))
   adds[uid]=chunk;p=OUT/('add-'+uid+'.native-chunk');p.write_bytes(chunk)
   ops.append({'action':'add','UUID':uid,'kind':'segment','raw_net':net,'layer':t['layer'],'width_IU':200000,'start_IU':[int(round(v*1e6))for v in t['a']],'end_IU':[int(round(v*1e6))for v in t['b']],'locked_yes':False,'file':str(p.resolve()),'SHA256':sha(p),'basis_index':r['index']})
 identity.assert_chunks(adds);at=raw.rfind(b')');assert at>0;addition=b''.join(adds.values());candidate=raw[:at]+addition+raw[at:];after=K.C.inventory(candidate)
 assert set(after[3])==set(iv[3])|set(adds)
 assert all(after[3][u]==ch for u,ch in iv[3].items())
 assert all(after[3][u]==ch for u,ch in adds.items())
 assert candidate[:at]+candidate[at+len(addition):]==raw
 manifest=OUT/'minimal-exact-ground-watchdog-native-add-manifest.json'
 manifest.write_text(json.dumps({'baseline_file':str(source.resolve()),'baseline_SHA256':sha(source),'operations':ops,'all_unlisted_native_chunks_FP_pad_zone_profile_header_tail_exact':True,'full_matching_NATIVE_AFTER_source_oldgroups_reference_current_ESD_SI':'OPEN'},indent=1)+'\n')
 put('receipt.json',{'status':'TWO_HOST_SOURCE_SCREENED_SHORT_NOMINEES_MINIMAL_NATIVE_ADD_MANIFEST_FROZEN','baseline_SHA256':sha(source),'nominee_packet_SHA256':sha(packet),'native_manifest_SHA256':sha(manifest),'actual_BEFORE_source_width_triage_SHA256':sha(triage),'tracks_added':len(adds),'vias_added':0,'old_Cu_removed':0,'all_original_UUID_chunks_byte_exact_count':len(iv[3]),'original_header_tail_byte_exact_in_memory_replay':True,'in_memory_candidate_SHA256':hashlib.sha256(candidate).hexdigest(),'current_ground_ESD_pulse_thermal_fault_IR_and_watchdog_timing_SI':'OPEN_NO_PHYSICAL_QUALIFICATION','native_API_allCu_and_matching_FULL_AFTER_groups_masks_source_oldreferences_full_DRC':'OPEN','PCB_emitted':False,'native_jobs':0,'adopted':False})
 print('R310_NATIVE_PATCH_FROZEN',len(adds),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
