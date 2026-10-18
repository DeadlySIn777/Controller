`timescale 1ns/1ps
module tb_stream_checker;
 reg clk=0;always #10 clk=~clk;
 reg reset_n=0,enable=1;reg[3:0] fault=0,accepted=0;reg[23:0] index=0;reg[255:0] data=0;
 wire[3:0] valid,failed;wire[511:0] serials;wire[383:0] uids;wire[127:0] generation;wire signature,factory,active;
 cnc_mbr2_stream_checker dut(.clk(clk),.reset_n(reset_n),.enable(enable),.lane_fault(fault),
 .chunk_accepted(accepted),.chunk_index(index),.chunk_data(data),.record_integrity_observed(valid),.record_failed(failed),
 .observed_board_serial(serials),.observed_mcu_uid(uids),.observed_generation(generation),
 .signature_authenticated(signature),.factory_identity_verified(factory),.commercial_active(active));
 reg[63:0] vectors[0:5119];integer checks=0,c,s,k;
 task ck(input bit b,input string label);begin checks++;if(!b)$fatal(1,"FAIL %s case%0d",label,c);end endtask
 task fresh;begin @(negedge clk);reset_n=0;accepted=0;enable=1;fault=0;repeat(3)@(negedge clk);reset_n=1;end endtask
 task send(input integer chunk,input integer scenario);begin
  @(negedge clk);for(s=0;s<4;s++)begin index[s*6+:6]=chunk;data[s*64+:64]=vectors[scenario*256+s*64+chunk];end
  accepted=15;@(negedge clk);accepted=0;repeat(300)@(negedge clk);
 end endtask
 always @(negedge clk)if(reset_n&&(signature||factory||active))$fatal(1,"record CRC granted trust/authority");
 initial begin
  $readmemh("vectors.hex",vectors);#50;
  for(c=0;c<20;c++)begin
   fresh();for(k=0;k<64;k++)send(k,c);
   if(c==0||c==19)ck(valid==15&&failed==0,"well-formed integrity observed; signature still unverified");
   else ck(valid==14&&failed==1,"malformed record rejected; other three independent contexts valid");
  end
  c=20;fresh();for(k=0;k<63;k++)send(k,0);
  @(negedge clk);for(s=0;s<4;s++)begin index[s*6+:6]=63;data[s*64+:64]=vectors[s*64+63];end
  accepted=15;@(negedge clk);accepted=1;@(posedge clk);#1;
  ck(failed[0]&&!valid[0],"final chunk pending collision rejects success in the exact same cycle");
  @(negedge clk);accepted=0;repeat(400)@(negedge clk);ck(valid==14&&failed==1,"collision poisons only affected lane and cannot pulse integrity");
  fresh();send(0,0);send(2,0);ck(failed==15&&valid==0,"missing chunk poisons every affected context");
  fresh();send(0,0);send(0,0);ck(failed==15&&valid==0,"repeated chunk cannot reuse prior CRC");
  fresh();@(negedge clk);accepted=15;repeat(2)@(negedge clk);accepted=0;
  repeat(5)@(negedge clk);accepted=15;@(negedge clk);accepted=0;repeat(400)@(negedge clk);
  ck(failed==15&&valid==0,"shared queue overflow cannot overwrite accepted identity");
  fresh();send(0,0);@(negedge clk);index=24'h041041;accepted=15;@(negedge clk);accepted=0;repeat(5)@(negedge clk);
  fault=15;repeat(400)@(negedge clk);ck(valid==0&&failed==15,"fault while shared CRC busy cannot revalidate");
  fresh();send(0,0);@(negedge clk);accepted=15;repeat(5)@(negedge clk);reset_n=0;#1;
  ck(valid==0&&failed==0&&serials==0&&uids==0&&generation==0,"reset clears pending contexts and diagnostic lineage");
  fresh();for(k=0;k<64;k++)send(k,0);ck(valid==15,"baseline after explicit reset");enable=0;repeat(4)@(negedge clk);
  ck(valid==0&&failed==15,"disable invalidates previously completed record");enable=1;repeat(400)@(negedge clk);ck(valid==0&&failed==15,"re-enable cannot recover without reset");
  $display("PASS stream checker checks=%0d cases=20",checks);$finish;
 end
 initial begin #50000000;$fatal(1,"deadline");end
endmodule
