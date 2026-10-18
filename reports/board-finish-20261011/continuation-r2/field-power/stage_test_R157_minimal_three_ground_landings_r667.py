"""Authorized existing test-only1 clone; append only23 explicit local zones."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT))
import native_pose_signal_contract as NC
OUT=H/'R157-minimal-local-three-ground-landings-selected-native-r667'
P=ROOT/'R155-known-reference-native-diagnostic-r157'
R=H/'R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();rr=R/'receipt.json';assert sha(rr)=='f804da80445f226e7e10cfd9660b35bf6ba7dd3b935b2dbb7a542c32769cbabd';r=json.loads(rr.read_bytes());assert r['accepted_nominee_count']==23 and r['guard_error_count']==0;rows=json.loads((R/'native-exact-local-zone-chunk-rows.json').read_bytes());assert len(rows)==23
 parent=P/'measure/copy/board.kicad_pcb';assert sha(parent)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38';old=NC.C.inventory(parent.read_bytes());newchunks=[]
 for row in rows:
  f=Path(row['chunk_file']);assert sha(f)==row['chunk_SHA256'];ch=f.read_bytes();assert NC.C.pcbtext.chunk_uuid(ch)==row['uuid']and row['uuid']not in old[3];assert NC.C.pcbtext.chunk_kind(ch)=='zone';newchunks.append(ch)
 data=old[0]+b''.join(old[1])+b''.join(newchunks)+old[2];new=NC.C.inventory(data);assert new[0]==old[0]and new[2]==old[2]and new[4]==old[4];assert all(new[3][uid]==ch for uid,ch in old[3].items());assert set(new[3])==set(old[3])|{r['uuid']for r in rows}
 cp=OUT/'copy';cp.mkdir();board=cp/'board.kicad_pcb';board.write_bytes(data)
 for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
 spec={'candidate_sha256':sha(board),'zones':[{k:v for k,v in row.items()if k in('uuid','raw_net','layer','rings_IU','declared_native_settings')}for row in rows]};put(OUT/'expected-23-local-zone-native-API.json',spec)
 expected=json.loads((P/'all-copper-expected.json').read_bytes());assert expected['board_sha256']==sha(parent);expected.update(board_sha256=sha(board),board_path=str(board));put(OUT/'all-copper-expected.json',expected)
 api=Path('C:/Program Files/KiCad/10.0/bin/python.exe');wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');check=ROOT/'native_declared_selected_zone_contract_r2.py';helper=H/'native_R157_selected_three_ground_landing_fill_r667.py';masks=P/'measure/actual-full-refill-via-flashes.json'
 files=[Path(__file__),rr,R/'native-exact-local-zone-chunk-rows.json',parent,parent.with_suffix('.kicad_pro'),parent.with_suffix('.kicad_dru'),wrapper,api,check,helper,masks,OUT/'expected-23-local-zone-native-API.json',OUT/'all-copper-expected.json']+[Path(x['chunk_file'])for x in rows]+list(cp.iterdir());pins={str(f.resolve()):sha(f)for f in files}
 prefix=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(api)];cmds=[prefix+[str(check),str(OUT/'expected-23-local-zone-native-API.json'),str(board),str(OUT/'native-23-local-zone-API.json')],prefix+[str(helper),str(board),str(OUT/'all-copper-expected.json'),str(masks),str(OUT/'selected-ground-fill')]]
 record={'phase':'EXACT23_LOCAL_API_THEN_SELECTED_THREE_GROUND_FILL_RUNNING','parent_SHA256':sha(parent),'candidate_SHA256':sha(board),'pins':pins,'commands':cmds,'old_native_Cu_holes_outlines_profiles_source_rules_ALL_exact':True,'existing_missing_layer_masks_NOT_FORCED':True,'slot':'EXISTING_TEST_ONLY1','new_slots':0,'new_zone_count':23,'all_raw_R157_mask_reference_current_TMR_and_zone_overlap_FAILs_retained':True,'no_full_refill_save_or_adoption':True};put(OUT/'inputs.json',record);put(OUT/'status.json',record)
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env['PYTHONUTF8']='1'
 for i,cmd in enumerate(cmds):
  with(OUT/('native-'+str(i)+'.log')).open('w',encoding='utf-8')as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
  assert run.returncode==0,(i,run.returncode);assert all(sha(f)==v for f,v in pins.items())
  if i==0:assert not json.loads((OUT/'native-23-local-zone-API.json').read_bytes())['errors']
 put(OUT/'receipt.json',{'status':'MINIMAL23_LOCAL_LANDINGS_NATIVE_EXACT_API_SELECTED_THREE_GROUND_FILL_COMPLETE_ACTUAL_PROOF_OPEN','candidate_SHA256':sha(board),'parent_SHA256':sha(parent),'input_manifest_SHA256':sha(OUT/'inputs.json'),'native_API_SHA256':sha(OUT/'native-23-local-zone-API.json'),'native_selected_fill_receipt_SHA256':sha(OUT/'selected-ground-fill/receipt.json'),'all_original_bytes_except_appended23_zones_exact':True,'required_old_mask_source_contacts_reference_current_minfeature_barrel_SI_thermal':'OPEN_FRESH_ACTUAL_REVIEW','no_native_save_full_refill_forced_flash_or_adoption':True,'elapsed_seconds':time.monotonic()-st});put(OUT/'status.json',json.loads((OUT/'receipt.json').read_bytes()));print('R667_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
