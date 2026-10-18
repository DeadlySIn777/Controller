`timescale 1ns/1ps
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
