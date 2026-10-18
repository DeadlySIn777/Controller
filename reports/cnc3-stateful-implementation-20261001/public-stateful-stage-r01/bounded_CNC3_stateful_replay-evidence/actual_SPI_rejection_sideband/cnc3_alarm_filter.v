`timescale 1ns/1ps
// Frozen 500-core-tick sampling, four agreeing samples: 30..40us at50MHz,
// plus actual three-stage input synchronization. Raw current-flow polarity.
module cnc3_alarm_filter(input wire clk,input wire rst_n,input wire[11:0] raw,
 output reg[11:0] level,output reg valid);
 reg[11:0] s0,s1,s2,candidate;
 reg[8:0] sample_age;reg[2:0] samples_seen;
 reg[1:0] stable[0:11];integer i;
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   s0<=0;s1<=0;s2<=0;candidate<=0;level<=0;sample_age<=0;samples_seen<=0;valid<=0;
   for(i=0;i<12;i=i+1)stable[i]<=0;
  end else begin
   s0<=raw;s1<=s0;s2<=s1;
   if(sample_age==499)begin
    sample_age<=0;
    if(samples_seen<4)samples_seen<=samples_seen+1'b1;
    if(samples_seen==3)valid<=1;
    for(i=0;i<12;i=i+1)begin
     if(s2[i]==level[i])stable[i]<=0;
     else if(s2[i]!=candidate[i])begin candidate[i]<=s2[i];stable[i]<=1;end
     else if(stable[i]==3)begin level[i]<=s2[i];stable[i]<=0;end
     else stable[i]<=stable[i]+1'b1;
    end
   end else sample_age<=sample_age+1'b1;
  end
 end
endmodule
