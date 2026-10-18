`timescale 1ns/1ps
// Diagnostic bench target, not a production CNC3 or twelve-axis endpoint.
module cnc_motherboard_watchdog_bringup #(
    parameter [15:0] IOL1_EPOCH = 16'h0001,
    parameter integer IO_PERIOD_CYCLES = 5000
) (
    input wire clk, input wire reset_n, input wire inhibit_n,
    input wire rails_ok,
    input wire spi_cs_n, input wire spi_sclk, input wire spi_mosi,
    output wire spi_miso, output wire spi_miso_oe,
    input wire [1:0] enc_a, enc_b, enc_z,
    output wire [11:0] step_out, dir_out, enable_n,
    output wire motion_request, endpoint_ready,
    output wire output_request, progress_m, output wire progress_o,
    output wire [3:0] iol1_cs_n, iol1_sclk, iol1_mosi,
    input wire [3:0] iol1_miso,
    output wire [3:0] io_fault,
    output wire link_fault, watchdog_fault, inhibit_fault, timing_fault,
    output wire [1:0] pwm, process_request,
    output wire permit_out_request, arm_lamp_request
);
    wire [5:0] step6, dir6, enabled6;
    cnc_motherboard_motion_bringup motion (
        .clk(clk),.reset_n(reset_n),.inhibit_n(inhibit_n),
        .spi_cs_n(spi_cs_n),.spi_sclk(spi_sclk),.spi_mosi(spi_mosi),
        .spi_miso(spi_miso),.spi_miso_oe(spi_miso_oe),
        .enc_a(enc_a),.enc_b(enc_b),.enc_z(enc_z),
        .step_out(step6),.dir_out(dir6),.axis_enabled(enabled6),
        .motion_enable(motion_request),.endpoint_ready(endpoint_ready),
        .link_fault(link_fault),.watchdog_fault(watchdog_fault),
        .inhibit_fault(inhibit_fault),.timing_fault(timing_fault),.progress_wdi(progress_m)
    );
    assign step_out = {6'b0,step6};
    assign dir_out = {6'b0,dir6};
    assign enable_n = {6'b111111,~enabled6};
    // No full production output-config/authority implementation is inferred
    // from diagnostic replies or the historical motion session.
    assign output_request = 0;
    assign pwm = 0;
    assign process_request = 0;
    assign permit_out_request = 0;
    assign arm_lamp_request = 0;
    wire [3:0] accepted;
    genvar g;
    generate for(g=0;g<4;g=g+1) begin: ports
        cnc_iol1_readonly_master #(
            .CLASS_ID(g==0 ? 8'h11 : g==3 ? 8'h31 : 8'h21),
            .SLOT_ID(g),.EPOCH(IOL1_EPOCH),.PERIOD_CYCLES(IO_PERIOD_CYCLES)
        ) io_master (
            .clk(clk),.reset_n(reset_n),.enable(rails_ok),
            .miso(iol1_miso[g]),.cs_n(iol1_cs_n[g]),
            .sclk(iol1_sclk[g]),.mosi(iol1_mosi[g]),
            .accepted(accepted[g]),.fault_latched(io_fault[g])
        );
    end endgenerate
    reg [5:0] o_remaining;
    reg o_pulse;
    assign progress_o = o_pulse;
    always @(posedge clk or negedge reset_n) begin
        if(!reset_n) begin o_remaining <= 0; o_pulse <= 0; end
        else begin
            if(o_remaining > 1) o_remaining <= o_remaining-1;
            else begin o_remaining <= 0; o_pulse <= 0; end
            // Identical parallel poll clocks mean these acceptance strobes
            // name the same completed physical cycle, never a stale union.
            if((&accepted) && !(|io_fault) && rails_ok) begin
                o_remaining <= 50; o_pulse <= 1;
            end
        end
    end
endmodule
