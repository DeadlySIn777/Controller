`timescale 1ns/1ps
// x4 quadrature: positive sequence AB=00,01,11,10,00. Index never zeros count.
module cnc_encoder (
    input wire clk, input wire rst_n,
    input wire a, input wire b, input wire z,
    output reg signed [31:0] count,
    output reg signed [31:0] index_count,
    output reg index_seen, output reg invalid_transition
);
    reg [2:0] a_sync, b_sync, z_sync;
    reg [1:0] previous_ab;
    reg previous_z;
    reg signed [31:0] next_count;
    wire [1:0] ab = {a_sync[2], b_sync[2]};
    always @* begin
        next_count = count;
        case ({previous_ab, ab})
            4'b0001, 4'b0111, 4'b1110, 4'b1000: next_count = count + 2'd2;
            4'b0010, 4'b1011, 4'b1101, 4'b0100: next_count = count - 1'b1;
            default: next_count = count;
        endcase
    end
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_sync <= 0; b_sync <= 0; z_sync <= 0; previous_ab <= 0;
            previous_z <= 0; count <= 0; index_count <= 0;
            index_seen <= 0; invalid_transition <= 0;
        end else begin
            a_sync <= {a_sync[1:0], a}; b_sync <= {b_sync[1:0], b};
            z_sync <= {z_sync[1:0], z};
            count <= next_count; previous_ab <= ab; previous_z <= z_sync[2];
            if ((previous_ab ^ ab) == 2'b11) invalid_transition <= 1;
            if (z_sync[2] && !previous_z) begin
                index_count <= next_count; index_seen <= 1;
            end
        end
    end
endmodule
