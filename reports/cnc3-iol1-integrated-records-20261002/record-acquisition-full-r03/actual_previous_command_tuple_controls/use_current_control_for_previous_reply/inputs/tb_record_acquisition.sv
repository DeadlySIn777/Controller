`timescale 1ns/1ps
module tb_record_acquisition;
 reg clk=0;always #10 clk=~clk;
 reg reset_n=0,enable=0;wire[3:0] cs,sclk,mosi,miso,accepted,fault,valid,seen;
 reg[4:0] injected[0:3];reg[3:0] corrupt_request=0;
 wire[31:0] commands[0:3],bad[0:3];
 wire[3:0] records,record_failed,chunks;wire[23:0] indices;wire[255:0] data;
 wire[511:0] serials,samples,integrity;wire[383:0] uids;wire[127:0] generations;
 wire[63:0] ages,sequences,codes;wire[11:0] states;wire[3:0] active,factory,ai_valid;
 wire[23:0] filtered,raw;wire[15:0] outputs;wire config_ok,authenticated;wire[31:0] config_crc;
 cnc_iol1_record_acquisition dut(.clk(clk),.reset_n(reset_n),.enable(enable),.miso(miso),
 .cs_n(cs),.sclk(sclk),.mosi(mosi),.fault_latched(fault),.accepted(accepted),
 .diagnostic_sample_valid(valid),.diagnostic_transport_seen(seen),.commercial_active(active),
 .factory_identity_verified(factory),.last_valid_realtime(samples),.last_integrity_realtime(integrity),
 .sample_age_us(ages),.last_reply_sequence(sequences),.last_reply_state(states),
 .diagnostic_filtered_di(filtered),.diagnostic_raw_di(raw),.diagnostic_do_applied(outputs),
 .analog_valid(ai_valid),.analog_codes(codes),.record_integrity_observed(records),.record_failed(record_failed),
 .observed_board_serial(serials),.observed_mcu_uid(uids),.observed_generation(generations),
 .chunk_accepted(chunks),.chunk_index(indices),.chunk_data(data),
 .dic_configuration_echo_valid(config_ok),.dic_configuration_crc(config_crc),.signature_authenticated(authenticated));
 genvar g;generate for(g=0;g<4;g++)begin: peers
  iol1_target_c_peer #(.CLASS_ID(g==0?8'h11:g==3?8'h31:8'h21),.SLOT(g)) peer(
  .reset_n(reset_n),.cs_n(cs[g]),.sclk(sclk[g]),.mosi(mosi[g]^corrupt_request[g]),
  .injected_error(injected[g]),.miso(miso[g]),.bad_commands(bad[g]),.command_count(commands[g]));
 end endgenerate
 integer checks=0,actual_bytes=0,i,k,selected,match_result,base_commands;
 integer received[0:3];reg check_bytes=0;
 task ck(input bit c,input string label);begin checks++;if(!c)$fatal(1,"FAIL %s",label);$display("PASS %s",label);end endtask
 task observations;begin
  $iol1_observation_fixture(0,128'h563412214365000a0000000000000000,1,0);
  $iol1_observation_fixture(1,128'h00112233445566000014000000000000,1,0);
  $iol1_observation_fixture(2,128'h0077665544332200001e000000000000,1,0);
  $iol1_observation_fixture(3,128'h000000000000000000000000ffff0003,1,0);
 end endtask
 task fresh;begin
  check_bytes=0;enable=0;reset_n=0;corrupt_request=0;
  for(i=0;i<4;i++)begin injected[i]=0;received[i]=0;end
  #100;reset_n=1;observations();
  for(i=0;i<4;i++)begin $iol1_record_fixture(i,selected);ck(selected==1,"actual C selected UID-bound developer record");end
  #100;enable=1;
 end endtask
 always @(negedge clk)if(reset_n&&check_bytes)for(integer n=0;n<4;n++)if(chunks[n])begin
  ck(indices[n*6+:6]==received[n],"wire IDENT chunks arrive in exact order");
  $iol1_actual_chunk_check(n,indices[n*6+:6],data[n*64+:64],match_result);
  ck(match_result==1,"all eight received bytes equal actual C-selected record");received[n]++;actual_bytes+=8;
 end
 always @(negedge clk)if(reset_n)begin
  if(active!=0||factory!=0||authenticated||ai_valid!=0||codes!=0||outputs!=0)$fatal(1,"authority or unavailable analog became valid");
 end
 initial begin
  for(i=0;i<4;i++)begin injected[i]=0;received[i]=0;end
  #100;ck(records==0&&valid==0&&active==0&&factory==0&&!authenticated,"cold unavailable identity and authority");
  fresh();check_bytes=1;wait(records==15);#100;
  ck(record_failed==0&&fault==0&&valid==7&&seen==15,"all four records observed and read-only samples valid");
  ck(config_ok&&config_crc==32'he4528507,"DIC actual applied configuration CRC echo");
  ck(actual_bytes==2048,"all 2048 bytes traversed physical simulated SPI into exact C");
  for(i=0;i<4;i++)begin
   ck(received[i]==64&&bad[i]==0&&commands[i]>=67,"64 real IDENT commands plus no authority image");
   ck(serials[i*128+:128]==128'h444556454c4f504d454e542d4f4e4c59&&generations[i*32+:32]==1,"actual board serial/generation diagnostics");
   for(k=0;k<12;k++)ck(uids[i*96+95-k*8-:8]==i*16+k,"actual UID bytes observed without authenticity grant");
  end
  #300000;ck(records==15&&config_ok&&fault==0,"POLL after record completion preserves read-only diagnostics");
  @(posedge cs[0]);repeat(4)@(negedge clk);
  dut.lane[0].master.tx_sequence=16'hffff;dut.lane[0].master.expected_sequence=16'hfffe;
  $iol1_reachable_sequence_fixture(0,65534);
  @(posedge accepted[0]);repeat(2)@(negedge clk);ck(sequences[15:0]==16'hfffe,"new control tuple preserves actual prior-sequence wrap boundary");
  @(posedge accepted[0]);repeat(2)@(negedge clk);ck(sequences[15:0]==16'hffff,"actual cached FFFF response remains intact");
  @(posedge accepted[0]);repeat(2)@(negedge clk);ck(sequences[15:0]==1&&!fault[0]&&records[0],"sequence wraps to1 without reusing record/control tuple");
  check_bytes=0;enable=0;#100;ck(records==0&&valid==0&&!config_ok,"disable invalidates record/sample/config observations");
  enable=1;#200000;ck(fault==15&&records==0,"no automatic epoch restart after interrupt");
  // A valid IOL1 CRC does not make corrupted record bytes valid.
  fresh();injected[1]=20;#7000000;ck(record_failed[1]&&!records[1]&&!fault[1],"resealed corrupted record content fails shared CRC/shape");
  fresh();wait(chunks[0]&&indices[5:0]==8);injected[0]=1;base_commands=commands[0];
  wait(commands[0]==base_commands+1);#100;injected[0]=0;#7000000;
  ck(record_failed[0]&&!records[0]&&!fault[0],"lost response chunk cannot complete or reuse prior CRC");
  fresh();injected[2]=21;#700000;ck(fault[2]&&!records[2],"wrong IDENT chunk metadata rejects without progress");
  fresh();injected[2]=22;#700000;ck(fault[2]&&!records[2],"wrong IDENT page rejects without progress");
  fresh();injected[0]=23;#7000000;ck(!config_ok&&!valid[0]&&records[0],"wrong actual CONFIG echo never qualifies DI sample");
  fresh();wait(chunks[0]);repeat(10)@(negedge clk);reset_n=0;#1;
  ck(records==0&&valid==0&&record_failed==0&&!config_ok,"reset during shared CRC clears all pending integrity and config");
  fresh();wait(chunks[0]&&indices[5:0]==3);@(negedge cs[0]);corrupt_request[0]=1;
  #200000;corrupt_request[0]=0;#500000;
  ck(fault[0]&&!records[0]&&!valid[0],"actual C-rejected corrupted request loses sequence and fails closed");
  fresh();#400000;injected[1]=17;#700000;ck(fault[1]&&!records[1],"major profile mismatch cannot become implicit trust");
  $display("PASS record acquisition checks=%0d actual_bytes=%0d",checks,actual_bytes);$finish;
 end
 initial begin #80000000;$fatal(1,"deadline");end
endmodule
