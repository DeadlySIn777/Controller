"""Native-load a disposable one-footprint rotation; never refill, adopt or edit a source."""
import ast,hashlib,json,os,pickle,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H));sys.path.insert(0,str(H/'field-power'))
import native_pose_signal_contract as NC
import verify_source as V
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def main():
 out=H/'field-monitor-native-R9026-rotation-r67';assert not out.exists();out.mkdir()
 parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 recipe=H/'field-monitor-R9026-rotation-source-termination-r66';rr=json.loads((recipe/'receipt.json').read_bytes());assert rr['verdict']=='ROTATED_MONITOR_SIGNAL_AND_LOCAL_GROUND_PATHS_GEOMETRY_NOMINATION'and sha(recipe/'owned-delta.pkl')==rr['delta_sha256'];d=pickle.loads((recipe/'owned-delta.pkl').read_bytes())
 inv=NC.C.inventory(parent.read_bytes());fp=next(c for uid,c in inv[3].items()if NC.C.pcbtext.chunk_kind(c)=='footprint'and b'(property "Reference" "R9026"'in c);uid=NC.C.pcbtext.chunk_uuid(fp);tree=V.parse(fp.decode());at=V.child(tree,'at');prior=[float(x)for x in at[1:]]
 if len(prior)==2:prior.append(0.)
 assert prior[:2]==d['unchanged_FP_center_mm']==[347.26,59.5];target=[prior[0],prior[1],(prior[2]+180)%360];text=fp.decode();needle='(at '+' '.join(at[1:])+')';assert text.count(needle)>=1
 root_start=text.index(needle);replacement='(at 347.26 59.5 '+str(target[2])+')';new=text[:root_start]+replacement+text[root_start+len(needle):];after=V.parse(new)
 assert [q for q in tree if not(isinstance(q,list)and q and q[0]=='at')]==[q for q in after if not(isinstance(q,list)and q and q[0]=='at')],'Every other native pad/text/source/courtyard/local AST field must remain exact'
 oldfile=out/'R9026.original-footprint-chunk';newfile=out/'R9026.rotated-footprint-chunk';oldfile.write_bytes(fp);newfile.write_text(new)
 data=inv[0]+b''.join(new.encode()if NC.C.pcbtext.chunk_uuid(c)==uid else c for c in inv[1])+inv[2];ci=NC.C.inventory(data);assert ci[0]==inv[0]and ci[2]==inv[2]and all(ci[3][k]==v for k,v in inv[3].items()if k!=uid)
 copy=out/'copy';copy.mkdir();board=copy/'board.kicad_pcb';board.write_bytes(data)
 for ext in ('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
 expected={p['uuid']:{'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'at_IU':[round(p['x']*1e6),round(p['y']*1e6)]}for p in d['new_R9026_pads']};spec=out/'spec.json';put(spec,{'candidate_sha256':sha(board),'native_footprint_uuid':uid,'ref':'R9026','prior_pose':prior,'target_pose':target,'expected_pads':expected,'all_unchanged_parent_entities_exact':True,'single_exact_root_at_changed':True,'full_native_refill_source_and_monitor_current_reference_gate':'OPEN'})
 helper=H/'native_monitor_rotation_attestation_r67.py';cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper),str(spec),str(board),str(out/'native-attestation.json')];put(out/'invocation.json',{'command':cmd,'existing_slot':'test-only1','new_heavy_slots':0,'no_refill_or_original_save':True})
 with(out/'native.log').open('w')as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 result=json.loads((out/'native-attestation.json').read_bytes())if(out/'native-attestation.json').exists()else{}
 put(out/'receipt.json',{'verdict':'PASS_NATIVE_SCOPED_R9026_ROTATION_ONLY_FULL_MONITOR_GATES_OPEN'if run.returncode==0 and result.get('verdict')=='PASS_NATIVE_EXACT_ROTATED_R9026_PAD_POSE'else'FAIL_NATIVE_R9026_ROTATION_ATTESTATION','candidate_sha256':sha(board),'parent_sha256':sha(parent),'footprint_uuid':uid,'native_attestation':result,'replacement_chunk_sha256':sha(newfile),'original_chunk_sha256':sha(oldfile),'new_ground_trace_and_via_not_staged_in_this_diagnostic':True,'adopted':False,'whole_source_no_loss_full_refill_DRC_reference_threshold_current':'OPEN'})
 print('R67_NATIVE_ROTATION',run.returncode,result.get('verdict'),flush=True)
if __name__=='__main__':main()
