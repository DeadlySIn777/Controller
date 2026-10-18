`timescale 1ns/1ps
module event_dispatch_diff_tb;
 reg clk=0,rst_n=0,clear=0,provider_ready=1;
 reg [31:0] ticks=0,fault_word=0,safety_word=32'hc1a55afe;
 reg [11:0] armed_mask=12'ha56,pos_continuity=12'h5ab;
 reg [287:0] step_counts=288'hf123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789;
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
 cnc3_runtime_events_candidate dut(`INPUTS,.event_head(nh),.event_status(ns),.index_armed(ni),.probe_status(np),.overflow(no));
 task compare;
 begin
  if({oh,os,oi,op,oo} !== {nh,ns,ni,np,no} ||
    {old.rd,old.wr,old.count,old.next_sequence,old.snapshot_sequence,old.delivered_sequence,old.prefetched_rd} !==
    {dut.rd,dut.wr,dut.count,dut.next_sequence,dut.snapshot_sequence,dut.delivered_sequence,dut.prefetched_rd} ||
    {old.write_enable,old.write_address,old.write_data} !== {dut.write_enable,dut.write_address,dut.write_data})begin
   $display("FAIL cycle=%0d case=%0d mask=%0d bank=%0d free=%0d seq=%0d ACK=%0d oldcount=%0d newcount=%0d oldwe=%b newwe=%b",cycles,cases,mask,wb,free_slots,seq_value,ackcase,old.count,dut.count,old.write_enable,dut.write_enable);
   $fatal(1,"old/new event dispatch differs");
  end
 end endtask
 task tick;
 begin #4;clk=1;#1;cycles=cycles+1;compare;#4;clk=0;#1;ticks=ticks+1;end
 endtask
 task idle;
 begin clear=0;provider_ready=1;fault_word=0;index_pulse=0;index_request=0;probe_raw=0;probe_request=0;arm_commit=0;cmd_snapshot=0;cmd_complete=0;ack_commit=0;ack=0;io_page1=0;io_page1[423 -:8]=1;io_page1[375 -:8]=1;end
 endtask
 task reset;
 begin idle;rst_n=0;tick;rst_n=1;tick;end
 endtask
 function integer seqwrap;
 input integer value;
 begin seqwrap=((value-1)%255+255)%255+1;end
 endfunction
 function [159:0] record;
 input integer slot,read_slot,ncount,nextseq;
 integer delta,serial;
 begin delta=(slot-read_slot+256)%256;serial=seqwrap(nextseq-ncount+delta);
 record={8'(serial),8'd3,8'(slot),8'hb6,32'h55aa2345,32'(slot),32'hfedcba98,32'h12345678};end
 endfunction
 task memory_word;
 input integer slot;input [159:0] value;
 begin
 case(slot%8)
 0:begin old.banks[0].memory.memory[slot/8]=value;dut.banks[0].memory.memory[slot/8]=value;end
 1:begin old.banks[1].memory.memory[slot/8]=value;dut.banks[1].memory.memory[slot/8]=value;end
 2:begin old.banks[2].memory.memory[slot/8]=value;dut.banks[2].memory.memory[slot/8]=value;end
 3:begin old.banks[3].memory.memory[slot/8]=value;dut.banks[3].memory.memory[slot/8]=value;end
 4:begin old.banks[4].memory.memory[slot/8]=value;dut.banks[4].memory.memory[slot/8]=value;end
 5:begin old.banks[5].memory.memory[slot/8]=value;dut.banks[5].memory.memory[slot/8]=value;end
 6:begin old.banks[6].memory.memory[slot/8]=value;dut.banks[6].memory.memory[slot/8]=value;end
 7:begin old.banks[7].memory.memory[slot/8]=value;dut.banks[7].memory.memory[slot/8]=value;end
 endcase
 end endtask
 task boundary_case;
 input integer producer_mask,bank_offset,space,nextseq,doack;
 integer w,r,n,s;
 begin
  reset;
  n=256-space;w=248+bank_offset;r=(w-n+256)%256;
  old.wr=w;dut.wr=w;old.rd=r;dut.rd=r;old.count=n;dut.count=n;
  old.next_sequence=nextseq;dut.next_sequence=nextseq;
  old.prefetched_rd=r;dut.prefetched_rd=r;
  for(s=0;s<256;s=s+1)memory_word(s,record(s,r,n,nextseq));
  tick; // Actual synchronous RAM prefetch, no producer or ACK yet.
  old.index_armed=15;dut.index_armed=15;
  old.probe_armed=producer_mask[1:0];dut.probe_armed=producer_mask[1:0];
  old.probe_level=3;dut.probe_level=3;
  old.probe_sync1=3;dut.probe_sync1=3;old.probe_sync2=3;dut.probe_sync2=3;
  probe_raw=3;index_pulse=producer_mask[5:2];fault_word=producer_mask[6]?32'h80000010:0;
  ack=oh[159:152];ack_commit=doack;
  old.delivered_sequence=ack;dut.delivered_sequence=ack;
  tick;
  if(producer_mask==127 && space>=7)begin
   seven=seven+1;
   if(dut.accepted_valid!==7'b1111111)$fatal(1,"seven-producer case was not exercised");
  end
  if(doack)acks=acks+1;
  if(space==0)fulls=fulls+1;
  if(nextseq>=254 && producer_mask==127 && space>=7)wraps=wraps+1;
  index_pulse=0;fault_word=0;ack_commit=0;tick;tick;
  cases=cases+1;
 end endtask
 initial begin
  // Exhaustive producer mask/bank/free-space/sequence/ACK boundary cross.
  for(mask=0;mask<128;mask=mask+1)
   for(wb=0;wb<8;wb=wb+1)
    for(free_slots=0;free_slots<=8;free_slots=free_slots+1)
     for(seqcase=0;seqcase<3;seqcase=seqcase+1)
      for(ackcase=0;ackcase<2;ackcase=ackcase+1)begin
       case(seqcase)0:seq_value=254;1:seq_value=255;2:seq_value=1;endcase
       boundary_case(mask,wb,free_slots,seq_value,ackcase);
      end
  // External-only full-capacity/overflow/delivery/clear/reset traces.
  reset;
  for(a=0;a<260;a=a+1)begin fault_word=1;tick;fault_word=0;tick;end
  if(old.count!=256 || !oo)$fatal(1,"external fill did not hit capacity and overflow");
  for(a=0;a<256;a=a+1)begin
   cmd_snapshot=1;tick;cmd_snapshot=0;cmd_complete=1;tick;cmd_complete=0;
   ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;
  end
  if(old.count!=0)$fatal(1,"external delivered ACKs did not drain queue");
  fault_word=2;tick;clear=1;tick;clear=0;fault_word=0;tick;
  fault_word=4;tick;rst_n=0;#1;compare;tick;rst_n=1;fault_word=0;tick;
  // Deterministic external stress includes malformed ACKs, provider loss,
  // changing capture selectors/debounce/polarity, simultaneous requests,
  // periodic reset/clear, and payload X/Z values.
  for(a=0;a<30000;a=a+1)begin
   rng=rng*32'd1664525+32'd1013904223;
   provider_ready=rng[0] | rng[1];arm_commit=rng[2];index_request=rng[6:3];probe_request=rng[8:7];
   index_pulse=rng[12:9];probe_raw=rng[14:13];fault_word=rng[15]?rng:0;
   cmd_snapshot=rng[16];cmd_complete=rng[17];ack_commit=rng[18];
   ack=rng[19]?oh[159:152]:rng[27:20];clear=(a%211)==210;
   io_page1[423 -:8]={7'd0,rng[28]};io_page1[375 -:8]={7'd0,rng[29]};
   io_page1[415 -:8]=rng[31:30];io_page1[367 -:8]=rng[29:28];
   io_page1[407 -:8]=rng[4:0];io_page1[399 -:8]=rng[9:5];io_page1[391 -:8]=rng[14:10];io_page1[383 -:8]=rng[19:15];
   io_page1[359 -:8]=rng[24:20];io_page1[351 -:8]=rng[29:25];
   step_counts={9{rng}};encoder_counts={3{rng^32'h12345678}};index_counts={3{rng^32'h87654321}};
   if(a%317==0)begin step_counts[23:0]=24'hzzxzzz;fault_word[8]=1'bx;end
   if(a%337==0)begin index_pulse[0]=1'bx;probe_raw[0]=1'bz;end
   if(a%997==0)rst_n=0;else rst_n=1;
   tick;
  end
  $display("EVENT_DISPATCH_DIFF_PASS boundary_cases=%0d cycles=%0d seven_cases=%0d ACK_cases=%0d full_cases=%0d wrap_cases=%0d external_random_cycles=30000",cases,cycles,seven,acks,fulls,wraps);
  $finish;
 end
endmodule
