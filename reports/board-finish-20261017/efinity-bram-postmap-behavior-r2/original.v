`timescale 1ns/1ps
// One synchronous read/write bank, deliberately no array reset. Queue validity
// gates uninitialized entries. Explicit collision forwarding matches write-first.
module cnc3_event_bank_original(input wire clk,write_enable,
 input wire[4:0]write_address,read_address,input wire[159:0]write_data,
 output reg[159:0]read_data);
 reg[159:0]memory[0:31];
 always@(posedge clk)begin
  if(write_enable)memory[write_address]<=write_data;
  if(write_enable && write_address==read_address)read_data<=write_data;
  else read_data<=memory[read_address];
 end
endmodule
