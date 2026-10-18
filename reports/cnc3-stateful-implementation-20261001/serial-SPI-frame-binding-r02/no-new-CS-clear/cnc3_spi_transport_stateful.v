`timescale 1ns/1ps
// SPDX-License-Identifier: LicenseRef-Proprietary
// Real mode-0 SPI frame transport. One core-clock domain; independent asynchronous
// inputs are sampled through three-stage synchronizers. Logical timing guards are
// tested in RTL; metastability, board delay and vendor fit remain qualification.
// RX CMD is left aligned in 1408 bits. Snapshot inputs exclude their CRC bytes.
module cnc3_spi_transport_stateful (
 input wire clk, input wire rst_n,
 input wire spi_cs_fb_n, input wire spi_cs_cmd_n, input wire spi_sclk, input wire spi_mosi,
 input wire [1391:0] feedback_payload, input wire [751:0] status_payload,
 output reg spi_miso, output wire spi_miso_oe,
 output reg [1407:0] frame, output reg frame_cs_fb,
 output reg frame_valid, output reg frame_bad, output reg embedded_crc_good,
 output reg snapshot_start, output reg snapshot_cs_fb,
 // Rejection-only physical first-six-byte capture: never a valid command.
 output reg rejection_header_valid,output reg [47:0] rejection_header,
 output reg rejection_header_cs_fb,
 input wire rate_frame_good,output reg frame_rates_good,
 output reg rx_rate_word_valid,output reg[3:0] rx_rate_channel,output reg[31:0] rx_rate_word
);
 reg [2:0] fb_sync, cmd_sync, sck_sync, mosi_sync;
 wire fb_start=fb_sync[2] & ~fb_sync[1], cmd_start=cmd_sync[2] & ~cmd_sync[1];
 wire fb_end=~fb_sync[2] & fb_sync[1], cmd_end=~cmd_sync[2] & cmd_sync[1];
 wire sck_rise=~sck_sync[2] & sck_sync[1], sck_fall=sck_sync[2] & ~sck_sync[1];
 wire both_low=~fb_sync[1] & ~cmd_sync[1];
 reg active, selected_fb, invalid, rise_d;
 reg [10:0] bit_count, expected_bits, body_bits;
 reg [1407:0] rx_shift;
 reg [47:0] rx_header;
 reg [1391:0] tx_shift;
 reg [15:0] rx_crc, tx_crc;
 reg [31:0] inner_crc, ticks, start_tick, last_rise_tick, last_fall_tick, last_end_tick;
 reg seen_rise, seen_fall;
 // Physical bus release is independent of the synchronized state machine.
 assign spi_miso_oe=rst_n && (spi_cs_fb_n ^ spi_cs_cmd_n);
 function [15:0] crc_bit;
  input [15:0] old_crc; input data_bit;
  begin crc_bit={old_crc[14:0],1'b0}; if(old_crc[15]^data_bit) crc_bit=crc_bit^16'h1021; end
 endfunction
 function [31:0] crc32_byte;
  input [31:0] old_crc; input [7:0] data_byte;
  reg [31:0] c; integer i;
  begin c=old_crc^{24'b0,data_byte}; for(i=0;i<8;i=i+1) c=(c>>1)^((c[0])?32'h82f63b78:32'b0); crc32_byte=c; end
 endfunction
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin
   fb_sync<=7;cmd_sync<=7;sck_sync<=0;mosi_sync<=0;
   active<=0;selected_fb<=0;invalid<=0;frame_rates_good<=0;rx_rate_word_valid<=0;rx_rate_channel<=0;rx_rate_word<=0;rise_d<=0;bit_count<=0;expected_bits<=0;body_bits<=0;
   rx_shift<=0;rx_header<=0;rejection_header<=0;rejection_header_valid<=0;rejection_header_cs_fb<=0;tx_shift<=0;rx_crc<=16'hffff;tx_crc<=16'hffff;inner_crc<=32'hffffffff;
   ticks<=0;start_tick<=0;last_rise_tick<=0;last_fall_tick<=0;last_end_tick<=0;seen_rise<=0;seen_fall<=0;
   frame<=0;frame_cs_fb<=0;frame_valid<=0;frame_bad<=0;embedded_crc_good<=0;
   spi_miso<=0;snapshot_start<=0;snapshot_cs_fb<=0;
  end else begin
   fb_sync<={fb_sync[1:0],spi_cs_fb_n};cmd_sync<={cmd_sync[1:0],spi_cs_cmd_n};
   sck_sync<={sck_sync[1:0],spi_sclk};mosi_sync<={mosi_sync[1:0],spi_mosi};
   ticks<=ticks+1'b1;rise_d<=sck_rise;frame_valid<=0;frame_bad<=0;snapshot_start<=0;rejection_header_valid<=0;rx_rate_word_valid<=0;
   if(both_low) begin
    invalid<=1;frame_bad<=1;spi_miso<=0;
   end
   if((fb_start || cmd_start) && !active) begin
    active<=1;selected_fb<=fb_start;frame_rates_good<=frame_rates_good;invalid<=both_low || sck_sync[1] || ticks-last_end_tick<8;
    if(both_low || sck_sync[1] || ticks-last_end_tick<8) frame_bad<=1;
    bit_count<=0;expected_bits<=fb_start?11'd1408:11'd768;body_bits<=fb_start?11'd1392:11'd752;
    rx_shift<=0;rx_header<=0;rx_crc<=16'hffff;tx_crc<=16'hffff;inner_crc<=32'hffffffff;
    tx_shift<=fb_start?feedback_payload:{status_payload,640'b0};
    spi_miso<=fb_start?feedback_payload[1391]:status_payload[751];
    start_tick<=ticks;seen_rise<=0;seen_fall<=0;
    snapshot_start<=1;snapshot_cs_fb<=fb_start;
   end else if(active && ((selected_fb && fb_end) || (!selected_fb && cmd_end))) begin
    if(!invalid && !both_low && !fb_start && !cmd_start && !sck_sync[1] && !sck_fall && bit_count==expected_bits && seen_fall && ticks-last_fall_tick>=8 && rx_crc==rx_shift[15:0]) begin
     frame<=selected_fb?rx_shift:{rx_shift[767:0],640'b0};
     frame_cs_fb<=selected_fb;frame_valid<=1;frame_rates_good<=!selected_fb && rate_frame_good;
     embedded_crc_good<=selected_fb && (~inner_crc==rx_shift[983:952]);
    end else begin
     frame_bad<=1;
     if(bit_count>=48)begin
      rejection_header<=rx_header;rejection_header_valid<=1;rejection_header_cs_fb<=selected_fb;
     end
    end
    active<=0;spi_miso<=0;last_end_tick<=ticks;
   end else if(active) begin
    if((selected_fb && cmd_start) || (!selected_fb && fb_start)) begin invalid<=1;frame_bad<=1;end
    if(sck_rise) begin
     if((!seen_rise && ticks-start_tick<8) || (seen_rise && ticks-last_rise_tick<8) || (seen_fall && ticks-last_fall_tick<4)) begin invalid<=1;frame_bad<=1;end
     last_rise_tick<=ticks;seen_rise<=1;
     if(bit_count<48)rx_header<={rx_header[46:0],mosi_sync[2]};
     if(!selected_fb && bit_count>=128 && bit_count<512 && bit_count[4:0]==31)begin
      rx_rate_word_valid<=1;rx_rate_channel<=bit_count[8:5]-4'd4;
      rx_rate_word<={rx_shift[30:0],mosi_sync[2]};
     end
     if(bit_count<expected_bits) begin
      rx_shift<={rx_shift[1406:0],mosi_sync[2]};
      if(bit_count<body_bits) begin
       rx_crc<=crc_bit(rx_crc,mosi_sync[2]);tx_crc<=crc_bit(tx_crc,tx_shift[1391]);tx_shift<={tx_shift[1390:0],1'b0};
      end
      // The optional MAINT frame is bytes17..56; CRC32C covers17..52.
      if(selected_fb && bit_count[2:0]==7 && bit_count>=136 && bit_count<424)
       inner_crc<=crc32_byte(inner_crc,{rx_shift[6:0],mosi_sync[2]});
      bit_count<=bit_count+1'b1;
     end else begin invalid<=1;frame_bad<=1;bit_count<=expected_bits+1'b1;end
    end
    if(sck_fall) begin
     if(seen_rise && ticks-last_rise_tick<4) begin invalid<=1;frame_bad<=1;end
     last_fall_tick<=ticks;seen_fall<=1;
    end
    // Same tested timing convention as the historical transport: advance MISO
    // one core tick after detecting a rising edge, after the master sampled it.
    if(rise_d) begin
     if(bit_count<body_bits) spi_miso<=tx_shift[1391];
     else if(bit_count<expected_bits) spi_miso<=tx_crc[15-(bit_count-body_bits)];
     else spi_miso<=0;
    end
   end
  end
 end
endmodule
