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
 reg found;reg[1:0] selection;integer i,j;reg good,pad,seen;reg[7:0] b;
 function[7:0] byte_at;input[63:0] d;input integer n;begin byte_at=d[63-n*8-:8];end endfunction
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
     if(enable&&!lane_fault[owner]&&!record_failed[owner])begin crc[owner]<=crc_step;next_chunk[owner]<=next_chunk[owner]+1;end
     busy<=0;
    end else bit_number<=bit_number+1;
   end else if(found)begin
    pending[selection]<=0;owner<=selection;
    if(!enable||lane_fault[selection]||record_failed[selection]||{1'b0,queued_index[selection]}!=next_chunk[selection])begin
     record_failed[selection]<=1;record_integrity_observed[selection]<=0;
    end else if(queued_index[selection]==63)begin
     record_integrity_observed[selection]<=shape_good[selection]&&serial_seen[selection]&&
       queued_data[selection][63:32]==(crc[selection]^32'hffffffff)&&queued_data[selection][31:0]==32'h434d5432;
     if(!(shape_good[selection]&&serial_seen[selection]&&queued_data[selection][63:32]==(crc[selection]^32'hffffffff)&&queued_data[selection][31:0]==32'h434d5432))record_failed[selection]<=1;
     next_chunk[selection]<=64;
    end else begin
     good=shape_good[selection];pad=serial_pad[selection];seen=serial_seen[selection];
     case(queued_index[selection])
      0:good=good&&queued_data[selection]=={32'h4d425232,8'd2,selection==0?8'h11:selection==3?8'h31:8'h21,{6'b0,selection},{4'b0,HARDWARE_MAJOR}};
      1:begin good=good&&queued_data[selection][55:32]==24'h010200&&queued_data[selection][31:0]!=0;observed_generation[selection*32+:32]<=queued_data[selection][31:0];end
      2,3:begin
       for(j=0;j<8;j=j+1)begin b=byte_at(queued_data[selection],j);if(b==0)pad=1;else begin if(pad||b<33||b>126)good=0;seen=1;end end
       observed_board_serial[selection*128+(queued_index[selection]==2?64:0)+:64]<=queued_data[selection];
       serial_pad[selection]<=pad;serial_seen[selection]<=seen;
      end
      4:observed_mcu_uid[selection*96+32+:64]<=queued_data[selection];
      5:begin observed_mcu_uid[selection*96+:32]<=queued_data[selection][63:32];good=good&&queued_data[selection][31:16]!=0&&queued_data[selection][15:8]<=3&&queued_data[selection][7:0]>=3;end
      6:good=good&&queued_data[selection][63:48]<=1&&queued_data[selection][47:32]>=1&&queued_data[selection][31:16]<=3&&queued_data[selection][15:0]>=3;
      7:good=good&&queued_data[selection]==64'h0c04181002020202;
      8:good=good&&queued_data[selection][63:32]==32'h040f0000&&queued_data[selection][31:0]==SOURCE_SHA[255:224];
      9:good=good&&queued_data[selection]==SOURCE_SHA[223:160];
      10:good=good&&queued_data[selection]==SOURCE_SHA[159:96];
      11:good=good&&queued_data[selection]==SOURCE_SHA[95:32];
      12:good=good&&queued_data[selection][63:32]==SOURCE_SHA[31:0];
      26:good=good&&queued_data[selection][31:0]==32'hffffffff;
      default:if(queued_index[selection]>=27&&queued_index[selection]<=54)good=good&&queued_data[selection]==64'hffffffffffffffff;
     endcase
     shape_good[selection]<=good;work<=queued_data[selection];work_crc<=crc[selection];bit_number<=0;busy<=1;
    end
   end
   // Final priority: a fault/reset cannot be overwritten by a finishing CRC.
   for(i=0;i<4;i=i+1)if(!enable||lane_fault[i]||record_failed[i])record_integrity_observed[i]<=0;
  end
 end
endmodule
