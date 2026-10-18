`timescale 1ns/1ps
module postmap_bank_tb;
 reg clk,we;reg[4:0]wa,ra;reg[159:0]wd;
 wire[159:0]a,b;integer n,w,r,checks=0,seed=32'h5b341711;
 cnc3_event_bank_original refbank(clk,we,wa,ra,wd,a);
 cnc3_event_bank mapped(clk,we,wa,ra,wd,b);
 task tick;begin #5;clk=1;#1;if(a!==b)$fatal(1,"mapped bank mismatch check=%0d expected=%h actual=%h",checks,a,b);
  checks=checks+1;#4;clk=0;end endtask
 task data;begin wd={$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};end endtask
 initial begin
  #1;clk=0;we=1;wa=0;ra=0;wd=0;
  // Fully write every entry with collision forwarding before unknown-memory reads.
  for(n=0;n<32;n=n+1)begin wa=n;ra=n;data;tick;end
  for(w=0;w<32;w=w+1)for(r=0;r<32;r=r+1)begin wa=w;ra=r;data;we=0;tick;we=1;tick;we=0;tick;end
  for(n=0;n<32768;n=n+1)begin wa=$random(seed);ra=$random(seed);we=$random(seed);data;tick;end
  $display("NATIVE_POSTMAP_BANK_PASS checks=%0d",checks);$finish;
 end
endmodule
