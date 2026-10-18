`timescale 1ns/1ps
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
