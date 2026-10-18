`timescale 1ns/1ps
module provider_tb;
 reg clk=0,rst_n=0,strobe=0;reg[31:0]expected_hash=2,hash=2,seq=1;
 wire ready,error;wire[7:0]age;wire[31:0]accepted;
 integer checks=0,i;
 cnc3_runtime_provider dut(.clk(clk),.rst_n(rst_n),.sim_context(1'b1),
  .sim_expected_session(32'd1),.sim_expected_config_hash(expected_hash),
  .provider_strobe(strobe),.provider_tag(32'h53494d32),.provider_abi(8'd1),
  .provider_session(32'd1),.provider_config_hash(hash),.provider_sequence(seq),
  .provider_valid_mask(8'h1f),.provider_faults(32'd0),.di_raw(24'habcdef),
  .do_applied(16'd0),.do_fault(16'd0),.home_raw(12'd0),.limit_low_raw(12'd0),.limit_high_raw(12'd0),
  .din_stale_limit_us(16'd440),.ready(ready),.fault_latched(error),.din_age(age),.accepted_sequence(accepted));
 task tick;begin #5;clk=1;#5;clk=0;end endtask
 task verify;input good;input[511:0]msg;begin checks=checks+1;if(!good)$fatal(1,"%0s",msg);end endtask
 initial begin
  tick;rst_n=1;tick;verify(!ready && age==255,"never sampled is unavailable");
  expected_hash=0;hash=0;strobe=1;tick;strobe=0;
  verify(error && !ready && accepted==0,"zero context hash cannot qualify");
  rst_n=0;tick;rst_n=1;expected_hash=2;hash=2;strobe=1;tick;strobe=0;
  verify(ready && accepted==1 && age==0,"first exact snapshot accepted");
  for(i=0;i<21999;i=i+1)tick;
  verify(ready && age==43,"439.98us is fresh");
  tick;verify(!ready && age==255,"exact440us is stale");
  tick;verify(error,"staleness latches");
  seq=2;strobe=1;tick;strobe=0;
  verify(error && !ready && accepted==1,"fresh sequence cannot revive stale run");
  $display("SIM2_PROVIDER_PASS checks=%0d",checks);$finish;
 end
endmodule
