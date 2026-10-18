import os
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('Fresh evidence required')
 out.mkdir(parents=True)
 sources=[HERE/'cnc3_encoder_runtime.v',HERE/'cnc3_alarm_filter.v',HERE/'inputs/workspace/gateware/rtl/cnc_encoder.v']
 hashes={q.as_posix():sha(q) for q in sources}
 for q in sources:shutil.copyfile(q,out/q.name)
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;reg rst=0;
reg[3:0] a=0,b=0,z=0;reg[3:0] filter=0;reg clear=0;
wire signed[31:0] oldcount[0:3],newcount[0:3],oldindex[0:3],newindex[0:3];
wire[3:0] oldseen,newseen,oldbad,newbad,pulse;
reg[11:0] raw=0;wire[11:0] level;wire valid;
cnc3_alarm_filter alarms(clk,rst,raw,level,valid);
genvar g;generate for(g=0;g<4;g=g+1)begin:counters
cnc_encoder original(clk,rst,a[g],b[g],z[g],oldcount[g],oldindex[g],oldseen[g],oldbad[g]);
cnc3_encoder_runtime actual(clk,rst,a[g],b[g],z[g],filter,clear,newcount[g],newindex[g],newseen[g],newbad[g],pulse[g]);
end endgenerate
integer j,k,checks=0,cycle=0,edgecycle,startcycle;reg[31:0] seed=32'hAB434E43;
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
task check(input bit good,input string name);begin checks=checks+1;if(!good)$fatal(1,"%s",name);end endtask
always@(posedge clk)cycle=cycle+1;
initial begin
ticks(4);rst=1;
for(j=0;j<20000;j=j+1)begin
@(negedge clk);if(j%17==0)begin seed=(seed<<1)^(seed[31]?32'h04c11db7:0);a=seed[3:0];b=seed[7:4];z=seed[11:8];end
@(posedge clk);#1;
for(k=0;k<4;k=k+1)check(oldcount[k]==newcount[k] && oldindex[k]==newindex[k] && oldseen[k]==newseen[k] && oldbad[k]==newbad[k],"exact original encoder filter0 equivalence");
end
rst=0;a=0;b=0;z=0;raw=0;ticks(4);rst=1;filter=8;ticks(2200);
check(valid && level==0,"four real startup alarm samples");
// A pulse below the configured8 sampled ticks must never change counter.
b=15;ticks(4);b=0;
for(j=0;j<30;j=j+1)begin ticks(1);for(k=0;k<4;k=k+1)check(newcount[k]==0,"filtered short AB pulse emitted no count");end
b=15;ticks(20);a=15;ticks(20);b=0;ticks(20);a=0;ticks(20);
for(k=0;k<4;k=k+1)check(newcount[k]==4,"four true filtered quadrature counters");
z=15;ticks(20);for(k=0;k<4;k=k+1)check(newindex[k]==4 && newseen[k],"real filtered index observation");
z=0;a=15;b=15;ticks(20);check(newbad==15,"real illegal simultaneous AB transition");
clear=1;ticks(1);clear=0;ticks(2);
for(k=0;k<4;k=k+1)check(!newbad[k] && !newseen[k] && newcount[k]==4,"SYNC observations clear without position reset");
// Short alarm pulse does not survive four samples.
raw=12'hfff;ticks(900);raw=0;ticks(2200);check(level==0,"alarm short pulse rejected");
ticks(17);startcycle=cycle;raw=12'hfff;wait(level==12'hfff);edgecycle=cycle;
check(edgecycle-startcycle>=1500 && edgecycle-startcycle<=2003,"actual four-sample30..40us plus synchronizer");
raw=0;startcycle=cycle;wait(level==0);edgecycle=cycle;
check(edgecycle-startcycle>=1500 && edgecycle-startcycle<=2003,"both alarm polarities filtered");
$display("ACTUAL_FILTERS_PASS checks=%0d original_encoder_instances=4",checks);$finish;
end
endmodule
'''
 (out/'filters.sv').write_text(tb,encoding='utf8',newline='\n')
 cmd=f"cd '{unix(out)}' && iverilog -g2012 -s tb -o filters.vvp cnc3_encoder_runtime.v cnc3_alarm_filter.v cnc_encoder.v filters.sv && vvp filters.vvp"
 r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh','-c',cmd],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
 log=r.stdout+r.stderr;(out/'actual-iverilog.log').write_text(log,encoding='utf8',newline='\n')
 unchanged=all(sha(Path(q))==h for q,h in hashes.items())
 receipt={'status':'PASS' if r.returncode==0 and 'ACTUAL_FILTERS_PASS' in log and unchanged else 'FAIL','input_hashes':hashes,'source_unchanged':unchanged,'evidence_type':'actual compiled unchanged original encoder equivalence and runtime/alarm filter RTL','physical_metastability_signal_integrity_qualification':False,'index_one_shot_event_ring_implemented':False,'detail':log[-3000:]}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);raise SystemExit(main(ap.parse_args().out.resolve()))
