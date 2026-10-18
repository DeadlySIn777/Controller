`timescale 1ns/1ps
// Actual transaction-scoped shared shift/add timing admission. One unsigned
//36-bit addition per tick; eleven cycles per received rate word. No divider,
//no twelve parallel multipliers, no inherited previous-frame good mask.
module cnc3_rate_admission_serial (
 input wire clk,input wire rst_n,input wire transaction_start,
 input wire word_valid,input wire[3:0] word_channel,input wire[31:0] word_rate,
 input wire[191:0] pulse_ticks,space_ticks,
 output wire frame_good,output reg busy,output reg poisoned,
 output reg[11:0] channel_good
);
 reg[3:0] expected_channel,active_channel,iteration;
 reg[10:0] multiplier;
 reg[35:0] multiplicand,accumulator;
 reg base_good;
 wire[31:0] magnitude=word_rate[31]?(~word_rate+32'd1):word_rate;
 wire[15:0] high_value=word_channel<12?pulse_ticks[191-16*word_channel -:16]:16'd0;
 wire[15:0] low_value=word_channel<12?space_ticks[191-16*word_channel -:16]:16'd0;
 wire[10:0] period_ticks={1'b0,high_value[9:0]}+{1'b0,low_value[9:0]}+11'd1;
 wire[35:0] product_next=accumulator+(multiplier[0]?multiplicand:36'd0);
 assign frame_good=!poisoned && !busy && expected_channel==12 && channel_good==12'hfff;
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   busy<=0;poisoned<=0;channel_good<=channel_good;expected_channel<=0;
   active_channel<=0;iteration<=0;multiplier<=0;multiplicand<=0;accumulator<=0;base_good<=0;
  end else if(transaction_start)begin
   busy<=0;poisoned<=0;channel_good<=channel_good;expected_channel<=0;
   active_channel<=0;iteration<=0;multiplier<=0;multiplicand<=0;accumulator<=0;base_good<=0;
  end else begin
   if(word_valid)begin
    if(busy || word_channel>=12 || word_channel!=expected_channel)poisoned<=1;
    else begin
     busy<=1;iteration<=0;active_channel<=word_channel;
     expected_channel<=expected_channel+1'b1;accumulator<=0;
     multiplicand<={11'd0,magnitude[24:0]};multiplier<=period_ticks;
     base_good<=magnitude<=32'h01000000 && high_value>=100 && high_value<=1023 && low_value>=100 && low_value<=1023;
    end
   end
   if(busy)begin
    accumulator<=product_next;multiplier<=multiplier>>1;multiplicand<=multiplicand<<1;
    if(iteration==10)begin
     channel_good[active_channel]<=base_good && product_next<=36'd4294967296;
     busy<=0;
    end else iteration<=iteration+1'b1;
   end
  end
 end
endmodule
