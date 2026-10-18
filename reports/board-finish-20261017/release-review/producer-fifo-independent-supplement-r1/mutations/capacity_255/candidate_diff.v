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
 // Seven fixed producers share a global 256-entry admission/order contract.
 // Every producer can write once per cycle without a wide producer/bank crossbar.
 reg[6:0] write_enable;reg[55:0] write_address;reg[1175:0] write_data;
 wire[167:0] bank_data[0:6];reg[7:0] prefetched_rd;
 reg [7:0] rd,wr,next_sequence,snapshot_sequence,delivered_sequence;
 reg [7:0] producer_rd[0:6],producer_wr[0:6],producer_prefetched_rd[0:6];
 reg [8:0] producer_count[0:6],temp_producer_count[0:6];
 reg [7:0] temp_producer_wr[0:6];
 genvar bank;
 generate for(bank=0;bank<7;bank=bank+1)begin:producers
  cnc3_event_producer_bank memory(.clk(clk),.write_enable(write_enable[bank]),
   .write_address(write_address[8*bank +:8]),.write_data(write_data[168*bank +:168]),
   .read_address(producer_rd[bank]),.read_data(bank_data[bank]));
 end endgenerate
 reg [8:0] count;
 reg [3:0] index_level;
 reg [1:0] probe_level,probe_armed,probe_overrun;
 reg [1:0] probe_sync1,probe_sync2,filtered;
 reg [7:0] stable[0:1];
 reg [31:0] previous_fault;
 integer i,j,k,p;reg[8:0]temp_count;reg[7:0]temp_wr,temp_sequence;
 reg[6:0]next_write_enable;reg[55:0]next_write_address;reg[1175:0]next_write_data;
 reg [1:0] next_filtered,edges;
 reg [95:0] values;
 reg [7:0] source;
 reg [31:0] newly_set;
 wire [6:0] producer_head_valid;
 generate for(bank=0;bank<7;bank=bank+1)begin:heads
  wire pending=write_enable[bank] && write_address[8*bank +:8]==producer_rd[bank];
  assign producer_head_valid[bank]=producer_count[bank]!=0 &&
   producer_prefetched_rd[bank]==producer_rd[bank] && !pending &&
   bank_data[bank][167:160]==rd;
 end endgenerate
 wire head_valid=count!=0 && prefetched_rd==rd && |producer_head_valid;
 reg [159:0] selected_head;
 reg [2:0] head_producer;
 integer h;
 always@*begin
  selected_head=0;head_producer=0;
  for(h=0;h<7;h=h+1)if(producer_head_valid[h])begin
   selected_head=bank_data[h][159:0];head_producer=h;
  end
 end
 assign event_head=head_valid?selected_head:160'd0;
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
  input integer producer;
  input [7:0] kind,origin,flags;
  input [95:0] data;
  begin
   if(temp_count<255)begin
    next_write_enable[producer]=1;
    next_write_address[8*producer +:8]=temp_producer_wr[producer];
    next_write_data[168*producer +:168]={temp_wr,temp_sequence,kind,origin,flags,ticks,data};
    temp_producer_wr[producer]=temp_producer_wr[producer]+8'd1;
    temp_producer_count[producer]=temp_producer_count[producer]+9'd1;
    temp_wr=temp_wr+8'd1;temp_count=temp_count+9'd1;
    temp_sequence=temp_sequence==255?8'd1:temp_sequence+8'd1;
   end else overflow<=1;
  end
 endtask
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   rd<=0;wr<=0;count<=0;next_sequence<=1;snapshot_sequence<=0;delivered_sequence<=0;
   index_level<=0;index_armed<=0;probe_level<=0;probe_armed<=0;probe_overrun<=0;
   probe_sync1<=0;probe_sync2<=0;filtered<=0;stable[0]<=0;stable[1]<=0;
   previous_fault<=0;overflow<=0;
   write_enable<=0;write_address<=0;write_data<=0;prefetched_rd<=0;
   for(p=0;p<7;p=p+1)begin
    producer_rd[p]<=0;producer_wr[p]<=0;producer_count[p]<=0;producer_prefetched_rd[p]<=0;
   end
  end else begin
   probe_sync1<=probe_raw;probe_sync2<=probe_sync1;
   temp_count=count;temp_wr=wr;temp_sequence=next_sequence;
   for(p=0;p<7;p=p+1)begin
    temp_producer_count[p]=producer_count[p];temp_producer_wr[p]=producer_wr[p];
    producer_prefetched_rd[p]<=producer_rd[p];
   end
   next_write_enable=0;next_write_address=0;next_write_data=0;prefetched_rd<=rd;
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
    producer_rd[head_producer]<=producer_rd[head_producer]+8'd1;
    temp_producer_count[head_producer]=temp_producer_count[head_producer]-9'd1;
   end
   if(arm_commit)begin
    index_armed<=index_armed|(index_request&~index_level);index_level<=index_request;
    probe_armed<=probe_armed|(probe_request&~probe_level);probe_level<=probe_request;
   end
   if(provider_ready)begin
    for(i=0;i<2;i=i+1)if(edges[i])begin
     if(probe_armed[i])begin
      for(j=0;j<4;j=j+1)values[95-24*j -:24]=capture(io_page1[431-(3+6*i+j)*8 -:8]);
      enqueue(i,8'd1,i[7:0],{6'd0,probe_overrun[i],next_filtered[i]},values);
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
    enqueue(6,8'd3,source,8'd0,{fault_word[23:0],fault_word[31:24],4'd0,armed_mask,
                           safety_word[23:0],safety_word[31:24],4'd0,pos_continuity});
   end
   wr<=temp_wr[7:0];count<=temp_count[8:0];next_sequence<=temp_sequence[7:0];
   for(p=0;p<7;p=p+1)begin
    producer_wr[p]<=temp_producer_wr[p];producer_count[p]<=temp_producer_count[p];
   end
   write_enable<=next_write_enable;write_address<=next_write_address;write_data<=next_write_data;
   if(clear)begin
    rd<=0;wr<=0;count<=0;next_sequence<=1;snapshot_sequence<=0;delivered_sequence<=0;
    index_level<=0;index_armed<=0;probe_level<=0;probe_armed<=0;probe_overrun<=0;
    previous_fault<=fault_word;overflow<=0;
    write_enable<=0;prefetched_rd<=0;
    for(p=0;p<7;p=p+1)begin
     producer_rd[p]<=0;producer_wr[p]<=0;producer_count[p]<=0;producer_prefetched_rd[p]<=0;
    end
   end
  end
 end
endmodule

// Registered memory read and collision bypass preserve the original write-first
// visibility. Tags are global modulo-256 positions, independent of sequence IDs.
module cnc3_event_producer_bank(input wire clk,write_enable,
 input wire[7:0]write_address,read_address,input wire[167:0]write_data,
 output wire[167:0]read_data);
 reg[167:0]memory[0:255];
 reg[167:0]ram_read,forward_data;
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
