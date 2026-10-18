`timescale 1ns/1ps
module producer_fifo_supplement_tb;
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
 integer mask,wb,free_slots,seqcase,ackcase,a,z,seq_value,seed_mode=0;
 integer ledger_checks=0,admission_checks=0,stop_pending=0,postcommit_checks=0;
 reg [31:0] rng=32'h239ac175;
`define INPUTS .clk(clk),.rst_n(rst_n),.clear(clear),.provider_ready(provider_ready),.ticks(ticks),.fault_word(fault_word),.safety_word(safety_word),.armed_mask(armed_mask),.pos_continuity(pos_continuity),.step_counts(step_counts),.encoder_counts(encoder_counts),.index_counts(index_counts),.index_pulse(index_pulse),.probe_raw(probe_raw),.io_page1(io_page1),.arm_commit(arm_commit),.index_request(index_request),.probe_request(probe_request),.cmd_snapshot(cmd_snapshot),.cmd_complete(cmd_complete),.ack_commit(ack_commit),.ack(ack)
 cnc3_runtime_events_original old(`INPUTS,.event_head(oh),.event_status(os),.index_armed(oi),.probe_status(op),.overflow(oo));
 cnc3_runtime_events_candidate dut(`INPUTS,.event_head(nh),.event_status(ns),.index_armed(ni),.probe_status(np),.overflow(no));
 function integer producer_of;
 input [159:0] value;
 begin
  case(value[151:144])
   1:producer_of=value[143:136];2:producer_of=2+value[143:136];3:producer_of=6;
   default:producer_of=-1;
  endcase
 end endfunction
 task compare;
 integer p,q,total,seen;reg[159:0] value;reg[7:0] tag;
 begin
  if({oh,os,oi,op,oo} !== {nh,ns,ni,np,no} ||
    {old.rd,old.wr,old.count,old.next_sequence,old.snapshot_sequence,old.delivered_sequence,old.prefetched_rd,
     old.index_level,old.probe_level,old.probe_armed,old.probe_overrun,old.probe_sync1,old.probe_sync2,old.filtered,
     old.stable[0],old.stable[1],old.previous_fault} !==
    {dut.rd,dut.wr,dut.count,dut.next_sequence,dut.snapshot_sequence,dut.delivered_sequence,dut.prefetched_rd,
     dut.index_level,dut.probe_level,dut.probe_armed,dut.probe_overrun,dut.probe_sync1,dut.probe_sync2,dut.filtered,
     dut.stable[0],dut.stable[1],dut.previous_fault})begin
   $display("FAIL cycle=%0d case=%0d mask=%0d offset=%0d free=%0d seq=%0d ACK=%0d seed=%0d oldcount=%0d newcount=%0d oldhead=%h newhead=%h oldrd=%0d newrd=%0d localvalid=%b",cycles,cases,mask,wb,free_slots,seq_value,ackcase,seed_mode,old.count,dut.count,oh,nh,old.rd,dut.rd,dut.producer_head_valid);
   $fatal(1,"public/global/filter event state differs");
  end
  total=0;
  for(p=0;p<7;p=p+1)begin
   total=total+dut.producer_count[p];
   if(dut.producer_wr[p] !== 8'(dut.producer_rd[p]+dut.producer_count[p]))
    $fatal(1,"local pointer/count invariant differs producer=%0d",p);
  end
  if(total!==int'(old.count))$fatal(1,"local/global occupancy differs");
  seen=0;
  for(q=0;q<8;q=q+1)if(old.write_enable[q])begin
   value=old.write_data[160*q +:160];tag={old.write_address[5*q +:5],3'(q)};
   p=producer_of(value);
   if(p<0 || p>6 || (seen&(1<<p)))$fatal(1,"invalid/duplicate admitted producer");
   seen=seen|(1<<p);
   if(dut.write_enable[p]!==1'b1 || dut.write_data[168*p +:168]!=={tag,value})
    $fatal(1,"normalized admitted record differs producer=%0d",p);
   admission_checks=admission_checks+1;
  end
  if(7'(seen)!==dut.write_enable)$fatal(1,"normalized admission enables differ");
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
 begin case(slot%8)
 0:old.banks[0].memory.memory[slot/8]=value;
 1:old.banks[1].memory.memory[slot/8]=value;
 2:old.banks[2].memory.memory[slot/8]=value;
 3:old.banks[3].memory.memory[slot/8]=value;
 4:old.banks[4].memory.memory[slot/8]=value;
 5:old.banks[5].memory.memory[slot/8]=value;
 6:old.banks[6].memory.memory[slot/8]=value;
 7:old.banks[7].memory.memory[slot/8]=value;
 endcase end endtask
 function [159:0] old_word;
 input integer slot;
 begin
 case(slot%8)
 0:old_word=old.banks[0].memory.memory[slot/8];
 1:old_word=old.banks[1].memory.memory[slot/8];
 2:old_word=old.banks[2].memory.memory[slot/8];
 3:old_word=old.banks[3].memory.memory[slot/8];
 4:old_word=old.banks[4].memory.memory[slot/8];
 5:old_word=old.banks[5].memory.memory[slot/8];
 6:old_word=old.banks[6].memory.memory[slot/8];
 7:old_word=old.banks[7].memory.memory[slot/8];
 endcase
 if(old.write_enable[slot%8] && old.write_address[5*(slot%8) +:5]==5'(slot/8))
  old_word=old.write_data[160*(slot%8) +:160];
 end endfunction
 task producer_word;
 input integer producer,address;input[167:0]value;
 begin case(producer)
 0:dut.producers[0].memory.memory[address]=value;
 1:dut.producers[1].memory.memory[address]=value;
 2:dut.producers[2].memory.memory[address]=value;
 3:dut.producers[3].memory.memory[address]=value;
 4:dut.producers[4].memory.memory[address]=value;
 5:dut.producers[5].memory.memory[address]=value;
 6:dut.producers[6].memory.memory[address]=value;
 endcase end endtask
 function [167:0] new_word;
 input integer producer,address;
 begin case(producer)
 0:new_word=dut.producers[0].memory.memory[address];
 1:new_word=dut.producers[1].memory.memory[address];
 2:new_word=dut.producers[2].memory.memory[address];
 3:new_word=dut.producers[3].memory.memory[address];
 4:new_word=dut.producers[4].memory.memory[address];
 5:new_word=dut.producers[5].memory.memory[address];
 6:new_word=dut.producers[6].memory.memory[address];
 endcase
 if(dut.write_enable[producer] && dut.write_address[8*producer +:8]==8'(address))
  new_word=dut.write_data[168*producer +:168];
 end endfunction
 task queue_check;
 integer seen[0:6];integer n,p,slot,address;reg[159:0]value;
 begin
 for(p=0;p<7;p=p+1)seen[p]=0;
 for(n=0;n<old.count;n=n+1)begin
  slot=(int'(old.rd)+n)%256;value=old_word(slot);p=producer_of(value);
  if(p<0 || p>6)$fatal(1,"invalid logical record");
  address=(int'(dut.producer_rd[p])+seen[p])%256;
  if(new_word(p,address)!=={8'(slot),value})
   $fatal(1,"normalized live queue differs offset=%0d producer=%0d address=%0d",n,p,address);
  seen[p]=seen[p]+1;ledger_checks=ledger_checks+1;
 end
 for(p=0;p<7;p=p+1)if(seen[p]!==int'(dut.producer_count[p]))
  $fatal(1,"normalized queue count differs producer=%0d",p);
 end endtask
 task seed_queue;
 input integer r,n,nextseq;
 integer p,s,slot,address;reg[159:0]value;
 begin
 for(p=0;p<7;p=p+1)begin
  dut.producer_rd[p]=8'(248+((seed_mode*37+p*31+wb)%8));
  dut.producer_prefetched_rd[p]=dut.producer_rd[p];
  dut.producer_wr[p]=dut.producer_rd[p];dut.producer_count[p]=0;
 end
 for(s=0;s<n;s=s+1)begin
  slot=(r+s)%256;value=record(slot,r,n,nextseq);
  if(seed_mode==0)p=6;else if(seed_mode>=2 && seed_mode<=8)p=seed_mode-2;else if(seed_mode>=9)p=(s+seed_mode-9)%7;else p=s%7;
  if(p<2)begin value[151:144]=1;value[143:136]=8'(p);end
  else if(p<6)begin value[151:144]=2;value[143:136]=8'(p-2);end
  else begin value[151:144]=3;value[143:136]=8'(slot);end
  memory_word(slot,value);address=dut.producer_wr[p];
  producer_word(p,address,{8'(slot),value});
  dut.producer_wr[p]=dut.producer_wr[p]+8'd1;
  dut.producer_count[p]=dut.producer_count[p]+9'd1;
 end
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
  seed_queue(r,n,nextseq);
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
  queue_check;index_pulse=0;fault_word=0;ack_commit=0;if(!stop_pending)begin tick;tick;queue_check;postcommit_checks=postcommit_checks+1;end
  cases=cases+1;
 end endtask
 task drain_all;
 integer q,starting;
 begin
  starting=old.count;
  for(q=0;q<starting;q=q+1)begin
   if(oh[159:152]===8'd0)$fatal(1,"head unexpectedly masked before delivery");
   cmd_snapshot=1;tick;cmd_snapshot=0;cmd_complete=1;tick;cmd_complete=0;
   ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;queue_check;postcommit_checks=postcommit_checks+1;
  end
  if(old.count!==0 || dut.count!==0)$fatal(1,"focused queue did not drain");
 end endtask
 task external_seven_pending;
 begin
  index_request=0;probe_request=0;arm_commit=1;probe_raw=0;fault_word=0;index_pulse=0;tick;arm_commit=0;tick;tick;tick;
  index_request=15;probe_request=3;arm_commit=1;tick;arm_commit=0;
  probe_raw=3;tick;tick;index_pulse=15;fault_word=1;tick;
  if(old.count!==7 || $countones(dut.write_enable)!==7)$fatal(1,"focused external seven producers were not pending");
  queue_check;index_pulse=0;fault_word=0;
 end endtask
 integer producer,rotate;
 initial begin
  // Each producer alone holds all256 entries, including same-producer
  // full pop+append at every near-wrap local read/write alignment.
  for(producer=0;producer<7;producer=producer+1)begin
   seed_mode=producer+2;
   for(wb=0;wb<8;wb=wb+1)begin
    mask=1<<producer;free_slots=0;seq_value=255;ackcase=1;
    boundary_case(mask,wb,free_slots,seq_value,ackcase);
    if(wb==0)drain_all;
   end
  end
  // Every producer becomes global head; drain across all seven cached RAM
  // heads and local wrap positions, with new seven-way admission mixed in.
  for(rotate=0;rotate<7;rotate=rotate+1)begin
   seed_mode=9+rotate;
   for(wb=0;wb<8;wb=wb+1)begin
    mask=127;free_slots=248;seq_value=254;ackcase=1;
    boundary_case(mask,wb,free_slots,seq_value,ackcase);drain_all;
   end
  end
  // Empty producers must mask stale tags, before/after physical commit.
  for(producer=0;producer<7;producer=producer+1)begin
   seed_mode=producer+2;mask=1<<producer;wb=7;free_slots=256;seq_value=1;ackcase=0;
   boundary_case(mask,wb,free_slots,seq_value,ackcase);drain_all;
  end
  seed_mode=9;mask=127;wb=7;free_slots=256;seq_value=255;ackcase=0;
  boundary_case(mask,wb,free_slots,seq_value,ackcase);drain_all;
  // Real external stimulus: clear while seven RAM writes are pending.
  // Their stale tag0..6 contents remain physically present after clear.
  reset;external_seven_pending;clear=1;tick;clear=0;tick;tick;queue_check;
  external_seven_pending;tick;tick;queue_check;postcommit_checks=postcommit_checks+1;drain_all;
  // Repeat through asynchronous reset while writes are pending, with
  // literal X/Z payload bits and no RAM array reset.
  reset;step_counts={12{24'hz0x123}};index_counts={4{24'hx12z45}};encoder_counts={4{24'hz123x5}};
  external_seven_pending;rst_n=0;#1;compare;tick;rst_n=1;tick;
  external_seven_pending;tick;tick;queue_check;postcommit_checks=postcommit_checks+1;drain_all;
  $display("PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS cycles=%0d boundary_cases=%0d postcommit_checks=%0d live_record_checks=%0d admission_checks=%0d all7producer_full_pop_append=PASS rotated_head_drains=PASS empty_stale_clear_reset=PASS",cycles,cases,postcommit_checks,ledger_checks,admission_checks);$finish;
 end
endmodule
