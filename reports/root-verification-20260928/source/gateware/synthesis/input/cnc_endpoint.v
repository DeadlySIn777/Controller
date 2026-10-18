`timescale 1ns/1ps
// Custom CNC1 ABI. This is not Mesa HostMot2 and needs its own realtime HAL driver.
module cnc_endpoint #(
    parameter integer WATCHDOG_CYCLES = 250000,
    parameter [31:0] MAX_RATE = 32'h01000000,
    parameter integer PULSE_CYCLES = 100,
    parameter integer SPACE_CYCLES = 100,
    parameter integer DIR_SETUP_CYCLES = 100,
    parameter integer DIR_HOLD_CYCLES = 100,
    // Opt-in v2 discovery. Default remains the separately tested v1 endpoint.
    parameter integer ENABLE_DISCOVERY = 0,
    parameter [31:0] CORE_HZ = 50000000
) (
    input wire clk, input wire reset_n, input wire inhibit_n,
    input wire spi_cs_n, input wire spi_sclk, input wire spi_mosi,
    output wire spi_miso, output wire spi_miso_oe,
    input wire [1:0] enc_a, enc_b, enc_z,
    output wire [5:0] step_out, dir_out,
    output wire motion_enable, output wire endpoint_ready,
    output wire link_fault, watchdog_fault, inhibit_fault, timing_fault
);
    // Asynchronous reset assertion; synchronous release after two core clocks.
    reg reset_meta, reset_done;
    always @(posedge clk or negedge reset_n)
        if (!reset_n) begin reset_meta <= 0; reset_done <= 0; end
        else begin reset_meta <= 1; reset_done <= reset_meta; end
    wire rst_n = reset_done;
    reg [2:0] inhibit_sync;
    reg inhibit_authorized;
    wire inhibit_latched = !inhibit_authorized;
    wire permit_reset_n = rst_n & inhibit_n;
    // Single asynchronous clear per FF; authorization starts withheld at boot.
    // Actual pulse-capture minimum is a device/board constraint, not proved by RTL.
    always @(posedge clk or negedge permit_reset_n) begin
        if (!permit_reset_n) inhibit_sync <= 0;
        else inhibit_sync <= {inhibit_sync[1:0], 1'b1};
    end
    reg armed;
    reg [5:0] axis_mask;
    reg [3:0] faults;
    reg [31:0] session_id, last_seq, watchdog_count, timestamp;
    reg signed [31:0] rates [0:5];
    wire [5:0] steps_raw, dirs_raw, step_fault;
    wire signed [31:0] step_counts [0:5];
    wire signed [31:0] enc_counts [0:1], index_counts [0:1];
    wire [1:0] index_seen, enc_invalid;
    wire [511:0] frame;
    wire frame_valid, frame_bad;
    reg [495:0] status_payload;
    wire [7:0] opcode = frame[471:464];
    wire [5:0] cmd_mask = frame[461:456];
    wire [31:0] cmd_session = frame[447:416];
    wire [31:0] cmd_seq = frame[415:384];
    reg fields_good, rates_zero, rates_good;
    localparam [7:0] ABI_VERSION = (ENABLE_DISCOVERY != 0) ? 8'd2 : 8'd1;
    reg capability_pending;
    reg [31:0] parsed_rate, parsed_magnitude;
    integer j;
    wire sequence_good = session_id != 0 && cmd_session == session_id &&
        last_seq != 32'hffffffff && cmd_seq != 0 && cmd_seq == last_seq + 1'b1;
    wire sync_clear = frame_valid && fields_good && opcode == 1 && !armed &&
        cmd_mask == 0 && rates_zero && cmd_session != 0 &&
        cmd_session != session_id && cmd_seq == 0 && inhibit_sync[2];
    always @(posedge clk or negedge permit_reset_n) begin
        if (!permit_reset_n) inhibit_authorized <= 0;
        else if (sync_clear) inhibit_authorized <= 1;
    end
    assign motion_enable = rst_n && inhibit_n && !inhibit_latched &&
        inhibit_sync[2] && armed && faults == 0 && !(|step_fault);
    assign endpoint_ready = rst_n && session_id != 0 && faults == 0 &&
        !inhibit_latched && inhibit_sync[2];
    assign step_out = steps_raw & {6{motion_enable}};
    assign dir_out = dirs_raw & {6{motion_enable}};
    assign link_fault = faults[0];
    assign watchdog_fault = faults[1];
    assign inhibit_fault = faults[2] | inhibit_latched;
    assign timing_fault = faults[3];
    cnc_spi_frame spi (
        .clk(clk), .rst_n(rst_n), .spi_cs_n(spi_cs_n), .spi_sclk(spi_sclk),
        .spi_mosi(spi_mosi), .status_payload(status_payload), .spi_miso(spi_miso),
        .spi_miso_oe(spi_miso_oe), .frame(frame), .frame_valid(frame_valid), .frame_bad(frame_bad)
    );
    genvar g;
    generate for (g=0; g<6; g=g+1) begin: axes
        cnc_stepgen #(.PULSE_CYCLES(PULSE_CYCLES), .SPACE_CYCLES(SPACE_CYCLES),
            .DIR_SETUP_CYCLES(DIR_SETUP_CYCLES), .DIR_HOLD_CYCLES(DIR_HOLD_CYCLES)) stepgen (
            .clk(clk), .rst_n(rst_n), .enable(motion_enable && axis_mask[g]),
            .rate(rates[g]), .step(steps_raw[g]), .dir(dirs_raw[g]),
            .count(step_counts[g]), .timing_fault(step_fault[g]));
    end endgenerate
    generate for (g=0; g<2; g=g+1) begin: encoders
        cnc_encoder encoder (.clk(clk), .rst_n(rst_n), .a(enc_a[g]), .b(enc_b[g]), .z(enc_z[g]),
            .count(enc_counts[g]), .index_count(index_counts[g]),
            .index_seen(index_seen[g]), .invalid_transition(enc_invalid[g]));
    end endgenerate
    always @* begin
        fields_good = frame[511:480] == 32'h434e4331 && frame[479:472] == ABI_VERSION &&
            frame[463:462] == 0 && frame[455:448] == 0 && frame[191:16] == 0;
        rates_zero = frame[383:192] == 0;
        rates_good = 1;
        parsed_rate = 0; parsed_magnitude = 0;
        for (integer k=0; k<6; k=k+1) begin
            parsed_rate = frame[383-k*32 -: 32];
            parsed_magnitude = parsed_rate[31] ? (~parsed_rate + 32'd1) : parsed_rate;
            if (parsed_magnitude > MAX_RATE || (!cmd_mask[k] && parsed_rate != 0)) rates_good = 0;
        end
        status_payload = 0;
        status_payload[495:464] = 32'h434e5331;
        status_payload[463:456] = ABI_VERSION;
        status_payload[455:448] = {6'b0, endpoint_ready, motion_enable};
        status_payload[447:440] = {2'b0, axis_mask};
        status_payload[439:432] = {4'b0, faults[3], (faults[2] | inhibit_latched), faults[1:0]};
        status_payload[431:400] = session_id;
        status_payload[399:368] = last_seq;
        status_payload[367:336] = timestamp;
        for (integer k=0; k<6; k=k+1) status_payload[335-k*32 -:32] = step_counts[k];
        status_payload[143:112] = enc_counts[0]; status_payload[111:80] = enc_counts[1];
        status_payload[79:48] = index_counts[0]; status_payload[47:16] = index_counts[1];
        status_payload[15:8] = {2'b0, enc_invalid, 2'b0, index_seen};
        if ((ENABLE_DISCOVERY != 0) && capability_pending) begin
            status_payload = 0;
            status_payload[495:464] = 32'h434e4332; // CNC2 capability page
            status_payload[463:456] = ABI_VERSION;
            status_payload[455:448] = 8'd6;
            status_payload[447:440] = 8'd2;
            status_payload[439:432] = 8'd0; // No frequency-capture channels
            status_payload[431:400] = 32'h0000001f; // STEP, ABZ, index, atomic, watchdog
            status_payload[399:368] = CORE_HZ;
            status_payload[367:336] = MAX_RATE;
            status_payload[335:320] = 16'(PULSE_CYCLES);
            status_payload[319:304] = 16'(SPACE_CYCLES);
            status_payload[303:288] = 16'(DIR_SETUP_CYCLES);
            status_payload[287:272] = 16'(DIR_HOLD_CYCLES);
            status_payload[271:240] = WATCHDOG_CYCLES;
        end
    end
    // Failures dominate frame processing. No invalid transfer can update rates or arm.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            armed <= 0; axis_mask <= 0; faults <= 0; session_id <= 0; last_seq <= 0;
            watchdog_count <= 0; timestamp <= 0;
            capability_pending <= 0;
            for (j=0; j<6; j=j+1) rates[j] <= 0;
        end else begin
            timestamp <= timestamp + 1'b1;
            if (frame_valid) capability_pending <= (ENABLE_DISCOVERY != 0) && fields_good &&
                opcode == 5 && frame[463:16] == 0 && !armed;
            if (armed) watchdog_count <= watchdog_count + 1'b1;
            else watchdog_count <= 0;
            if (frame_bad || (|step_fault) ||
                (armed && (!inhibit_sync[2] || inhibit_latched || watchdog_count >= WATCHDOG_CYCLES-1))) begin
                armed <= 0; axis_mask <= 0;
                faults <= faults | {(|step_fault), (inhibit_latched | !inhibit_sync[2]),
                    (armed && watchdog_count >= WATCHDOG_CYCLES-1), frame_bad};
                for (j=0; j<6; j=j+1) rates[j] <= 0;
            end else if (frame_valid) begin
                if (sync_clear) begin
                    session_id <= cmd_session; last_seq <= 0; faults <= 0;
                    axis_mask <= 0; watchdog_count <= 0;
                    for (j=0; j<6; j=j+1) rates[j] <= 0;
                end else if (fields_good && opcode == 0 && frame[463:16] == 0) begin
                    // Read-only NOP does not feed the watchdog.
                end else if ((ENABLE_DISCOVERY != 0) && fields_good && opcode == 5 &&
                    frame[463:16] == 0 && !armed) begin
                    // Read-only capability request; no permission or watchdog effect.
                end else if (fields_good && sequence_good && opcode == 4 && cmd_mask == 0 && rates_zero) begin
                    armed <= 0; axis_mask <= 0; last_seq <= cmd_seq;
                    for (j=0; j<6; j=j+1) rates[j] <= 0;
                end else if (fields_good && sequence_good && faults == 0 && !inhibit_latched && inhibit_sync[2] &&
                    ((opcode == 2 && !armed && cmd_mask != 0 && rates_zero) ||
                     (opcode == 3 && armed && cmd_mask == axis_mask && rates_good))) begin
                    armed <= 1; axis_mask <= cmd_mask; last_seq <= cmd_seq; watchdog_count <= 0;
                    for (j=0; j<6; j=j+1) rates[j] <= frame[383-j*32 -:32];
                end else begin
                    armed <= 0; axis_mask <= 0; faults[0] <= 1;
                    for (j=0; j<6; j=j+1) rates[j] <= 0;
                end
            end
        end
    end
endmodule
