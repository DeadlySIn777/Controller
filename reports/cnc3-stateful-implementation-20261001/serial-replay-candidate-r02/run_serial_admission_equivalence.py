import os
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess
HERE=Path(__file__).resolve().parent
FROZEN=HERE/'inputs/diagnostic-parallel'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True)
 original=FROZEN/'cnc3_motion_state.v';parallel=original.read_text()
 fragment=parallel[parallel.index(' wire[11:0] update_channel_valid;'):parallel.index(' wire update_admissible=')]
 comparison='module parallel_guard(input[1407:0] request_frame,input[191:0] pulse_ticks,space_ticks,output wire[11:0] good);\n'+fragment+'\nassign good=update_channel_valid;\nendmodule\n'
 (out/'parallel_guard.v').write_text(comparison,encoding='utf8',newline='\n')
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,start=0,valid=0;reg[3:0] channel=0;reg[31:0] rate=0;
reg[191:0] high,low;reg[1407:0] frame=0;
wire good,busy,poisoned;wire[11:0] mask,parallel_good;
cnc3_rate_admission_serial d(clk,rst,start,valid,channel,rate,high,low,good,busy,poisoned,mask);
parallel_guard p(frame,high,low,parallel_good);
integer checks=0,cases=0,i,j,profile,sample,profile_case;reg[31:0] cap,seed=32'h72ab3419,magnitude;
reg[63:0] product;reg expected;integer h,l;
task tick(input integer n);begin repeat(n)@(negedge clk);end endtask
task check(input bit pass,input string text);begin checks=checks+1;if(!pass)$fatal(1,"SERIAL %s good%h busy%h poison%h mask%h",text,good,busy,poisoned,mask);end endtask
task fresh;
begin start=1;valid=0;tick(1);start=0;#1;check(!good&&!busy&&!poisoned&&mask==0,"new transaction clears prior admission");end endtask
task word(input[3:0] ch,input[31:0] value,input integer settle);
begin channel=ch;rate=value;valid=1;tick(1);valid=0;tick(settle);end endtask
task full_frame;
begin
fresh();expected=1;
for(i=0;i<12;i=i+1)begin
 magnitude=frame[1279-32*i -:32];if(magnitude[31])magnitude=~magnitude+32'd1;
 h=high[191-16*i -:16];l=low[191-16*i -:16];product={32'd0,magnitude}*(h+l+1);
 expected=expected&&(magnitude<=32'h01000000)&&(h>=100&&h<=1023)&&(l>=100&&l<=1023)&&(product<=64'd4294967296);
 word(i,frame[1279-32*i -:32],12);
 if(i<11)check(!good,"no incomplete frame can authorize");
end
#1;check(good==expected,"independent64bit math equivalence");
check(mask==parallel_good&&good==(&parallel_good),"exact frozen parallel RTL equivalence");
check(!busy&&!poisoned,"complete orderly words finish without optimism");cases=cases+1;
end endtask
task good_frame;
begin for(j=0;j<12;j=j+1)begin high[191-16*j -:16]=100;low[191-16*j -:16]=100;end frame=0;full_frame();check(good,"known good frame");end endtask
initial begin
tick(3);rst=1;tick(2);
for(profile=0;profile<5;profile=profile+1)begin
case(profile)
0:begin h=100;l=100;cap=16777216;end
1:begin h=100;l=155;cap=16777216;end
2:begin h=1023;l=1023;cap=2098176;end
3:begin h=101;l=900;cap=4286394;end
4:begin h=1023;l=100;cap=3821145;end
endcase
for(j=0;j<12;j=j+1)begin high[191-16*j -:16]=h;low[191-16*j -:16]=l;frame[1279-32*j -:32]=j%2?-cap:cap;end
full_frame();
for(sample=0;sample<12;sample=sample+1)begin
for(profile_case=0;profile_case<6;profile_case=profile_case+1)begin
frame=0;
case(profile_case)
0:frame[1279-32*sample -:32]=cap;
1:frame[1279-32*sample -:32]=-cap;
2:frame[1279-32*sample -:32]=cap+1;
3:frame[1279-32*sample -:32]=-(cap+1);
4:frame[1279-32*sample -:32]=32'h80000000;
5:frame[1279-32*sample -:32]=0;
endcase
full_frame();
end end
end
// Deterministic independently varying timing/rates in all channels.
for(sample=0;sample<200;sample=sample+1)begin
for(j=0;j<12;j=j+1)begin
seed=seed^(seed<<13);seed=seed^(seed>>17);seed=seed^(seed<<5);
h=100+(seed%924);l=100+((seed>>10)%924);high[191-16*j -:16]=h;low[191-16*j -:16]=l;
cap=64'd4294967296/(h+l+1);if(cap>16777216)cap=16777216;
case((seed>>20)%6)
0:frame[1279-32*j -:32]=cap;
1:frame[1279-32*j -:32]=-cap;
2:frame[1279-32*j -:32]=cap+1;
3:frame[1279-32*j -:32]=-(cap+1);
4:frame[1279-32*j -:32]=32'h80000000;
5:frame[1279-32*j -:32]=seed%cap;
endcase
end full_frame();end
good_frame();fresh();word(0,0,12);word(1,0,12);check(!good,"truncated two-word frame stays invalid");
fresh();word(0,0,12);word(0,0,12);check(poisoned&&!good,"duplicate cannot reuse previous channel mask");
fresh();word(1,0,12);check(poisoned&&!good,"missing first word rejects reordered frame");
fresh();word(15,0,12);check(poisoned&&!good,"out of range channel rejected");
fresh();word(0,0,0);check(busy&&!good,"pending compute is not ready");word(1,0,12);check(poisoned&&!good,"busy overlap rejects instead of replacing pending word");
fresh();word(0,0,0);tick(10);word(1,0,12);check(poisoned&&!good,"last compute tick overlap rejected");
good_frame();fresh();word(0,32'h01000001,12);for(j=1;j<12;j=j+1)word(j,0,12);check(!good&&mask!=12'hfff,"bad next frame cannot inherit good previous mask");good_frame();
fresh();word(0,0,0);start=1;valid=1;channel=1;rate=0;tick(1);start=0;valid=0;tick(12);check(!busy&&!poisoned&&mask==0&&!good,"transaction restart dominates simultaneous word and pending compute");
good_frame();rst=0;tick(2);check(!good&&!busy&&mask==0,"reset destroys completed admission metadata");rst=1;tick(2);fresh();word(0,0,0);rst=0;tick(2);rst=1;tick(12);check(!good&&!busy&&mask==0,"reset during pending compute discards metadata");good_frame();
$display("SERIAL_EQUIVALENCE_PASS checks=%0d exact_frame_cases=%0d",checks,cases);$finish;
end
endmodule
'''
 (out/'serial.sv').write_text(tb,encoding='utf8',newline='\n')
 source=HERE/'cnc3_rate_admission_serial.v';before={str(source):sha(source),str(original):sha(original)}
 text=source.read_text();rows=[]
 variants=[('baseline',None,None,None),('stale-channel-mask','busy<=0;poisoned<=0;channel_good<=0;expected_channel<=0;','busy<=0;poisoned<=0;channel_good<=channel_good;expected_channel<=0;','new transaction clears prior admission'),('lost-channel-order','word_channel!=expected_channel',"1'b0",'duplicate cannot reuse previous channel mask'),('lost-busy-rejection','if(busy || word_channel>=12',"if(1'b0 || word_channel>=12",'busy overlap rejects instead of replacing pending word')]
 for name,a,b,message in variants:
  folder=out/name;folder.mkdir();shutil.copyfile(out/'serial.sv',folder/'serial.sv');shutil.copyfile(out/'parallel_guard.v',folder/'parallel_guard.v')
  if name=='stale-channel-mask':
   head,tail=text.split('end else if(transaction_start)begin',1)
   body=head+'end else if(transaction_start)begin'+tail.replace(a,b,1)
  else:body=text if a is None else text.replace(a,b)
  if a is not None and a not in text:raise RuntimeError('Mutation anchor missing')
  (folder/source.name).write_text(body,encoding='utf8',newline='\n')
  cmd=f"cd '{unix(folder)}' && iverilog -g2012 -s tb -o serial.vvp cnc3_rate_admission_serial.v parallel_guard.v serial.sv && vvp serial.vvp"
  r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh','-c',cmd],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=120)
  log=r.stdout+r.stderr;(folder/'actual.log').write_text(log,encoding='utf8',newline='\n')
  passed=(r.returncode==0 and 'SERIAL_EQUIVALENCE_PASS' in log) if a is None else r.returncode!=0 and 'FATAL:' in log and message in log
  rows.append({'name':name,'passed':passed,'expected_runtime_assertion':message,'compiled_source_sha256':sha(folder/source.name),'log_sha256':sha(folder/'actual.log'),'detail':log[-1400:]})
 unchanged=all(sha(Path(q))==h for q,h in before.items())
 receipt={'status':'PASS' if unchanged and all(x['passed'] for x in rows) else 'FAIL','source_hashes':before,'source_unchanged':unchanged,'parallel_exact_fragment_sha256':hashlib.sha256(fragment.encode()).hexdigest(),'controls':rows,'evidence_type':'actual Icarus sequential versus exact immutable parallel RTL plus independent64bit arithmetic, real scheduling attacks and compiled mutations','actual_SPI_physical_HAL_vendor_qualification':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);raise SystemExit(main(ap.parse_args().out.resolve()))
