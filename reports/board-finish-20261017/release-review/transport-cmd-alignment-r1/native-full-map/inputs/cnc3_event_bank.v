`timescale 1ns/1ps
// Keep the unconditional registered memory read visible to RAM inference.
// A separate registered bypass preserves exact write-first collision behavior.
module cnc3_event_bank(input wire clk,write_enable,
 input wire[4:0]write_address,read_address,input wire[159:0]write_data,
 output wire[159:0]read_data);
 reg[159:0]memory[0:31];
 reg[159:0]ram_read,forward_data;
 reg forward_valid;
 always@(posedge clk)begin
  if(write_enable)memory[write_address]<=write_data;
  ram_read<=memory[read_address];
  if(write_enable && write_address==read_address)forward_valid<=1'b1;
  else forward_valid<=1'b0;
  forward_data<=write_data;
 end
 assign read_data=forward_valid?forward_data:ram_read;
endmodule
