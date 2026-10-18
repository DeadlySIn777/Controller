`timescale 1ns/1ps
// SIM2 local profile: exact frozen frame, explicit disconnected identity.
module cnc3_runtime_cap3(input wire ready,output reg[1391:0] payload);
 integer i;
 always@*begin
  payload=0;
  payload[1391 -:32]=32'h43415033;payload[1391-4*8 -:8]=3;
  payload[1391-6*8 -:8]=12;payload[1391-7*8 -:8]=ready?12:0;
  payload[1391-8*8 -:8]=4;payload[1391-9*8 -:8]=4;payload[1391-10*8 -:8]=ready?4:0;
  payload[1391-12*8 -:32]=32'h00017fff;
  payload[1391-16*8 -:32]=50000000;payload[1391-20*8 -:32]=32'h01000000;
  for(i=0;i<4;i=i+1)payload[1391-(24+2*i)*8 -:16]=100;
  payload[1391-32*8 -:16]=100;payload[1391-34*8 -:16]=1023;
  payload[1391-36*8 -:32]=250000;payload[1391-40*8 -:16]=500;
  payload[1391-42*8 -:8]=4;payload[1391-44*8 -:16]=176;payload[1391-46*8 -:16]=96;
  payload[1391-48*8 -:8]=8;payload[1391-49*8 -:8]=2;
  payload[1391-50*8 -:32]=32'h00080804;
  payload[1391-64*8 -:32]=32'hd3494d32;payload[1391-68*8 -:32]=32'h53494d32;
  payload[1391-72*8 -:16]=256;payload[1391-76*8 -:16]=50;
 end
endmodule
