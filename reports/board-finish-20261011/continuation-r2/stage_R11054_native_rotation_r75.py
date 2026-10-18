"""Attest the frozen fault-pin-preserving resistor rotation on a disposable native clone."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H));sys.path.insert(0,str(H/'field-power'))
import native_pose_signal_contract as NC
import verify_source as V
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def main():
 out=H/'field-R11054-native-fault-pin-rotation-r75';assert not out.exists();out.mkdir()
 folder=H/'field-power/R11054-static-and-AUX-bleed-native-owned-recipe-r208';recipe=folder/'receipt.json';assert sha(recipe)=='1e768077e1be6ca94c5da4d48e724f911679bb3b4454b2325aa748b343e8aa70'
 r=json.loads(recipe.read_bytes());assert r['verdict']=='EXACT_NATIVE_OWNED_RECIPE_HOST_GATES_PASS_NATIVE_CURRENT_FAULT_PENDING';rows=r['native_existing_owned_footprint_replacement_rows'];assert len(rows)==1;row=rows[0];assert row['ref']=='R11054'
 parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)==r['parent_native_board_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 old=Path(row['original_chunk_file']);new=Path(row['replacement_chunk_file']);author=Path(row['authorizing_recipe_file']);assert sha(old)==row['original_chunk_sha256']and sha(new)==row['replacement_chunk_sha256']and sha(author)==row['authorizing_recipe_sha256']
 auth=json.loads(author.read_bytes());assert auth['exact_changed_fields']==[{'kind':'root_at_only','original_tokens':['at','221','41.25','-90'],'replacement_tokens':['at','221','42.9','90']}]
 inv=NC.C.inventory(parent.read_bytes());uid=row['uuid'];assert inv[3][uid]==old.read_bytes();a=V.parse(old.read_text());b=V.parse(new.read_text());assert V.atom(a,'uuid')==V.atom(b,'uuid')==uid
 assert [q for q in a if not(isinstance(q,list)and q and q[0]=='at')]==[q for q in b if not(isinstance(q,list)and q and q[0]=='at')]
 assert [float(x)for x in V.child(a,'at')[1:]]==row['original_root_pose_mm_deg']==[221,41.25,-90];assert [float(x)for x in V.child(b,'at')[1:]]==row['replacement_root_pose_mm_deg']==[221,42.9,90]
 data=inv[0]+b''.join(new.read_bytes()if NC.C.pcbtext.chunk_uuid(q)==uid else q for q in inv[1])+inv[2];after=NC.C.inventory(data);assert after[0]==inv[0]and after[2]==inv[2]and set(after[3])==set(inv[3])and all(after[3][k]==v for k,v in inv[3].items()if k!=uid)
 copy=out/'copy';copy.mkdir();board=copy/'board.kicad_pcb';board.write_bytes(data)
 for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
 expected={q['pad_uuid']:{'ref':'R11054','pin':q['pin'],'raw_net':q['raw_net'],'at_IU':[round(v*1e6)for v in q['absolute_center_mm']]}for q in auth['absolute_pad_coordinate_ledger']};assert len(expected)==2
 spec=out/'spec.json';put(spec,{'candidate_sha256':sha(board),'native_footprint_uuid':uid,'ref':'R11054','prior_pose':row['original_root_pose_mm_deg'],'target_pose':row['replacement_root_pose_mm_deg'],'expected_pads':expected,'all_unowned_parent_native_items_exact':True,'only_one_root_at_changed':True,'pin2_FAULT_fixed_at_IU':[221000000,42075000],'new_discretes_and_plane_not_staged':True})
 source=H/'native_monitor_rotation_attestation_r67.py';helper=H/'native_R11054_rotation_attestation_r75.py';assert not helper.exists();s=source.read_text();assert s.count('PASS_NATIVE_EXACT_ROTATED_R9026_PAD_POSE')==1;s=s.replace('PASS_NATIVE_EXACT_ROTATED_R9026_PAD_POSE','PASS_NATIVE_EXACT_FAULT_PIN_FIXED_R11054_PAD_POSE').replace('R67_NATIVE_PAD_POSE_PASS','R75_NATIVE_PAD_POSE_PASS');compile(s,str(helper),'exec');helper.write_text(s)
 cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper),str(spec),str(board),str(out/'native-attestation.json')];put(out/'invocation.json',{'command':cmd,'existing_slot':'test-kicad1','new_heavy_slots':0,'no_fill_save_or_original_edit':True,'helper_derived_from_sha256':sha(source),'helper_sha256':sha(helper)})
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
 with(out/'native.log').open('w')as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
 result=json.loads((out/'native-attestation.json').read_bytes())if(out/'native-attestation.json').exists()else{};assert sha(parent)==r['parent_native_board_sha256'];ok=run.returncode==0 and result.get('verdict')=='PASS_NATIVE_EXACT_FAULT_PIN_FIXED_R11054_PAD_POSE'
 put(out/'receipt.json',{'verdict':'PASS_NATIVE_SCOPED_R11054_FAULT_PIN_FIXED_ROTATION_ONLY'if ok else'FAIL_NATIVE_R11054_FAULT_PIN_ROTATION','parent_sha256':sha(parent),'candidate_sha256':sha(board),'frozen_recipe_sha256':sha(recipe),'exact_replacement_FP_chunk_sha256':sha(new),'native_attestation':result,'native_pad_polygons_must_replace_host_nominal_mesh_before_peer_gates':True,'all_other_parent_native_bytes_exact':True,'new_discretes_via_plane_current_fault_DRC_full_native':'OPEN','adopted':False})
 print('R75_NATIVE_R11054',run.returncode,result.get('verdict'),flush=True)
if __name__=='__main__':main()
