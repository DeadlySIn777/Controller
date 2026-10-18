`timescale 1ns/1ps
// Report-local implementation candidate. Exact cnc_stepgen DDS/timer semantics,
// with validated runtime timing and a pulse-boundary clean-stop input.
module cnc3_stepgen_runtime #(parameter integer TIMER_BITS=16) (
 input wire clk, input wire rst_n, input wire enable, input wire stop,
 input wire signed [31:0] rate,
 input wire [15:0] pulse_ticks, space_ticks, setup_ticks, hold_ticks,
 output reg step, output reg dir, output reg signed [31:0] count,
 output reg timing_fault, output wire quiescent, output wire[63:0] timer_witness, output wire[31:0] phase_witness
);
 reg [31:0] phase;
 // Inputs are16-bit; retaining16 timer bits preserves every representable
 // dynamic value and the original100-tick algorithm without32-bit carry chains.
 localparam[1:0] IDLE=0,HIGH=1,LOW=2,SETUP=3;
 reg[1:0] delay_kind;reg[TIMER_BITS-1:0] delay_left,hold_left;
 wire[15:0] high_left=delay_kind==HIGH?{{(16-TIMER_BITS){1'b0}},delay_left}:16'd0;
 wire[15:0] low_left=delay_kind==LOW?{{(16-TIMER_BITS){1'b0}},delay_left}:16'd0;
 wire[15:0] setup_left=delay_kind==SETUP?{{(16-TIMER_BITS){1'b0}},delay_left}:16'd0;
 wire wanted_dir=rate[31];
 wire [31:0] magnitude=wanted_dir?(~rate+32'd1):rate;
 wire [32:0] sum={1'b0,phase}+{1'b0,magnitude};
 assign timer_witness={high_left,low_left,setup_left,{{(16-TIMER_BITS){1'b0}},hold_left}};
 assign phase_witness=phase;
 assign quiescent=!step && high_left==0 && low_left==0 && hold_left==0;
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin
   phase<=0;step<=0;dir<=0;count<=0;delay_kind<=IDLE;delay_left<=0;hold_left<=0;timing_fault<=0;
  end else if(!enable) begin
   phase<=0;step<=0;dir<=0;delay_kind<=SETUP;delay_left<=setup_ticks[TIMER_BITS-1:0];hold_left<=0;timing_fault<=0;
  end else begin
   if(delay_left!=0)delay_left<=delay_left-1'b1;
   if(hold_left!=0)hold_left<=hold_left-1'b1;
   if(high_left==1)begin step<=0;delay_kind<=LOW;delay_left<=space_ticks[TIMER_BITS-1:0];end
   // stop does not truncate STEP or DIR hold. No new rising edge may be emitted.
   if(stop || rate==0)phase<=0;
   else if(wanted_dir!=dir)begin
    phase<=0;
    if(high_left==0 && low_left==0 && hold_left==0)begin
     dir<=wanted_dir;delay_kind<=SETUP;delay_left<=setup_ticks[TIMER_BITS-1:0];
    end
   end else if(setup_left==0)begin
    phase<=sum[31:0];
    if(sum[32])begin
     if(high_left==0 && low_left==0)begin
      step<=1;delay_kind<=HIGH;delay_left<=pulse_ticks[TIMER_BITS-1:0];hold_left<=hold_ticks[TIMER_BITS-1:0];
      count<=count+(dir?32'hffffffff:32'd1);
     end else timing_fault<=1;
    end
   end else phase<=0;
  end
 end
endmodule
