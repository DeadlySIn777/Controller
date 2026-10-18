`timescale 1ns/1ps
module event_selector_tb;
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
   if($countones(dut.write_enable)!==7)$fatal(1,"seven-producer case was not exercised");
  end
  if(doack)acks=acks+1;
  if(space==0)fulls=fulls+1;
  if(nextseq>=254 && producer_mask==127 && space>=7)wraps=wraps+1;
  index_pulse=0;fault_word=0;ack_commit=0;tick;tick;
  cases=cases+1;
 end endtask
 reg [7:0] selector;
 integer profile,pattern,bitno,selector_checks=0,unknown_checks=0;
 reg [23:0] previous_result;
 initial begin
  reset;
  for(profile=0;profile<3;profile=profile+1)begin
   case(profile)
    0:begin step_counts=288'h0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789;encoder_counts=96'hf123456789abcdef01234567;end
    1:begin step_counts={12{24'hz0x123}};encoder_counts={4{24'hx12z45}};end
    2:begin step_counts={12{24'h5az0x9}};encoder_counts={4{24'hz12x45}};end
   endcase
   for(pattern=0;pattern<65536;pattern=pattern+1)begin
    for(bitno=0;bitno<8;bitno=bitno+1)begin
     case((pattern>>(2*bitno))&3)
      0:selector[bitno]=0;1:selector[bitno]=1;2:selector[bitno]=1'bx;3:selector[bitno]=1'bz;
     endcase
    end
    #1;
    if(old.capture(selector)!==dut.capture(selector))$fatal(1,"capture selector differs profile=%0d pattern=%0d selector=%b",profile,pattern,selector);
    if($isunknown(selector))begin
     unknown_checks=unknown_checks+1;
     if(dut.capture(selector)!==24'd0)$fatal(1,"unknown selector did not return zero");
    end else if((selector>=12 && selector<16) || selector>=20)begin
     if(dut.capture(selector)!==24'd0)$fatal(1,"invalid known selector did not return zero");
    end
    selector_checks=selector_checks+1;
   end
  end
  $display("EVENT_SELECTOR_EXHAUSTION_PASS checks=%0d unknown_selector_checks=%0d profiles=3 all256known_values=PASS all65536four_state_values=PASS literal_payload_XZ=PASS",selector_checks,unknown_checks);$finish;
 end
endmodule
