`timescale 1ns/1ps
module tb_timer_equivalence;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,enable=0,stop=0;reg signed[31:0] rate=0;
 reg[15:0] pulse_ticks=100,space_ticks=100,setup_ticks=100,hold_ticks=100;
 wire old_step,old_dir,old_fault,old_quiet,new_step,new_dir,new_fault,new_quiet;
 wire signed[31:0] old_count,new_count;
 cnc3_stepgen_runtime_reference original(.clk(clk),.rst_n(rst_n),.enable(enable),.stop(stop),.rate(rate),.pulse_ticks(pulse_ticks),.space_ticks(space_ticks),.setup_ticks(setup_ticks),.hold_ticks(hold_ticks),.step(old_step),.dir(old_dir),.count(old_count),.timing_fault(old_fault),.quiescent(old_quiet));
 cnc3_stepgen_runtime optimized(.clk(clk),.rst_n(rst_n),.enable(enable),.stop(stop),.rate(rate),.pulse_ticks(pulse_ticks),.space_ticks(space_ticks),.setup_ticks(setup_ticks),.hold_ticks(hold_ticks),.step(new_step),.dir(new_dir),.count(new_count),.timing_fault(new_fault),.quiescent(new_quiet));
 reg[31:0] rng=32'h19728a51;integer cycles=0,edges=0,profile,k;reg previous_step=0;
 function[31:0] random_next(input[31:0] x);reg[31:0] y;begin y=x^(x<<13);y=y^(y>>17);random_next=y^(y<<5);end endfunction
 always @(posedge clk)begin #1;
  if({new_step,new_dir,new_fault,new_quiet,new_count,optimized.phase,optimized.high_left,optimized.low_left,optimized.setup_left,optimized.hold_left}!=={old_step,old_dir,old_fault,old_quiet,old_count,original.phase,original.high_left,original.low_left,original.setup_left,original.hold_left})
    $fatal(1,"cycle%0d profile%0d timing counter/output/phase mismatch",cycles,profile);
  if(new_step&&!previous_step)edges++;previous_step=new_step;cycles++;
 end
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  for(profile=0;profile<12;profile++)begin
   for(k=0;k<100000;k++)begin
    @(negedge clk);rng=random_next(rng);
    if(k%997==0)begin
     case(profile)
      0:begin pulse_ticks=100;space_ticks=100;setup_ticks=100;hold_ticks=100;end
      1:begin pulse_ticks=100;space_ticks=1023;setup_ticks=1023;hold_ticks=100;end
      2:begin pulse_ticks=1023;space_ticks=100;setup_ticks=100;hold_ticks=1023;end
      3:begin pulse_ticks=1;space_ticks=1;setup_ticks=1;hold_ticks=1;end
      4:begin pulse_ticks=0;space_ticks=0;setup_ticks=0;hold_ticks=0;end
      5:begin pulse_ticks=65535;space_ticks=65535;setup_ticks=65535;hold_ticks=65535;end
      default:begin pulse_ticks=rng[15:0];space_ticks=rng[31:16];setup_ticks=rng[7:0];hold_ticks=rng[23:8];end
     endcase
    end
    if(k%101==0)begin
     case(rng[2:0])
      0:rate=0;1:rate=32'h01000000;2:rate=-32'sh01000000;
      3:rate=32'h80000000;4:rate=32'h7fffffff;default:rate=rng;
     endcase
    end
    if(k%43==0)stop=rng[3];
    if(k%191==0)enable=rng[9];
    if(k%50000==49999)begin rst_n=0;@(negedge clk);rst_n=1;end
   end
  end
  $display("PASS exact timer sharing cycles=%0d edges=%0d profiles=12",cycles,edges);$finish;
 end
endmodule
