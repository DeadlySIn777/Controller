"""Attest one exact native B-side rigid pose using the existing main slot."""
import hashlib,json,pickle,shutil,subprocess,sys,os
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'R10007-exact-native-B-pose-and-pad-mask-attestation-r237';assert not OUT.exists();OUT.mkdir()
pp=H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';assert sha(pp)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402';d=pickle.loads(pp.read_bytes())
parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=K.C.inventory(parent.read_bytes());before=Path(d['exact_FP_before_file']).read_bytes();after=Path(d['exact_FP_after_file']).read_bytes();uid=d['FP_UUID'];assert iv[3][uid]==before
data=iv[0]+b''.join(after if K.C.pcbtext.chunk_uuid(c)==uid else c for c in iv[1])+iv[2];ci=K.C.inventory(data);assert ci[0]==iv[0]and ci[2]==iv[2]and all(ci[3][u]==v for u,v in iv[3].items()if u!=uid)
copydir=OUT/'copy';copydir.mkdir();board=copydir/'board.kicad_pcb';board.write_bytes(data)
for ext in ('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
mp=H/'R10007-HOST-exact-packet-current-diagnostic-r236/model.pkl';assert sha(mp)=='2f9e864a70afb766c7995ae8220c795c4aab3ed03dc279ba9ff9b2302685e057';g,h,b,q,f=pickle.loads(mp.read_bytes());expected={p['uuid']:{'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'at_IU':[round(p['x']*1e6),round(p['y']*1e6)]}for p in h['pads']if p['ref']=='R10007'};assert len(expected)==2
spec=OUT/'spec.json';spec.write_text(json.dumps({'candidate_sha256':sha(board),'native_footprint_uuid':uid,'ref':'R10007','prior_pose':d['original_root_mm_deg'],'target_pose':d['target_root_mm_deg'],'expected_pads':expected,'all_unchanged_parent_entities_exact':True,'single_exact_root_at_changed':True,'source_packet_sha256':sha(pp),'source_current_model_sha256':sha(mp)},indent=1)+'\n')
oldhelper=H/'native_monitor_rotation_attestation_r67.py';helper=OUT/'native_R10007_B_pose_read_only_attestation_r237.py';code=oldhelper.read_text().replace("assert list(layers)==['F.Cu']","assert list(layers)==['B.Cu']").replace('R9026','R10007').replace('R67','R237').replace('full_monitor_source_reference_DRC_threshold_current','full_HOST_source_reference_DRC_current_joint_FG');compile(code,str(helper),'exec');helper.write_text(code)
wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavym.sh');cmd=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper),str(spec),str(board),str(OUT/'native-attestation.json')]
(OUT/'invocation.json').write_text(json.dumps({'command':cmd,'existing_slot':'main1','new_heavy_slots':0,'native_parent_unchanged':True,'no_refill_or_save':True,'helper_before_sha256':sha(oldhelper),'helper_after_sha256':sha(helper),'wrapper_sha256':sha(wrapper)},indent=1)+'\n')
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
with(OUT/'native.log').open('w')as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';att=OUT/'native-attestation.json';result=json.loads(att.read_bytes())if att.exists()else{}
receipt={'verdict':'PASS_NATIVE_EXACT_R10007_B_RIGID_POSE_ONLY_ALL_SOURCE_REFERENCE_JOINT_NATIVE_GATES_OPEN'if run.returncode==0 and result.get('verdict')=='PASS_NATIVE_EXACT_ROTATED_R10007_PAD_POSE'else'FAIL_NATIVE_R10007_POSE','exit_code':run.returncode,'native_attestation':result,'candidate_sha256':sha(board),'parent_sha256':sha(parent),'native_attestation_sha256':sha(att)if att.exists()else None,'packet_sha256':sha(pp),'six_tracks_new_via_not_staged_in_pose_only_native_test':True,'no_refill_no_save':True,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R237_NATIVE_POSE',run.returncode,result.get('verdict'),sha(OUT/'receipt.json'),flush=True)
