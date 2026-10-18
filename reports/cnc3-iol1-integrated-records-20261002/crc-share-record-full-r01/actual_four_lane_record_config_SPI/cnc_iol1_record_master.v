`timescale 1ns/1ps
// Physical mode-0 IOL1 diagnostic master. It never requests output authority.
// Header/class/slot/epoch/previous-command sequence, CRC32C, state, age,
// reserved fields and zero-output readback are checked before accepted rises.
module cnc_iol1_record_master #(
    parameter [3:0] HARDWARE_MAJOR = 1,
    parameter [7:0] CLASS_ID = 8'h11,
    parameter [3:0] SLOT_ID = 0,
    parameter [15:0] EPOCH = 16'h0001,
    parameter integer PERIOD_CYCLES = 5000,
    parameter integer SETUP_CYCLES = 1000,
    parameter integer HOLD_CYCLES = 250
) (
    input wire clk, input wire reset_n, input wire enable,
    input wire miso,
    input wire [7:0] request_control,input wire [207:0] request_payload,
    output reg operation_sent,output reg [7:0] sent_control,
    output reg [7:0] accepted_control,output reg [5:0] accepted_chunk,
    output reg cs_n, output reg sclk, output reg mosi,
    output reg accepted, output reg fault_latched,
    output reg frame_seen, output reg header_crc_good, output wire [319:0] checked_frame,
    output wire link_synced, output wire [1:0] failed_polls
);
    localparam [2:0] WAIT = 0, PREP = 1, START = 2, SHIFT = 3, CHECK = 4, SETUP = 5, HOLD = 6;
    reg [2:0] state, phase;
    localparam integer PERIOD_W = PERIOD_CYCLES>1?$clog2(PERIOD_CYCLES):1;
    localparam integer GUARD_W = SETUP_CYCLES>HOLD_CYCLES?(SETUP_CYCLES>1?$clog2(SETUP_CYCLES):1):(HOLD_CYCLES>1?$clog2(HOLD_CYCLES):1);
    reg [PERIOD_W-1:0] period_count;
    reg [GUARD_W-1:0] guard_count;
    reg [8:0] bit_index;
    reg [5:0] prep_index;
    reg [319:0] tx_frame, rx_shift;
    reg [31:0] tx_crc, rx_crc;
    reg synced;
    reg [15:0] tx_sequence, expected_sequence;
    reg [1:0] failures;
    reg[7:0] expected_control;reg[5:0] expected_chunk;

    function [31:0] crc_byte;
        input [31:0] initial_crc; input [7:0] octet;
        reg [31:0] c; integer k;
        begin
            c = initial_crc ^ {24'b0,octet};
            for(k=0;k<8;k=k+1)
                c = c[0] ? ((c >> 1) ^ 32'h82f63b78) : (c >> 1);
            crc_byte = c;
        end
    endfunction
    function [7:0] octet;
        input [319:0] f; input integer index;
        begin octet = f[319-index*8 -:8]; end
    endfunction
    function [15:0] next_sequence;
        input [15:0] v;
        begin next_sequence = v == 16'hffff ? 16'h0001 : v + 16'h0001; end
    endfunction
    // PREP and SHIFT are mutually exclusive. One combinational byte CRC
    // datapath serves TX preparation and the received complete-byte update.
    wire [31:0] shared_crc = crc_byte(state==PREP ? tx_crc : rx_crc,
       state==PREP ? octet(tx_frame,{26'b0,prep_index}) : {rx_shift[6:0],miso});
    assign checked_frame = rx_shift;
    assign link_synced = synced;
    assign failed_polls = failures;
    reg header_good;
    reg response_good;
    reg [15:0] response_age;
    always @* begin
        response_age = CLASS_ID == 8'h11 ? rx_shift[191:176] :
                       CLASS_ID == 8'h21 ? rx_shift[175:160] : rx_shift[143:128];
        header_good = (EPOCH != 0) &&
            rx_shift[319:304] == 16'h7a01 &&
            rx_shift[303:296] == CLASS_ID && rx_shift[295:288] == {HARDWARE_MAJOR,SLOT_ID} &&
            rx_shift[287:272] == EPOCH && rx_shift[271:256] == expected_sequence &&
            rx_shift[31:0] == (rx_crc ^ 32'hffffffff);
        response_good = header_good &&
            (rx_shift[250:248] == 3'd1 || rx_shift[250:248] == 3'd2) &&
            // Fresh reset/fault or field-supply loss prevents progress. Output
            // permission and enabled flags must stay LOW in this diagnostic image.
            rx_shift[255:251] == 5'b00100;
        if(CLASS_ID == 8'h11)
            response_good = response_good && rx_shift[159:112] == 0 && ((expected_control==8)?octet(rx_shift,9)=={2'b10,expected_chunk}:octet(rx_shift,9)<=2) && response_age <= 16'd440;
        else if(CLASS_ID == 8'h21)
            response_good = response_good && octet(rx_shift,10) == 0 &&
                rx_shift[159:112] == 0 && ((expected_control==8)?octet(rx_shift,9)=={2'b10,expected_chunk}:octet(rx_shift,9)<=11) &&
                !rx_shift[182] && response_age <= 16'd440;
        else if(CLASS_ID == 8'h31)
            // Actual OUT_PERMIT LOW holds AI and both DACs RESET. This
            // diagnostic branch validates powered/reset/clamp controls and
            // explicitly UNAVAILABLE ADC/register-readback, not fictional0F.
            response_good = response_good && rx_shift[239:144] == 0 &&
                ((expected_control==8)?octet(rx_shift,9)=={2'b10,expected_chunk}:octet(rx_shift,9)==6) && response_age == 16'hffff &&
                octet(rx_shift,24) == 0 && octet(rx_shift,25) == 8'h03;
        else response_good = 0;
        if(expected_control==8)response_good=response_good && rx_shift[111:96]=={10'd0,expected_chunk};
        if(expected_control==8'h10)response_good=response_good && CLASS_ID==8'h11 && octet(rx_shift,9)==1 && rx_shift[111:64]==0;
    end

    always @(posedge clk or negedge reset_n) begin
        if(!reset_n) begin
            state <= WAIT; period_count <= 0; guard_count <= 0; phase <= 0; bit_index <= 319;
            prep_index <= 0; tx_frame <= 0; rx_shift <= 0;
            tx_crc <= 32'hffffffff; rx_crc <= 32'hffffffff;
            synced <= 0; tx_sequence <= 0; expected_sequence <= 0;
            failures <= 0; fault_latched <= 0; accepted <= 0;
            frame_seen <= 0; header_crc_good <= 0;
            operation_sent<=0;sent_control<=0;accepted_control<=0;accepted_chunk<=0;
            expected_control<=1;expected_chunk<=0;
            cs_n <= 1; sclk <= 0; mosi <= 0;
        end else begin
            accepted <= 0; frame_seen <= 0; header_crc_good <= 0;operation_sent<=0;
            if(!enable || EPOCH == 0) begin
                cs_n <= 1; sclk <= 0; mosi <= 0; state <= WAIT;
                // Re-enable cannot silently reuse an epoch after a running link
                // was interrupted. A reset plus newly provisioned epoch is needed.
                if(synced) fault_latched <= 1;
                period_count <= 0;
            end else if(fault_latched) begin
                cs_n <= 1; sclk <= 0; mosi <= 0;
            end else begin
                if({ {(32-PERIOD_W){1'b0}},period_count} < PERIOD_CYCLES-1) period_count <= period_count+1;
                else period_count <= 0;
                case(state)
                WAIT: if(period_count == 0) begin
                    if(synced && !(request_control==0 || request_control==8 || (request_control==8'h10 && CLASS_ID==8'h11)))begin
                        fault_latched<=1;
                    end else begin
                    tx_frame <= {8'ha7,8'h01,CLASS_ID,4'b0,SLOT_ID,EPOCH,
                                 tx_sequence,synced ? request_control : 8'h01,8'hff,synced?request_payload:208'd0,32'd0};
                    tx_crc <= 32'hffffffff; prep_index <= 0; state <= PREP;
                    end
                end
                PREP: begin
                    tx_crc <= shared_crc;
                    if(prep_index == 35) begin
                        tx_frame[31:0] <= shared_crc ^ 32'hffffffff;
                        state <= START;
                    end else prep_index <= prep_index+1;
                end
                START: begin
                    cs_n <= 0; sclk <= 0; mosi <= tx_frame[319];
                    bit_index <= 319; phase <= 0; rx_shift <= 0;
                    rx_crc <= 32'hffffffff; guard_count <= 0; state <= SETUP;
                end
                SETUP: begin
                    if({ {(32-GUARD_W){1'b0}},guard_count} == SETUP_CYCLES-1) begin state <= SHIFT; guard_count <= 0; end
                    else guard_count <= guard_count+1;
                end
                SHIFT: begin
                    if(phase == 2) begin
                        sclk <= 1; rx_shift <= {rx_shift[318:0],miso};
                        if(bit_index >= 32 && bit_index[2:0] == 0)
                            rx_crc <= shared_crc;
                    end
                    if(phase == 5) begin
                        sclk <= 0; phase <= 0;
                        if(bit_index == 0) begin mosi <= 0; guard_count <= 0; state <= HOLD; end
                        else begin bit_index <= bit_index-1; mosi <= tx_frame[bit_index-1]; end
                    end else phase <= phase+1;
                end
                HOLD: begin
                    if({ {(32-GUARD_W){1'b0}},guard_count} == HOLD_CYCLES-1) begin cs_n <= 1; state <= CHECK; end
                    else guard_count <= guard_count+1;
                end
                CHECK: begin
                    frame_seen <= 1; header_crc_good <= header_good;
                    // Reply n describes physical command n-1. Once SYNCED,
                    // transmit/expected sequence advances for EVERY completed
                    // command, not only a valid returned reply. This is header
                    // bookkeeping, never accepted progress or output authority.
                    if(synced)begin
                        expected_sequence<=tx_sequence;tx_sequence<=next_sequence(tx_sequence);
                        expected_control<=tx_frame[255:248];expected_chunk<=tx_frame[237:232];
                        operation_sent<=1;sent_control<=tx_frame[255:248];
                    end
                    if(response_good) begin
                        accepted <= 1; failures <= 0;accepted_control<=expected_control;accepted_chunk<=expected_chunk;
                        synced <= 1;
                        if(!synced)begin expected_sequence<=tx_sequence;tx_sequence<=next_sequence(tx_sequence);expected_control<=tx_frame[255:248];expected_chunk<=0;end
                    end else begin
                        // During initial no-authority readiness, INIT/missing peers
                        // produce NO useful progress; don't latch before boot.
                        // Once qualified, three failed polls stop the port.
                        if(synced) begin
                            if(failures == 2) fault_latched <= 1;
                            else failures <= failures+1;
                        end
                    end
                    state <= WAIT;
                end
                default: begin fault_latched <= 1; cs_n <= 1; sclk <= 0; mosi <= 0; end
                endcase
            end
        end
    end
endmodule
