`timescale 1ns/1ps
module equivalence_tb;
 reg clk=0,rst_n=0,clear=0,provider_ready=1;
 reg[31:0]ticks=0,fault_word=0;reg[287:0]step_counts=0;
 reg[95:0]encoder_counts=0,index_counts=0;reg[3:0]index_pulse=0,index_request=0;
 reg[1:0]probe_raw=0,probe_request=0;reg[431:0]page=0;
 reg arm_commit=0,cmd_snapshot=0,cmd_complete=0,ack_commit=0;reg[7:0]ack=0;
 wire[159:0]golden_head,new_head;wire[7:0]golden_status,new_status,golden_probe,new_probe;
 wire[3:0]golden_armed,new_armed;wire golden_overflow,new_overflow;
 integer cycle,checks=0,cooldown=16,j;
 golden_events golden_dut(.clk(clk),.rst_n(rst_n),.clear(clear),.provider_ready(provider_ready),
 .ticks(ticks),.fault_word(fault_word),.safety_word(32'h12345678),.armed_mask(12'hfff),.pos_continuity(12'ha55),
 .step_counts(step_counts),.encoder_counts(encoder_counts),.index_counts(index_counts),.index_pulse(index_pulse),
 .probe_raw(probe_raw),.io_page1(page),.arm_commit(arm_commit),.index_request(index_request),.probe_request(probe_request),
 .cmd_snapshot(cmd_snapshot),.cmd_complete(cmd_complete),.ack_commit(ack_commit),.ack(ack),
 .event_head(golden_head),.event_status(golden_status),.index_armed(golden_armed),.probe_status(golden_probe),.overflow(golden_overflow));
cnc3_runtime_events new_dut(.clk(clk),.rst_n(rst_n),.clear(clear),.provider_ready(provider_ready),
 .ticks(ticks),.fault_word(fault_word),.safety_word(32'h12345678),.armed_mask(12'hfff),.pos_continuity(12'ha55),
 .step_counts(step_counts),.encoder_counts(encoder_counts),.index_counts(index_counts),.index_pulse(index_pulse),
 .probe_raw(probe_raw),.io_page1(page),.arm_commit(arm_commit),.index_request(index_request),.probe_request(probe_request),
 .cmd_snapshot(cmd_snapshot),.cmd_complete(cmd_complete),.ack_commit(ack_commit),.ack(ack),
 .event_head(new_head),.event_status(new_status),.index_armed(new_armed),.probe_status(new_probe),.overflow(new_overflow));
 task tick;begin #5;clk=1;#5;clk=0;ticks=ticks+1;end endtask
 initial begin
  page[431-1*8 -:8]=1;page[431-7*8 -:8]=1;
  for(j=0;j<4;j=j+1)begin page[431-(3+j)*8 -:8]=j;page[431-(9+j)*8 -:8]=16+j;end
  tick;rst_n=1;
  for(cycle=0;cycle<160000;cycle=cycle+1)begin
   clear=(cycle%40003)==2001;
   arm_commit=(cycle%8192==0 || cycle%8192==4096);
   index_request=(cycle%8192<4096)?15:0;probe_request=(cycle%8192<4096)?3:0;
   index_pulse=(cycle%8192==4)?15:0;
   probe_raw=(cycle%8192>=2 && cycle%8192<4096)?3:0;
   if(cycle%40003>=100 && cycle%40003<700)fault_word=(cycle&1)?32'h55aa:32'haa55;
   else fault_word=(cycle%31==8)?32'h00080000:0;
   step_counts=step_counts+288'h0102030405060708090a0b0c0d0e0f;encoder_counts=encoder_counts+96'h010203040506;index_counts=index_counts+96'h040302010001;
   cmd_snapshot=(cycle%17==0);cmd_complete=(cycle%17==1);ack_commit=(cycle%17==2);
   if(cmd_snapshot)ack=golden_head[159:152];
   if(clear || arm_commit)cooldown=12;else if(cooldown>0)cooldown=cooldown-1;
   tick;
   if(golden_status!==new_status || golden_probe!==new_probe || golden_armed!==new_armed || golden_overflow!==new_overflow)
    $fatal(1,"status differs cycle=%0d golden=%h actual=%h",cycle,golden_status,new_status);
   if(cooldown==0 && golden_head!==new_head)
    $fatal(1,"record differs cycle=%0d golden=%h actual=%h",cycle,golden_head,new_head);
   checks=checks+1;
  end
  $display("SERIALIZED_EQUIVALENCE_PASS cycles=%0d exact_status_and_record_checks=%0d",cycle,checks);$finish;
 end
endmodule
