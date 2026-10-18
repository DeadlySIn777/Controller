"""Execute the mapped bank against installed Efinix primitive simulation models."""
import hashlib
import json
from pathlib import Path
import subprocess
import psutil
H=Path(__file__).resolve().parent
ROOT=H.parent.parent
OUT=H/'efinity-bram-postmap-behavior-r1'
TB='''`timescale 1ns/1ps
module postmap_bank_tb;
 reg clk=0,we=1;reg[4:0]wa=0,ra=0;reg[159:0]wd=0;
 wire[159:0]a,b;integer n,w,r,checks=0,seed=32'h5b341711;
 cnc3_event_bank_original refbank(clk,we,wa,ra,wd,a);
 cnc3_event_bank mapped(clk,we,wa,ra,wd,b);
 task tick;begin #5;clk=1;#1;if(a!==b)$fatal(1,"mapped bank mismatch check=%0d expected=%h actual=%h",checks,a,b);
  checks=checks+1;#4;clk=0;end endtask
 task data;begin wd={$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};end endtask
 initial begin
  // Fully write every entry with collision forwarding before unknown-memory reads.
  for(n=0;n<32;n=n+1)begin wa=n;ra=n;data;tick;end
  for(w=0;w<32;w=w+1)for(r=0;r<32;r=r+1)begin wa=w;ra=r;data;we=0;tick;we=1;tick;we=0;tick;end
  for(n=0;n<32768;n=n+1)begin wa=$random(seed);ra=$random(seed);we=$random(seed);data;tick;end
  $display("NATIVE_POSTMAP_BANK_PASS checks=%0d",checks);$finish;
 end
endmodule
'''


def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()


def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')


def main():
    assert not OUT.exists();OUT.mkdir()
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    mapped=H/'efinity-memory-inference-r1/registered-bypass/outflow/cnc3_event_bank.map.v'
    original=ROOT/'gateware/v3/runtime/cnc3_event_bank.v'
    modelroot=Path('C:/Efinity/2026.1/sim_models/verilog')
    models=[modelroot/x for x in ('efx_lut4.v','efx_ff.v','efx_gbufce.v','efx_ram_5k.v')]
    (OUT/'original.v').write_text(original.read_text().replace('module cnc3_event_bank(','module cnc3_event_bank_original('))
    (OUT/'postmap_bank_tb.sv').write_text(TB)
    pins={str(p):sha(p) for p in [Path(__file__),original,mapped,*models]}
    runs=[]
    for name,args in [('compile',['iverilog','-g2012','-s','postmap_bank_tb','-o',linux(OUT/'postmap.vvp'),linux(OUT/'original.v'),linux(mapped),linux(OUT/'postmap_bank_tb.sv'),*map(linux,models)]),
                      ('execute',['vvp',linux(OUT/'postmap.vvp')])]:
        p=subprocess.run(['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        log=OUT/(name+'.log');log.write_bytes(p.stdout)
        runs.append({'name':name,'exit':p.returncode,'log_SHA256':sha(log)})
        assert p.returncode==0,name+' failed; raw output retained'
    assert all(sha(p)==v for p,v in pins.items())
    record={'status':'MAPPED_BANK_VENDOR_PRIMITIVE_FUNCTIONAL_SIMULATION_PASS','checks':35872,
        'mapped_design':'one 32x160 registered-bypass candidate bank, actual Efinity map output',
        'scope':'known initialized entries, binary controls, zero-delay functional models; no postroute timing or physical measurements',
        'canonical_RTL_unchanged':True,'input_SHA256':pins,'executions':runs,'adopted':False,'manufacturing_ready':False}
    assert 'checks=35872' in (OUT/'execute.log').read_text()
    (OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':record['status'],'checks':record['checks']}))


if __name__=='__main__':main()
