`timescale 1ns/1ps
module producer_postmap_tb;
 reg clk=0,rst_n=0,clear=0,provider_ready=1;
 reg [31:0] ticks=0,fault_word=0,safety_word=32'hc1a55afe;
 reg [11:0] armed_mask=12'ha56,pos_continuity=12'h5ab;
 reg [287:0] step_counts={9{32'h12345678}};
 reg [95:0] encoder_counts=96'h112233445566778899aabbcc,index_counts=96'haabbcc123456223344556677;
 reg [3:0] index_pulse=0,index_request=0;
 reg [1:0] probe_raw=0,probe_request=0;
 reg [431:0] io_page1=0;
 reg arm_commit=0,cmd_snapshot=0,cmd_complete=0,ack_commit=0;
 reg [7:0] ack=0;
 wire [159:0] oh,nh;wire [7:0] os,ns,op,np;wire [3:0] oi,ni;wire oo,no;
 integer cycles=0,cases=0,seven=0,acks=0,wraps=0,fulls=0;
 integer mask,wb,free_slots,seqcase,ackcase,a,z,seq_value;
 reg [31:0] rng=32'h239ac175;
`define INPUTS .clk(clk),.rst_n(rst_n),.clear(clear),.provider_ready(provider_ready),.ticks(ticks),.fault_word(fault_word),.safety_word(safety_word),.armed_mask(armed_mask),.pos_continuity(pos_continuity),.step_counts(step_counts),.encoder_counts(encoder_counts),.index_counts(index_counts),.index_pulse(index_pulse),.probe_raw(probe_raw),.io_page1(io_page1),.arm_commit(arm_commit),.index_request(index_request),.probe_request(probe_request),.cmd_snapshot(cmd_snapshot),.cmd_complete(cmd_complete),.ack_commit(ack_commit),.ack(ack)
 cnc3_runtime_events_original old(`INPUTS,.event_head(oh),.event_status(os),.index_armed(oi),.probe_status(op),.overflow(oo));
 cnc3_runtime_events dut(`INPUTS,.event_head(nh),.event_status(ns),.index_armed(ni),.probe_status(np),.overflow(no));
 integer producer,n,checks=0,full_producers=0,seven_batches=0;
 task compare;
 begin
  checks=checks+1;
  if({oh,os,oi,op,oo}!=={nh,ns,ni,np,no})begin
   $display("POSTMAP_FAIL cycle=%0d producer=%0d oldhead=%h mappedhead=%h oldstatus=%h mappedstatus=%h oldindex=%h mappedindex=%h oldprobe=%h mappedprobe=%h",cycles,producer,oh,nh,os,ns,oi,ni,op,np);
   $fatal(1,"mapped event engine differs from original public outputs");
  end
 end endtask
 task tick;
 begin #4;clk=1;#1;cycles=cycles+1;compare;#4;clk=0;#1;ticks=ticks+1;end endtask
 task idle;
 begin clear=0;provider_ready=1;fault_word=0;index_pulse=0;index_request=0;probe_raw=0;probe_request=0;arm_commit=0;cmd_snapshot=0;cmd_complete=0;ack_commit=0;ack=0;io_page1=0;io_page1[423 -:8]=1;io_page1[375 -:8]=1;end endtask
 task reset;
 begin idle;rst_n=0;tick;rst_n=1;tick;end endtask
 task emit;
 input integer p;
 begin
  if(p<2)begin
   probe_request=0;probe_raw=0;arm_commit=1;tick;arm_commit=0;tick;tick;tick;
   probe_request=2'(1<<p);arm_commit=1;tick;arm_commit=0;
   probe_raw=2'(1<<p);tick;tick;tick;tick;probe_raw=0;tick;tick;tick;
   probe_request=0;arm_commit=1;tick;arm_commit=0;tick;
  end else if(p<6)begin
   index_request=0;arm_commit=1;tick;index_request=4'(1<<(p-2));tick;
   arm_commit=0;index_pulse=4'(1<<(p-2));tick;index_pulse=0;tick;
  end else begin fault_word=1;tick;fault_word=0;tick;end
 end endtask
 task deliver;
 begin cmd_snapshot=1;tick;cmd_snapshot=0;cmd_complete=1;tick;cmd_complete=0;end endtask
 task append_with_ack;
 input integer p;
 begin
  deliver;ack=oh[159:152];
  if(p<2)begin
   probe_request=2'(1<<p);arm_commit=1;tick;arm_commit=0;
   probe_raw=2'(1<<p);tick;tick;ack_commit=1;tick;ack_commit=0;
   probe_raw=0;tick;tick;tick;probe_request=0;arm_commit=1;tick;arm_commit=0;tick;
  end else if(p<6)begin
   index_request=0;arm_commit=1;tick;index_request=4'(1<<(p-2));tick;
   arm_commit=0;index_pulse=4'(1<<(p-2));ack_commit=1;tick;ack_commit=0;index_pulse=0;tick;
  end else begin fault_word=1;ack_commit=1;tick;ack_commit=0;fault_word=0;tick;end
 end endtask
 task drain;
 integer j;
 begin
  for(j=0;j<256;j=j+1)begin
   deliver;ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;
  end
  if(os[6:0]!==0 || oh!==0)$fatal(1,"external full queue failed to drain");
 end endtask
 task emit_all;
 begin
  probe_request=0;index_request=0;probe_raw=0;index_pulse=0;fault_word=0;arm_commit=1;
  tick;tick;tick;tick;probe_request=3;index_request=15;tick;arm_commit=0;
  probe_raw=3;tick;tick;index_pulse=15;fault_word=1;tick;
  index_pulse=0;fault_word=0;tick;probe_raw=0;tick;tick;tick;
 end endtask
 initial begin
  // Force explicit events before the first clock, avoiding time-zero input
  // initialization differences in vendor event-driven primitive models.
  {clk,rst_n,clear,provider_ready,ticks,fault_word,safety_word,armed_mask,pos_continuity,
   step_counts,encoder_counts,index_counts,index_pulse,probe_raw,io_page1,arm_commit,
   index_request,probe_request,cmd_snapshot,cmd_complete,ack_commit,ack}='x;
  #1;clk=0;rst_n=0;ticks=0;safety_word=32'hc1a55afe;armed_mask=12'ha56;pos_continuity=12'h5ab;
  step_counts=0;encoder_counts=96'h112233445566778899aabbcc;index_counts=96'haabbcc123456223344556677;
  idle;#1;reset;
  for(n=0;n<12;n=n+1)step_counts[287-24*n -:24]=24'h102030+24'(n*1021);
  encoder_counts=96'hf123456789abcdef01234567;
  for(producer=0;producer<7;producer=producer+1)begin
   reset;
   for(n=0;n<256;n=n+1)emit(producer);
   if(old.count!==256 || oo!==0)$fatal(1,"producer did not fill exactly256");
   append_with_ack(producer);
   if(old.count!==256 || oo!==0)$fatal(1,"full same-producer ACK+append differs");
   emit(producer);if(oo!==1)$fatal(1,"capacity overflow was not reached");
   drain;full_producers=full_producers+1;
  end
  reset;
  for(n=0;n<40;n=n+1)begin
   a=old.count;emit_all;
   if(n<36 && old.count!==a+7)$fatal(1,"seven-producer batch did not enqueue7");
   seven_batches=seven_batches+1;
  end
  if(old.count!==256 || !oo)$fatal(1,"mixed queue capacity not reached");drain;
  // Clear/reset with pending writes and different stale producer heads.
  emit_all;clear=1;tick;clear=0;tick;
  emit(0);rst_n=0;#1;compare;tick;rst_n=1;tick;emit(6);tick;
  for(n=0;n<3000;n=n+1)begin
   rng=rng*32'd1664525+32'd1013904223;
   provider_ready=rng[0]|rng[1];arm_commit=rng[2];index_request=rng[6:3];probe_request=rng[8:7];
   index_pulse=rng[12:9];probe_raw=rng[14:13];fault_word=rng[15]?rng:0;
   cmd_snapshot=rng[16];cmd_complete=rng[17];ack_commit=rng[18];ack=rng[19]?oh[159:152]:rng[27:20];
   clear=(n%211)==210;step_counts={9{rng}};index_counts={3{rng}};
   io_page1[407 -:8]=rng[4:0];io_page1[399 -:8]=rng[9:5];io_page1[391 -:8]=rng[14:10];io_page1[383 -:8]=rng[19:15];
   io_page1[359 -:8]=rng[24:20];io_page1[351 -:8]=rng[29:25];tick;
  end
  $display("PRODUCER_POSTMAP_PASS checks=%0d cycles=%0d full_producers=%0d seven_batches=%0d binary_random_cycles=3000",checks,cycles,full_producers,seven_batches);$finish;
 end
endmodule
