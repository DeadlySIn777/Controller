"""Compile copied SIM2 sources and execute disconnected SPI regression."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);a.add_argument('--mutation',choices=['provider_identity','event_ack','output_application']);args=a.parse_args()
 out=(ROOT/args.out).resolve();out.mkdir(parents=True,exist_ok=False);inputs=out/'inputs';inputs.mkdir()
 sources=list((ROOT/'gateware/v3/runtime').glob('*.v'))+list((ROOT/'gateware/v3/runtime/tests').glob('*.cpp'))+list((ROOT/'gateware/v3/runtime/tests').glob('*.sv'))+[Path(__file__).resolve()]
 inventory={str(p.relative_to(ROOT)):sha(p) for p in sources}
 for p in sources:shutil.copyfile(p,inputs/p.name)
 shutil.copyfile(Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261017\\efinity-memory-inference-r1\\registered-bypass\\cnc3_event_bank.v'),inputs/"cnc3_event_bank.v")
 shutil.copyfile(Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261017/release-review/event-dispatch-r1/cnc3_runtime_events.v'),inputs/'cnc3_runtime_events.v')
 if args.mutation:
  mutations={
   'provider_identity':('cnc3_runtime_provider.v',"provider_tag==32'h53494d32", "1'b1"),
   'event_ack':('cnc3_runtime_events.v','ack==delivered_sequence && ack==event_head[159:152]',"1'b1"),
   'output_application':('cnc3_runtime_sim.v',"?dout_image:16'd0", "?(dout_image&16'hfffd):16'd0"),
  }
  name,old,new=mutations[args.mutation];p=inputs/name;s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new))
 receipt={'started_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':inventory,'physical_authority':False,'production_ready':False,'hardware_accessed':False,'executions':[]}
 def execute(name,argv):
  argv=argv[:4]+["taskset","-c","16,17"]+argv[4:]
  r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
  log=out/(name+'.log');log.write_bytes(r.stdout)
  receipt['executions'].append({'name':name,'argv':argv,'exit':r.returncode,'log_sha256':sha(log)})
  if r.returncode:raise RuntimeError(f'{name} failed: {log}')
 try:
  execute('verilate',['wsl.exe','-d','GarciaMechBuilder','--','verilator','--cc','--compiler','clang','-Wno-fatal','--top-module','cnc3_runtime_sim','--Mdir',linux(out/'obj'),*map(linux,sorted(inputs.glob('*.v')))])
  execute('compile',['wsl.exe','-d','GarciaMechBuilder','--','clang++','-std=c++17','-O1','-pthread','-I/usr/share/verilator/include','-I/usr/share/verilator/include/vltstd','-I'+linux(out/'obj'),linux(inputs/'runtime_suite.cpp'),*map(linux,sorted((out/'obj').glob('*.cpp'))),'/usr/share/verilator/include/verilated.cpp','/usr/share/verilator/include/verilated_threads.cpp','-o',linux(out/'runtime_suite')])
  execute('execute',['wsl.exe','-d','GarciaMechBuilder','--',linux(out/'runtime_suite')])
  if args.mutation:raise RuntimeError('MUTATION_SURVIVED')
  for module,bench in (('events','events'),('provider','provider'),('events','events_storage')):
   execute(bench+'-compile',['wsl.exe','-d','GarciaMechBuilder','--','iverilog','-g2012','-s',bench+'_tb','-o',linux(out/(bench+'.vvp')),linux(inputs/('cnc3_runtime_'+module+'.v')),linux(inputs/'cnc3_event_bank.v'),linux(inputs/(bench+'_tb.sv'))])
   execute(bench+'-execute',['wsl.exe','-d','GarciaMechBuilder','--','vvp',linux(out/(bench+'.vvp'))])
  execute('default-verilate',['wsl.exe','-d','GarciaMechBuilder','--','verilator','--cc','--compiler','clang','-Wno-fatal','--top-module','cnc3_runtime','--Mdir',linux(out/'default_obj'),*map(linux,sorted(inputs.glob('*.v')))])
  execute('default-compile',['wsl.exe','-d','GarciaMechBuilder','--','clang++','-std=c++17','-O1','-pthread','-I/usr/share/verilator/include','-I/usr/share/verilator/include/vltstd','-I'+linux(out/'default_obj'),linux(inputs/'default_guard.cpp'),*map(linux,sorted((out/'default_obj').glob('*.cpp'))),'/usr/share/verilator/include/verilated.cpp','/usr/share/verilator/include/verilated_threads.cpp','-o',linux(out/'default_guard')])
  execute('default-execute',['wsl.exe','-d','GarciaMechBuilder','--',linux(out/'default_guard')])
  receipt['status']='PASS'
 except Exception as e:
  receipt['status']='FAIL';receipt['error']=repr(e)
  if args.mutation and receipt['executions'][-1]['name']=='execute' and receipt['executions'][-1]['exit']!=0:
   marker={'provider_identity':'wrong provider identity rejected','event_ack':'wrong acknowledgment cannot pop','output_application':'actual applied sixteen DO feedback'}[args.mutation]
   if marker in (out/'execute.log').read_text():
    receipt['status']='PASS';receipt['mutation_detected']=args.mutation;receipt['expected_failure']=marker
 finally:
  receipt['sources_unchanged']=all(sha(ROOT/p)==h for p,h in inventory.items())
  receipt['completed_utc']=datetime.now(timezone.utc).isoformat()
  receipt['copied_input_sha256']={p.name:sha(p) for p in inputs.iterdir() if p.is_file()}
  (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(receipt,indent=2));return 0 if receipt['status']=='PASS' and receipt['sources_unchanged'] else 1
if __name__=='__main__':raise SystemExit(main())
