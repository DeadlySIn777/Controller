`timescale 1ns/1ps
// Original cnc_encoder quadrature/count/index algorithm, retaining its three-
// stage input synchronizers, with runtime AB/Z stability filtering and explicit
// SYNC clearing of illegal/index observations WITHOUT clearing position count.
module cnc3_encoder_runtime (
 input wire clk,input wire rst_n,input wire a,input wire b,input wire z,
 input wire [3:0] filter_ticks,input wire clear_observations,
 output reg signed [31:0] count,output reg signed [31:0] index_count,
 output reg index_seen,output reg invalid_transition,
 output reg index_capture
);
 reg[2:0] a_sync,b_sync,z_sync;
 reg[2:0] filtered;
 reg[3:0] stable_a,stable_b,stable_z;
 wire[2:0] sampled={a_sync[2],b_sync[2],z_sync[2]};
 wire[2:0] observed=(filter_ticks==0)?sampled:filtered;
 wire[1:0] ab=observed[2:1];
 reg[1:0] previous_ab;reg previous_z;
 reg signed[31:0] next_count;
 always@*begin
  next_count=count;
  case({previous_ab,ab})
   4'b0001,4'b0111,4'b1110,4'b1000:next_count=count+1'b1;
   4'b0010,4'b1011,4'b1101,4'b0100:next_count=count-1'b1;
   default:next_count=count;
  endcase
 end
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   a_sync<=0;b_sync<=0;z_sync<=0;filtered<=0;stable_a<=0;stable_b<=0;stable_z<=0;
   previous_ab<=0;previous_z<=0;count<=0;index_count<=0;
   index_seen<=0;invalid_transition<=0;index_capture<=0;
  end else begin
   a_sync<={a_sync[1:0],a};b_sync<={b_sync[1:0],b};z_sync<={z_sync[1:0],z};
   if(sampled[2]==filtered[2])stable_a<=0;
   else if(filter_ticks==0 || stable_a+1'b1>=filter_ticks)begin filtered[2]<=sampled[2];stable_a<=0;end
   else stable_a<=stable_a+1'b1;
   if(sampled[1]==filtered[1])stable_b<=0;
   else if(filter_ticks==0 || stable_b+1'b1>=filter_ticks)begin filtered[1]<=sampled[1];stable_b<=0;end
   else stable_b<=stable_b+1'b1;
   if(sampled[0]==filtered[0])stable_z<=0;
   else if(filter_ticks==0 || stable_z+1'b1>=filter_ticks)begin filtered[0]<=sampled[0];stable_z<=0;end
   else stable_z<=stable_z+1'b1;
   count<=next_count;previous_ab<=ab;previous_z<=observed[0];index_capture<=0;
   if(clear_observations)begin invalid_transition<=0;index_seen<=0;end
   else if((previous_ab^ab)==2'b11)invalid_transition<=1;
   if(observed[0]&&!previous_z)begin index_count<=next_count;index_seen<=1;index_capture<=1;end
  end
 end
endmodule
