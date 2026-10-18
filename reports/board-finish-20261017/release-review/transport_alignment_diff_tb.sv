`timescale 1ns/1ps
module transport_alignment_diff_tb;
 reg clk=0,rst_n=1,spi_cs_fb_n=1,spi_cs_cmd_n=1,spi_sclk=0,spi_mosi=0,rate_frame_good=0;
 reg[1391:0]feedback_payload=0;reg[751:0]status_payload=0;
 wire om,nm,oe,ne,ofb,nfb,ov,nv,ob,nb,oc,nc,oss,nss,osf,nsf,orv,nrv,orf,nrf,org,nrg,owv,nwv;
 wire[1407:0]oframe,nframe;wire[47:0]oh,nh;wire[3:0]owc,nwc;wire[31:0]ow,nw;
`define INPUTS .clk(clk),.rst_n(rst_n),.spi_cs_fb_n(spi_cs_fb_n),.spi_cs_cmd_n(spi_cs_cmd_n),.spi_sclk(spi_sclk),.spi_mosi(spi_mosi),.feedback_payload(feedback_payload),.status_payload(status_payload),.rate_frame_good(rate_frame_good)
`define OUTPUTS(P) .spi_miso(P``m),.spi_miso_oe(P``e),.frame(P``frame),.frame_cs_fb(P``fb),.frame_valid(P``v),.frame_bad(P``b),.embedded_crc_good(P``c),.snapshot_start(P``ss),.snapshot_cs_fb(P``sf),.rejection_header_valid(P``rv),.rejection_header(P``h),.rejection_header_cs_fb(P``rf),.frame_rates_good(P``rg),.rx_rate_word_valid(P``wv),.rx_rate_channel(P``wc),.rx_rate_word(P``w)
 cnc3_spi_transport_stateful_original old(`INPUTS,`OUTPUTS(o));
 cnc3_spi_transport_stateful_candidate dut(`INPUTS,`OUTPUTS(n));
 wire[1407:0]normalized_old_rx=old.selected_fb?old.rx_shift:{old.rx_shift[767:0],640'd0};
 integer cycles=0,transactions=0,valid_frames=0,bad_pulses=0,reject_headers=0,snapshots=0,rate_words=0;
 integer cmd_valid=0,fb_valid=0,trial=0,bit_index=0,i,j,k,n,valid_before,bad_before,word_before;
 reg[31:0]rng=32'h4a8fc731;
 reg[1407:0]bits=0,expected_frame=0;
 reg check_valid_frame=0,check_rate_words=0,expected_fb=0,expected_inner=0;
 reg[15:0]crc16_work;reg[31:0]crc32_work;
 task compare;
 begin
  if({om,oe,oframe,ofb,ov,ob,oc,oss,osf,orv,oh,orf,org,owv,owc,ow} !==
     {nm,ne,nframe,nfb,nv,nb,nc,nss,nsf,nrv,nh,nrf,nrg,nwv,nwc,nw} ||
     {old.fb_sync,old.cmd_sync,old.sck_sync,old.mosi_sync,old.active,old.selected_fb,old.invalid,old.rise_d,old.bit_count,old.expected_bits,old.body_bits,old.rx_header,old.tx_shift,old.rx_crc,old.tx_crc,old.inner_crc,old.ticks,old.start_tick,old.last_rise_tick,old.last_fall_tick,old.last_end_tick,old.seen_rise,old.seen_fall} !==
     {dut.fb_sync,dut.cmd_sync,dut.sck_sync,dut.mosi_sync,dut.active,dut.selected_fb,dut.invalid,dut.rise_d,dut.bit_count,dut.expected_bits,dut.body_bits,dut.rx_header,dut.tx_shift,dut.rx_crc,dut.tx_crc,dut.inner_crc,dut.ticks,dut.start_tick,dut.last_rise_tick,dut.last_fall_tick,dut.last_end_tick,dut.seen_rise,dut.seen_fall} ||
     normalized_old_rx !== dut.rx_shift)begin
   $display("TRANSPORT_DIFF_FAIL cycle=%0d transaction=%0d trial=%0d bit=%0d CS=%b%b SCK=%b MOSI=%b active=%b selected=%b count=%0d CRC=%h oldvalid=%b newvalid=%b",cycles,transactions,trial,bit_index,spi_cs_fb_n,spi_cs_cmd_n,spi_sclk,spi_mosi,old.active,old.selected_fb,old.bit_count,old.rx_crc,ov,nv);
   $fatal(1,"transport output/state or normalized RX differs");
  end
 end endtask
 task core;
 begin
  #1;compare;clk=1;#1;cycles=cycles+1;compare;
  if(ov)begin
   valid_frames=valid_frames+1;if(ofb)fb_valid=fb_valid+1;else cmd_valid=cmd_valid+1;
   if(check_valid_frame && (oframe!==expected_frame || ofb!==expected_fb || oc!==expected_inner || org!==(!expected_fb&&rate_frame_good)))$fatal(1,"valid frame oracle differs");
  end
  if(ob)bad_pulses=bad_pulses+1;
  if(orv)reject_headers=reject_headers+1;
  if(oss)snapshots=snapshots+1;
  if(owv)begin
   if(check_rate_words && (owc!==(rate_words-word_before) || ow!==expected_frame[1407-128-32*(rate_words-word_before) -:32]))$fatal(1,"streamed CMD rate-word oracle differs channel=%0d",owc);
   rate_words=rate_words+1;
  end
  clk=0;#1;compare;
 end endtask
 task wait_core;input integer clocks;integer q;begin for(q=0;q<clocks;q=q+1)core;end endtask
 task reset;
 begin
  check_valid_frame=0;check_rate_words=0;spi_cs_fb_n=1;spi_cs_cmd_n=1;spi_sclk=0;spi_mosi=0;
  rst_n=0;wait_core(4);rst_n=1;wait_core(24);
 end endtask
 function[31:0]random_word;
 input[31:0]value;
 begin random_word=value*32'd1664525+32'd1013904223;end
 endfunction
 function[15:0]crc16_bit;
 input[15:0]value;input bitvalue;
 reg[15:0]shifted;
 begin shifted={value[14:0],1'b0};crc16_bit=(value[15]^bitvalue)?shifted^16'h1021:shifted;end
 endfunction
 function[31:0]crc32_byte;
 input[31:0]value;input[7:0]bytevalue;reg[31:0]c;integer q;
 begin c=value^{24'd0,bytevalue};for(q=0;q<8;q=q+1)c=(c>>1)^((c[0])?32'h82f63b78:0);crc32_byte=c;end
 endfunction
 task make_frame;
 input fb;input inner_good;integer q,body;
 begin
  for(q=0;q<44;q=q+1)begin rng=random_word(rng);bits[1407-32*q -:32]=rng;end
  for(q=0;q<1392;q=q+1)feedback_payload[q]=bits[q];
  for(q=0;q<752;q=q+1)status_payload[q]=bits[1407-q];
  body=fb?1392:752;
  if(fb)begin
   crc32_work=32'hffffffff;
   for(q=17;q<=52;q=q+1)crc32_work=crc32_byte(crc32_work,bits[1407-8*q -:8]);
   bits[983:952]=~crc32_work;if(!inner_good)bits[952]=~bits[952];
  end else bits[639:0]=0;
  crc16_work=16'hffff;
  for(q=0;q<body;q=q+1)crc16_work=crc16_bit(crc16_work,bits[1407-q]);
  bits[1407-body -:16]=crc16_work;
 end endtask
 // Actual mode-0 wire traffic, including independent CS overlap/reset faults.
 task transfer;
 input fb;input integer number_bits,low_clocks,high_clocks,overlap_at,reset_at;
 integer q;reg sampled_bit;
 begin
  transactions=transactions+1;spi_sclk=0;
  if(fb)spi_cs_fb_n=0;else spi_cs_cmd_n=0;
  wait_core(20);
  for(q=0;q<number_bits;q=q+1)begin
   bit_index=q;sampled_bit=(q<(fb?1408:768))?bits[1407-q]:rng[0];spi_mosi=sampled_bit;
   if(q==overlap_at)begin if(fb)spi_cs_cmd_n=0;else spi_cs_fb_n=0;end
   if(q==overlap_at+4 && overlap_at>=0)begin if(fb)spi_cs_cmd_n=1;else spi_cs_fb_n=1;end
   if(q==reset_at)begin rst_n=0;wait_core(3);rst_n=1;end
   wait_core(low_clocks);spi_sclk=1;wait_core(high_clocks);spi_sclk=0;
   // These external payloads may change while the preserved snapshot shifts.
   if(q%31==0)begin rng=random_word(rng);feedback_payload[31:0]=rng;status_payload[31:0]=~rng;end
  end
  wait_core(20);spi_cs_fb_n=1;spi_cs_cmd_n=1;wait_core(24);
 end endtask
 task valid_transfer;
 input fb;input inner_good;
 begin
  make_frame(fb,inner_good);expected_frame=bits;expected_fb=fb;expected_inner=fb&&inner_good;
  check_valid_frame=1;check_rate_words=!fb;rate_frame_good=rng[0];valid_before=valid_frames;word_before=rate_words;
  transfer(fb,fb?1408:768,8,8,-1,-1);
  if(valid_frames!=valid_before+1)$fatal(1,"valid physical SPI frame did not complete");
  if(!fb && rate_words!=word_before+12)$fatal(1,"valid CMD did not emit twelve rate words");
  check_valid_frame=0;check_rate_words=0;
 end endtask
 initial begin
  reset;
  for(trial=0;trial<16;trial=trial+1)begin valid_transfer(0,0);valid_transfer(1,trial[0]);end
  // Malformed outer CRC and each truncation/header boundary, both frame types.
  for(i=0;i<2;i=i+1)begin
   make_frame(i[0],1);bits[i?0:640]=~bits[i?0:640];valid_before=valid_frames;bad_before=bad_pulses;
   transfer(i[0],i?1408:768,8,8,-1,-1);
   if(valid_frames!=valid_before || bad_pulses==bad_before)$fatal(1,"bad outer CRC was accepted");
   for(j=0;j<14;j=j+1)begin
    case(j)0:n=0;1:n=1;2:n=7;3:n=47;4:n=48;5:n=49;6:n=127;7:n=128;8:n=159;9:n=511;10:n=752;11:n=767;12:n=i?1407:769;13:n=i?1409:770;endcase
    make_frame(i[0],1);valid_before=valid_frames;bad_before=bad_pulses;
    transfer(i[0],n,8,8,-1,-1);
    if(valid_frames!=valid_before || bad_pulses==bad_before)$fatal(1,"truncated/overlong frame accepted n=%0d FB=%0d",n,i);
   end
  end
  // CS overlap, timing violations, and reset at different receive positions.
  for(trial=0;trial<24;trial=trial+1)begin
   reset;make_frame(trial[0],1);
   case(trial%4)
    0:transfer(trial[0],trial[0]?1408:768,8,8,trial*13,-1);
    1:transfer(trial[0],trial[0]?1408:768,1,1,-1,-1);
    2:transfer(trial[0],trial[0]?1408:768,8,8,-1,trial*17);
    3:begin spi_sclk=1;wait_core(20);if(trial[0])spi_cs_fb_n=0;else spi_cs_cmd_n=0;wait_core(20);spi_sclk=0;wait_core(10);spi_cs_fb_n=1;spi_cs_cmd_n=1;wait_core(24);end
   endcase
  end
  // Arbitrary binary wire transitions, inactive clocks, both-CS states and
  // asynchronous sub-clock reset pulses; no protocol-validity assumption.
  reset;
  for(trial=0;trial<180000;trial=trial+1)begin
   rng=random_word(rng);spi_cs_fb_n=rng[3];spi_cs_cmd_n=rng[7];spi_sclk=rng[11];spi_mosi=rng[15];rate_frame_good=rng[19];
   feedback_payload[63:32]=rng;status_payload[63:32]=~rng;
   if(trial%997==0)begin rst_n=0;#1;compare;rst_n=1;end
   core;
  end
  // Unknown wire samples are differential RTL tests, not metastability proof.
  reset;
  for(trial=0;trial<3000;trial=trial+1)begin
   rng=random_word(rng);spi_cs_fb_n=rng[3];spi_cs_cmd_n=rng[7];spi_sclk=rng[11];spi_mosi=rng[15];
   if(trial%37==0)spi_cs_fb_n=1'bx;if(trial%41==0)spi_cs_cmd_n=1'bz;
   if(trial%43==0)spi_sclk=1'bx;if(trial%47==0)spi_mosi=1'bz;
   if(trial%211==0)begin rst_n=0;core;rst_n=1;end
   core;
  end
  $display("TRANSPORT_ALIGNMENT_DIFF_PASS cycles=%0d transactions=%0d valid_CMD=%0d valid_FB=%0d bad_pulses=%0d rejected_headers=%0d snapshots=%0d rate_words=%0d binary_fuzz=180000 four_state_fuzz=3000",cycles,transactions,cmd_valid,fb_valid,bad_pulses,reject_headers,snapshots,rate_words);$finish;
 end
endmodule
