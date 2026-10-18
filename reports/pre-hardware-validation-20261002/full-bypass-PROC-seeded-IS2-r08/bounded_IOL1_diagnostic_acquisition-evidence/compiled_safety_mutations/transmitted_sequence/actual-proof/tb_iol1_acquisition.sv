`timescale 1ns/1ps
module tb_iol1_acquisition;
 reg clk=0;always #10 clk=~clk;
 reg reset_n=0,enable=1;
 wire[3:0]cs,sclk,mosi,miso,fault,accepted,valid,seen,active,factory;
 wire[511:0]samples,integrity;
 wire[63:0]ages,sequences,analog_codes;
 wire[11:0]states;
 wire[23:0]filtered,raw;
 wire[15:0]applied;
 wire[3:0]ai_valid;
 reg[4:0]inject[0:3];reg[3:0]request_crc_corruption=0;wire[31:0]bad[0:3],commands[0:3];
 cnc_iol1_diagnostic_acquisition dut(.clk(clk),.reset_n(reset_n),.enable(enable),.miso(miso),.cs_n(cs),.sclk(sclk),.mosi(mosi),.fault_latched(fault),.accepted(accepted),.diagnostic_sample_valid(valid),.diagnostic_transport_seen(seen),.commercial_active(active),.factory_identity_verified(factory),.last_valid_realtime(samples),.last_integrity_realtime(integrity),.sample_age_us(ages),.last_reply_sequence(sequences),.last_reply_state(states),.diagnostic_filtered_di(filtered),.diagnostic_raw_di(raw),.diagnostic_do_applied(applied),.analog_valid(ai_valid),.analog_codes(analog_codes));
 genvar g;generate for(g=0;g<4;g=g+1)begin: peers
  wire physical_mosi=mosi[g]^(request_crc_corruption[g]&&peer.bits==319);
  iol1_target_c_peer #(.CLASS_ID(g==0?8'h11:g==3?8'h31:8'h21),.SLOT(g)) peer(.reset_n(reset_n),.cs_n(cs[g]),.sclk(sclk[g]),.mosi(physical_mosi),.injected_error(inject[g]),.miso(miso[g]),.bad_commands(bad[g]),.command_count(commands[g]));
 end endgenerate
 integer checks=0,i,k,prev_age,base_commands;reg[511:0]saved;
 task ck(input bit c,input string label);begin checks++;if(!c)$fatal(1,"FAIL %s",label);$display("PASS %s",label);end endtask
 task observations;begin
  // These bytes are explicit disconnected fixtures, not converter execution.
  $iol1_observation_fixture(0,128'h563412214365000a0000000000000000,1,0);
  $iol1_observation_fixture(1,128'h00112233445566000014000000000000,1,0);
  $iol1_observation_fixture(2,128'h0077665544332200001e000000000000,1,0);
  $iol1_observation_fixture(3,128'h000000000000000000000000ffff0003,1,0);
 end endtask
 task fresh;begin reset_n=0;request_crc_corruption=0;#100;reset_n=1;for(i=0;i<4;i++)inject[i]=0;observations();#600000;end endtask
 task reply_event(input integer lane);begin @(posedge accepted[lane]);@(negedge clk);@(negedge clk);end endtask
 initial begin
  for(i=0;i<4;i++)inject[i]=0;
  #100;ck(valid==0&&seen==0&&ages==64'hffffffffffffffff&&samples==0,"cold unavailable/default off");
  reset_n=1;observations();#600000;
  ck(valid==7&&seen==15&&fault==0,"four actual C cached replies; three fresh diagnostic samples and held-reset ACC");
  ck(filtered==24'h123456&&raw==24'h654321,"actual received little-endian 24DI decoded without command oracle");
  ck(applied==0&&samples[375:368]==8'h11&&samples[247:240]==8'h77,"actual two distinct DO diagnostic payloads retained; no commanded outputs");
  ck(active==0&&factory==0&&ai_valid==0&&analog_codes==0,"SYNCED/transport binding never factory ACTIVE or invented ADC validity");
  ck(states==12'h249,"all four current actual targets remain SYNCED");
  reply_event(0);ck(ages[15:0]>=110&&ages[15:0]<=112,"DI age includes measured previous-release reply residency and quantization");
  for(i=0;i<4;i++)ck(bad[i]==0&&commands[i]>3,"independent physical CRC/zero authority/header commands");
  // Last good sample survives two CRC failures; age grows rather than resets.
  inject[0]=1;saved=samples;prev_age=ages[15:0];base_commands=commands[0];
  wait(commands[0]==base_commands+2);#100;
  ck(!fault[0]&&valid[0]&&samples==saved&&ages[15:0]>prev_age+180,"up to two rejected replies preserve actual last sample with growing age");
  inject[0]=0;reply_event(0);ck(valid[0]&&!fault[0]&&ages[15:0]<=112,"next real accepted packet refreshes sample after two rejects");
  fresh();@(negedge cs[0]);base_commands=commands[0];request_crc_corruption[0]=1;
  wait(commands[0]==base_commands+1);#100;
  ck(peers[0].peer.result==0&&bad[0]>0,"physically corrupted request CRC cannot refresh actual target acceptance");
  request_crc_corruption[0]=0;#400000;
  ck(fault[0]&&!valid[0],"lost accepted-command sequence cannot fake recovery or accepted progress; new epoch required");
  fresh();@(posedge cs[0]);repeat(4)@(negedge clk);
  ck(dut.lane[0].master.state==0,"wrap fixture starts only after complete prior physical poll and bookkeeping");
  dut.lane[0].master.tx_sequence=16'hffff;dut.lane[0].master.expected_sequence=16'hfffe;
  $iol1_reachable_sequence_fixture(0,65534);
  reply_event(0);ck(sequences[15:0]==16'hfffe,"actual prior-command reply at reachable sequence wrap boundary");
  reply_event(0);ck(sequences[15:0]==16'hffff&&valid[0],"actual sealed FFFF reply and command1 accepted by unchanged C");
  reply_event(0);ck(sequences[15:0]==1&&valid[0]&&!fault[0],"IOL1 FFFF-to1 skipzero wrap remains distinct from CNC3 nonwrap");
  inject[0]=1;base_commands=commands[0];wait(commands[0]==base_commands+3);#100;
  ck(fault[0]&&!valid[0]&&!seen[0],"third failed poll latches unavailable and stops source progress");
  base_commands=commands[0];inject[0]=0;#300000;ck(fault[0]&&commands[0]==base_commands,"no automatic epoch restart after recovery");
  // Trusted unhealthy/unavailable reply invalidates immediately.
  for(k=6;k<=19;k++)begin
   fresh();inject[1]=k;base_commands=commands[1];wait(commands[1]==base_commands+1);#100;
   if(k==6||k==7||k==8||k==11||k==12||k==13||k==18||k==19)
     ck(!valid[1],"authenticated unhealthy/stale/reset-state reply invalidates immediately");
   #300000;ck(fault[1]&&!valid[1],"CRC/slot/epoch/sequence/policy/floating rejection fail closed");
  end
  fresh();inject[0]=17;#400000;ck(fault[0]&&!valid[0],"unsupported response hardware-major nibble cannot alias expected current diagnostic major0");
  for(k=12;k<=16;k++)begin fresh();inject[3]=k;#400000;ck(fault[3]&&ai_valid==0&&!valid[3],"ACC clamp/reset/readback discrepancy never becomes valid analog");end
  // Even valid CRC/header cannot hide in-flight age accumulated since preparing.
  fresh();$iol1_observation_fixture(0,128'h563412214365015e0000000000000000,1,0);
  #300000;ck(!valid[0]&&!fault[0]&&ages[15:0]>440,"raw age350 passes transport but true sample450 is stale");
  fresh();$iol1_observation_fixture(0,128'h56341221436500f00000000000000000,1,0);
  #300000;inject[0]=1;wait(ages[15:0]==440);#1;ck(valid[0],"sample is fresh at exact configured440us boundary");
  wait(ages[15:0]==441);#1;ck(!valid[0]&&!fault[0],"staleness invalidates before a third bad packet");
  fresh();enable=0;#100;ck(valid==0&&seen==0&&cs==15,"disable invalidates all read-only observations");
  enable=1;#200000;ck(fault==15&&valid==0,"enable recovery cannot reuse interrupted synchronized epochs");
  reset_n=0;#1;ck(valid==0&&seen==0&&active==0&&factory==0&&ages==64'hffffffffffffffff,"reset immediately clears provenance and valid flags");
  $display("PASS acquisition checks=%0d; actual unchanged target C protocol, cached previous-release replies, explicit disconnected observation fixtures",checks);$finish;
 end
 initial begin #40000000;$fatal(1,"deadline");end
endmodule
