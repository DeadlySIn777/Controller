`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,start=0,valid=0;reg[3:0] channel=0;reg[31:0] rate=0;
reg[191:0] high,low;reg[1407:0] frame=0;
wire good,busy,poisoned;wire[11:0] mask,parallel_good;
cnc3_rate_admission_serial d(clk,rst,start,valid,channel,rate,high,low,good,busy,poisoned,mask);
parallel_guard p(frame,high,low,parallel_good);
integer checks=0,cases=0,i,j,profile,sample;reg[31:0] cap,seed=32'h72ab3419,magnitude;
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
integer profile_case;
endmodule
