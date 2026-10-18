`timescale 1ns/1ps
// Component-only ideal digital model. No receiver, cable, metastability or
// fitted FPGA timing model; four base-channel instances, not twelve ABZ ports.
module tb_encoder4_limits;
 reg clk=0;always #10 clk=!clk;
 reg rst_n=0;
 reg[3:0]a=0,b=0,z=0;
 wire signed[31:0] count[0:3],index_count[0:3];
 wire[3:0]index_seen,invalid;
 genvar g;generate for(g=0;g<4;g=g+1)begin:encoders
  cnc_encoder dut(.clk(clk),.rst_n(rst_n),.a(a[g]),.b(b[g]),.z(z[g]),.count(count[g]),.index_count(index_count[g]),.index_seen(index_seen[g]),.invalid_transition(invalid[g]));
 end endgenerate
 integer edge_ns[0:8];integer k,rev,phase_case,j,rows=0,checks=0,failures;
 task automatic drive(input integer channel,input integer period_ns,input integer reverse,input integer offset);
  integer n,sequence_index;reg[1:0]ab;
  begin
   #(offset);
   for(n=1;n<=1000;n=n+1)begin
    #(period_ns);sequence_index=reverse?(4-n%4)%4:n%4;
    case(sequence_index)0:ab=2'b00;1:ab=2'b01;2:ab=2'b11;3:ab=2'b10;endcase
    {a[channel],b[channel]}=ab;
   end
  end
 endtask
 task automatic exercise(input integer period_ns,input integer reverse,input integer phase_offset);
  begin
   @(negedge clk);#2;rst_n=0;a=0;b=0;z=0;
   repeat(6)@(negedge clk);#2;rst_n=1;
   repeat(6)@(negedge clk);#2;
   fork
    drive(0,period_ns,reverse,phase_offset);
    drive(1,period_ns,reverse,phase_offset+2);
    drive(2,period_ns,reverse,phase_offset+4);
    drive(3,period_ns,reverse,phase_offset+6);
   join
   repeat(8)@(negedge clk);#2;
   failures=0;
   for(j=0;j<4;j=j+1)begin
    if(count[j]!=(reverse?-1000:1000)||invalid[j])failures=failures+1;
    checks=checks+1;
   end
   if(period_ns>=20&&failures!=0)$fatal(1,"Ideal sampled encoder failed at or below one edge/corecycle");
   if(period_ns<20&&failures!=4)$fatal(1,"Overspeed sweep did not expose all four expected count/transition failures");
   // Known-stationary index capture. Simultaneous-edge index timing is a
   // separate integration test and must not be inferred from this check.
   z=4'hf;repeat(8)@(negedge clk);#2;
   for(j=0;j<4;j=j+1)begin
    if(!index_seen[j]||index_count[j]!=count[j])$fatal(1,"Stationary index snapshot mismatch");
    checks=checks+1;
   end
   $display("RESULT period_ns=%0d reverse=%0d phase_offset_ns=%0d commanded_edges_per_channel=1000 failed_channels=%0d count0=%0d invalid_mask=%0d",period_ns,reverse,phase_offset,failures,count[0],invalid);
   rows=rows+1;
  end
 endtask
 initial begin
  edge_ns[0]=80;edge_ns[1]=40;edge_ns[2]=25;edge_ns[3]=21;edge_ns[4]=20;edge_ns[5]=19;edge_ns[6]=18;edge_ns[7]=15;edge_ns[8]=10;
  for(k=0;k<9;k=k+1)for(rev=0;rev<2;rev=rev+1)for(phase_case=0;phase_case<4;phase_case=phase_case+1)exercise(edge_ns[k],rev,1+phase_case*4);
  @(negedge clk);#2;rst_n=0;a=0;b=0;z=0;
  repeat(8)@(negedge clk);#2;rst_n=1;
  repeat(8)@(negedge clk);#2;a=4'hf;b=4'hf;
  repeat(8)@(negedge clk);#2;
  if(invalid!=4'hf)$fatal(1,"Illegal two-bit transition was not latched");
  for(j=0;j<4;j=j+1)if(count[j]!=0)$fatal(1,"Illegal transition invented position");
  $display("PASS encoder4 rows=%0d checks=%0d illegal_transition_channels=4 assumed_clock_hz=50000000",rows,checks);
  $finish;
 end
endmodule
