from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def run(out,name,args):
 r=subprocess.run(args,text=True,capture_output=True,encoding='utf8',errors='replace',timeout=300)
 (out/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf8',newline='\n')
 if r.returncode:raise RuntimeError(name+' failed: '+(r.stdout+r.stderr)[-3000:])
 return r.stdout
def main(out):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True)
 prior=HERE/'inputs/workspace/gateware/rtl/cnc_stepgen.v'
 source=HERE/'cnc3_stepgen_runtime.v'
 before={p.as_posix():sha(p) for p in (prior,source)}
 for p in (prior,source):shutil.copyfile(p,out/p.name)
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,enable=0,stop=0;reg signed[31:0] rates[0:11];
wire[11:0] oldstep,newstep,olddir,newdir,oldfault,newfault,quiet;
wire signed[31:0] oldcount[0:11],newcount[0:11];
integer cycles=0,checks=0,k;reg[31:0] seed=32'hc3dd512;
genvar i;generate for(i=0;i<12;i=i+1)begin:g
cnc_stepgen original(clk,rst,enable,rates[i],oldstep[i],olddir[i],oldcount[i],oldfault[i]);
cnc3_stepgen_runtime actual(clk,rst,enable,stop,rates[i],16'd100,16'd100,16'd100,16'd100,newstep[i],newdir[i],newcount[i],newfault[i],quiet[i]);
end endgenerate
initial begin
for(k=0;k<12;k=k+1)rates[k]=0;
repeat(4)@(negedge clk);rst=1;enable=1;
for(cycles=0;cycles<200000;cycles=cycles+1)begin
@(negedge clk);
if(cycles%997==0)begin
for(k=0;k<12;k=k+1)begin
seed=(seed<<1) ^ (seed[31]?32'h04c11db7:0);
rates[k]=(seed[0]?-1:1)*(seed &32'h00ffffff);
end end
if(cycles%15997==0)enable=0;
else if(cycles%15997==5)enable=1;
if(cycles==99871)rst=0;
if(cycles==99873)rst=1;
@(posedge clk);#1;
for(k=0;k<12;k=k+1)begin
if(oldstep[k]!==newstep[k] || olddir[k]!==newdir[k] || oldcount[k]!==newcount[k] || oldfault[k]!==newfault[k])$fatal(1,"exact original mismatch c%0d ch%0d",cycles,k);
checks=checks+1;
end
end
$display("RUNTIME_ORIGINAL_EQUIVALENCE_PASS cycles=%0d channels=12 checks=%0d",cycles,checks);
$finish;
end
endmodule
'''
 (out/'equivalence.sv').write_text(tb,encoding='utf8',newline='\n')
 dynamic=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,en=0,stop=0;reg signed[31:0] rate=0;
reg[15:0] high=100,low=173,setup=137,hold=300;
wire step,dir,fault,quiet;wire signed[31:0] count;
cnc3_stepgen_runtime d(clk,rst,en,stop,rate,high,low,setup,hold,step,dir,count,fault,quiet);
integer cycles=0,last_rise=-1,last_fall=-1,last_dir=-1,rises=0,checks=0;
reg oldstep=0,olddir=0;reg signed[31:0] stopcount;
always@(posedge clk)begin
#1;cycles=cycles+1;
if(en)begin
if(step&&!oldstep)begin
if(last_fall>=0 && cycles-last_fall<low)$fatal(1,"SPACE violation");
if(last_dir>=0 && cycles-last_dir<setup)$fatal(1,"SETUP violation");
if(stop)$fatal(1,"new STEP while clean stop");
last_rise=cycles;rises=rises+1;
end
if(!step&&oldstep)begin
if(cycles-last_rise!=high)$fatal(1,"HIGH width %0d",cycles-last_rise);
last_fall=cycles;
end
if(dir!=olddir)begin
if(last_rise>=0 && cycles-last_rise<hold)$fatal(1,"HOLD violation");
last_dir=cycles;
end
if(fault)$fatal(1,"unexpected timing fault");checks=checks+1;
end
oldstep=step;olddir=dir;
end
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
initial begin
ticks(4);rst=1;en=1;rate=32'h00400000;
ticks(15000);rate=-32'sh00400000;
ticks(15000);wait(step);@(negedge clk);stopcount=count;stop=1;
wait(quiet);@(negedge clk);
if(count!=stopcount)$fatal(1,"clean stop emitted extra count");
if(last_fall<0 || cycles-last_fall<low || cycles-last_rise<hold)$fatal(1,"drain incomplete");
ticks(50);en=0;ticks(3);high=1023;low=1023;setup=1023;hold=1023;
last_rise=-1;last_fall=-1;last_dir=-1;stop=0;en=1;rate=32'h00100000;
ticks(15000);rate=-32'sh00100000;ticks(15000);
if(rises<30)$fatal(1,"insufficient actual pulses");
$display("RUNTIME_DYNAMIC_DRAIN_PASS checks=%0d rises=%0d",checks,rises);$finish;
end
endmodule
'''
 (out/'dynamic.sv').write_text(dynamic,encoding='utf8',newline='\n')
 cmd=f"cd '{unix(out)}' && iverilog -g2012 -s tb -o equivalence.vvp cnc_stepgen.v cnc3_stepgen_runtime.v equivalence.sv && vvp equivalence.vvp && iverilog -g2012 -s tb -o dynamic.vvp cnc3_stepgen_runtime.v dynamic.sv && vvp dynamic.vvp"
 try:
  log=run(out,'actual-iverilog',['wsl','-d','GarciaMechBuilder','--','sh','-c',cmd])
  if 'RUNTIME_ORIGINAL_EQUIVALENCE_PASS' not in log or 'RUNTIME_DYNAMIC_DRAIN_PASS' not in log:raise RuntimeError('Missing actual pass markers')
  status='PASS'
 except Exception as e:status='FAIL';log=str(e)
 unchanged=all(sha(Path(p))==h for p,h in before.items())
 receipt={'status':status if unchanged else 'FAIL','source_hashes':before,'inputs_unchanged':unchanged,'evidence_type':'actual Icarus RTL simulation','original_algorithm_equivalence':True,'twelve_simultaneous_generator_instances':True,'dynamic_timing_clean_stop':True,'CNC3_frame_stateful_or_Hardware_qualification':False,'outputs':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()},'detail':log[-1200:]}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
 print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);raise SystemExit(main(ap.parse_args().out.resolve()))
