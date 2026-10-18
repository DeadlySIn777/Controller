`timescale 1ns/1ps
// Bounded 256-record frozen CNS3 event ring with real probe/index capture.
module cnc3_runtime_events(
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
 integer i,j,k;reg[8:0]temp_count;reg[7:0]temp_wr,temp_sequence;
 reg[7:0]next_write_enable;reg[39:0]next_write_address;reg[1279:0]next_write_data;
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
   if(selector<12)capture=step_counts[287-24*selector -:24];
   else if(selector>=16 && selector<20)capture=encoder_counts[95-24*(selector-16) -:24];
   else capture=0;
  end
 endfunction
 task enqueue;
  input [7:0] kind,origin,flags;
  input [95:0] data;
  begin
   if(temp_count<256)begin
    case(temp_wr[2:0])
     3'd0:begin next_write_enable[0]=1;next_write_address[0 +:5]=temp_wr[7:3];next_write_data[0 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd1:begin next_write_enable[1]=1;next_write_address[5 +:5]=temp_wr[7:3];next_write_data[160 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd2:begin next_write_enable[2]=1;next_write_address[10 +:5]=temp_wr[7:3];next_write_data[320 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd3:begin next_write_enable[3]=1;next_write_address[15 +:5]=temp_wr[7:3];next_write_data[480 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd4:begin next_write_enable[4]=1;next_write_address[20 +:5]=temp_wr[7:3];next_write_data[640 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd5:begin next_write_enable[5]=1;next_write_address[25 +:5]=temp_wr[7:3];next_write_data[800 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd6:begin next_write_enable[6]=1;next_write_address[30 +:5]=temp_wr[7:3];next_write_data[960 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
     3'd7:begin next_write_enable[7]=1;next_write_address[35 +:5]=temp_wr[7:3];next_write_data[1120 +:160]={temp_sequence,kind,origin,flags,ticks,data};end
    endcase
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
  end else begin
   probe_sync1<=probe_raw;probe_sync2<=probe_sync1;
   temp_count=count;temp_wr=wr;temp_sequence=next_sequence;
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
   end
   if(arm_commit)begin
    index_armed<=index_armed|(index_request&~index_level);index_level<=index_request;
    probe_armed<=probe_armed|(probe_request&~probe_level);probe_level<=probe_request;
   end
   if(provider_ready)begin
    for(i=0;i<2;i=i+1)if(edges[i])begin
     if(probe_armed[i])begin
      for(j=0;j<4;j=j+1)values[95-24*j -:24]=capture(io_page1[431-(3+6*i+j)*8 -:8]);
      enqueue(8'd1,i[7:0],{6'd0,probe_overrun[i],next_filtered[i]},values);
      probe_armed[i]<=0;
     end else if(probe_level[i])probe_overrun[i]<=1;
    end
    for(i=0;i<4;i=i+1)if(index_pulse[i] && index_armed[i])begin
     enqueue(8'd2,i[7:0],8'd0,{index_counts[95-24*i -:24],72'd0});index_armed[i]<=0;
    end
   end else begin index_armed<=0;probe_armed<=0;end
   newly_set=fault_word&~previous_fault;previous_fault<=fault_word;
   if(newly_set!=0)begin
    source=0;for(k=31;k>=0;k=k-1)if(newly_set[k])source=k[7:0];
    enqueue(8'd3,source,8'd0,{fault_word[23:0],fault_word[31:24],4'd0,armed_mask,
                           safety_word[23:0],safety_word[31:24],4'd0,pos_continuity});
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
