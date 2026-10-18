`timescale 1ns/1ps
module ff_lut_reset_probe_tb;
reg clk=0,rst_n=0,d=0;wire[3:0]q;wire nor4,nor3;
genvar i;generate for(i=0;i<4;i=i+1)begin:f
 EFX_FF x(.D(d),.CE(1'b1),.CLK(clk),.SR(rst_n),.Q(q[i]));
 defparam x.SR_POLARITY=1'b0;defparam x.SR_SYNC=1'b0;defparam x.SR_VALUE=1'b0;
end endgenerate
EFX_LUT4 four(.I0(q[0]),.I1(q[1]),.I2(q[2]),.I3(q[3]),.O(nor4));defparam four.LUTMASK=16'h0001;
EFX_LUT4 three(.I0(q[0]),.I1(q[1]),.I2(q[2]),.O(nor3));defparam three.LUTMASK=16'h0101;
integer initial_wrong=0,reset_still_wrong=0;
initial begin
 #1;$display("FF_INIT q=%h nor4=%b expected1 nor3=%b",q,nor4,nor3);
 initial_wrong=(q===0&&nor4===0&&nor3===1);
 clk=1'bx;rst_n=1'bx;d=1'bx;#1;clk=0;rst_n=0;d=0;#1;
 clk=1;#1;$display("EXPLICIT_EXTERNAL_X_AND_RESET q=%h nor4=%b expected1 nor3=%b",q,nor4,nor3);
 reset_still_wrong=(q===0&&nor4===0&&nor3===1);
 clk=0;rst_n=1;d=1;#1;clk=1;#1;
 $display("ACTUAL_FF_CHANGE q=%h nor4=%b expected0 nor3=%b",q,nor4,nor3);
 if(q!==4'hf||nor4!==0||nor3!==0)$fatal(1,"FF change control failed");
 rst_n=0;#1;$display("RESET_AFTER_ACTUAL_FF_CHANGE q=%h nor4=%b expected1 nor3=%b",q,nor4,nor3);
 if(q!==0||nor4!==1||nor3!==1)$fatal(1,"actual reset after FF transition control failed");
 if(!initial_wrong||!reset_still_wrong)$fatal(1,"reported startup mechanism not reproduced");
 $display("FF_FED_LUT_MODEL_STARTUP_DEFECT_REPRODUCED_WITH_RESET_CONTROL");$finish;
end
endmodule
