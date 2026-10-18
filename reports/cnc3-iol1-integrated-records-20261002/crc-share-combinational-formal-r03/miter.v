module crc_datapath_miter(input wire prep,input wire[31:0] tx_crc,rx_crc,input wire[319:0]tx_frame,input wire[5:0]prep_index,input wire[7:0]received_byte);
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

wire[31:0] shared_crc=crc_byte(prep?tx_crc:rx_crc,prep?octet(tx_frame,{26'b0,prep_index}):received_byte);
always @* begin
 // PREP's reachable index is0..35. SHIFT uses the complete received byte.
 if(prep && prep_index<=35)assert(shared_crc==crc_byte(tx_crc,octet(tx_frame,{26'b0,prep_index})));
 if(prep && prep_index==35)assert(shared_crc==crc_byte(tx_crc,octet(tx_frame,35)));
 if(!prep)assert(shared_crc==crc_byte(rx_crc,received_byte));
end
endmodule
