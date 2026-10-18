`timescale 1ns/1ps
// SPDX-License-Identifier: LicenseRef-Proprietary
// Bounded structural endpoint boundary. request_valid is NOT semantic acceptance
// and never grants motion or output authority. The future stateful receiver must
// check session/sequence continuity, configuration, safety, watchdogs and IOL1.
module cnc3_frame_endpoint (
 input wire clk, input wire rst_n,
 input wire spi_cs_fb_n, input wire spi_cs_cmd_n, input wire spi_sclk, input wire spi_mosi,
 input wire [1391:0] feedback_payload, input wire [751:0] status_payload,
 output wire spi_miso, output wire spi_miso_oe,
 input wire request_ready,
 output reg request_valid, output reg request_cs_fb, output reg [1407:0] request_frame,
 output wire [7:0] request_opcode, output wire [15:0] request_channel_mask,
 output wire [31:0] request_session, output wire [31:0] request_sequence,
 output wire [383:0] request_rates,
 output wire [239:0] request_output_image,
 output reg link_fault, output reg reject_pulse, output reg [7:0] reject_result,
 output wire snapshot_start, output wire snapshot_cs_fb
);
 wire [1407:0] frame;wire frame_valid,frame_bad,frame_cs_fb,embedded_crc_good;wire [7:0] validation_result;
 cnc3_spi_transport transport(.clk(clk),.rst_n(rst_n),.spi_cs_fb_n(spi_cs_fb_n),.spi_cs_cmd_n(spi_cs_cmd_n),.spi_sclk(spi_sclk),.spi_mosi(spi_mosi),.feedback_payload(feedback_payload),.status_payload(status_payload),.spi_miso(spi_miso),.spi_miso_oe(spi_miso_oe),.frame(frame),.frame_cs_fb(frame_cs_fb),.frame_valid(frame_valid),.frame_bad(frame_bad),.embedded_crc_good(embedded_crc_good),.snapshot_start(snapshot_start),.snapshot_cs_fb(snapshot_cs_fb));
 cnc3_command_validate validate(.frame(frame),.cs_fb(frame_cs_fb),.frame_bytes(frame_cs_fb?9'd176:9'd96),.crc_good(1'b1),.embedded_crc_good(embedded_crc_good),.result(validation_result));
 // crc_good is safe here ONLY because transport emits frame_valid after its
 // actual streamed CRC check. Standalone validator callers must supply real CRC.
 assign request_opcode=request_frame[1367:1360];
 assign request_channel_mask=request_frame[1359:1344];
 assign request_session=request_frame[1343:1312];assign request_sequence=request_frame[1311:1280];
 assign request_rates=request_frame[1279:896];
 // Complete bytes64..93; includes all output requests and reserved bytes.
 assign request_output_image=request_frame[895:656];
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin request_valid<=0;request_cs_fb<=0;request_frame<=0;link_fault<=0;reject_pulse<=0;reject_result<=0;end
  else begin
   reject_pulse<=0;
   if(request_valid && request_ready) request_valid<=0;
   // FE is a transport rejection (length/CRC/CS/clock guards); FF is overrun.
   // Other nonzero values retain the frozen structural C codec result codes.
   if(frame_bad) begin link_fault<=1;reject_pulse<=1;reject_result<=8'hfe;end
   if(frame_valid) begin
    if(validation_result!=0) begin link_fault<=1;reject_pulse<=1;reject_result<=validation_result;end
    else if(request_valid && !request_ready) begin link_fault<=1;reject_pulse<=1;reject_result<=8'hff;end
    else begin request_frame<=frame;request_cs_fb<=frame_cs_fb;request_valid<=1;end
   end
  end
 end
endmodule
