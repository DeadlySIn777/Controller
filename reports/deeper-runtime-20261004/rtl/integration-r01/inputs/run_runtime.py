"""Compile copied SIM2 sources and execute disconnected SPI regression."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args()
 out=(ROOT/args.out).resolve();out.mkdir(parents=True,exist_ok=False);inputs=out/'inputs';inputs.mkdir()
 sources=list((ROOT/'gateware/v3/runtime').glob('*.v'))+[Path(__file__).resolve(),ROOT/'gateware/v3/runtime/tests/runtime_suite.cpp']
 inventory={str(p.relative_to(ROOT)):sha(p) for p in sources}
 for p in sources:shutil.copyfile(p,inputs/p.name)
 receipt={'started_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':inventory,'physical_authority':False,'production_ready':False,'hardware_accessed':False,'executions':[]}
 def execute(name,argv):
  r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
  log=out/(name+'.log');log.write_bytes(r.stdout)
  receipt['executions'].append({'name':name,'argv':argv,'exit':r.returncode,'log_sha256':sha(log)})
  if r.returncode:raise RuntimeError(f'{name} failed: {log}')
 try:
  execute('compile',['wsl.exe','-d','GarciaMechBuilder','--','verilator','--cc','--exe','--build','-j','2','--compiler','clang','-Wno-fatal','--top-module','cnc3_runtime_sim','--Mdir',linux(out/'obj'),*map(linux,sorted(inputs.glob('*.v'))),linux(inputs/'runtime_suite.cpp')])
  execute('execute',['wsl.exe','-d','GarciaMechBuilder','--',linux(out/'obj/Vcnc3_runtime_sim')])
  receipt['status']='PASS'
 except Exception as e:
  receipt['status']='FAIL';receipt['error']=repr(e)
 finally:
  receipt['sources_unchanged']=all(sha(ROOT/p)==h for p,h in inventory.items())
  receipt['completed_utc']=datetime.now(timezone.utc).isoformat()
  (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(receipt,indent=2));return 0 if receipt['status']=='PASS' and receipt['sources_unchanged'] else 1
if __name__=='__main__':raise SystemExit(main())
