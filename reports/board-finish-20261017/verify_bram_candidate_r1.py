"""Differential memory and frozen existing SIM2 regression of an isolated candidate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import psutil
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
ROOT=H.parent.parent
OUT=H/'efinity-bram-behavior-r1'
TB='''`timescale 1ns/1ps
module bank_equivalence_tb;
 reg clk=0,we=0;reg[4:0]wa=0,ra=0;reg[159:0]wd=0;
 wire[159:0]a,b;integer n,w,r,checks=0,seed=32'h1910cafe;
 cnc3_event_bank_original refbank(clk,we,wa,ra,wd,a);
 cnc3_event_bank candidate(clk,we,wa,ra,wd,b);
 task tick;begin #5;clk=1;#1;if(a!==b)$fatal(1,"bank mismatch at check %0d",checks);
  checks=checks+1;#4;clk=0;end endtask
 task data;begin wd={$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};end endtask
 initial begin
  tick;
  // Every ordered read/write address pair, with and without writes, includes all collisions.
  for(w=0;w<32;w=w+1)for(r=0;r<32;r=r+1)begin wa=w;ra=r;data;we=0;tick;we=1;tick;we=0;tick;end
  for(n=0;n<32768;n=n+1)begin wa=$random(seed);ra=$random(seed);we=$random(seed);data;tick;end
  // Four-state procedural-if behavior, unknown addresses/data and unwritten startup.
  we=1'bx;wa=ra;data;tick;we=1'bz;tick;
  we=1;wa=5'bxxxxx;tick;we=0;ra=5'bxxxxx;tick;
  wa=7;ra=7;we=1;wd={160{1'bx}};tick;we=0;tick;
  $display("BANK_EQUIVALENCE_PASS checks=%0d",checks);$finish;
 end
endmodule
'''


def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()


def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')


def main():
    assert not OUT.exists();OUT.mkdir()
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    candidate=H/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v'
    canonical=ROOT/'gateware/v3/runtime/cnc3_event_bank.v'
    candidate_sha=sha(candidate);canonical_sha=sha(canonical)
    assert candidate_sha=='6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841'
    (OUT/'original.v').write_text(canonical.read_text().replace('module cnc3_event_bank(','module cnc3_event_bank_original('))
    shutil.copyfile(candidate,OUT/'candidate.v');(OUT/'bank_equivalence_tb.sv').write_text(TB)
    runs=[]
    def execute(name,args):
        p=subprocess.run(['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
        log=OUT/(name+'.log');log.write_bytes(p.stdout);runs.append({'name':name,'exit':p.returncode,'log_SHA256':sha(log)})
        assert p.returncode==0, name+' failed; raw log retained'
    execute('bank-compile',['iverilog','-g2012','-s','bank_equivalence_tb','-o',linux(OUT/'bank.vvp'),linux(OUT/'original.v'),linux(OUT/'candidate.v'),linux(OUT/'bank_equivalence_tb.sv')])
    execute('bank-execute',['vvp',linux(OUT/'bank.vvp')])
    original_runner=ROOT/'gateware/v3/runtime/tests/run_runtime.py'
    text=original_runner.read_text().replace('ROOT=Path(__file__).resolve().parents[4]','ROOT=Path('+repr(str(ROOT))+')')
    marker=' for p in sources:shutil.copyfile(p,inputs/p.name)'
    assert text.count(marker)==1
    overlay=marker+'\n shutil.copyfile(Path('+repr(str(candidate))+'),inputs/"cnc3_event_bank.v")'
    text=text.replace(marker,overlay)
    # Confine actual Linux children too; affinity on wsl.exe alone is insufficient.
    marker='  r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)'
    assert text.count(marker)==1
    text=text.replace(marker,'  argv=argv[:4]+["taskset","-c","16,17"]+argv[4:]\n  r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)')
    runner=OUT/'run_isolated_runtime.py';runner.write_text(text)
    with (OUT/'runtime-runner-console.log').open('w') as log:
        p=subprocess.run([sys.executable,str(runner),'--out',str(OUT/'full-runtime')],stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    native=json.loads((OUT/'full-runtime/receipt.json').read_bytes())
    assert p.returncode==0 and native['status']=='PASS' and native['sources_unchanged']
    assert sha(candidate)==candidate_sha and sha(canonical)==canonical_sha
    record={'status':'ISOLATED_BRAM_CANDIDATE_BANK_DIFFERENTIAL_AND_EXISTING_FULL_SIM2_REGRESSION_PASS',
        'bank_runs':runs,'existing_runtime_receipt':str(OUT/'full-runtime/receipt.json'),
        'existing_runtime_receipt_SHA256':sha(OUT/'full-runtime/receipt.json'),
        'existing_runtime_checks':'see preserved individual logs; unchanged frozen tests',
        'candidate_SHA256':candidate_sha,'canonical_SHA256':canonical_sha,'canonical_RTL_unchanged':True,
        'runner_derivation':'explicit repo root, copied bank overlay and two-CPU Linux taskset; tests otherwise unchanged',
        'script_SHA256':sha(Path(__file__)),'derived_runner_SHA256':sha(runner),'original_runner_SHA256':sha(original_runner),
        'full_physical_wrapper_fit_timing':'OPEN','adopted':False,'manufacturing_ready':False}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':record['status'],'runtime_executions':len(native['executions'])}),flush=True)


if __name__=='__main__':main()
