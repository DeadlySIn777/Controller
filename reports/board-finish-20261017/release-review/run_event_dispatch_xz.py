"""Target explicit seven-producer X/Z payload forwarding, independent old/new."""
from pathlib import Path
import subprocess, hashlib, json
H=Path(__file__).resolve().parent
OUT=H/'event-dispatch-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    source=(H/'event_dispatch_diff_tb.sv').read_text()
    prefix=source.split(' initial begin\n')[0].replace('module event_dispatch_diff_tb;', 'module event_dispatch_xz_tb;')
    prefix=prefix.replace("288'hf123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789", "{9{32'h12345678}}")
    tail=''' initial begin
  reset;
  step_counts={12{24'hz0x123}};encoder_counts={4{24'hx12z45}};index_counts={4{24'hz123x5}};
  index_request=15;probe_request=3;arm_commit=1;tick;arm_commit=0;
  probe_raw=3;tick;tick;
  index_pulse=15;fault_word=32'h80000001;tick;
  if(dut.accepted_valid!==7'b1111111 || dut.write_enable!==8'h7f)$fatal(1,"seven explicit X/Z producers absent");
  if(dut.write_data[23:0]!==24'hz0x123)$fatal(1,"probe capture Z/X payload was not preserved");
  index_pulse=0;fault_word=0;tick;tick;
  if(nh[23:0]!==24'hz0x123)$fatal(1,"observable head Z/X payload was not preserved");
  cmd_snapshot=1;tick;cmd_snapshot=0;cmd_complete=1;tick;cmd_complete=0;ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;
  if(dut.count!==6)$fatal(1,"delivered X/Z-payload head did not pop exactly once");
  // Unknown controls retain the original Verilog if semantics.
  provider_ready=1'bx;index_pulse=4'bx111;fault_word=32'hxxxxxxxx;arm_commit=1'bx;tick;
  provider_ready=1;arm_commit=0;index_pulse=0;fault_word=0;clear=1;tick;clear=0;tick;
  $display("EVENT_DISPATCH_EXPLICIT_XZ_PASS cycles=%0d seven_producers=7 observable_head_ZX=PASS unknown_control_if=PASS",cycles);$finish;
 end
endmodule
'''
    bench=OUT/'explicit_xz_tb.sv';bench.write_text(prefix+tail)
    paths=[OUT/'original_diff.v',OUT/'candidate_diff.v',H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v',bench]
    commands=[('xz-compile',['iverilog','-g2012','-s','event_dispatch_xz_tb','-o',linux(OUT/'explicit_xz.vvp'),*map(linux,paths)]),('xz-execute',['vvp',linux(OUT/'explicit_xz.vvp')])]
    runs=[]
    for name,args in commands:
        argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
        run=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
        log=OUT/(name+'.log');log.write_bytes(run.stdout)
        runs.append({'name':name,'argv':argv,'exit':run.returncode,'log_SHA256':sha(log)})
        print(run.stdout.decode(errors='replace'),end='')
        if run.returncode:break
    record={'status':'EXPLICIT_XZ_OLD_NEW_DISPATCH_PASS' if all(r['exit']==0 for r in runs) and len(runs)==2 else 'FAIL','executions':runs,'input_SHA256':{str(p):sha(p) for p in [Path(__file__),*paths]},'adopted':False}
    (OUT/'explicit-xz-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    return 0 if record['status']!='FAIL' else 1
if __name__=='__main__':raise SystemExit(main())
