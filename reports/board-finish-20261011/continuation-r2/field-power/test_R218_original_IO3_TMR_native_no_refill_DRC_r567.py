"""Pinned existing test-only1 native no-refill DRC boundary diagnostic."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,hashlib,subprocess,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
N=ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'
OUT=H/'R218-original-IO3-TMR-native-no-refill-boundary-DRC-r567'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();board=N/'copy/board.kicad_pcb';assert sha(board)=='6befbca6dcac6bfe812dc8be04069701338f8ef95159faf9a5cb4a114395d55e'
 wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');cli=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
 files=[Path(__file__),wrapper,cli,N/'receipt.json',N/'scoped-fill/receipt.json',H/'original-IO3-native-TMR-boundary-outline-cache-fill-provenance-r565/receipt.json']+[p for p in (N/'copy').rglob('*')if p.is_file()]
 pins={str(x.resolve()):sha(x)for x in files}
 command=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str((OUT/'drc.json').resolve()),'board.kicad_pcb']
 record={'phase':'NATIVE_NO_REFILL_DRC_RUNNING_TEST_ONLY1','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':command,'pins':pins,'cwd':str((N/'copy').resolve()),'original_zone_UUID':'54921f4b-0308-4821-9549-ff9360bf05ca','exact_TMR_AREA_UUID':'db0285ed-ad42-400f-9df4-32278be33f57','no_refill_option':True,'no_schematic_parity_request':True,'scope':'items_not_allowed boundary semantics on exact original5492/nativeAREA; all other stale cached-net results retained without full-board DRC acceptance','existing_test_slot':'test-only1','new_heavy_slots':0,'no_native_board_save_no_input_edit':True,'R563_closed_boundary_LineString_FAIL_is_preserved_regardless_of_DRC_result':True,'adopted':False}
 put(OUT/'inputs.json',record);put(OUT/'status.json',record);print(record['phase'],flush=True)
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
 with (OUT/'drc.log').open('w',encoding='utf-8')as log:r=subprocess.run(command,cwd=N/'copy',env=env,stdout=log,stderr=subprocess.STDOUT)
 changed=[p for p,v in pins.items()if sha(p)!=v];assert not changed,changed
 report=json.loads((OUT/'drc.json').read_bytes());rows=report.get('violations',[]);target=[]
 for x in rows:
  text=json.dumps(x)
  if x.get('type')=='items_not_allowed' or record['original_zone_UUID']in text or record['exact_TMR_AREA_UUID']in text:target.append(x)
 put(OUT/'all-items-not-allowed-and-target-UUID-report-rows.json',target)
 result={'status':'NATIVE_NO_REFILL_BOUNDARY_DIAGNOSTIC_COMPLETE_NOT_FULL_DRC_ACCEPTANCE','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cli_exit_code':r.returncode,'inputs_SHA256':sha(OUT/'inputs.json'),'DRC_report_SHA256':sha(OUT/'drc.json'),'full_log_SHA256':sha(OUT/'drc.log'),'all_report_counts':{key:len(report.get(key,[]))for key in('violations','unconnected_items','schematic_parity')},'all_items_not_allowed_and_target_rows':target,'target_original5492_explicit_native_violation':any(record['original_zone_UUID']in json.dumps(x)for x in rows),'original_and_all_input_bytes_exact':True,'no_additional_native_refill_requested':True,'unrefilled_cache_does_not_establish_full_native_source_contacts_or_DRCSUCCESS':True,'R563_closed_boundary_LineString_FAIL_is_NOT_overridden':True,'adopted':False,'manufacturing_ready':False}
 put(OUT/'receipt.json',result);put(OUT/'status.json',result);print('R567',sha(OUT/'receipt.json'),'exit',r.returncode,'target5492',result['target_original5492_explicit_native_violation'],flush=True)
if __name__=='__main__':main()
