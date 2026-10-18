
//
// Verific Verilog Description of module cnc3_event_bank
//

module cnc3_event_bank (clk, write_enable, write_address, read_address, 
            write_data, read_data) /* verific EFX_ATTRIBUTE_NETLIST__EFINITY_VERSION=2026.1.132 */ ;
    input clk /* verific EFX_ATTRIBUTE_PORT__IS_PRIMARY_INPUT=TRUE */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(4)
    input write_enable /* verific EFX_ATTRIBUTE_PORT__IS_PRIMARY_INPUT=TRUE */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(4)
    input [4:0]write_address /* verific EFX_ATTRIBUTE_PORT__IS_PRIMARY_INPUT=TRUE */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(5)
    input [4:0]read_address /* verific EFX_ATTRIBUTE_PORT__IS_PRIMARY_INPUT=TRUE */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(5)
    input [159:0]write_data /* verific EFX_ATTRIBUTE_PORT__IS_PRIMARY_INPUT=TRUE */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(5)
    output [159:0]read_data /* verific EFX_ATTRIBUTE_PORT__IS_PRIMARY_OUTPUT=TRUE */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(6)
    
    wire [159:0]forward_data;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(8)
    
    wire \ram_read[20] , \ram_read[21] , \ram_read[22] , \ram_read[23] , 
        \ram_read[24] , \ram_read[25] , \ram_read[26] , \ram_read[27] , 
        \ram_read[28] , \ram_read[29] , \ram_read[30] , \ram_read[31] , 
        \ram_read[32] , \ram_read[33] , \ram_read[34] , \ram_read[35] , 
        \ram_read[36] , \ram_read[37] , \ram_read[38] , \ram_read[39] , 
        \ram_read[40] , \ram_read[41] , \ram_read[42] , \ram_read[43] , 
        \ram_read[44] , \ram_read[45] , \ram_read[46] , \ram_read[47] , 
        \ram_read[48] , \ram_read[49] , \ram_read[50] , \ram_read[51] , 
        \ram_read[52] , \ram_read[53] , \ram_read[54] , \ram_read[55] , 
        \ram_read[56] , \ram_read[57] , \ram_read[58] , \ram_read[59] , 
        forward_valid, \ram_read[60] , \ram_read[61] , \ram_read[62] , 
        \ram_read[63] , \ram_read[64] , \ram_read[65] , \ram_read[66] , 
        \ram_read[67] , \ram_read[68] , \ram_read[69] , \ram_read[70] , 
        \ram_read[71] , \ram_read[72] , \ram_read[73] , \ram_read[74] , 
        \ram_read[75] , \ram_read[76] , \ram_read[77] , \ram_read[78] , 
        \ram_read[79] , \ram_read[80] , \ram_read[81] , \ram_read[82] , 
        \ram_read[83] , \ram_read[84] , \ram_read[85] , \ram_read[86] , 
        \ram_read[87] , \ram_read[88] , \ram_read[89] , \ram_read[90] , 
        \ram_read[91] , \ram_read[92] , \ram_read[93] , \ram_read[94] , 
        \ram_read[95] , \ram_read[96] , \ram_read[97] , \ram_read[98] , 
        \ram_read[99] , \ram_read[100] , \ram_read[101] , \ram_read[102] , 
        \ram_read[103] , \ram_read[104] , \ram_read[105] , \ram_read[106] , 
        \ram_read[107] , \ram_read[108] , \ram_read[109] , \ram_read[110] , 
        \ram_read[111] , \ram_read[112] , \ram_read[113] , \ram_read[114] , 
        \ram_read[115] , \ram_read[116] , \ram_read[117] , \ram_read[118] , 
        \ram_read[119] , \ram_read[120] , \ram_read[121] , \ram_read[122] , 
        \ram_read[123] , \ram_read[124] , \ram_read[125] , \ram_read[126] , 
        \ram_read[127] , \ram_read[128] , \ram_read[129] , \ram_read[130] , 
        \ram_read[131] , \ram_read[132] , \ram_read[133] , \ram_read[134] , 
        \ram_read[135] , \ram_read[136] , \ram_read[137] , \ram_read[138] , 
        \ram_read[139] , \ram_read[140] , \ram_read[141] , \ram_read[142] , 
        \ram_read[143] , \ram_read[144] , \ram_read[145] , \ram_read[146] , 
        \ram_read[147] , \ram_read[148] , \ram_read[149] , \ram_read[150] , 
        \ram_read[151] , \ram_read[152] , \ram_read[153] , \ram_read[154] , 
        \ram_read[155] , \ram_read[156] , \ram_read[157] , \ram_read[158] , 
        \ram_read[159] , \ram_read[0] , \ram_read[1] , \ram_read[2] , 
        \ram_read[3] , \ram_read[4] , \ram_read[5] , \ram_read[6] , 
        \ram_read[7] , \ram_read[8] , \ram_read[9] , \ram_read[10] , 
        \ram_read[11] , \ram_read[12] , \ram_read[13] , \ram_read[14] , 
        \ram_read[15] , \ram_read[16] , \ram_read[17] , \ram_read[18] , 
        \ram_read[19] , n170, \clk~O , n829, n830, n831;
    
    EFX_LUT4 LUT__1322 (.I0(forward_data[159]), .I1(\ram_read[159] ), .I2(forward_valid), 
            .O(read_data[159])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1322.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1323 (.I0(forward_data[158]), .I1(\ram_read[158] ), .I2(forward_valid), 
            .O(read_data[158])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1323.LUTMASK = 16'hacac;
    EFX_FF \forward_data[4]~FF  (.D(write_data[4]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[4])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[4]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[4]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[4]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[4]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[4]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[4]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[4]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[3]~FF  (.D(write_data[3]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[3])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[3]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[3]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[3]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[3]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[3]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[3]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[3]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[2]~FF  (.D(write_data[2]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[2])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[2]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[2]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[2]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[2]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[2]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[2]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[2]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[1]~FF  (.D(write_data[1]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[1])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[1]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[1]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[1]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[1]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[1]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[1]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[1]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[0]~FF  (.D(write_data[0]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[0])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[0]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[0]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[0]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[0]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[0]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[0]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[0]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_valid~FF  (.D(n170), .CE(1'b1), .CLK(\clk~O ), .SR(1'b0), 
           .Q(forward_valid)) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_valid~FF .CLK_POLARITY = 1'b1;
    defparam \forward_valid~FF .CE_POLARITY = 1'b1;
    defparam \forward_valid~FF .SR_POLARITY = 1'b1;
    defparam \forward_valid~FF .D_POLARITY = 1'b1;
    defparam \forward_valid~FF .SR_SYNC = 1'b1;
    defparam \forward_valid~FF .SR_VALUE = 1'b0;
    defparam \forward_valid~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[5]~FF  (.D(write_data[5]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[5])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[5]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[5]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[5]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[5]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[5]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[5]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[5]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[6]~FF  (.D(write_data[6]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[6])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[6]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[6]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[6]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[6]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[6]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[6]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[6]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[7]~FF  (.D(write_data[7]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[7])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[7]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[7]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[7]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[7]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[7]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[7]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[7]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[8]~FF  (.D(write_data[8]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[8])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[8]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[8]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[8]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[8]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[8]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[8]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[8]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[9]~FF  (.D(write_data[9]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[9])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[9]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[9]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[9]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[9]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[9]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[9]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[9]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[10]~FF  (.D(write_data[10]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[10])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[10]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[10]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[10]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[10]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[10]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[10]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[10]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[11]~FF  (.D(write_data[11]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[11])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[11]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[11]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[11]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[11]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[11]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[11]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[11]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[12]~FF  (.D(write_data[12]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[12])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[12]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[12]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[12]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[12]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[12]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[12]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[12]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[13]~FF  (.D(write_data[13]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[13])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[13]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[13]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[13]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[13]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[13]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[13]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[13]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[14]~FF  (.D(write_data[14]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[14])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[14]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[14]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[14]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[14]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[14]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[14]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[14]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[15]~FF  (.D(write_data[15]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[15])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[15]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[15]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[15]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[15]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[15]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[15]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[15]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[16]~FF  (.D(write_data[16]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[16])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[16]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[16]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[16]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[16]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[16]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[16]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[16]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[17]~FF  (.D(write_data[17]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[17])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[17]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[17]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[17]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[17]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[17]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[17]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[17]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[18]~FF  (.D(write_data[18]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[18])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[18]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[18]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[18]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[18]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[18]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[18]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[18]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[19]~FF  (.D(write_data[19]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[19])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[19]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[19]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[19]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[19]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[19]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[19]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[19]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[20]~FF  (.D(write_data[20]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[20])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[20]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[20]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[20]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[20]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[20]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[20]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[20]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[21]~FF  (.D(write_data[21]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[21])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[21]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[21]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[21]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[21]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[21]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[21]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[21]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[22]~FF  (.D(write_data[22]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[22])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[22]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[22]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[22]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[22]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[22]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[22]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[22]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[23]~FF  (.D(write_data[23]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[23])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[23]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[23]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[23]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[23]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[23]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[23]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[23]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[24]~FF  (.D(write_data[24]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[24])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[24]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[24]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[24]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[24]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[24]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[24]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[24]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[25]~FF  (.D(write_data[25]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[25])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[25]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[25]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[25]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[25]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[25]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[25]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[25]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[26]~FF  (.D(write_data[26]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[26])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[26]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[26]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[26]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[26]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[26]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[26]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[26]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[27]~FF  (.D(write_data[27]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[27])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[27]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[27]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[27]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[27]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[27]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[27]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[27]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[28]~FF  (.D(write_data[28]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[28])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[28]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[28]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[28]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[28]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[28]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[28]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[28]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[29]~FF  (.D(write_data[29]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[29])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[29]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[29]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[29]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[29]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[29]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[29]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[29]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[30]~FF  (.D(write_data[30]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[30])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[30]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[30]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[30]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[30]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[30]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[30]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[30]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[31]~FF  (.D(write_data[31]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[31])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[31]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[31]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[31]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[31]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[31]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[31]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[31]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[32]~FF  (.D(write_data[32]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[32])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[32]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[32]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[32]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[32]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[32]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[32]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[32]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[33]~FF  (.D(write_data[33]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[33])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[33]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[33]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[33]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[33]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[33]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[33]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[33]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[34]~FF  (.D(write_data[34]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[34])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[34]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[34]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[34]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[34]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[34]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[34]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[34]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[35]~FF  (.D(write_data[35]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[35])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[35]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[35]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[35]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[35]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[35]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[35]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[35]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[36]~FF  (.D(write_data[36]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[36])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[36]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[36]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[36]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[36]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[36]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[36]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[36]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[37]~FF  (.D(write_data[37]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[37])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[37]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[37]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[37]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[37]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[37]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[37]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[37]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[38]~FF  (.D(write_data[38]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[38])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[38]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[38]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[38]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[38]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[38]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[38]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[38]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[39]~FF  (.D(write_data[39]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[39])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[39]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[39]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[39]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[39]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[39]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[39]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[39]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[40]~FF  (.D(write_data[40]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[40])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[40]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[40]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[40]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[40]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[40]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[40]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[40]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[41]~FF  (.D(write_data[41]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[41])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[41]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[41]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[41]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[41]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[41]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[41]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[41]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[42]~FF  (.D(write_data[42]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[42])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[42]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[42]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[42]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[42]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[42]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[42]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[42]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[43]~FF  (.D(write_data[43]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[43])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[43]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[43]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[43]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[43]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[43]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[43]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[43]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[44]~FF  (.D(write_data[44]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[44])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[44]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[44]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[44]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[44]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[44]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[44]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[44]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[45]~FF  (.D(write_data[45]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[45])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[45]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[45]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[45]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[45]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[45]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[45]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[45]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[46]~FF  (.D(write_data[46]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[46])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[46]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[46]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[46]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[46]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[46]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[46]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[46]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[47]~FF  (.D(write_data[47]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[47])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[47]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[47]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[47]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[47]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[47]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[47]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[47]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[48]~FF  (.D(write_data[48]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[48])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[48]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[48]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[48]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[48]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[48]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[48]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[48]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[49]~FF  (.D(write_data[49]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[49])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[49]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[49]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[49]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[49]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[49]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[49]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[49]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[50]~FF  (.D(write_data[50]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[50])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[50]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[50]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[50]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[50]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[50]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[50]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[50]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[51]~FF  (.D(write_data[51]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[51])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[51]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[51]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[51]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[51]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[51]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[51]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[51]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[52]~FF  (.D(write_data[52]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[52])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[52]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[52]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[52]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[52]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[52]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[52]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[52]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[53]~FF  (.D(write_data[53]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[53])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[53]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[53]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[53]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[53]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[53]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[53]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[53]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[54]~FF  (.D(write_data[54]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[54])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[54]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[54]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[54]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[54]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[54]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[54]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[54]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[55]~FF  (.D(write_data[55]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[55])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[55]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[55]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[55]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[55]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[55]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[55]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[55]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[56]~FF  (.D(write_data[56]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[56])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[56]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[56]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[56]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[56]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[56]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[56]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[56]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[57]~FF  (.D(write_data[57]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[57])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[57]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[57]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[57]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[57]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[57]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[57]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[57]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[58]~FF  (.D(write_data[58]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[58])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[58]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[58]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[58]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[58]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[58]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[58]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[58]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[59]~FF  (.D(write_data[59]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[59])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[59]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[59]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[59]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[59]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[59]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[59]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[59]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[60]~FF  (.D(write_data[60]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[60])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[60]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[60]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[60]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[60]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[60]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[60]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[60]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[61]~FF  (.D(write_data[61]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[61])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[61]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[61]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[61]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[61]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[61]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[61]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[61]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[62]~FF  (.D(write_data[62]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[62])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[62]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[62]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[62]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[62]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[62]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[62]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[62]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[63]~FF  (.D(write_data[63]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[63])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[63]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[63]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[63]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[63]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[63]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[63]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[63]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[64]~FF  (.D(write_data[64]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[64])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[64]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[64]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[64]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[64]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[64]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[64]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[64]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[65]~FF  (.D(write_data[65]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[65])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[65]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[65]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[65]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[65]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[65]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[65]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[65]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[66]~FF  (.D(write_data[66]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[66])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[66]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[66]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[66]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[66]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[66]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[66]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[66]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[67]~FF  (.D(write_data[67]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[67])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[67]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[67]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[67]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[67]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[67]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[67]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[67]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[68]~FF  (.D(write_data[68]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[68])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[68]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[68]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[68]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[68]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[68]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[68]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[68]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[69]~FF  (.D(write_data[69]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[69])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[69]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[69]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[69]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[69]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[69]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[69]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[69]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[70]~FF  (.D(write_data[70]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[70])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[70]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[70]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[70]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[70]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[70]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[70]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[70]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[71]~FF  (.D(write_data[71]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[71])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[71]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[71]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[71]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[71]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[71]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[71]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[71]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[72]~FF  (.D(write_data[72]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[72])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[72]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[72]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[72]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[72]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[72]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[72]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[72]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[73]~FF  (.D(write_data[73]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[73])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[73]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[73]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[73]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[73]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[73]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[73]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[73]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[74]~FF  (.D(write_data[74]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[74])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[74]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[74]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[74]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[74]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[74]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[74]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[74]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[75]~FF  (.D(write_data[75]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[75])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[75]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[75]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[75]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[75]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[75]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[75]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[75]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[76]~FF  (.D(write_data[76]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[76])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[76]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[76]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[76]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[76]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[76]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[76]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[76]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[77]~FF  (.D(write_data[77]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[77])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[77]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[77]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[77]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[77]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[77]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[77]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[77]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[78]~FF  (.D(write_data[78]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[78])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[78]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[78]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[78]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[78]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[78]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[78]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[78]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[79]~FF  (.D(write_data[79]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[79])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[79]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[79]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[79]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[79]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[79]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[79]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[79]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[80]~FF  (.D(write_data[80]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[80])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[80]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[80]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[80]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[80]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[80]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[80]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[80]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[81]~FF  (.D(write_data[81]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[81])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[81]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[81]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[81]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[81]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[81]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[81]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[81]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[82]~FF  (.D(write_data[82]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[82])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[82]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[82]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[82]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[82]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[82]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[82]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[82]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[83]~FF  (.D(write_data[83]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[83])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[83]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[83]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[83]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[83]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[83]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[83]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[83]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[84]~FF  (.D(write_data[84]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[84])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[84]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[84]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[84]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[84]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[84]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[84]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[84]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[85]~FF  (.D(write_data[85]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[85])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[85]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[85]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[85]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[85]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[85]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[85]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[85]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[86]~FF  (.D(write_data[86]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[86])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[86]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[86]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[86]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[86]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[86]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[86]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[86]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[87]~FF  (.D(write_data[87]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[87])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[87]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[87]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[87]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[87]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[87]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[87]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[87]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[88]~FF  (.D(write_data[88]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[88])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[88]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[88]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[88]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[88]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[88]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[88]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[88]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[89]~FF  (.D(write_data[89]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[89])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[89]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[89]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[89]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[89]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[89]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[89]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[89]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[90]~FF  (.D(write_data[90]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[90])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[90]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[90]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[90]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[90]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[90]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[90]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[90]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[91]~FF  (.D(write_data[91]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[91])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[91]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[91]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[91]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[91]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[91]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[91]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[91]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[92]~FF  (.D(write_data[92]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[92])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[92]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[92]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[92]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[92]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[92]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[92]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[92]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[93]~FF  (.D(write_data[93]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[93])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[93]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[93]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[93]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[93]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[93]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[93]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[93]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[94]~FF  (.D(write_data[94]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[94])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[94]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[94]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[94]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[94]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[94]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[94]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[94]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[95]~FF  (.D(write_data[95]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[95])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[95]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[95]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[95]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[95]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[95]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[95]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[95]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[96]~FF  (.D(write_data[96]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[96])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[96]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[96]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[96]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[96]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[96]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[96]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[96]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[97]~FF  (.D(write_data[97]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[97])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[97]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[97]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[97]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[97]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[97]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[97]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[97]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[98]~FF  (.D(write_data[98]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[98])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[98]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[98]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[98]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[98]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[98]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[98]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[98]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[99]~FF  (.D(write_data[99]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[99])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[99]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[99]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[99]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[99]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[99]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[99]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[99]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[100]~FF  (.D(write_data[100]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[100])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[100]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[100]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[100]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[100]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[100]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[100]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[100]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[101]~FF  (.D(write_data[101]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[101])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[101]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[101]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[101]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[101]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[101]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[101]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[101]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[102]~FF  (.D(write_data[102]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[102])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[102]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[102]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[102]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[102]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[102]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[102]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[102]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[103]~FF  (.D(write_data[103]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[103])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[103]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[103]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[103]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[103]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[103]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[103]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[103]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[104]~FF  (.D(write_data[104]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[104])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[104]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[104]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[104]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[104]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[104]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[104]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[104]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[105]~FF  (.D(write_data[105]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[105])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[105]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[105]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[105]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[105]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[105]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[105]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[105]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[106]~FF  (.D(write_data[106]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[106])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[106]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[106]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[106]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[106]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[106]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[106]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[106]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[107]~FF  (.D(write_data[107]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[107])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[107]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[107]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[107]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[107]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[107]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[107]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[107]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[108]~FF  (.D(write_data[108]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[108])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[108]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[108]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[108]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[108]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[108]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[108]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[108]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[109]~FF  (.D(write_data[109]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[109])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[109]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[109]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[109]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[109]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[109]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[109]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[109]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[110]~FF  (.D(write_data[110]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[110])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[110]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[110]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[110]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[110]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[110]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[110]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[110]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[111]~FF  (.D(write_data[111]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[111])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[111]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[111]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[111]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[111]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[111]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[111]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[111]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[112]~FF  (.D(write_data[112]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[112])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[112]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[112]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[112]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[112]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[112]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[112]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[112]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[113]~FF  (.D(write_data[113]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[113])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[113]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[113]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[113]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[113]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[113]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[113]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[113]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[114]~FF  (.D(write_data[114]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[114])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[114]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[114]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[114]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[114]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[114]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[114]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[114]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[115]~FF  (.D(write_data[115]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[115])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[115]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[115]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[115]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[115]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[115]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[115]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[115]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[116]~FF  (.D(write_data[116]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[116])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[116]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[116]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[116]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[116]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[116]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[116]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[116]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[117]~FF  (.D(write_data[117]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[117])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[117]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[117]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[117]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[117]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[117]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[117]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[117]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[118]~FF  (.D(write_data[118]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[118])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[118]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[118]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[118]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[118]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[118]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[118]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[118]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[119]~FF  (.D(write_data[119]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[119])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[119]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[119]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[119]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[119]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[119]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[119]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[119]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[120]~FF  (.D(write_data[120]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[120])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[120]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[120]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[120]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[120]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[120]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[120]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[120]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[121]~FF  (.D(write_data[121]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[121])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[121]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[121]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[121]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[121]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[121]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[121]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[121]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[122]~FF  (.D(write_data[122]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[122])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[122]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[122]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[122]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[122]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[122]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[122]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[122]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[123]~FF  (.D(write_data[123]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[123])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[123]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[123]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[123]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[123]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[123]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[123]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[123]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[124]~FF  (.D(write_data[124]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[124])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[124]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[124]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[124]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[124]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[124]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[124]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[124]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[125]~FF  (.D(write_data[125]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[125])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[125]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[125]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[125]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[125]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[125]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[125]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[125]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[126]~FF  (.D(write_data[126]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[126])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[126]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[126]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[126]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[126]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[126]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[126]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[126]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[127]~FF  (.D(write_data[127]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[127])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[127]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[127]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[127]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[127]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[127]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[127]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[127]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[128]~FF  (.D(write_data[128]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[128])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[128]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[128]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[128]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[128]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[128]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[128]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[128]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[129]~FF  (.D(write_data[129]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[129])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[129]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[129]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[129]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[129]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[129]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[129]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[129]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[130]~FF  (.D(write_data[130]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[130])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[130]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[130]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[130]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[130]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[130]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[130]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[130]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[131]~FF  (.D(write_data[131]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[131])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[131]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[131]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[131]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[131]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[131]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[131]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[131]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[132]~FF  (.D(write_data[132]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[132])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[132]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[132]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[132]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[132]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[132]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[132]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[132]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[133]~FF  (.D(write_data[133]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[133])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[133]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[133]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[133]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[133]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[133]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[133]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[133]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[134]~FF  (.D(write_data[134]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[134])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[134]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[134]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[134]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[134]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[134]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[134]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[134]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[135]~FF  (.D(write_data[135]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[135])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[135]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[135]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[135]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[135]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[135]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[135]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[135]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[136]~FF  (.D(write_data[136]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[136])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[136]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[136]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[136]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[136]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[136]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[136]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[136]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[137]~FF  (.D(write_data[137]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[137])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[137]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[137]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[137]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[137]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[137]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[137]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[137]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[138]~FF  (.D(write_data[138]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[138])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[138]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[138]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[138]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[138]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[138]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[138]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[138]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[139]~FF  (.D(write_data[139]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[139])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[139]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[139]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[139]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[139]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[139]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[139]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[139]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[140]~FF  (.D(write_data[140]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[140])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[140]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[140]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[140]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[140]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[140]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[140]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[140]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[141]~FF  (.D(write_data[141]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[141])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[141]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[141]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[141]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[141]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[141]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[141]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[141]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[142]~FF  (.D(write_data[142]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[142])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[142]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[142]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[142]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[142]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[142]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[142]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[142]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[143]~FF  (.D(write_data[143]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[143])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[143]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[143]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[143]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[143]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[143]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[143]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[143]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[144]~FF  (.D(write_data[144]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[144])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[144]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[144]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[144]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[144]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[144]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[144]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[144]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[145]~FF  (.D(write_data[145]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[145])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[145]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[145]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[145]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[145]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[145]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[145]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[145]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[146]~FF  (.D(write_data[146]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[146])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[146]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[146]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[146]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[146]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[146]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[146]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[146]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[147]~FF  (.D(write_data[147]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[147])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[147]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[147]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[147]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[147]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[147]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[147]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[147]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[148]~FF  (.D(write_data[148]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[148])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[148]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[148]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[148]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[148]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[148]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[148]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[148]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[149]~FF  (.D(write_data[149]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[149])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[149]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[149]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[149]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[149]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[149]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[149]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[149]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[150]~FF  (.D(write_data[150]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[150])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[150]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[150]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[150]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[150]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[150]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[150]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[150]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[151]~FF  (.D(write_data[151]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[151])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[151]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[151]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[151]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[151]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[151]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[151]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[151]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[152]~FF  (.D(write_data[152]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[152])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[152]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[152]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[152]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[152]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[152]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[152]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[152]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[153]~FF  (.D(write_data[153]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[153])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[153]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[153]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[153]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[153]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[153]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[153]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[153]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[154]~FF  (.D(write_data[154]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[154])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[154]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[154]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[154]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[154]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[154]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[154]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[154]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[155]~FF  (.D(write_data[155]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[155])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[155]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[155]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[155]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[155]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[155]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[155]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[155]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[156]~FF  (.D(write_data[156]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[156])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[156]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[156]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[156]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[156]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[156]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[156]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[156]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[157]~FF  (.D(write_data[157]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[157])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[157]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[157]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[157]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[157]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[157]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[157]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[157]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[158]~FF  (.D(write_data[158]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[158])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[158]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[158]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[158]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[158]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[158]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[158]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[158]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_FF \forward_data[159]~FF  (.D(write_data[159]), .CE(1'b1), .CLK(\clk~O ), 
           .SR(1'b0), .Q(forward_data[159])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_FF, CLK_POLARITY=1'b1, D_POLARITY=1'b1, CE_POLARITY=1'b1, SR_SYNC=1'b1, SR_SYNC_PRIORITY=1'b1, SR_VALUE=1'b0, SR_POLARITY=1'b1 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(16)
    defparam \forward_data[159]~FF .CLK_POLARITY = 1'b1;
    defparam \forward_data[159]~FF .CE_POLARITY = 1'b1;
    defparam \forward_data[159]~FF .SR_POLARITY = 1'b1;
    defparam \forward_data[159]~FF .D_POLARITY = 1'b1;
    defparam \forward_data[159]~FF .SR_SYNC = 1'b1;
    defparam \forward_data[159]~FF .SR_VALUE = 1'b0;
    defparam \forward_data[159]~FF .SR_SYNC_PRIORITY = 1'b1;
    EFX_RAM_5K memory__D$12 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[39:20]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[39] , \ram_read[38] , \ram_read[37] , \ram_read[36] , 
            \ram_read[35] , \ram_read[34] , \ram_read[33] , \ram_read[32] , 
            \ram_read[31] , \ram_read[30] , \ram_read[29] , \ram_read[28] , 
            \ram_read[27] , \ram_read[26] , \ram_read[25] , \ram_read[24] , 
            \ram_read[23] , \ram_read[22] , \ram_read[21] , \ram_read[20] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$12.READ_WIDTH = 20;
    defparam memory__D$12.WRITE_WIDTH = 20;
    defparam memory__D$12.WCLK_POLARITY = 1'b1;
    defparam memory__D$12.WCLKE_POLARITY = 1'b1;
    defparam memory__D$12.WE_POLARITY = 1'b1;
    defparam memory__D$12.RCLK_POLARITY = 1'b1;
    defparam memory__D$12.RE_POLARITY = 1'b1;
    defparam memory__D$12.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$12.OUTPUT_REG = 1'b0;
    defparam memory__D$12.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$b12 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[59:40]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[59] , \ram_read[58] , \ram_read[57] , \ram_read[56] , 
            \ram_read[55] , \ram_read[54] , \ram_read[53] , \ram_read[52] , 
            \ram_read[51] , \ram_read[50] , \ram_read[49] , \ram_read[48] , 
            \ram_read[47] , \ram_read[46] , \ram_read[45] , \ram_read[44] , 
            \ram_read[43] , \ram_read[42] , \ram_read[41] , \ram_read[40] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$b12.READ_WIDTH = 20;
    defparam memory__D$b12.WRITE_WIDTH = 20;
    defparam memory__D$b12.WCLK_POLARITY = 1'b1;
    defparam memory__D$b12.WCLKE_POLARITY = 1'b1;
    defparam memory__D$b12.WE_POLARITY = 1'b1;
    defparam memory__D$b12.RCLK_POLARITY = 1'b1;
    defparam memory__D$b12.RE_POLARITY = 1'b1;
    defparam memory__D$b12.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$b12.OUTPUT_REG = 1'b0;
    defparam memory__D$b12.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$c12 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[79:60]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[79] , \ram_read[78] , \ram_read[77] , \ram_read[76] , 
            \ram_read[75] , \ram_read[74] , \ram_read[73] , \ram_read[72] , 
            \ram_read[71] , \ram_read[70] , \ram_read[69] , \ram_read[68] , 
            \ram_read[67] , \ram_read[66] , \ram_read[65] , \ram_read[64] , 
            \ram_read[63] , \ram_read[62] , \ram_read[61] , \ram_read[60] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$c12.READ_WIDTH = 20;
    defparam memory__D$c12.WRITE_WIDTH = 20;
    defparam memory__D$c12.WCLK_POLARITY = 1'b1;
    defparam memory__D$c12.WCLKE_POLARITY = 1'b1;
    defparam memory__D$c12.WE_POLARITY = 1'b1;
    defparam memory__D$c12.RCLK_POLARITY = 1'b1;
    defparam memory__D$c12.RE_POLARITY = 1'b1;
    defparam memory__D$c12.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$c12.OUTPUT_REG = 1'b0;
    defparam memory__D$c12.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$d12 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[99:80]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[99] , \ram_read[98] , \ram_read[97] , \ram_read[96] , 
            \ram_read[95] , \ram_read[94] , \ram_read[93] , \ram_read[92] , 
            \ram_read[91] , \ram_read[90] , \ram_read[89] , \ram_read[88] , 
            \ram_read[87] , \ram_read[86] , \ram_read[85] , \ram_read[84] , 
            \ram_read[83] , \ram_read[82] , \ram_read[81] , \ram_read[80] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$d12.READ_WIDTH = 20;
    defparam memory__D$d12.WRITE_WIDTH = 20;
    defparam memory__D$d12.WCLK_POLARITY = 1'b1;
    defparam memory__D$d12.WCLKE_POLARITY = 1'b1;
    defparam memory__D$d12.WE_POLARITY = 1'b1;
    defparam memory__D$d12.RCLK_POLARITY = 1'b1;
    defparam memory__D$d12.RE_POLARITY = 1'b1;
    defparam memory__D$d12.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$d12.OUTPUT_REG = 1'b0;
    defparam memory__D$d12.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$e12 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[119:100]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[119] , \ram_read[118] , \ram_read[117] , 
            \ram_read[116] , \ram_read[115] , \ram_read[114] , \ram_read[113] , 
            \ram_read[112] , \ram_read[111] , \ram_read[110] , \ram_read[109] , 
            \ram_read[108] , \ram_read[107] , \ram_read[106] , \ram_read[105] , 
            \ram_read[104] , \ram_read[103] , \ram_read[102] , \ram_read[101] , 
            \ram_read[100] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$e12.READ_WIDTH = 20;
    defparam memory__D$e12.WRITE_WIDTH = 20;
    defparam memory__D$e12.WCLK_POLARITY = 1'b1;
    defparam memory__D$e12.WCLKE_POLARITY = 1'b1;
    defparam memory__D$e12.WE_POLARITY = 1'b1;
    defparam memory__D$e12.RCLK_POLARITY = 1'b1;
    defparam memory__D$e12.RE_POLARITY = 1'b1;
    defparam memory__D$e12.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$e12.OUTPUT_REG = 1'b0;
    defparam memory__D$e12.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$f12 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[139:120]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[139] , \ram_read[138] , \ram_read[137] , 
            \ram_read[136] , \ram_read[135] , \ram_read[134] , \ram_read[133] , 
            \ram_read[132] , \ram_read[131] , \ram_read[130] , \ram_read[129] , 
            \ram_read[128] , \ram_read[127] , \ram_read[126] , \ram_read[125] , 
            \ram_read[124] , \ram_read[123] , \ram_read[122] , \ram_read[121] , 
            \ram_read[120] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$f12.READ_WIDTH = 20;
    defparam memory__D$f12.WRITE_WIDTH = 20;
    defparam memory__D$f12.WCLK_POLARITY = 1'b1;
    defparam memory__D$f12.WCLKE_POLARITY = 1'b1;
    defparam memory__D$f12.WE_POLARITY = 1'b1;
    defparam memory__D$f12.RCLK_POLARITY = 1'b1;
    defparam memory__D$f12.RE_POLARITY = 1'b1;
    defparam memory__D$f12.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$f12.OUTPUT_REG = 1'b0;
    defparam memory__D$f12.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$g1 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[159:140]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[159] , \ram_read[158] , \ram_read[157] , 
            \ram_read[156] , \ram_read[155] , \ram_read[154] , \ram_read[153] , 
            \ram_read[152] , \ram_read[151] , \ram_read[150] , \ram_read[149] , 
            \ram_read[148] , \ram_read[147] , \ram_read[146] , \ram_read[145] , 
            \ram_read[144] , \ram_read[143] , \ram_read[142] , \ram_read[141] , 
            \ram_read[140] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$g1.READ_WIDTH = 20;
    defparam memory__D$g1.WRITE_WIDTH = 20;
    defparam memory__D$g1.WCLK_POLARITY = 1'b1;
    defparam memory__D$g1.WCLKE_POLARITY = 1'b1;
    defparam memory__D$g1.WE_POLARITY = 1'b1;
    defparam memory__D$g1.RCLK_POLARITY = 1'b1;
    defparam memory__D$g1.RE_POLARITY = 1'b1;
    defparam memory__D$g1.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$g1.OUTPUT_REG = 1'b0;
    defparam memory__D$g1.WRITE_MODE = "READ_FIRST";
    EFX_RAM_5K memory__D$2 (.WCLK(\clk~O ), .RCLK(\clk~O ), .WCLKE(1'b1), 
            .WE(write_enable), .RE(1'b1), .WDATA({write_data[19:0]}), 
            .WADDR({3'b000, write_address}), .RADDR({3'b000, read_address}), 
            .RDATA({\ram_read[19] , \ram_read[18] , \ram_read[17] , \ram_read[16] , 
            \ram_read[15] , \ram_read[14] , \ram_read[13] , \ram_read[12] , 
            \ram_read[11] , \ram_read[10] , \ram_read[9] , \ram_read[8] , 
            \ram_read[7] , \ram_read[6] , \ram_read[5] , \ram_read[4] , 
            \ram_read[3] , \ram_read[2] , \ram_read[1] , \ram_read[0] })) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_RAM_5K, READ_WIDTH=20, WRITE_WIDTH=20, WCLK_POLARITY=1'b1, WCLKE_POLARITY=1'b1, WE_POLARITY=1'b1, RCLK_POLARITY=1'b1, RE_POLARITY=1'b1, OUTPUT_REG=1'b0, WRITE_MODE="READ_FIRST", INIT_0=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_1=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_2=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_3=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_4=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_5=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_6=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_7=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_8=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_9=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_A=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_B=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_C=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_D=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_E=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_F=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_10=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_11=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_12=256'h0000000000000000000000000000000000000000000000000000000000000000, INIT_13=256'h0000000000000000000000000000000000000000000000000000000000000000, PRESERVE_USER_INIT=1'b0 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(7)
    defparam memory__D$2.READ_WIDTH = 20;
    defparam memory__D$2.WRITE_WIDTH = 20;
    defparam memory__D$2.WCLK_POLARITY = 1'b1;
    defparam memory__D$2.WCLKE_POLARITY = 1'b1;
    defparam memory__D$2.WE_POLARITY = 1'b1;
    defparam memory__D$2.RCLK_POLARITY = 1'b1;
    defparam memory__D$2.RE_POLARITY = 1'b1;
    defparam memory__D$2.INIT_0 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_1 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_2 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_3 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_4 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_5 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_6 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_7 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_8 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_9 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_A = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_B = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_C = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_D = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_E = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_F = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_10 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_11 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_12 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.INIT_13 = 256'h0000000000000000000000000000000000000000000000000000000000000000;
    defparam memory__D$2.OUTPUT_REG = 1'b0;
    defparam memory__D$2.WRITE_MODE = "READ_FIRST";
    EFX_LUT4 LUT__1324 (.I0(forward_data[157]), .I1(\ram_read[157] ), .I2(forward_valid), 
            .O(read_data[157])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1324.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1325 (.I0(forward_data[156]), .I1(\ram_read[156] ), .I2(forward_valid), 
            .O(read_data[156])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1325.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1326 (.I0(forward_data[155]), .I1(\ram_read[155] ), .I2(forward_valid), 
            .O(read_data[155])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1326.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1327 (.I0(forward_data[154]), .I1(\ram_read[154] ), .I2(forward_valid), 
            .O(read_data[154])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1327.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1328 (.I0(forward_data[153]), .I1(\ram_read[153] ), .I2(forward_valid), 
            .O(read_data[153])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1328.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1329 (.I0(forward_data[152]), .I1(\ram_read[152] ), .I2(forward_valid), 
            .O(read_data[152])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1329.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1330 (.I0(forward_data[151]), .I1(\ram_read[151] ), .I2(forward_valid), 
            .O(read_data[151])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1330.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1331 (.I0(forward_data[150]), .I1(\ram_read[150] ), .I2(forward_valid), 
            .O(read_data[150])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1331.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1332 (.I0(forward_data[149]), .I1(\ram_read[149] ), .I2(forward_valid), 
            .O(read_data[149])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1332.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1333 (.I0(forward_data[148]), .I1(\ram_read[148] ), .I2(forward_valid), 
            .O(read_data[148])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1333.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1334 (.I0(forward_data[147]), .I1(\ram_read[147] ), .I2(forward_valid), 
            .O(read_data[147])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1334.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1335 (.I0(forward_data[146]), .I1(\ram_read[146] ), .I2(forward_valid), 
            .O(read_data[146])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1335.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1336 (.I0(forward_data[145]), .I1(\ram_read[145] ), .I2(forward_valid), 
            .O(read_data[145])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1336.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1337 (.I0(forward_data[144]), .I1(\ram_read[144] ), .I2(forward_valid), 
            .O(read_data[144])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1337.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1338 (.I0(forward_data[143]), .I1(\ram_read[143] ), .I2(forward_valid), 
            .O(read_data[143])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1338.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1339 (.I0(forward_data[142]), .I1(\ram_read[142] ), .I2(forward_valid), 
            .O(read_data[142])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1339.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1340 (.I0(forward_data[141]), .I1(\ram_read[141] ), .I2(forward_valid), 
            .O(read_data[141])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1340.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1341 (.I0(forward_data[140]), .I1(\ram_read[140] ), .I2(forward_valid), 
            .O(read_data[140])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1341.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1342 (.I0(forward_data[139]), .I1(\ram_read[139] ), .I2(forward_valid), 
            .O(read_data[139])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1342.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1343 (.I0(forward_data[138]), .I1(\ram_read[138] ), .I2(forward_valid), 
            .O(read_data[138])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1343.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1344 (.I0(forward_data[137]), .I1(\ram_read[137] ), .I2(forward_valid), 
            .O(read_data[137])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1344.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1345 (.I0(forward_data[136]), .I1(\ram_read[136] ), .I2(forward_valid), 
            .O(read_data[136])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1345.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1346 (.I0(forward_data[135]), .I1(\ram_read[135] ), .I2(forward_valid), 
            .O(read_data[135])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1346.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1347 (.I0(forward_data[134]), .I1(\ram_read[134] ), .I2(forward_valid), 
            .O(read_data[134])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1347.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1348 (.I0(forward_data[133]), .I1(\ram_read[133] ), .I2(forward_valid), 
            .O(read_data[133])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1348.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1349 (.I0(forward_data[132]), .I1(\ram_read[132] ), .I2(forward_valid), 
            .O(read_data[132])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1349.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1350 (.I0(forward_data[131]), .I1(\ram_read[131] ), .I2(forward_valid), 
            .O(read_data[131])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1350.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1351 (.I0(forward_data[130]), .I1(\ram_read[130] ), .I2(forward_valid), 
            .O(read_data[130])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1351.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1352 (.I0(forward_data[129]), .I1(\ram_read[129] ), .I2(forward_valid), 
            .O(read_data[129])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1352.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1353 (.I0(forward_data[128]), .I1(\ram_read[128] ), .I2(forward_valid), 
            .O(read_data[128])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1353.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1354 (.I0(forward_data[127]), .I1(\ram_read[127] ), .I2(forward_valid), 
            .O(read_data[127])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1354.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1355 (.I0(forward_data[126]), .I1(\ram_read[126] ), .I2(forward_valid), 
            .O(read_data[126])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1355.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1356 (.I0(forward_data[125]), .I1(\ram_read[125] ), .I2(forward_valid), 
            .O(read_data[125])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1356.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1357 (.I0(forward_data[124]), .I1(\ram_read[124] ), .I2(forward_valid), 
            .O(read_data[124])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1357.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1358 (.I0(forward_data[123]), .I1(\ram_read[123] ), .I2(forward_valid), 
            .O(read_data[123])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1358.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1359 (.I0(forward_data[122]), .I1(\ram_read[122] ), .I2(forward_valid), 
            .O(read_data[122])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1359.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1360 (.I0(forward_data[121]), .I1(\ram_read[121] ), .I2(forward_valid), 
            .O(read_data[121])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1360.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1361 (.I0(forward_data[120]), .I1(\ram_read[120] ), .I2(forward_valid), 
            .O(read_data[120])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1361.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1362 (.I0(forward_data[119]), .I1(\ram_read[119] ), .I2(forward_valid), 
            .O(read_data[119])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1362.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1363 (.I0(forward_data[118]), .I1(\ram_read[118] ), .I2(forward_valid), 
            .O(read_data[118])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1363.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1364 (.I0(forward_data[117]), .I1(\ram_read[117] ), .I2(forward_valid), 
            .O(read_data[117])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1364.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1365 (.I0(forward_data[116]), .I1(\ram_read[116] ), .I2(forward_valid), 
            .O(read_data[116])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1365.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1366 (.I0(forward_data[115]), .I1(\ram_read[115] ), .I2(forward_valid), 
            .O(read_data[115])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1366.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1367 (.I0(forward_data[114]), .I1(\ram_read[114] ), .I2(forward_valid), 
            .O(read_data[114])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1367.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1368 (.I0(forward_data[113]), .I1(\ram_read[113] ), .I2(forward_valid), 
            .O(read_data[113])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1368.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1369 (.I0(forward_data[112]), .I1(\ram_read[112] ), .I2(forward_valid), 
            .O(read_data[112])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1369.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1370 (.I0(forward_data[111]), .I1(\ram_read[111] ), .I2(forward_valid), 
            .O(read_data[111])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1370.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1371 (.I0(forward_data[110]), .I1(\ram_read[110] ), .I2(forward_valid), 
            .O(read_data[110])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1371.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1372 (.I0(forward_data[109]), .I1(\ram_read[109] ), .I2(forward_valid), 
            .O(read_data[109])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1372.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1373 (.I0(forward_data[108]), .I1(\ram_read[108] ), .I2(forward_valid), 
            .O(read_data[108])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1373.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1374 (.I0(forward_data[107]), .I1(\ram_read[107] ), .I2(forward_valid), 
            .O(read_data[107])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1374.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1375 (.I0(forward_data[106]), .I1(\ram_read[106] ), .I2(forward_valid), 
            .O(read_data[106])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1375.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1376 (.I0(forward_data[105]), .I1(\ram_read[105] ), .I2(forward_valid), 
            .O(read_data[105])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1376.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1377 (.I0(forward_data[104]), .I1(\ram_read[104] ), .I2(forward_valid), 
            .O(read_data[104])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1377.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1378 (.I0(forward_data[103]), .I1(\ram_read[103] ), .I2(forward_valid), 
            .O(read_data[103])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1378.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1379 (.I0(forward_data[102]), .I1(\ram_read[102] ), .I2(forward_valid), 
            .O(read_data[102])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1379.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1380 (.I0(forward_data[101]), .I1(\ram_read[101] ), .I2(forward_valid), 
            .O(read_data[101])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1380.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1381 (.I0(forward_data[100]), .I1(\ram_read[100] ), .I2(forward_valid), 
            .O(read_data[100])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1381.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1382 (.I0(forward_data[99]), .I1(\ram_read[99] ), .I2(forward_valid), 
            .O(read_data[99])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1382.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1383 (.I0(forward_data[98]), .I1(\ram_read[98] ), .I2(forward_valid), 
            .O(read_data[98])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1383.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1384 (.I0(forward_data[97]), .I1(\ram_read[97] ), .I2(forward_valid), 
            .O(read_data[97])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1384.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1385 (.I0(forward_data[96]), .I1(\ram_read[96] ), .I2(forward_valid), 
            .O(read_data[96])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1385.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1386 (.I0(forward_data[95]), .I1(\ram_read[95] ), .I2(forward_valid), 
            .O(read_data[95])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1386.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1387 (.I0(forward_data[94]), .I1(\ram_read[94] ), .I2(forward_valid), 
            .O(read_data[94])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1387.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1388 (.I0(forward_data[93]), .I1(\ram_read[93] ), .I2(forward_valid), 
            .O(read_data[93])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1388.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1389 (.I0(forward_data[92]), .I1(\ram_read[92] ), .I2(forward_valid), 
            .O(read_data[92])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1389.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1390 (.I0(forward_data[91]), .I1(\ram_read[91] ), .I2(forward_valid), 
            .O(read_data[91])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1390.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1391 (.I0(forward_data[90]), .I1(\ram_read[90] ), .I2(forward_valid), 
            .O(read_data[90])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1391.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1392 (.I0(forward_data[89]), .I1(\ram_read[89] ), .I2(forward_valid), 
            .O(read_data[89])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1392.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1393 (.I0(forward_data[88]), .I1(\ram_read[88] ), .I2(forward_valid), 
            .O(read_data[88])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1393.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1394 (.I0(forward_data[87]), .I1(\ram_read[87] ), .I2(forward_valid), 
            .O(read_data[87])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1394.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1395 (.I0(forward_data[86]), .I1(\ram_read[86] ), .I2(forward_valid), 
            .O(read_data[86])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1395.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1396 (.I0(forward_data[85]), .I1(\ram_read[85] ), .I2(forward_valid), 
            .O(read_data[85])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1396.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1397 (.I0(forward_data[84]), .I1(\ram_read[84] ), .I2(forward_valid), 
            .O(read_data[84])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1397.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1398 (.I0(forward_data[83]), .I1(\ram_read[83] ), .I2(forward_valid), 
            .O(read_data[83])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1398.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1399 (.I0(forward_data[82]), .I1(\ram_read[82] ), .I2(forward_valid), 
            .O(read_data[82])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1399.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1400 (.I0(forward_data[81]), .I1(\ram_read[81] ), .I2(forward_valid), 
            .O(read_data[81])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1400.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1401 (.I0(forward_data[80]), .I1(\ram_read[80] ), .I2(forward_valid), 
            .O(read_data[80])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1401.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1402 (.I0(forward_data[79]), .I1(\ram_read[79] ), .I2(forward_valid), 
            .O(read_data[79])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1402.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1403 (.I0(forward_data[78]), .I1(\ram_read[78] ), .I2(forward_valid), 
            .O(read_data[78])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1403.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1404 (.I0(forward_data[77]), .I1(\ram_read[77] ), .I2(forward_valid), 
            .O(read_data[77])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1404.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1405 (.I0(forward_data[76]), .I1(\ram_read[76] ), .I2(forward_valid), 
            .O(read_data[76])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1405.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1406 (.I0(forward_data[75]), .I1(\ram_read[75] ), .I2(forward_valid), 
            .O(read_data[75])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1406.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1407 (.I0(forward_data[74]), .I1(\ram_read[74] ), .I2(forward_valid), 
            .O(read_data[74])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1407.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1408 (.I0(forward_data[73]), .I1(\ram_read[73] ), .I2(forward_valid), 
            .O(read_data[73])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1408.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1409 (.I0(forward_data[72]), .I1(\ram_read[72] ), .I2(forward_valid), 
            .O(read_data[72])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1409.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1410 (.I0(forward_data[71]), .I1(\ram_read[71] ), .I2(forward_valid), 
            .O(read_data[71])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1410.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1411 (.I0(forward_data[70]), .I1(\ram_read[70] ), .I2(forward_valid), 
            .O(read_data[70])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1411.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1412 (.I0(forward_data[69]), .I1(\ram_read[69] ), .I2(forward_valid), 
            .O(read_data[69])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1412.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1413 (.I0(forward_data[68]), .I1(\ram_read[68] ), .I2(forward_valid), 
            .O(read_data[68])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1413.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1414 (.I0(forward_data[67]), .I1(\ram_read[67] ), .I2(forward_valid), 
            .O(read_data[67])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1414.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1415 (.I0(forward_data[66]), .I1(\ram_read[66] ), .I2(forward_valid), 
            .O(read_data[66])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1415.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1416 (.I0(forward_data[65]), .I1(\ram_read[65] ), .I2(forward_valid), 
            .O(read_data[65])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1416.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1417 (.I0(forward_data[64]), .I1(\ram_read[64] ), .I2(forward_valid), 
            .O(read_data[64])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1417.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1418 (.I0(forward_data[63]), .I1(\ram_read[63] ), .I2(forward_valid), 
            .O(read_data[63])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1418.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1419 (.I0(forward_data[62]), .I1(\ram_read[62] ), .I2(forward_valid), 
            .O(read_data[62])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1419.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1420 (.I0(forward_data[61]), .I1(\ram_read[61] ), .I2(forward_valid), 
            .O(read_data[61])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1420.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1421 (.I0(forward_data[60]), .I1(\ram_read[60] ), .I2(forward_valid), 
            .O(read_data[60])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1421.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1422 (.I0(\ram_read[59] ), .I1(forward_data[59]), .I2(forward_valid), 
            .O(read_data[59])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1422.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1423 (.I0(\ram_read[58] ), .I1(forward_data[58]), .I2(forward_valid), 
            .O(read_data[58])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1423.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1424 (.I0(\ram_read[57] ), .I1(forward_data[57]), .I2(forward_valid), 
            .O(read_data[57])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1424.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1425 (.I0(\ram_read[56] ), .I1(forward_data[56]), .I2(forward_valid), 
            .O(read_data[56])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1425.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1426 (.I0(\ram_read[55] ), .I1(forward_data[55]), .I2(forward_valid), 
            .O(read_data[55])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1426.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1427 (.I0(\ram_read[54] ), .I1(forward_data[54]), .I2(forward_valid), 
            .O(read_data[54])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1427.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1428 (.I0(\ram_read[53] ), .I1(forward_data[53]), .I2(forward_valid), 
            .O(read_data[53])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1428.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1429 (.I0(\ram_read[52] ), .I1(forward_data[52]), .I2(forward_valid), 
            .O(read_data[52])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1429.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1430 (.I0(\ram_read[51] ), .I1(forward_data[51]), .I2(forward_valid), 
            .O(read_data[51])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1430.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1431 (.I0(\ram_read[50] ), .I1(forward_data[50]), .I2(forward_valid), 
            .O(read_data[50])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1431.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1432 (.I0(\ram_read[49] ), .I1(forward_data[49]), .I2(forward_valid), 
            .O(read_data[49])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1432.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1433 (.I0(\ram_read[48] ), .I1(forward_data[48]), .I2(forward_valid), 
            .O(read_data[48])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1433.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1434 (.I0(\ram_read[47] ), .I1(forward_data[47]), .I2(forward_valid), 
            .O(read_data[47])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1434.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1435 (.I0(\ram_read[46] ), .I1(forward_data[46]), .I2(forward_valid), 
            .O(read_data[46])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1435.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1436 (.I0(\ram_read[45] ), .I1(forward_data[45]), .I2(forward_valid), 
            .O(read_data[45])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1436.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1437 (.I0(\ram_read[44] ), .I1(forward_data[44]), .I2(forward_valid), 
            .O(read_data[44])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1437.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1438 (.I0(\ram_read[43] ), .I1(forward_data[43]), .I2(forward_valid), 
            .O(read_data[43])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1438.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1439 (.I0(\ram_read[42] ), .I1(forward_data[42]), .I2(forward_valid), 
            .O(read_data[42])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1439.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1440 (.I0(\ram_read[41] ), .I1(forward_data[41]), .I2(forward_valid), 
            .O(read_data[41])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1440.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1441 (.I0(\ram_read[40] ), .I1(forward_data[40]), .I2(forward_valid), 
            .O(read_data[40])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1441.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1442 (.I0(\ram_read[39] ), .I1(forward_data[39]), .I2(forward_valid), 
            .O(read_data[39])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1442.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1443 (.I0(\ram_read[38] ), .I1(forward_data[38]), .I2(forward_valid), 
            .O(read_data[38])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1443.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1444 (.I0(\ram_read[37] ), .I1(forward_data[37]), .I2(forward_valid), 
            .O(read_data[37])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1444.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1445 (.I0(\ram_read[36] ), .I1(forward_data[36]), .I2(forward_valid), 
            .O(read_data[36])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1445.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1446 (.I0(\ram_read[35] ), .I1(forward_data[35]), .I2(forward_valid), 
            .O(read_data[35])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1446.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1447 (.I0(\ram_read[34] ), .I1(forward_data[34]), .I2(forward_valid), 
            .O(read_data[34])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1447.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1448 (.I0(\ram_read[33] ), .I1(forward_data[33]), .I2(forward_valid), 
            .O(read_data[33])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1448.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1449 (.I0(\ram_read[32] ), .I1(forward_data[32]), .I2(forward_valid), 
            .O(read_data[32])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1449.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1450 (.I0(\ram_read[31] ), .I1(forward_data[31]), .I2(forward_valid), 
            .O(read_data[31])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1450.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1451 (.I0(\ram_read[30] ), .I1(forward_data[30]), .I2(forward_valid), 
            .O(read_data[30])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1451.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1452 (.I0(\ram_read[29] ), .I1(forward_data[29]), .I2(forward_valid), 
            .O(read_data[29])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1452.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1453 (.I0(\ram_read[28] ), .I1(forward_data[28]), .I2(forward_valid), 
            .O(read_data[28])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1453.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1454 (.I0(\ram_read[27] ), .I1(forward_data[27]), .I2(forward_valid), 
            .O(read_data[27])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1454.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1455 (.I0(\ram_read[26] ), .I1(forward_data[26]), .I2(forward_valid), 
            .O(read_data[26])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1455.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1456 (.I0(\ram_read[25] ), .I1(forward_data[25]), .I2(forward_valid), 
            .O(read_data[25])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1456.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1457 (.I0(\ram_read[24] ), .I1(forward_data[24]), .I2(forward_valid), 
            .O(read_data[24])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1457.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1458 (.I0(\ram_read[23] ), .I1(forward_data[23]), .I2(forward_valid), 
            .O(read_data[23])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1458.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1459 (.I0(\ram_read[22] ), .I1(forward_data[22]), .I2(forward_valid), 
            .O(read_data[22])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1459.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1460 (.I0(\ram_read[21] ), .I1(forward_data[21]), .I2(forward_valid), 
            .O(read_data[21])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1460.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1461 (.I0(\ram_read[20] ), .I1(forward_data[20]), .I2(forward_valid), 
            .O(read_data[20])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hcaca */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1461.LUTMASK = 16'hcaca;
    EFX_LUT4 LUT__1462 (.I0(forward_data[19]), .I1(\ram_read[19] ), .I2(forward_valid), 
            .O(read_data[19])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1462.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1463 (.I0(forward_data[18]), .I1(\ram_read[18] ), .I2(forward_valid), 
            .O(read_data[18])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1463.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1464 (.I0(forward_data[17]), .I1(\ram_read[17] ), .I2(forward_valid), 
            .O(read_data[17])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1464.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1465 (.I0(forward_data[16]), .I1(\ram_read[16] ), .I2(forward_valid), 
            .O(read_data[16])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1465.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1466 (.I0(forward_data[15]), .I1(\ram_read[15] ), .I2(forward_valid), 
            .O(read_data[15])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1466.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1467 (.I0(forward_data[14]), .I1(\ram_read[14] ), .I2(forward_valid), 
            .O(read_data[14])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1467.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1468 (.I0(forward_data[13]), .I1(\ram_read[13] ), .I2(forward_valid), 
            .O(read_data[13])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1468.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1469 (.I0(forward_data[12]), .I1(\ram_read[12] ), .I2(forward_valid), 
            .O(read_data[12])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1469.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1470 (.I0(forward_data[11]), .I1(\ram_read[11] ), .I2(forward_valid), 
            .O(read_data[11])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1470.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1471 (.I0(forward_data[10]), .I1(\ram_read[10] ), .I2(forward_valid), 
            .O(read_data[10])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1471.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1472 (.I0(forward_data[9]), .I1(\ram_read[9] ), .I2(forward_valid), 
            .O(read_data[9])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1472.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1473 (.I0(forward_data[8]), .I1(\ram_read[8] ), .I2(forward_valid), 
            .O(read_data[8])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1473.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1474 (.I0(forward_data[7]), .I1(\ram_read[7] ), .I2(forward_valid), 
            .O(read_data[7])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1474.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1475 (.I0(forward_data[6]), .I1(\ram_read[6] ), .I2(forward_valid), 
            .O(read_data[6])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1475.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1476 (.I0(forward_data[5]), .I1(\ram_read[5] ), .I2(forward_valid), 
            .O(read_data[5])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1476.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1477 (.I0(forward_data[4]), .I1(\ram_read[4] ), .I2(forward_valid), 
            .O(read_data[4])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1477.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1478 (.I0(forward_data[3]), .I1(\ram_read[3] ), .I2(forward_valid), 
            .O(read_data[3])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1478.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1479 (.I0(forward_data[2]), .I1(\ram_read[2] ), .I2(forward_valid), 
            .O(read_data[2])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1479.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1480 (.I0(forward_data[1]), .I1(\ram_read[1] ), .I2(forward_valid), 
            .O(read_data[1])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1480.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1481 (.I0(forward_data[0]), .I1(\ram_read[0] ), .I2(forward_valid), 
            .O(read_data[0])) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'hacac */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(17)
    defparam LUT__1481.LUTMASK = 16'hacac;
    EFX_LUT4 LUT__1482 (.I0(write_address[4]), .I1(read_address[4]), .I2(write_enable), 
            .O(n829)) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'h9090 */ ;
    defparam LUT__1482.LUTMASK = 16'h9090;
    EFX_LUT4 LUT__1483 (.I0(write_address[3]), .I1(read_address[3]), .I2(write_address[2]), 
            .I3(read_address[2]), .O(n830)) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'h9009 */ ;
    defparam LUT__1483.LUTMASK = 16'h9009;
    EFX_LUT4 LUT__1484 (.I0(write_address[1]), .I1(read_address[1]), .I2(write_address[0]), 
            .I3(read_address[0]), .O(n831)) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'h9009 */ ;
    defparam LUT__1484.LUTMASK = 16'h9009;
    EFX_LUT4 LUT__1485 (.I0(n829), .I1(n830), .I2(n831), .O(n170)) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_LUT4, LUTMASK=16'h8080 */ ;   // C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261017\efinity-memory-inference-r1\registered-bypass\cnc3_event_bank.v(13)
    defparam LUT__1485.LUTMASK = 16'h8080;
    EFX_GBUFCE CLKBUF__0 (.CE(1'b1), .I(clk), .O(\clk~O )) /* verific EFX_ATTRIBUTE_CELL_NAME=EFX_GBUFCE, CE_POLARITY=1'b1 */ ;
    defparam CLKBUF__0.CE_POLARITY = 1'b1;
    
endmodule

//
// Verific Verilog Description of module EFX_LUT4_54157662_0
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_FF_54157662_0
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_0
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_1
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_2
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_3
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_4
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_5
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_6
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_RAM_5K_54157662__20_20_7
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_LUT4_54157662_1
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_LUT4_54157662_2
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_LUT4_54157662_3
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_LUT4_54157662_4
// module not written out since it is a black box. 
//


//
// Verific Verilog Description of module EFX_GBUFCE_54157662_0
// module not written out since it is a black box. 
//

