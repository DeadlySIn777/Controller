`timescale 1ns/1ps
// Physical mode-0 IOL1 diagnostic master. It never requests output authority.
// Header/class/slot/epoch/previous-command sequence, CRC32C, state, age,
// reserved fields and zero-output readback are checked before accepted rises.
module cnc_iol1_readonly_master #(
    parameter [7:0] CLASS_ID = 8'h11,
    parameter [3:0] SLOT_ID = 0,
    parameter [15:0] EPOCH = 16'h0001,
    parameter integer PERIOD_CYCLES = 5000
) (
    input wire clk, input wire reset_n, input wire enable,
    input wire miso,
    output reg cs_n, output reg sclk, output reg mosi,
    output reg accepted, output reg fault_latched
);
    localparam [2:0] WAIT = 0, PREP = 1, START = 2, SHIFT = 3, CHECK = 4;
    reg [2:0] state, phase;
    reg [31:0] period_count;
    reg [8:0] bit_index;
    reg [5:0] prep_index;
    reg [319:0] tx_frame, rx_shift;
    reg [31:0] tx_crc, rx_crc;
    reg synced;
    reg [15:0] tx_sequence, expected_sequence;
    reg [1:0] failures;

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
    reg response_good;
    reg [15:0] response_age;
    always @* begin
        response_age = CLASS_ID == 8'h11 ? rx_shift[191:176] :
                       CLASS_ID == 8'h21 ? rx_shift[175:160] : rx_shift[143:128];
        response_good = (EPOCH != 0) &&
            rx_shift[319:304] == 16'h7a01 &&
            rx_shift[303:296] == CLASS_ID && rx_shift[291:288] == SLOT_ID &&
            rx_shift[287:272] == EPOCH && rx_shift[271:256] == expected_sequence &&
            rx_shift[31:0] == (rx_crc ^ 32'hffffffff) &&
            (rx_shift[250:248] == 3'd1 || rx_shift[250:248] == 3'd2) &&
            // Fresh reset/fault or field-supply loss prevents progress. Output
            // permission and enabled flags must stay LOW in this diagnostic image.
            rx_shift[255:251] == 5'b00100 && response_age <= 16'd440;
        if(CLASS_ID == 8'h11)
            response_good = response_good && rx_shift[159:112] == 0 && octet(rx_shift,9) <= 2;
        else if(CLASS_ID == 8'h21)
            response_good = response_good && octet(rx_shift,10) == 0 &&
                rx_shift[159:112] == 0 && octet(rx_shift,9) <= 11 &&
                !rx_shift[182];
        else if(CLASS_ID == 8'h31)
            response_good = response_good && rx_shift[239:208] == 0 &&
                octet(rx_shift,9) <= 7 && rx_shift[119:112] == 8'h0f;
        else response_good = 0;
    end

    always @(posedge clk or negedge reset_n) begin
        if(!reset_n) begin
            state <= WAIT; period_count <= 0; phase <= 0; bit_index <= 319;
            prep_index <= 0; tx_frame <= 0; rx_shift <= 0;
            tx_crc <= 32'hffffffff; rx_crc <= 32'hffffffff;
            synced <= 0; tx_sequence <= 0; expected_sequence <= 0;
            failures <= 0; fault_latched <= 0; accepted <= 0;
            cs_n <= 1; sclk <= 0; mosi <= 0;
        end else begin
            accepted <= 0;
            if(!enable || EPOCH == 0) begin
                cs_n <= 1; sclk <= 0; mosi <= 0; state <= WAIT;
                // Re-enable cannot silently reuse an epoch after a running link
                // was interrupted. A reset plus newly provisioned epoch is needed.
                if(synced) fault_latched <= 1;
                period_count <= 0;
            end else if(fault_latched) begin
                cs_n <= 1; sclk <= 0; mosi <= 0;
            end else begin
                if(period_count < PERIOD_CYCLES-1) period_count <= period_count+1;
                else period_count <= 0;
                case(state)
                WAIT: if(period_count == 0) begin
                    tx_frame <= {8'ha7,8'h01,CLASS_ID,4'b0,SLOT_ID,EPOCH,
                                 tx_sequence,synced ? 8'h00 : 8'h01,8'hff,240'b0};
                    tx_crc <= 32'hffffffff; prep_index <= 0; state <= PREP;
                end
                PREP: begin
                    tx_crc <= crc_byte(tx_crc,octet(tx_frame,{26'b0,prep_index}));
                    if(prep_index == 35) begin
                        tx_frame[31:0] <= crc_byte(tx_crc,octet(tx_frame,35)) ^ 32'hffffffff;
                        state <= START;
                    end else prep_index <= prep_index+1;
                end
                START: begin
                    cs_n <= 0; sclk <= 0; mosi <= tx_frame[319];
                    bit_index <= 319; phase <= 0; rx_shift <= 0;
                    rx_crc <= 32'hffffffff; state <= SHIFT;
                end
                SHIFT: begin
                    if(phase == 2) begin
                        sclk <= 1; rx_shift <= {rx_shift[318:0],miso};
                        if(bit_index >= 32 && bit_index[2:0] == 0)
                            rx_crc <= crc_byte(rx_crc,{rx_shift[6:0],miso});
                    end
                    if(phase == 5) begin
                        sclk <= 0; phase <= 0;
                        if(bit_index == 0) begin cs_n <= 1; mosi <= 0; state <= CHECK; end
                        else begin bit_index <= bit_index-1; mosi <= tx_frame[bit_index-1]; end
                    end else phase <= phase+1;
                end
                CHECK: begin
                    if(response_good) begin
                        accepted <= 1; failures <= 0;
                        synced <= 1; expected_sequence <= tx_sequence;
                        tx_sequence <= next_sequence(tx_sequence);
                    end else begin
                        if(failures == 2) fault_latched <= 1;
                        else failures <= failures+1;
                    end
                    state <= WAIT;
                end
                default: begin fault_latched <= 1; cs_n <= 1; sclk <= 0; mosi <= 0; end
                endcase
            end
        end
    end
endmodule
