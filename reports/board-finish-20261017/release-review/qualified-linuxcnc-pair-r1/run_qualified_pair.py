"""Run two fresh disconnected LinuxCNC integrations from a frozen report closure."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
STAGE=BASE/'source-root'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--out',required=True,type=Path,help='New exclusive output folder under reports')
 parser.add_argument('--motors',nargs='+',type=int,choices=[8,12],default=[12,8])
 args=parser.parse_args()
 assert len(args.motors)==len(set(args.motors))
 output=args.out.resolve();assert output.is_relative_to(ROOT/'reports') and output!=ROOT/'reports'
 assert not output.exists()
 preparation=json.loads((BASE/'preparation-receipt.json').read_text())
 assert all(sha(STAGE/p)==h for p,h in preparation['staged_runtime_source_SHA256'].items())
 gate=ROOT/'reports/board-finish-20261017/event-producer-fifo-r1/postmap-behavior-r3/receipt.json'
 assert gate.exists(),'Mapped event-engine qualification is pending; do not run or adopt on startup-failed evidence.'
 postmap=json.loads(gate.read_text())
 assert postmap['status']=='MAPPED_FULL_EVENT_ENGINE_VENDOR_PRIMITIVE_FUNCTIONAL_PASS'
 assert '-g2005' in postmap['executions'][0]['argv']
 output.mkdir()
 commands=[];error=None
 try:
  for motors in args.motors:
   run_out=output/f'linuxcnc-{motors}'
   cmd=[sys.executable,str(STAGE/'cnc3_runtime/run.py'),'--motors',str(motors),'--linuxcnc','--out',str(run_out)]
   with (output/f'launcher-{motors}.log').open('wb') as log:
    result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1500)
   commands.append({'motors':motors,'argv':cmd,'exit':result.returncode})
   print(json.dumps(commands[-1]),flush=True)
   assert result.returncode==0
   r=json.loads((run_out/'receipt.json').read_text())
   assert r['status']=='PASS' and r['source_inputs_unchanged'] and r['settings_preserved'] and r['installed_existing_rootfs_modules_preserved']
   assert r['scope']['actual_CNC3_C_driver'] and r['scope']['actual_serial_SPI'] and r['scope']['compiled_RTL'] and r['scope']['actual_LinuxCNC_task_trajectory']
   assert r['scope']['hardware_connections']==0 and r['scope']['physical_qualification'] is False
 except Exception as e:error=repr(e)
 unchanged=all(sha(STAGE/p)==h for p,h in preparation['staged_runtime_source_SHA256'].items())
 fixtures_preserved=all(sha(item['original'])==item['SHA256'] for files in preparation['fixture_inputs'].values() for item in files.values())
 receipt={'status':'PASS' if not error and unchanged and fixtures_preserved else 'FAIL','error':error,
  'preparation_receipt_SHA256':sha(BASE/'preparation-receipt.json'),'mapped_event_qualification_receipt_SHA256':sha(gate),
  'commands':commands,'frozen_source_closure_unchanged':unchanged,'original_fixture_settings_preserved':fixtures_preserved,
  'scope':'Actual LinuxCNC task/FREE joint planners/HAL→C driver→serial SPI→selected compiled RTL→independent virtual STEP/DIR plant;8or12active,all12fitted,disconnectedSIM2. No physical timing/commissioning or Cartesian machining qualification.',
  'production_adopted':False,'physical_authority':False,'hardware_connections':0}
 (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'status':receipt['status'],'error':error}),flush=True)
 return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
