`timescale 1ns/1ps
// Mode-0, MSB-first, exactly 512 clocks per CS assertion.
// All SPI input transitions are sampled in clk domain. See PROTOCOL.md timing.
// MISO changes one core tick after the detected SCLK rising edge, i.e. after the
// master has sampled the current bit, leaving the whole low phase for setup.
module cnc_spi_frame (
    input wire clk, input wire rst_n,
    input wire spi_cs_n, input wire spi_sclk, input wire spi_mosi,
    input wire [495:0] status_payload,
    output reg spi_miso, output wire spi_miso_oe,
    output reg [511:0] frame,
    output reg frame_valid, output reg frame_bad
);
    reg [2:0] cs_sync, sck_sync, mosi_sync;
    wire cs_start = cs_sync[2] & ~cs_sync[1];
    wire cs_end = ~cs_sync[2] & cs_sync[1];
    wire sck_rise = ~sck_sync[2] & sck_sync[1];
    reg sck_rise_d;
    reg active;
    reg [9:0] bit_count;
    reg [511:0] rx_shift;
    reg [495:0] tx_shift;
    reg [15:0] rx_crc, tx_crc;
    assign spi_miso_oe = ~spi_cs_n & rst_n;
    function [15:0] crc_bit;
        input [15:0] old_crc; input data_bit;
        begin
            crc_bit = {old_crc[14:0], 1'b0};
            if (old_crc[15] ^ data_bit) crc_bit = crc_bit ^ 16'h1021;
        end
    endfunction
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cs_sync <= 3'b111; sck_sync <= 0; mosi_sync <= 0; sck_rise_d <= 0;
            active <= 0; bit_count <= 0; rx_shift <= 0; tx_shift <= 0;
            rx_crc <= 16'hffff; tx_crc <= 16'hffff;
            spi_miso <= 0; frame <= 0; frame_valid <= 0; frame_bad <= 0;
        end else begin
            cs_sync <= {cs_sync[1:0], spi_cs_n};
            sck_sync <= {sck_sync[1:0], spi_sclk};
            mosi_sync <= {mosi_sync[1:0], spi_mosi};
            sck_rise_d <= sck_rise;
            frame_valid <= 0; frame_bad <= 0;
            if (cs_start) begin
                active <= 1; bit_count <= 0; rx_shift <= 0;
                tx_shift <= status_payload; spi_miso <= status_payload[495];
                rx_crc <= 16'hffff; tx_crc <= 16'hffff;
                if (sck_sync[1]) begin active <= 0; frame_bad <= 1; end
            end else if (cs_end) begin
                if (active && bit_count == 512 && rx_crc == rx_shift[15:0]) begin
                    frame <= rx_shift; frame_valid <= 1;
                end else frame_bad <= 1;
                active <= 0; spi_miso <= 0;
            end else if (active) begin
                if (sck_rise) begin
                    if (bit_count < 512) begin
                        rx_shift <= {rx_shift[510:0], mosi_sync[2]};
                        if (bit_count < 496) begin
                            rx_crc <= crc_bit(rx_crc, mosi_sync[2]);
                            tx_crc <= crc_bit(tx_crc, tx_shift[495]);
                            tx_shift <= {tx_shift[494:0], 1'b0};
                        end
                        bit_count <= bit_count + 1'b1;
                    end else begin
                        bit_count <= 513; frame_bad <= 1;
                    end
                end
                // One tick after the detected rise, tx_shift/tx_crc/bit_count
                // already hold their post-rise values: same indexing as before.
                if (sck_rise_d) begin
                    if (bit_count < 496) spi_miso <= tx_shift[495];
                    else if (bit_count < 512) spi_miso <= tx_crc[511-bit_count];
                    else spi_miso <= 0;
                end
            end
        end
    end
endmodule
