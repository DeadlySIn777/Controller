module parallel_guard(input[1407:0] request_frame,input[191:0] pulse_ticks,space_ticks,output wire[11:0] good);
 wire[11:0] update_channel_valid;
 genvar channel;
 generate for(channel=0;channel<12;channel=channel+1)begin:rate_admission
  wire[31:0] raw=request_frame[1279-32*channel -:32];
  wire[31:0] magnitude=raw[31]?(~raw+32'd1):raw;
  wire[15:0] high_value=pulse_ticks[191-16*channel -:16];
  wire[15:0] low_value=space_ticks[191-16*channel -:16];
  wire[10:0] period_ticks={1'b0,high_value[9:0]}+{1'b0,low_value[9:0]}+11'd1;
  wire[35:0] period_product=magnitude[24:0]*period_ticks;
  assign update_channel_valid[channel]=magnitude<=32'h01000000 &&
   high_value>=100 && high_value<=1023 && low_value>=100 && low_value<=1023 &&
   period_product<=36'd4294967296;
 end endgenerate

assign good=update_channel_valid;
endmodule
