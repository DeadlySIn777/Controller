`timescale 1ns/1ps
// SIM2 snapshot boundary. This validates model provenance/freshness; it is not
// a physical identity reader, IOL1 controller or electrical safety provider.
module cnc3_runtime_provider(
 input wire clk,rst_n,sim_context,
 input wire [31:0] sim_expected_session,sim_expected_config_hash,
 input wire provider_strobe,input wire [31:0] provider_tag,
 input wire [7:0] provider_abi,
 input wire [31:0] provider_session,provider_config_hash,provider_sequence,
 input wire [7:0] provider_valid_mask,input wire [31:0] provider_faults,
 input wire [23:0] di_raw,input wire [15:0] do_applied,do_fault,
 input wire [11:0] home_raw,limit_low_raw,limit_high_raw,
 input wire [15:0] din_stale_limit_us,
 output wire ready,output reg fault_latched,
 output reg [23:0] din,output reg [15:0] applied,faults,
 output reg [11:0] home,limit_low,limit_high,
 output wire [7:0] din_age,output reg [31:0] accepted_sequence
);
 reg seen;reg [15:0] age_us;reg [5:0] subtick;
 reg [31:0] bound_session,bound_hash;
 wire context_good=sim_context && sim_expected_session!=0 && sim_expected_config_hash!=0 &&
  1'b1 && provider_abi==1 &&
  provider_session==sim_expected_session && provider_config_hash==sim_expected_config_hash &&
  provider_valid_mask==8'h1f && provider_faults==0;
 wire sequence_good=(!seen && provider_sequence==1) ||
  (seen && accepted_sequence!=32'hffffffff && provider_sequence==accepted_sequence+1'b1);
 wire stale=age_us>=din_stale_limit_us || din_stale_limit_us<250 || din_stale_limit_us>440;
 assign ready=sim_context && seen && !fault_latched && !stale &&
  bound_session==sim_expected_session && bound_hash==sim_expected_config_hash;
 wire[15:0] age_units=age_us/16'd10;
 assign din_age=ready ? age_units[7:0] : 8'hff;
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   seen<=0;fault_latched<=0;age_us<=16'hffff;subtick<=0;
   bound_session<=0;bound_hash<=0;accepted_sequence<=0;
   din<=0;applied<=0;faults<=0;home<=0;limit_low<=0;limit_high<=0;
  end else begin
   if(subtick==49)begin subtick<=0;if(age_us!=16'hffff)age_us<=age_us+1'b1;end
   else subtick<=subtick+1'b1;
   if(seen && (!sim_context || stale || bound_session!=sim_expected_session || bound_hash!=sim_expected_config_hash))fault_latched<=1;
   if(provider_strobe)begin
    if(context_good && sequence_good && !fault_latched && (!seen || !stale))begin
     seen<=1;bound_session<=provider_session;bound_hash<=provider_config_hash;
     accepted_sequence<=provider_sequence;age_us<=0;subtick<=0;
     din<=di_raw;applied<=do_applied;faults<=do_fault;
     home<=home_raw;limit_low<=limit_low_raw;limit_high<=limit_high_raw;
    end else fault_latched<=1;
   end
  end
 end
endmodule
