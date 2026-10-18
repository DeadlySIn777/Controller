`timescale 1ns/1ps
// Signed DDS velocity, externally bounded by endpoint. Counts emitted rising edges.
module cnc_stepgen #(
    parameter integer PULSE_CYCLES = 100,
    parameter integer SPACE_CYCLES = 100,
    parameter integer DIR_SETUP_CYCLES = 100,
    parameter integer DIR_HOLD_CYCLES = 100
) (
    input wire clk, input wire rst_n, input wire enable,
    input wire signed [31:0] rate,
    output reg step, output reg dir,
    output reg signed [31:0] count,
    output reg timing_fault
);
    reg [31:0] phase;
    reg [31:0] high_left, low_left, setup_left, hold_left;
    wire wanted_dir = rate[31];
    wire [31:0] magnitude = wanted_dir ? (~rate + 32'd1) : rate;
    wire [32:0] sum = {1'b0, phase} + {1'b0, magnitude};
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phase <= 0; step <= 0; dir <= 0; count <= 0;
            high_left <= 0; low_left <= 0; setup_left <= 0; hold_left <= 0;
            timing_fault <= 0;
        end else if (!enable) begin
            phase <= 0; step <= 0; dir <= 0;
            high_left <= 0; low_left <= 0; setup_left <= DIR_SETUP_CYCLES;
            hold_left <= 0; timing_fault <= 0;
        end else begin
            if (high_left != 0) high_left <= high_left - 1'b1;
            if (low_left != 0) low_left <= low_left - 1'b1;
            if (setup_left != 0) setup_left <= setup_left - 1'b1;
            if (hold_left != 0) hold_left <= hold_left - 1'b1;
            if (high_left == 1) begin step <= 0; low_left <= SPACE_CYCLES; end
            if (rate == 0) phase <= 0;
            else if (wanted_dir != dir) begin
                phase <= 0;
                if (high_left == 0 && low_left == 0 && hold_left == 0) begin
                    dir <= wanted_dir; setup_left <= DIR_SETUP_CYCLES;
                end
            end else if (setup_left == 0) begin
                phase <= sum[31:0];
                if (sum[32]) begin
                    if (high_left == 0 && low_left == 0) begin
                        step <= 1; high_left <= PULSE_CYCLES;
                        hold_left <= DIR_HOLD_CYCLES;
                        count <= count;
                    end else timing_fault <= 1;
                end
            end else phase <= 0;
        end
    end
endmodule
