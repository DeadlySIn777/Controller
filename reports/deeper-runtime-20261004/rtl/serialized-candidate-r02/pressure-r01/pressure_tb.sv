`timescale 1ns/1ps
module pressure_tb;
 reg clk=0,rst_n=0,arm=0;reg[3:0]req=0,pulse=0;wire[159:0]head;wire[7:0]status;wire overflow;
 integer i,checks=0;
 cnc3_runtime_events dut(.clk(clk),.rst_n(rst_n),.clear(1'b0),.provider_ready(1'b1),
 .ticks(32'd123),.fault_word(32'd0),.safety_word(32'd0),.armed_mask(12'd0),.pos_continuity(12'd0),
 .step_counts(288'd0),.encoder_counts(96'd0),.index_counts(96'h123456123456123456123456),.index_pulse(pulse),
 .probe_raw(2'd0),.io_page1(432'd0),.arm_commit(arm),.index_request(req),.probe_request(2'd0),
 .cmd_snapshot(1'b0),.cmd_complete(1'b0),.ack_commit(1'b0),.ack(8'd0),
 .event_head(head),.event_status(status),.overflow(overflow));
 task tick;begin #5;clk=1;#5;clk=0;end endtask
 initial begin
  tick;rst_n=1;
  // Deliberately impossible at real SPI cadence: stress private queue bookkeeping.
  for(i=0;i<64;i=i+1)begin
   arm=1;req=(i&1)?0:15;pulse=(i&1)?15:0;tick;
   checks=checks+1;if(dut.count !== dut.stored_count+dut.stage_count)
    $fatal(1,"phantom accepted record under staging pressure cycle=%0d count=%0d stored=%0d staged=%0d",i,dut.count,dut.stored_count,dut.stage_count);
  end
  arm=0;req=0;pulse=0;repeat(16)tick;
  if(!overflow || dut.stage_count!=0 || dut.count!=dut.stored_count)$fatal(1,"pressure must latch explicit overflow and retain exact accepted count");
  $display("SERIALIZED_PRESSURE_PASS invariant_checks=%0d",checks);$finish;
 end
endmodule
