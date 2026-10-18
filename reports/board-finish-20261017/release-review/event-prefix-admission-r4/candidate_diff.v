`timescale 1ns/1ps
// Bounded 256-record frozen CNS3 event ring with real probe/index capture.
module cnc3_runtime_events_candidate(
 input wire clk,rst_n,clear,provider_ready,
 input wire [31:0] ticks,fault_word,safety_word,
 input wire [11:0] armed_mask,pos_continuity,
 input wire [287:0] step_counts,input wire [95:0] encoder_counts,index_counts,
 input wire [3:0] index_pulse,
 input wire [1:0] probe_raw,input wire [431:0] io_page1,
 input wire arm_commit,input wire [3:0] index_request,input wire [1:0] probe_request,
 input wire cmd_snapshot,cmd_complete,
 input wire ack_commit,input wire [7:0] ack,
 output wire [159:0] event_head,output wire [7:0] event_status,
 output reg [3:0] index_armed,output wire [7:0] probe_status,
 output reg overflow
);
 // At most seven producers enqueue on one clock. Consecutive entries land
 // in distinct banks, giving every RAM one write port without reducing depth.
 reg[7:0] write_enable;reg[39:0] write_address;reg[1279:0] write_data;
 wire[159:0] bank_data[0:7];reg[7:0] prefetched_rd;
 reg [7:0] rd,wr,next_sequence,snapshot_sequence,delivered_sequence;
 genvar bank;
 generate for(bank=0;bank<8;bank=bank+1)begin:banks
  cnc3_event_bank memory(.clk(clk),.write_enable(write_enable[bank]),
   .write_address(write_address[5*bank +:5]),.write_data(write_data[160*bank +:160]),
   .read_address(rd[7:3]),.read_data(bank_data[bank]));
 end endgenerate
 reg [8:0] count;
 reg [3:0] index_level;
 reg [1:0] probe_level,probe_armed,probe_overrun;
 reg [1:0] probe_sync1,probe_sync2,filtered;
 reg [7:0] stable[0:1];
 reg [31:0] previous_fault;
 integer i,j,k,b,p;reg[8:0]temp_count;reg[7:0]temp_wr,temp_sequence;
 reg[7:0]next_write_enable;reg[39:0]next_write_address;reg[1279:0]next_write_data;
 // Fixed producers preserve their source ordering. Admission is a small
 // prefix of offered records; wide payloads are assembled once per producer.
 reg[6:0] offered_valid,accepted_valid,bank_select;
 reg[151:0] offered_payload[0:6];
 reg[159:0] accepted_payload[0:6];
 reg[7:0] accepted_slot[0:6],slot_value[0:7],sequence_value[0:7];
 reg[2:0] offered_prefix,accepted_count;
 reg [1:0] next_filtered,edges;
 reg [95:0] values;
 reg [7:0] source;
 reg [31:0] newly_set;
 wire head_pending=write_enable[rd[2:0]] && write_address[5*rd[2:0] +:5]==rd[7:3];
 wire head_valid=count!=0 && prefetched_rd==rd && !head_pending;
 assign event_head=head_valid?bank_data[prefetched_rd[2:0]]:160'd0;
 assign event_status={overflow,(count>127?7'd127:count[6:0])};
 assign probe_status={probe_overrun,probe_armed,probe_sync2,filtered};
 function [23:0] capture;
  input [7:0] selector;
  begin
   // Decode the sixteen legal records directly; avoid arithmetic-controlled
   // wide variable part-selects. Exact case defaults unknown selectors to zero,
   // matching the guarded original, while preserving selected data X/Z bits.
   case(selector)
    8'd0:capture=step_counts[287 -:24];
    8'd1:capture=step_counts[263 -:24];
    8'd2:capture=step_counts[239 -:24];
    8'd3:capture=step_counts[215 -:24];
    8'd4:capture=step_counts[191 -:24];
    8'd5:capture=step_counts[167 -:24];
    8'd6:capture=step_counts[143 -:24];
    8'd7:capture=step_counts[119 -:24];
    8'd8:capture=step_counts[95 -:24];
    8'd9:capture=step_counts[71 -:24];
    8'd10:capture=step_counts[47 -:24];
    8'd11:capture=step_counts[23 -:24];
    8'd16:capture=encoder_counts[95 -:24];
    8'd17:capture=encoder_counts[71 -:24];
    8'd18:capture=encoder_counts[47 -:24];
    8'd19:capture=encoder_counts[23 -:24];
    default:capture=24'd0;
   endcase
  end
 endfunction
 task enqueue;
  input[2:0]producer;
  input[7:0]kind,origin,flags;
  input[95:0]data;
  begin
   offered_valid[producer]=1'b1;
   offered_payload[producer]={kind,origin,flags,ticks,data};
  end
 endtask
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   rd<=0;wr<=0;count<=0;next_sequence<=1;snapshot_sequence<=0;delivered_sequence<=0;
   index_level<=0;index_armed<=0;probe_level<=0;probe_armed<=0;probe_overrun<=0;
   probe_sync1<=0;probe_sync2<=0;filtered<=0;stable[0]<=0;stable[1]<=0;
   previous_fault<=0;overflow<=0;
   write_enable<=0;write_address<=0;write_data<=0;prefetched_rd<=0;
  end else begin
   probe_sync1<=probe_raw;probe_sync2<=probe_sync1;
   temp_count=count;temp_wr=wr;temp_sequence=next_sequence;
   next_write_enable=0;next_write_address=0;next_write_data=0;prefetched_rd<=rd;
   offered_valid=0;accepted_valid=0;
   for(p=0;p<7;p=p+1)begin offered_payload[p]=0;accepted_payload[p]=0;accepted_slot[p]=0;end
   next_filtered=filtered;edges=0;
   for(i=0;i<2;i=i+1)begin
    if(probe_sync2[i]==filtered[i])stable[i]<=0;
    else if(io_page1[431-(2+6*i)*8 -:8]==0 ||
       {1'b0,stable[i]}+9'd1>={1'b0,io_page1[431-(2+6*i)*8 -:8]})begin
     next_filtered[i]=probe_sync2[i];stable[i]<=0;
    end else stable[i]<=stable[i]+1'b1;
    edges[i]=next_filtered[i]!=filtered[i] &&
      next_filtered[i]==io_page1[431-(1+6*i)*8-7];
   end
   filtered<=next_filtered;
   if(cmd_snapshot)snapshot_sequence<=event_head[159:152];
   if(cmd_complete)delivered_sequence<=snapshot_sequence;
   // Only the exact head actually delivered by a complete CMD may be popped.
   if(ack_commit && ack!=0 && head_valid && ack==delivered_sequence && ack==event_head[159:152])begin
    rd<=rd+1'b1;temp_count=temp_count-1;delivered_sequence<=0;
   end
   if(arm_commit)begin
    index_armed<=index_armed|(index_request&~index_level);index_level<=index_request;
    probe_armed<=probe_armed|(probe_request&~probe_level);probe_level<=probe_request;
   end
   if(provider_ready)begin
    for(i=0;i<2;i=i+1)if(edges[i])begin
     if(probe_armed[i])begin
      for(j=0;j<4;j=j+1)values[95-24*j -:24]=capture(io_page1[431-(3+6*i+j)*8 -:8]);
      enqueue(i[2:0],8'd1,i[7:0],{6'd0,probe_overrun[i],next_filtered[i]},values);
      probe_armed[i]<=0;
     end else if(probe_level[i])probe_overrun[i]<=1;
    end
    for(i=0;i<4;i=i+1)if(index_pulse[i] && index_armed[i])begin
     enqueue(i+2,8'd2,i[7:0],8'd0,{index_counts[95-24*i -:24],72'd0});index_armed[i]<=0;
    end
   end else begin index_armed<=0;probe_armed<=0;end
   newly_set=fault_word&~previous_fault;previous_fault<=fault_word;
   if(newly_set!=0)begin
    source=0;for(k=31;k>=0;k=k-1)if(newly_set[k])source=k[7:0];
    enqueue(3'd6,8'd3,source,8'd0,{fault_word[23:0],fault_word[31:24],4'd0,armed_mask,
                           safety_word[23:0],safety_word[31:24],4'd0,pos_continuity});
   end
   // Prefix zero is copied literally: adding zero to a partially X/Z
   // value would erase known bits in four-state simulation.
   sequence_value[0]=temp_sequence;slot_value[0]=temp_wr;
   for(p=1;p<8;p=p+1)begin
    sequence_value[p]=sequence_value[p-1]==255?8'd1:sequence_value[p-1]+8'd1;
    slot_value[p]=temp_wr+p[7:0];
   end
   offered_prefix=0;accepted_count=0;
   for(p=0;p<7;p=p+1)begin
    if(offered_valid[p])begin
     if(temp_count<256 && {6'd0,offered_prefix}<(9'd256-temp_count))begin
      accepted_valid[p]=1'b1;
      accepted_slot[p]=slot_value[offered_prefix];
      accepted_payload[p]={sequence_value[offered_prefix],offered_payload[p]};
      accepted_count=accepted_count+3'd1;
     end else overflow<=1;
     offered_prefix=offered_prefix+3'd1;
    end
   end
   for(b=0;b<8;b=b+1)begin
    bank_select=0;
    for(p=0;p<7;p=p+1)begin
     if(accepted_valid[p] && accepted_slot[p][2:0]==b[2:0])bank_select[p]=1'b1;
    end
    case(bank_select)
     7'b0000001:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[0][7:3];next_write_data[160*b +:160]=accepted_payload[0];end
     7'b0000010:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[1][7:3];next_write_data[160*b +:160]=accepted_payload[1];end
     7'b0000100:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[2][7:3];next_write_data[160*b +:160]=accepted_payload[2];end
     7'b0001000:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[3][7:3];next_write_data[160*b +:160]=accepted_payload[3];end
     7'b0010000:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[4][7:3];next_write_data[160*b +:160]=accepted_payload[4];end
     7'b0100000:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[5][7:3];next_write_data[160*b +:160]=accepted_payload[5];end
     7'b1000000:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[6][7:3];next_write_data[160*b +:160]=accepted_payload[6];end
     default:begin end
    endcase
   end
   if(accepted_count!=0)begin
    temp_wr=temp_wr+{5'd0,accepted_count};
    temp_count=temp_count+{6'd0,accepted_count};
    temp_sequence=sequence_value[accepted_count];
   end
   wr<=temp_wr[7:0];count<=temp_count[8:0];next_sequence<=temp_sequence[7:0];
   write_enable<=next_write_enable;write_address<=next_write_address;write_data<=next_write_data;
   if(clear)begin
    rd<=0;wr<=0;count<=0;next_sequence<=1;snapshot_sequence<=0;delivered_sequence<=0;
    index_level<=0;index_armed<=0;probe_level<=0;probe_armed<=0;probe_overrun<=0;
    previous_fault<=fault_word;overflow<=0;
    write_enable<=0;prefetched_rd<=0;
   end
  end
 end
endmodule
