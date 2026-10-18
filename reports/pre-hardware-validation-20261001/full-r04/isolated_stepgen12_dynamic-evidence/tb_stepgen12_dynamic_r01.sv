`timescale 1ns/1ps
// Twelve real generators with 1ms command changes at an assumed 50MHz.
// No CNC3 endpoint, LinuxCNC plant, physical drive or vendor timing is modeled.
module tb_stepgen12_dynamic;
 parameter integer HIGH=12, LOW=12, SETUP=12, HOLD=12;
 reg clk=0; always #10 clk=!clk;
 reg rst_n=0,enable=0;
 reg signed [31:0] rates[0:11];
 wire [11:0] step,dir,fault;
 wire signed [31:0] count[0:11];
 genvar g;
 generate for(g=0;g<12;g=g+1)begin:channels
  cnc_stepgen #(.PULSE_CYCLES(HIGH),.SPACE_CYCLES(LOW),.DIR_SETUP_CYCLES(SETUP),.DIR_HOLD_CYCLES(HOLD)) dut(
   .clk(clk),.rst_n(rst_n),.enable(enable),.rate(rates[g]),.step(step[g]),.dir(dir[g]),.count(count[g]),.timing_fault(fault[g]));
 end endgenerate
 integer tick=0,checks=0,j,k,i;
 integer last_rise[0:11],last_fall[0:11],last_dir[0:11];
 integer signed_edges[0:11],total_rises[0:11],dir_changes[0:11];
 reg [11:0] previous_step=0,previous_dir=0;
 reg [63:0] safe_word,scaled;
 reg [31:0] random_state=32'h5eed1234;
 always @(posedge clk)begin
  #1;tick=tick+1;
  if(!rst_n)begin
   previous_step=step;previous_dir=dir;
   for(j=0;j<12;j=j+1)begin
    signed_edges[j]=0;total_rises[j]=0;dir_changes[j]=0;
    last_rise[j]=-1000000;last_fall[j]=-1000000;last_dir[j]=-1000000;
   end
  end else begin
   for(j=0;j<12;j=j+1)begin
    if(!enable)begin
     if(step[j]||dir[j])$fatal(1,"Disabled outputs active");
     // Deliberate inhibition is allowed to truncate STEP. This fixture does
     // not claim an outer endpoint restart policy or machine stopping bound.
     last_rise[j]=-1000000;last_fall[j]=-1000000;last_dir[j]=tick;
    end else begin
     if(fault[j])$fatal(1,"Unexpected timing fault below profile limit");
     if(dir[j]!=previous_dir[j])begin
      if(step[j]||tick-last_rise[j]<HOLD)$fatal(1,"DIR hold or STEP stability violated");
      last_dir[j]=tick;dir_changes[j]=dir_changes[j]+1;
     end
     if(step[j]&&!previous_step[j])begin
      if(tick-last_fall[j]<LOW)$fatal(1,"STEP low violated");
      if(tick-last_dir[j]<SETUP)$fatal(1,"DIR setup violated");
      signed_edges[j]=signed_edges[j]+(dir[j]?-1:1);
      total_rises[j]=total_rises[j]+1;last_rise[j]=tick;
     end
     if(!step[j]&&previous_step[j])begin
      if(tick-last_rise[j]<HIGH)$fatal(1,"STEP high violated");
      last_fall[j]=tick;
     end
    end
    if(count[j]!=signed_edges[j])$fatal(1,"Dynamic actual pulse/count mismatch");
    checks=checks+1;
   end
   previous_step=step;previous_dir=dir;
  end
 end
 initial begin
  for(i=0;i<12;i=i+1)rates[i]=0;
  safe_word=64'h100000000/(HIGH+LOW+1);
  repeat(4)@(negedge clk);#2;rst_n=1;
  repeat(4)@(negedge clk);#2;enable=1;
  for(k=0;k<24;k=k+1)begin
   for(i=0;i<12;i=i+1)begin
    random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
    scaled=safe_word*(25+random_state%51)/100;
    // Independent rates, opposing gantry-like signs and repeated reversals.
    rates[i]=((k+i)%4<2)?$signed(scaled[31:0]):-$signed(scaled[31:0]);
    if(k==7||k==15)rates[i]=0;
   end
   repeat(50000)@(negedge clk);#2;
  end
  enable=0;repeat(5)@(negedge clk);#2;
  for(i=0;i<12;i=i+1)begin
   if(total_rises[i]<100||dir_changes[i]<5)$fatal(1,"Dynamic channel inactive or reversals missing");
   $display("CHANNEL %0d pulses=%0d reversals=%0d signed_count=%0d",i,total_rises[i],dir_changes[i],signed_edges[i]);
  end
  $display("PASS dynamic12 checks=%0d updates=24 assumed_clock_hz=50000000 command_period_cycles=50000 high=%0d low=%0d",checks,HIGH,LOW);
  $finish;
 end
endmodule
