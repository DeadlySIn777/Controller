`timescale 1ns/1ps
// Real target protocol C is linked through VPI; GPIO observations are explicit
// disconnected fixtures. This is not execution of target DMA/ISR instructions.
module iol1_target_c_peer #(parameter [7:0] CLASS_ID=8'h11,parameter [3:0] SLOT=0)(
 input wire reset_n,cs_n,sclk,mosi,input wire [4:0] injected_error,
 output reg miso,output integer bad_commands,output integer command_count);
 reg [319:0] command_shift,response;integer bits,result;
 realtime cs_start,last_fall;integer first_edge;
    function [31:0] crc32;
        input [287:0] body;
        reg [31:0] c; reg [7:0] b; integer i,j;
        begin
            c = 32'hffffffff;
            for(i=0;i<36;i=i+1) begin
                b=body[287-i*8 -:8];
                for(j=0;j<8;j=j+1)
                    c = (c[0]^b[j]) ? ((c>>1)^32'h82f63b78) : (c>>1);
            end
            crc32 = c ^ 32'hffffffff;
        end
    endfunction

 always @(negedge reset_n) begin bits=0;bad_commands=0;command_count=0;miso=0;$iol1_c_reset;end
 initial begin bits=0;bad_commands=0;command_count=0;miso=0;end
 always @(negedge cs_n) if(reset_n) begin
  bits=0;command_shift=0;first_edge=1;cs_start=$realtime;
  $iol1_c_reply(SLOT,response,injected_error);miso=response[319];
 end
 always @(posedge sclk) if(reset_n && !cs_n) begin
  if(first_edge)begin if($realtime-cs_start<20000.0)$fatal(1,"insufficient20ussetup");first_edge=0;end
  command_shift={command_shift[318:0],mosi};bits=bits+1;
 end
 always @(negedge sclk) if(reset_n && !cs_n) begin
  last_fall=$realtime;if(bits<320)miso=response[319-bits];else miso=0;
 end
 always @(posedge cs_n) if(reset_n && bits>0) begin
  if($realtime-last_fall<5000.0)$fatal(1,"insufficient5ushold");
  $iol1_c_accept(SLOT,command_shift,bits,$rtoi($realtime/1000.0),result);
  command_count=command_count+1;
  if(bits!=320 || command_shift[319:288]!={8'ha7,8'h01,CLASS_ID,4'b0,SLOT} || command_shift[31:0]!=crc32(command_shift[319:32]) || !(command_shift[255:248]==0 || command_shift[255:248]==1 || command_shift[255:248]==8 || (SLOT==0&&command_shift[255:248]==16)))begin
   bad_commands=bad_commands+1;
  end
  miso=0;
 end
endmodule
