`timescale 1ns/1ps
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
