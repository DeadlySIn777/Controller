`timescale 1ns/1ps
// SPDX-License-Identifier: LicenseRef-Proprietary
// GENERATED: exact frozen IS-1 static acceptance only; never grants ARM or output authority.
// Byte zero is frame[1407:1400]; CMD occupies high 768 bits, low 640 bits are padding.
module cnc3_command_validate_logic(input wire [1407:0] frame, input wire cs_fb,
 input wire [8:0] frame_bytes, input wire crc_good, input wire embedded_crc_good, output reg [7:0] result);
wire [7:0] opcode=frame[1367:1360];
wire [15:0] mask=frame[1359:1344];
wire [31:0] session=frame[1343:1312], sequence_value=frame[1311:1280];
function u_ge32;input[31:0] x,k;reg equal,greater;integer n;
 begin equal=1;greater=0;for(n=31;n>=0;n=n-1)begin greater=greater|(equal&&x[n]&&!k[n]);equal=equal&&!(x[n]^k[n]);end u_ge32=greater|equal;end
endfunction
function u_le32;input[31:0] x,k;reg equal,less;integer n;
 begin equal=1;less=0;for(n=31;n>=0;n=n-1)begin less=less|(equal&&!x[n]&&k[n]);equal=equal&&!(x[n]^k[n]);end u_le32=less|equal;end
endfunction
always @* begin
result=0;
if (result==0 && (frame_bytes != (cs_fb ? 176 : 96))) result=8'd2;
if (result==0 && (!crc_good)) result=8'd3;
if (result==0 && (frame[1407 -: 32] != 32'h434e4333)) result=8'd4;
if (result==0 && (frame[1375 -: 8] != 8'd3)) result=8'd5;
if (result==0 && (!(opcode==8'h00 || opcode==8'h01 || opcode==8'h02 || opcode==8'h03 || opcode==8'h04 || opcode==8'h05 || opcode==8'h06 || opcode==8'h07 || opcode==8'h08 || opcode==8'h09 || opcode==8'h0a || opcode==8'h0b || opcode==8'h0c || opcode==8'h0d || opcode==8'h0e || opcode==8'h10))) result=8'd6;
if (result==0 && ((cs_fb && !(opcode==8'h05 || opcode==8'h06 || opcode==8'h07 || opcode==8'h0c || opcode==8'h10)) || (!cs_fb && !(opcode==8'h00 || opcode==8'h01 || opcode==8'h02 || opcode==8'h03 || opcode==8'h04 || opcode==8'h08 || opcode==8'h09 || opcode==8'h0a || opcode==8'h0b || opcode==8'h0d || opcode==8'h0e)))) result=8'd7;
if (result==0 && ((mask & 16'hf000) != 0)) result=8'd8;
case(opcode)
8'h00: begin
if (result==0 && (sequence_value != 0)) result=8'd9;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && (|frame[1359 -: 16])) result=8'd14;
if (result==0 && (|frame[1279 -: 624])) result=8'd14;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h01: begin
if (result==0 && (sequence_value != 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && (|frame[1279 -: 624])) result=8'd14;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h02: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (mask == 0)) result=8'd11;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h03: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h04: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (mask != 0)) result=8'd11;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h05: begin
if (result==0 && (sequence_value != 0)) result=8'd9;
if (result==0 && (|frame[1271 -: 1256])) result=8'd14;
if (result==0 && (!((u_le32({24'd0,frame[1279 -: 8]},32'd3))))) result=8'd15;
end
8'h06: begin
if (result==0 && ((session==0) != (sequence_value==0))) result=8'd9;
if (result==0 && (!((u_ge32({24'd0,frame[1279 -: 8]},32'd2) && u_le32({24'd0,frame[1279 -: 8]},32'd2))))) result=8'd15;
if (result==0 && (frame[1263 -: 16] == 0)) result=8'd15;
if (result==0 && ((frame[1231 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && (!((u_ge32({16'd0,frame[1215 -: 16]},32'd100) && u_le32({16'd0,frame[1215 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1199 -: 16]},32'd100) && u_le32({16'd0,frame[1199 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1183 -: 16]},32'd100) && u_le32({16'd0,frame[1183 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1167 -: 16]},32'd100) && u_le32({16'd0,frame[1167 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1151 -: 16]},32'd100) && u_le32({16'd0,frame[1151 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1135 -: 16]},32'd100) && u_le32({16'd0,frame[1135 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1119 -: 16]},32'd100) && u_le32({16'd0,frame[1119 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1103 -: 16]},32'd100) && u_le32({16'd0,frame[1103 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1087 -: 16]},32'd100) && u_le32({16'd0,frame[1087 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1071 -: 16]},32'd100) && u_le32({16'd0,frame[1071 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1055 -: 16]},32'd100) && u_le32({16'd0,frame[1055 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1039 -: 16]},32'd100) && u_le32({16'd0,frame[1039 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1023 -: 16]},32'd100) && u_le32({16'd0,frame[1023 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1007 -: 16]},32'd100) && u_le32({16'd0,frame[1007 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[991 -: 16]},32'd100) && u_le32({16'd0,frame[991 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[975 -: 16]},32'd100) && u_le32({16'd0,frame[975 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[959 -: 16]},32'd100) && u_le32({16'd0,frame[959 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[943 -: 16]},32'd100) && u_le32({16'd0,frame[943 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[927 -: 16]},32'd100) && u_le32({16'd0,frame[927 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[911 -: 16]},32'd100) && u_le32({16'd0,frame[911 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[895 -: 16]},32'd100) && u_le32({16'd0,frame[895 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[879 -: 16]},32'd100) && u_le32({16'd0,frame[879 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[863 -: 16]},32'd100) && u_le32({16'd0,frame[863 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[847 -: 16]},32'd100) && u_le32({16'd0,frame[847 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[831 -: 16]},32'd100) && u_le32({16'd0,frame[831 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[815 -: 16]},32'd100) && u_le32({16'd0,frame[815 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[799 -: 16]},32'd100) && u_le32({16'd0,frame[799 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[783 -: 16]},32'd100) && u_le32({16'd0,frame[783 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[767 -: 16]},32'd100) && u_le32({16'd0,frame[767 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[751 -: 16]},32'd100) && u_le32({16'd0,frame[751 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[735 -: 16]},32'd100) && u_le32({16'd0,frame[735 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[719 -: 16]},32'd100) && u_le32({16'd0,frame[719 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[703 -: 16]},32'd100) && u_le32({16'd0,frame[703 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[687 -: 16]},32'd100) && u_le32({16'd0,frame[687 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[671 -: 16]},32'd100) && u_le32({16'd0,frame[671 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[655 -: 16]},32'd100) && u_le32({16'd0,frame[655 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[639 -: 16]},32'd100) && u_le32({16'd0,frame[639 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[623 -: 16]},32'd100) && u_le32({16'd0,frame[623 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[607 -: 16]},32'd100) && u_le32({16'd0,frame[607 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[591 -: 16]},32'd100) && u_le32({16'd0,frame[591 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[575 -: 16]},32'd100) && u_le32({16'd0,frame[575 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[559 -: 16]},32'd100) && u_le32({16'd0,frame[559 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[543 -: 16]},32'd100) && u_le32({16'd0,frame[543 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[527 -: 16]},32'd100) && u_le32({16'd0,frame[527 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[511 -: 16]},32'd100) && u_le32({16'd0,frame[511 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[495 -: 16]},32'd100) && u_le32({16'd0,frame[495 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[479 -: 16]},32'd100) && u_le32({16'd0,frame[479 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[463 -: 16]},32'd100) && u_le32({16'd0,frame[463 -: 16]},32'd1023))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[415 -: 16]},32'd250) && u_le32({16'd0,frame[415 -: 16]},32'd2500))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[399 -: 8]},32'd0)) || (u_ge32({24'd0,frame[399 -: 8]},32'd1) && u_le32({24'd0,frame[399 -: 8]},32'd1))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[391 -: 8]},32'd15))))) result=8'd15;
if (result==0 && ((frame[367 -: 8] & 8'hf0) != 0)) result=8'd18;
if (result==0 && (|frame[359 -: 344])) result=8'd17;
if (result==0 && ((frame[1263 -: 16] & 16'hf00) != 0 && (frame[1271 -: 8] == 0))) result=8'd19;
if (result==0 && ((frame[1247 -: 16] & ~frame[1263 -: 16]) != 0)) result=8'd19;
if (result==0 && ((frame[383 -: 16] & 16'hff0) != 0 && (frame[399 -: 8] != 1))) result=8'd19;
end
8'h07: begin
if (result==0 && ((session==0) != (sequence_value==0))) result=8'd9;
case(frame[1279 -: 8])
8'd2, 8'd3, 8'd4, 8'd5, 8'd6, 8'd7, 8'd8, 8'd9: begin
if (result==0 && (!((u_ge32({24'd0,frame[1279 -: 8]},32'd2) && u_le32({24'd0,frame[1279 -: 8]},32'd9))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1271 -: 8]},32'd3))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1263 -: 8]},32'd7))))) result=8'd15;
if (result==0 && (|frame[1063 -: 1048])) result=8'd17;
end
8'd0: begin
if (result==0 && (!((u_le32({24'd0,frame[1279 -: 8]},32'd0))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1167 -: 16]},32'd250) && u_le32({16'd0,frame[1167 -: 16]},32'd440))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1151 -: 16]},32'd250) && u_le32({16'd0,frame[1151 -: 16]},32'd440))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1135 -: 8]},32'd0))))) result=8'd15;
if (result==0 && (|frame[1127 -: 1112])) result=8'd17;
end
8'd1: begin
if (result==0 && (!((u_ge32({24'd0,frame[1279 -: 8]},32'd1) && u_le32({24'd0,frame[1279 -: 8]},32'd1))))) result=8'd15;
if (result==0 && ((frame[1271 -: 8] & 8'hfe) != 0)) result=8'd18;
if (result==0 && (!((u_le32({24'd0,frame[1255 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1255 -: 8]},32'd16) && u_le32({24'd0,frame[1255 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1255 -: 8]},32'd32) && u_le32({24'd0,frame[1255 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1255 -: 8]},32'd255))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1247 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1247 -: 8]},32'd16) && u_le32({24'd0,frame[1247 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1247 -: 8]},32'd32) && u_le32({24'd0,frame[1247 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1247 -: 8]},32'd255))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1239 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1239 -: 8]},32'd16) && u_le32({24'd0,frame[1239 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1239 -: 8]},32'd32) && u_le32({24'd0,frame[1239 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1239 -: 8]},32'd255))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1231 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1231 -: 8]},32'd16) && u_le32({24'd0,frame[1231 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1231 -: 8]},32'd32) && u_le32({24'd0,frame[1231 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1231 -: 8]},32'd255))))) result=8'd15;
if (result==0 && ((frame[1223 -: 8] & 8'hfe) != 0)) result=8'd18;
if (result==0 && (!((u_le32({24'd0,frame[1207 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1207 -: 8]},32'd16) && u_le32({24'd0,frame[1207 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1207 -: 8]},32'd32) && u_le32({24'd0,frame[1207 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1207 -: 8]},32'd255))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1199 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1199 -: 8]},32'd16) && u_le32({24'd0,frame[1199 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1199 -: 8]},32'd32) && u_le32({24'd0,frame[1199 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1199 -: 8]},32'd255))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1191 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1191 -: 8]},32'd16) && u_le32({24'd0,frame[1191 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1191 -: 8]},32'd32) && u_le32({24'd0,frame[1191 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1191 -: 8]},32'd255))))) result=8'd15;
if (result==0 && (!((u_le32({24'd0,frame[1183 -: 8]},32'd11)) || (u_ge32({24'd0,frame[1183 -: 8]},32'd16) && u_le32({24'd0,frame[1183 -: 8]},32'd27)) || (u_ge32({24'd0,frame[1183 -: 8]},32'd32) && u_le32({24'd0,frame[1183 -: 8]},32'd32)) || (u_ge32({24'd0,frame[1183 -: 8]},32'd255))))) result=8'd15;
if (result==0 && ((frame[1175 -: 8] & 8'hfe) != 0)) result=8'd18;
if (result==0 && (!((u_le32({24'd0,frame[1167 -: 8]},32'd15))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1159 -: 16]},32'd1) && u_le32({16'd0,frame[1159 -: 16]},32'd10000))))) result=8'd15;
if (result==0 && ((frame[1143 -: 8] & 8'hfe) != 0)) result=8'd18;
if (result==0 && (!((u_le32({24'd0,frame[1135 -: 8]},32'd15))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[1127 -: 16]},32'd1) && u_le32({16'd0,frame[1127 -: 16]},32'd10000))))) result=8'd15;
if (result==0 && (!((u_ge32(frame[1111 -: 32],32'd50) && u_le32(frame[1111 -: 32],32'd50000000))))) result=8'd15;
if (result==0 && (frame[1063 -: 8] != 0)) result=8'd17;
if (result==0 && (!((u_ge32(frame[1055 -: 32],32'd50) && u_le32(frame[1055 -: 32],32'd50000000))))) result=8'd15;
if (result==0 && (frame[1007 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[967 -: 8] & 8'hc0) != 0)) result=8'd18;
if (result==0 && (!((u_ge32({16'd0,frame[959 -: 16]},32'd500) && u_le32({16'd0,frame[959 -: 16]},32'd10000))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[943 -: 16]},32'd20) && u_le32({16'd0,frame[943 -: 16]},32'd2000))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[927 -: 16]},32'd100) && u_le32({16'd0,frame[927 -: 16]},32'd5000))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[911 -: 16]},32'd10) && u_le32({16'd0,frame[911 -: 16]},32'd2000))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[895 -: 16]},32'd10) && u_le32({16'd0,frame[895 -: 16]},32'd2000))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[879 -: 16]},32'd1) && u_le32({16'd0,frame[879 -: 16]},32'd2000))))) result=8'd15;
if (result==0 && (!((u_ge32({16'd0,frame[863 -: 16]},32'd10) && u_le32({16'd0,frame[863 -: 16]},32'd5000))))) result=8'd15;
if (result==0 && (|frame[847 -: 832])) result=8'd17;
end
default: if(result==0) result=8'd15; endcase
end
8'h08: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (mask != 0)) result=8'd11;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h09: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (mask != 0)) result=8'd11;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h0a: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && (|frame[1279 -: 624])) result=8'd14;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h0b: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && (|frame[1279 -: 624])) result=8'd14;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h0c: begin
if (result==0 && (sequence_value != 0)) result=8'd9;
if (result==0 && (!((u_le32({24'd0,frame[1279 -: 8]},32'd3))))) result=8'd15;
if (result==0 && (!embedded_crc_good || frame[1271 -: 8]!=8'ha7 || frame[1263 -: 8]!=1 || (frame[1247 -: 8] & 8'hf0)!=0 || frame[1239 -: 16]==0 || (frame[1207 -: 8] & 8'hc0)!=0 || ((frame[1207 -: 8] & 1)!=0) != (frame[1223 -: 16]==0) || (frame[1207 -: 8] & 8'h20)==0)) result=8'd16;
if (result==0 && (frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0 || frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0 || frame[895 -: 8] != 0 || frame[887 -: 8] != 0 || frame[879 -: 8] != 0 || frame[871 -: 8] != 0 || frame[863 -: 8] != 0 || frame[855 -: 8] != 0 || frame[847 -: 8] != 0 || frame[839 -: 8] != 0 || frame[831 -: 8] != 0 || frame[823 -: 8] != 0 || frame[815 -: 8] != 0 || frame[807 -: 8] != 0 || frame[799 -: 8] != 0 || frame[791 -: 8] != 0 || frame[783 -: 8] != 0 || frame[775 -: 8] != 0 || frame[767 -: 8] != 0 || frame[759 -: 8] != 0 || frame[751 -: 8] != 0 || frame[743 -: 8] != 0 || frame[735 -: 8] != 0 || frame[727 -: 8] != 0 || frame[719 -: 8] != 0 || frame[711 -: 8] != 0 || frame[703 -: 8] != 0 || frame[695 -: 8] != 0 || frame[687 -: 8] != 0 || frame[679 -: 8] != 0 || frame[671 -: 8] != 0 || frame[663 -: 8] != 0 || frame[655 -: 8] != 0 || frame[647 -: 8] != 0 || frame[639 -: 8] != 0 || frame[631 -: 8] != 0 || frame[623 -: 8] != 0 || frame[615 -: 8] != 0 || frame[607 -: 8] != 0 || frame[599 -: 8] != 0 || frame[591 -: 8] != 0 || frame[583 -: 8] != 0 || frame[575 -: 8] != 0 || frame[567 -: 8] != 0 || frame[559 -: 8] != 0 || frame[551 -: 8] != 0 || frame[543 -: 8] != 0 || frame[535 -: 8] != 0 || frame[527 -: 8] != 0 || frame[519 -: 8] != 0 || frame[511 -: 8] != 0 || frame[503 -: 8] != 0 || frame[495 -: 8] != 0 || frame[487 -: 8] != 0 || frame[479 -: 8] != 0 || frame[471 -: 8] != 0 || frame[463 -: 8] != 0 || frame[455 -: 8] != 0 || frame[447 -: 8] != 0 || frame[439 -: 8] != 0 || frame[431 -: 8] != 0 || frame[423 -: 8] != 0 || frame[415 -: 8] != 0 || frame[407 -: 8] != 0 || frame[399 -: 8] != 0 || frame[391 -: 8] != 0 || frame[383 -: 8] != 0 || frame[375 -: 8] != 0 || frame[367 -: 8] != 0 || frame[359 -: 8] != 0 || frame[351 -: 8] != 0 || frame[343 -: 8] != 0 || frame[335 -: 8] != 0 || frame[327 -: 8] != 0 || frame[319 -: 8] != 0 || frame[311 -: 8] != 0 || frame[303 -: 8] != 0 || frame[295 -: 8] != 0 || frame[287 -: 8] != 0 || frame[279 -: 8] != 0 || frame[271 -: 8] != 0 || frame[263 -: 8] != 0 || frame[255 -: 8] != 0 || frame[247 -: 8] != 0 || frame[239 -: 8] != 0 || frame[231 -: 8] != 0 || frame[223 -: 8] != 0 || frame[215 -: 8] != 0 || frame[207 -: 8] != 0 || frame[199 -: 8] != 0 || frame[191 -: 8] != 0 || frame[183 -: 8] != 0 || frame[175 -: 8] != 0 || frame[167 -: 8] != 0 || frame[159 -: 8] != 0 || frame[151 -: 8] != 0 || frame[143 -: 8] != 0 || frame[135 -: 8] != 0 || frame[127 -: 8] != 0 || frame[119 -: 8] != 0 || frame[111 -: 8] != 0 || frame[103 -: 8] != 0 || frame[95 -: 8] != 0 || frame[87 -: 8] != 0 || frame[79 -: 8] != 0 || frame[71 -: 8] != 0 || frame[63 -: 8] != 0 || frame[55 -: 8] != 0 || frame[47 -: 8] != 0 || frame[39 -: 8] != 0 || frame[31 -: 8] != 0 || frame[23 -: 8] != 0)) result=8'd14;
end
8'h0d: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && (!((u_ge32({24'd0,frame[1279 -: 8]},32'd1) && u_le32({24'd0,frame[1279 -: 8]},32'd1)) || (u_ge32({24'd0,frame[1279 -: 8]},32'd2) && u_le32({24'd0,frame[1279 -: 8]},32'd2))))) result=8'd15;
if (result==0 && (frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0 || frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0 || frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0 || frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0 || frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0 || frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0 || frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0 || frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0 || frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0 || frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0 || frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0 || frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0 || frame[895 -: 8] != 0 || frame[887 -: 8] != 0 || frame[879 -: 8] != 0 || frame[871 -: 8] != 0 || frame[863 -: 8] != 0 || frame[855 -: 8] != 0 || frame[847 -: 8] != 0 || frame[839 -: 8] != 0 || frame[831 -: 8] != 0 || frame[823 -: 8] != 0 || frame[815 -: 8] != 0 || frame[807 -: 8] != 0 || frame[799 -: 8] != 0 || frame[791 -: 8] != 0 || frame[783 -: 8] != 0 || frame[775 -: 8] != 0 || frame[767 -: 8] != 0 || frame[759 -: 8] != 0 || frame[751 -: 8] != 0 || frame[743 -: 8] != 0 || frame[735 -: 8] != 0 || frame[727 -: 8] != 0 || frame[719 -: 8] != 0 || frame[711 -: 8] != 0 || frame[703 -: 8] != 0 || frame[695 -: 8] != 0 || frame[687 -: 8] != 0 || frame[679 -: 8] != 0 || frame[671 -: 8] != 0 || frame[663 -: 8] != 0)) result=8'd14;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h0e: begin
if (result==0 && (sequence_value == 0)) result=8'd9;
if (result==0 && (session == 0)) result=8'd10;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0)) result=8'd12;
if (result==0 && (frame[895 -: 8] != 0 || frame[887 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[767 -: 8] != 0 || frame[759 -: 8] != 0)) result=8'd13;
if (result==0 && (frame[1279 -: 8] != 0 || frame[1271 -: 8] != 0 || frame[1263 -: 8] != 0 || frame[1255 -: 8] != 0 || frame[1247 -: 8] != 0 || frame[1239 -: 8] != 0 || frame[1231 -: 8] != 0 || frame[1223 -: 8] != 0 || frame[1215 -: 8] != 0 || frame[1207 -: 8] != 0 || frame[1199 -: 8] != 0 || frame[1191 -: 8] != 0 || frame[1183 -: 8] != 0 || frame[1175 -: 8] != 0 || frame[1167 -: 8] != 0 || frame[1159 -: 8] != 0 || frame[1151 -: 8] != 0 || frame[1143 -: 8] != 0 || frame[1135 -: 8] != 0 || frame[1127 -: 8] != 0 || frame[1119 -: 8] != 0 || frame[1111 -: 8] != 0 || frame[1103 -: 8] != 0 || frame[1095 -: 8] != 0 || frame[1087 -: 8] != 0 || frame[1079 -: 8] != 0 || frame[1071 -: 8] != 0 || frame[1063 -: 8] != 0 || frame[1055 -: 8] != 0 || frame[1047 -: 8] != 0 || frame[1039 -: 8] != 0 || frame[1031 -: 8] != 0 || frame[1023 -: 8] != 0 || frame[1015 -: 8] != 0 || frame[1007 -: 8] != 0 || frame[999 -: 8] != 0 || frame[991 -: 8] != 0 || frame[983 -: 8] != 0 || frame[975 -: 8] != 0 || frame[967 -: 8] != 0 || frame[959 -: 8] != 0 || frame[951 -: 8] != 0 || frame[943 -: 8] != 0 || frame[935 -: 8] != 0 || frame[927 -: 8] != 0 || frame[919 -: 8] != 0 || frame[911 -: 8] != 0 || frame[903 -: 8] != 0 || frame[895 -: 8] != 0 || frame[887 -: 8] != 0 || frame[879 -: 8] != 0 || frame[871 -: 8] != 0 || frame[863 -: 8] != 0 || frame[855 -: 8] != 0 || frame[847 -: 8] != 0 || frame[839 -: 8] != 0 || frame[831 -: 8] != 0 || frame[823 -: 8] != 0 || frame[815 -: 8] != 0 || frame[807 -: 8] != 0 || frame[799 -: 8] != 0 || frame[791 -: 8] != 0 || frame[783 -: 8] != 0 || frame[775 -: 8] != 0 || frame[767 -: 8] != 0 || frame[759 -: 8] != 0 || frame[751 -: 8] != 0 || frame[743 -: 8] != 0 || frame[735 -: 8] != 0 || frame[727 -: 8] != 0 || frame[719 -: 8] != 0 || frame[711 -: 8] != 0 || frame[703 -: 8] != 0 || frame[695 -: 8] != 0 || frame[687 -: 8] != 0 || frame[679 -: 8] != 0 || frame[671 -: 8] != 0 || frame[663 -: 8] != 0)) result=8'd14;
if (result==0 && ((frame[879 -: 8] & 8'h80) != 0)) result=8'd18;
if (result==0 && (frame[871 -: 8] != 0)) result=8'd17;
if (result==0 && ((frame[863 -: 16] & 16'hf000) != 0)) result=8'd18;
if (result==0 && ((frame[847 -: 8] & 8'hfc) != 0)) result=8'd18;
if (result==0 && (frame[839 -: 8] != 0)) result=8'd17;
if (result==0 && (|frame[751 -: 96])) result=8'd17;
if (result==0 && ((frame[767 -: 16] & frame[895 -: 16]) != 0)) result=8'd19;
if (result==0 && (!mask[0] && frame[1279 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[1] && frame[1247 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[2] && frame[1215 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[3] && frame[1183 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[4] && frame[1151 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[5] && frame[1119 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[6] && frame[1087 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[7] && frame[1055 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[8] && frame[1023 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[9] && frame[991 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[10] && frame[959 -: 32] != 0)) result=8'd20;
if (result==0 && (!mask[11] && frame[927 -: 32] != 0)) result=8'd20;
end
8'h10: begin
if (result==0 && (sequence_value != 0)) result=8'd9;
if (result==0 && (|frame[1255 -: 1240])) result=8'd17;
end
default: begin end
endcase
end
endmodule
