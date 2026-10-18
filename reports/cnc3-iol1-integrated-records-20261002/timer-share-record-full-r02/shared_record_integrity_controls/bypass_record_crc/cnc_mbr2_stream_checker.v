`timescale 1ns/1ps
// One shared bit-serial CRC engine over actual accepted IDENT chunks.
// Integrity/shape observations do not authenticate the record, UID or factory.
module cnc_mbr2_stream_checker #(
 parameter [3:0] HARDWARE_MAJOR=1,
 parameter [255:0] SOURCE_SHA=256'h6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8
)(input wire clk,reset_n,enable,input wire[3:0] lane_fault,
 input wire[3:0] chunk_accepted,input wire[23:0] chunk_index,input wire[255:0] chunk_data,
 output reg[3:0] record_integrity_observed,record_failed,
 output reg[511:0] observed_board_serial,output reg[383:0] observed_mcu_uid,
 output reg[127:0] observed_generation,
 output wire signature_authenticated,output wire factory_identity_verified,
 output wire commercial_active);
 assign signature_authenticated=0;assign factory_identity_verified=0;assign commercial_active=0;
 reg[3:0] pending;reg[63:0] queued_data[0:3];reg[5:0] queued_index[0:3];
 reg[31:0] crc[0:3];reg[6:0] next_chunk[0:3];reg[3:0] shape_good,serial_seen,serial_pad;
 reg busy;reg[1:0] owner;reg[63:0] work;reg[5:0] bit_number;
 reg[31:0] work_crc;
 wire[5:0] bit_address=6'd56-{bit_number[5:3],3'b0}+{3'd0,bit_number[2:0]};
 wire bit_value=work[bit_address];
 wire[31:0] crc_step=(work_crc[0]^bit_value)?((work_crc>>1)^32'h82f63b78):(work_crc>>1);
 reg found;reg[1:0] selection;integer i;
 wire[3:0] current_queue_fault;
 genvar q;generate for(q=0;q<4;q=q+1)begin: incoming_fault
  assign current_queue_fault[q]=chunk_accepted[q]&&(pending[q]||(busy&&owner==q[1:0])||record_integrity_observed[q]||record_failed[q]);
 end endgenerate
 function[7:0] byte_at;input[63:0] d;input integer n;begin byte_at=d[63-n*8-:8];end endfunction
 function[2:0] shape;
  input old_good,old_pad,old_seen;input[63:0] d;input[5:0] index;input[1:0] slot;
  reg good,pad,seen;reg[7:0] b;integer j;
  begin
   good=old_good;pad=old_pad;seen=old_seen;
   case(index)
    0:good=good&&d=={32'h4d425232,8'd2,slot==0?8'h11:slot==3?8'h31:8'h21,{6'b0,slot},{4'b0,HARDWARE_MAJOR}};
    1:good=good&&d[55:32]==24'h010200&&d[31:0]!=0;
    2,3:for(j=0;j<8;j=j+1)begin b=byte_at(d,j);if(b==0)pad=1;else begin if(pad||b<33||b>126)good=0;seen=1;end end
    5:good=good&&d[31:16]!=0&&d[15:8]<=3&&d[7:0]>=3;
    6:good=good&&d[63:48]<=1&&d[47:32]>=1&&d[31:16]<=3&&d[15:0]>=3;
    7:good=good&&d==64'h0c04181002020202;
    8:good=good&&d[63:32]==32'h040f0000&&d[31:0]==SOURCE_SHA[255:224];
    9:good=good&&d==SOURCE_SHA[223:160];
    10:good=good&&d==SOURCE_SHA[159:96];
    11:good=good&&d==SOURCE_SHA[95:32];
    12:good=good&&d[63:32]==SOURCE_SHA[31:0];
    26:good=good&&d[31:0]==32'hffffffff;
    default:if(index>=27&&index<=54)good=good&&d==64'hffffffffffffffff;
   endcase
   shape={good,pad,seen};
  end
 endfunction
 wire[2:0] next_shape=shape(shape_good[selection],serial_pad[selection],serial_seen[selection],queued_data[selection],queued_index[selection],selection);
 always @*begin
  found=0;selection=0;
  for(integer n=3;n>=0;n=n-1)if(pending[n])begin found=1;selection=n[1:0];end
 end
 always @(posedge clk or negedge reset_n)begin
  if(!reset_n)begin
   pending<=0;busy<=0;owner<=0;work<=0;bit_number<=0;work_crc<=32'hffffffff;
   record_integrity_observed<=0;record_failed<=0;shape_good<=15;serial_seen<=0;serial_pad<=0;
   observed_board_serial<=0;observed_mcu_uid<=0;observed_generation<=0;
   for(i=0;i<4;i=i+1)begin crc[i]<=32'hffffffff;next_chunk[i]<=0;queued_data[i]<=0;queued_index[i]<=0;end
  end else begin
   for(i=0;i<4;i=i+1)begin
    if(chunk_accepted[i])begin
     if(pending[i]||(busy&&owner==i[1:0])||record_integrity_observed[i]||record_failed[i])begin record_failed[i]<=1;record_integrity_observed[i]<=0;end
     else begin pending[i]<=1;queued_data[i]<=chunk_data[i*64+:64];queued_index[i]<=chunk_index[i*6+:6];end
    end
    if(!enable||lane_fault[i])begin pending[i]<=0;record_integrity_observed[i]<=0;if(lane_fault[i]||next_chunk[i]!=0||pending[i]||(busy&&owner==i[1:0]))begin record_failed[i]<=1;shape_good[i]<=0;end end
   end
   if(busy)begin
    work_crc<=crc_step;
    if(bit_number==63)begin
     if(enable&&!lane_fault[owner]&&!record_failed[owner]&&!current_queue_fault[owner])begin crc[owner]<=crc_step;next_chunk[owner]<=next_chunk[owner]+1;end
     busy<=0;
    end else bit_number<=bit_number+1;
   end else if(found)begin
    pending[selection]<=0;owner<=selection;
    if(!enable||lane_fault[selection]||record_failed[selection]||current_queue_fault[selection]||{1'b0,queued_index[selection]}!=next_chunk[selection])begin
     record_failed[selection]<=1;record_integrity_observed[selection]<=0;
    end else if(queued_index[selection]==63)begin
     record_integrity_observed[selection]<=shape_good[selection]&&serial_seen[selection]&&
       1'b1&&queued_data[selection][31:0]==32'h434d5432;
     if(!(shape_good[selection]&&serial_seen[selection]&&1'b1&&queued_data[selection][31:0]==32'h434d5432))record_failed[selection]<=1;
     next_chunk[selection]<=64;
    end else begin
     // Fixed-lane writes avoid a barrel shifter over the entire board tuple.
     for(i=0;i<4;i=i+1)if(selection==i[1:0])begin
      case(queued_index[selection])
       1:observed_generation[i*32+:32]<=queued_data[selection][31:0];
       2:observed_board_serial[i*128+64+:64]<=queued_data[selection];
       3:observed_board_serial[i*128+:64]<=queued_data[selection];
       4:observed_mcu_uid[i*96+32+:64]<=queued_data[selection];
       5:observed_mcu_uid[i*96+:32]<=queued_data[selection][63:32];
       default:begin end
      endcase
     end
     shape_good[selection]<=next_shape[2];serial_pad[selection]<=next_shape[1];serial_seen[selection]<=next_shape[0];work<=queued_data[selection];work_crc<=crc[selection];bit_number<=0;busy<=1;
    end
   end
   // Final priority: a fault/reset cannot be overwritten by a finishing CRC.
   for(i=0;i<4;i=i+1)if(!enable||lane_fault[i]||record_failed[i]||current_queue_fault[i])record_integrity_observed[i]<=0;
  end
 end
endmodule
