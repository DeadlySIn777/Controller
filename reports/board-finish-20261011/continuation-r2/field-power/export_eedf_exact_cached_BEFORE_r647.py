"""Authorized existing shared KiCad-slot no-refill native parent export."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import datetime,hashlib,json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
OUT=H/'eedf-original-parent-exact-cached-native-BEFORE-dump-r647'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 board=ROOT/'sbc-native-contract-r1/copy/board.kicad_pcb';masks=ROOT/'R155-known-reference-native-diagnostic-r157/measure/original-parent-retained-via-actual-flash-masks.json'
 helper=H/'native_eedf_exact_cached_BEFORE_dump_r647.py';wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavy.sh');api=Path('C:/Program Files/KiCad/10.0/bin/python.exe')
 files=[Path(__file__),helper,wrapper,api,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),masks,Path('Z:/pcb-runs/claude-finish/tools/fix/plane_dump.py')]
 pins={str(f.resolve()):sha(f)for f in files}
 assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 cmd=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(api),str(helper),str(board),str(masks),str(OUT/'native-cached')]
 put(OUT/'inputs.json',{'pins':pins,'command':cmd,'slot':'EXISTING_SHARED_KICAD_MAIN1','new_slots':0,'native_refill':False,'save':False,'adopted':False,'evidence_class':'CACHED_NATIVE_BEFORE'})
 put(OUT/'status.json',{'phase':'WAITING_EXISTING_SHARED_SLOT_THEN_NO_REFILL_EXPORT','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env['PYTHONUTF8']='1'
 with(OUT/'native.log').open('w',encoding='utf-8')as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert all(sha(f)==v for f,v in pins.items()),'Frozen source/helper/project changed'
 receipt=OUT/'native-cached/receipt.json';assert r.returncode==0 and receipt.exists(),r.returncode
 native=json.loads(receipt.read_bytes());assert not native['errors']and native['no_refill']and native['all_original_input_bytes_unchanged']
 final={'verdict':'PASS_CACHED_NATIVE_EEDF_BEFORE_EXPORT_NO_REFILL_NO_SAVE','input_manifest_SHA256':sha(OUT/'inputs.json'),'native_receipt_SHA256':sha(receipt),'geometry_SHA256':native['geometry_SHA256'],'actual_via_geometry_and_flashes_SHA256':native['actual_via_geometry_and_flashes_SHA256'],'all_original_input_bytes_unchanged':True,'refilled_evidence':False,'new_slots':0,'adopted':False,'elapsed_seconds':time.monotonic()-st}
 put(OUT/'receipt.json',final);put(OUT/'status.json',final);print('R647_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
