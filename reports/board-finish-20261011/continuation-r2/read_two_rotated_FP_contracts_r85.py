"""Use the existing test-only KiCad slot for exact read-only collector metadata."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
out=H/'two-rotated-native-FP-masks-r85';assert not out.exists();out.mkdir();rows=[]
for folder,pin,filename in[('field-monitor-native-R9026-rotation-r68','3fbf5fa8c80a3bb9e03328108b677777482ae884786aef4d5ea2c09612a0baa4','R9026.rotated-footprint-chunk'),('field-R11054-native-fault-pin-rotation-r75','8c1576328972121a3fbc391c63088dc43dc6ce651153d079fe62e62243bb780c',None)]:
 d=H/folder;rp=d/'receipt.json';assert sha(rp)==pin;r=json.loads(rp.read_bytes());board=d/'copy/board.kicad_pcb';assert sha(board)==r['candidate_sha256'];spec=d/'spec.json'
 if filename is None:fp=H/'field-power/R11054-static-and-AUX-bleed-native-owned-recipe-r208/R11054.rotated-about-fault-pin-footprint-chunk';assert sha(fp)==r['exact_replacement_FP_chunk_sha256']
 else:fp=d/filename;assert sha(fp)==r['replacement_chunk_sha256']
 rows.append({'board_file':str(board.resolve()),'candidate_sha256':sha(board),'pose_spec_file':str(spec.resolve()),'pose_spec_sha256':sha(spec),'replacement_FP_chunk_file':str(fp.resolve()),'replacement_FP_chunk_sha256':sha(fp),'native_rotation_receipt_file':str(rp.resolve()),'native_rotation_receipt_sha256':sha(rp)})
spec=out/'spec.json';put(spec,{'footprints':rows});helper=H/'native_two_rotated_FP_masks_r85.py';cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper),str(spec),str(out/'native-metadata.json')];put(out/'invocation.json',{'command':cmd,'existing_test_only_slot':1,'new_heavy_slots':0,'no_original_or_candidate_save':True});env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
with(out/'native.log').open('w')as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
rp=out/'native-metadata.json';r=json.loads(rp.read_bytes())if rp.exists()else{};ok=run.returncode==0 and r.get('verdict')=='PASS_TWO_EXACT_NATIVE_ROTATED_FP_MASKS_ANGLES_AND_FIELDS';put(out/'receipt.json',{'verdict':'PASS_READ_ONLY_TWO_ROTATED_NATIVE_FP_COLLECTOR_METADATA'if ok else'FAIL_NATIVE_ROTATED_FP_METADATA','exit_code':run.returncode,'spec_sha256':sha(spec),'helper_sha256':sha(helper),'native_metadata_sha256':sha(rp)if rp.exists()else None,'all_original_FP_local_AST_bytes_bound_by_R68_R75':True,'collector_extension_full_geometry_native_Cu_fill_DRC_current':'OPEN','adopted':False});print('R85_FP_METADATA',ok,sha(out/'receipt.json'),flush=True)
