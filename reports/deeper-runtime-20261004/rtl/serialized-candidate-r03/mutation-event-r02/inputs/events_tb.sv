`timescale 1ns/1ps
module events_tb;
 reg clk=0,rst_n=0,clear=0,provider_ready=1;reg[31:0]ticks=0,fault_word=0;
 reg cmd_snapshot=0,cmd_complete=0,ack_commit=0;reg[7:0]ack=0;
 wire[159:0]head;wire[7:0]status,probe_status;wire[3:0]index_armed;wire overflow;
 integer checks=0,i;
 cnc3_runtime_events dut(.clk(clk),.rst_n(rst_n),.clear(clear),.provider_ready(provider_ready),
  .ticks(ticks),.fault_word(fault_word),.safety_word(32'd0),.armed_mask(12'd0),.pos_continuity(12'd0),
  .step_counts(288'd0),.encoder_counts(96'd0),.index_counts(96'd0),.index_pulse(4'd0),
  .probe_raw(2'd0),.io_page1(432'd0),.arm_commit(1'b0),.index_request(4'd0),.probe_request(2'd0),
  .cmd_snapshot(cmd_snapshot),.cmd_complete(cmd_complete),.ack_commit(ack_commit),.ack(ack),
  .event_head(head),.event_status(status),.index_armed(index_armed),.probe_status(probe_status),.overflow(overflow));
 task tick;begin #5;clk=1;#5;clk=0;ticks=ticks+1;end endtask
 task verify;input good;input[511:0]msg;begin checks=checks+1;if(!good)$fatal(1,"%0s",msg);end endtask
 initial begin
  tick;rst_n=1;tick;
  for(i=0;i<256;i=i+1)begin fault_word=1;tick;fault_word=0;tick;end
  verify(dut.count==256 && !overflow && status==127,"exact capacity, no lost record");
  verify(head[159:152]==1 && head[151:144]==3,"oldest fault retained");
  fault_word=2;tick;fault_word=0;tick;
  verify(dut.count==256 && overflow && status==255,"overflow is sticky and bounded");
  ack=1;ack_commit=1;tick;ack_commit=0;tick;
  verify(dut.count==256,"undelivered acknowledgment rejected");
  cmd_snapshot=1;tick;cmd_snapshot=0;ack_commit=1;tick;ack_commit=0;
  verify(dut.count==256,"truncated command snapshot is not delivery");
  cmd_complete=1;tick;cmd_complete=0;ack=2;ack_commit=1;tick;ack_commit=0;
  verify(dut.count==256,"wrong delivered-head acknowledgment rejected");
  ack=1;ack_commit=1;tick;ack_commit=0;tick;
  verify(dut.count==255 && head[159:152]==2,"exact delivered acknowledgment pops once");
  ack_commit=1;tick;ack_commit=0;
  verify(dut.count==255,"repeated acknowledgment cannot pop next record");
  clear=1;tick;clear=0;tick;
  verify(status==0 && head==0 && !overflow,"SYNC clears ring and overflow");
  $display("SIM2_EVENTS_PASS checks=%0d",checks);$finish;
 end
endmodule
