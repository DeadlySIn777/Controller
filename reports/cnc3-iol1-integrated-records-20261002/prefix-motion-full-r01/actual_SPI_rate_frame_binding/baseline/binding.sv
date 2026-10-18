`timescale 1ns/1ps
module tb;
localparam[1407:0] cfg=1408'h434e433303060000000000000000000002010fff0fff000000fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00fa0000000003e80004000f00000000000000000000000000000000000000000000000000000000000000000000000000000000000000007da2;
localparam[1407:0] sync=1408'h434e4333030100001122334400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e8070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] testm=1408'h434e4333030d0000112233440000000101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000055ce0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] testo=1408'h434e4333030d000011223344000000020200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009e390000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] clear=1408'h434e4333030e0fff1122334400000003000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000f3790000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] arm=1408'h434e433303020fff11223344000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002ed40000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] update=1408'h434e433303030fff112233440000000500800000ff80000000800000ff80000000800000ff80000000800000ff80000000800000ff80000000800000ff80000000000000000000000000000000000000000000000000000000000000000027870000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] disarm=1408'h434e433303040000112233440000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000057900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] arm2=1408'h434e433303020fff112233440000000700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000050aa0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] zero=1408'h434e433303030fff1122334400000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000d2ba0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] nop=1408'h434e433303000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000022220000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
localparam[1407:0] read=1408'h434e433303100000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004479;
localparam[1407:0] unsupported_page=1408'h434e433303050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001724;
reg clk=0;always #10 clk=~clk;
reg rst=0,fb=1,cmd=1,sck=0,mosi=0;wire miso,oe;
reg wm=1,wo=1,inhibit=1;reg[3:0] opi=0;wire[3:0] rearm;
reg[3:0] ea=0,eb=0,ez=0;wire[11:0] steps,dirs,en_n,am,cont;
wire mreq,oreq,permit,pm,po,consume,cfgv,accepted;wire[31:0] session,seq,fault;
wire[1:0] tests;wire[2:0] teststate;wire[7:0] rejected;
wire[1391:0] actualfb;wire[751:0] actualstatus;
wire[3:0] gates={4{mreq&&inhibit}};
cnc3_motion_spi dut(.clk(clk),.rst_n(rst),.spi_cs_fb_n(fb),.spi_cs_cmd_n(cmd),.spi_sclk(sck),.spi_mosi(mosi),.spi_miso(miso),.spi_miso_oe(oe),.qualification_complete(1'b1),.installed_input(12'hfff),.installed_module_class(8'd1),.inhibit_n(inhibit),.wd_m_ok(wm),.wd_o_ok(wo),.reset_arm_ready(1'b1),.reset_arm_held(1'b0),.contactor_deenergized(1'b1),.sto_arm_expected(1'b1),.motion_critical_ports_valid(1'b1),.gate_high(gates),.opi_ok(opi),.alarm_current_raw(12'd0),.encoder_a(ea),.encoder_b(eb),.encoder_z(ez),.encoder_installed(4'hf),.encoder_port_valid(4'hf),.external_fault_word(32'd0),.motion_critical_io_fault(1'b0),.provider_feedback(1392'd0),.provider_status(752'd0),.physical_safety_power_word(32'd0),.step_out(steps),.dir_out(dirs),.enable_n(en_n),.motion_request(mreq),.output_request(oreq),.permit_out_req(permit),.progress_m(pm),.progress_o(po),.opi_rearm(rearm),.reset_arm_consumed(consume),.session(session),.last_sequence(seq),.fault_word(fault),.armed_mask(am),.pos_continuity(cont),.config_valid(cfgv),.selftest_passed(tests),.selftest_state(teststate),.accepted_pulse(accepted),.last_reject(rejected),.actual_feedback_payload(actualfb),.actual_status_payload(actualstatus));
// Explicit ideal physical gate/OPI test fixture. These are ports in production.
always@(posedge clk)if(!mreq||!inhibit)opi<=0;else opi<=opi|rearm;
integer checks=0,file,j,core_cycles=0,progress_start=0,progress_pulses=0;reg[1407:0] reply;reg oldprogress=0;
always@(posedge clk)begin
#1;core_cycles=core_cycles+1;
if(pm&&!oldprogress)progress_start=core_cycles;
if(!pm&&oldprogress)begin
if(rst && core_cycles-progress_start!=50)$fatal(1,"actual accepted motion progress is not50ticks");
progress_pulses=progress_pulses+1;
end
oldprogress=pm;
end
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
task check(input bit good,input string message);begin checks=checks+1;if(!good)$fatal(1,"%s seq%0d fault%h",message,seq,fault);end endtask
task transaction(input string name,input bit usefb,input[1407:0] data);
integer i,bits;begin
bits=usefb?1408:768;ticks(12);if(usefb)fb=0;else cmd=0;#160;reply=0;
for(i=0;i<bits;i=i+1)begin mosi=data[1407-i];#80;sck=1;reply={reply[1406:0],miso};#80;sck=0;end
#160;fb=1;cmd=1;ticks(12);$fdisplay(file,"%s %0d %h",name,bits/8,reply);
check(!oe,"MISO released after actual transaction");
end endtask
task watchdog(input bit outputtest);begin
transaction(outputtest?"testO":"testM",0,outputtest?testo:testm);
check(teststate==(outputtest?3:1),"actual SPI starts selected selftest");
ticks(500000);check(en_n==12'hfff && steps==0 && dirs==0 && permit==0 && pm==0 && po==0,"actual SPI selftest field containment");
check(outputtest?!tests[1]:!tests[0],"SPI no instant selftest pass");
if(outputtest)wo=0;else wm=0;ticks(5);check(teststate==(outputtest?4:2),"actual SPI observed external fall");
ticks(100);if(outputtest)wo=1;else wm=1;ticks(5);check(teststate==0,"SPI recovery observed");
end endtask

reg[1407:0] workframe,active_data;
reg[31:0] hostsession=32'h22000000,value;
integer actual_accepts=0,valid_frames=0,stream_words=0,base_accepts,base_valid,cases=0,selected,n;
bit check_stream=0,stream_fb=0,last_rate_good=0;
reg[1407:0] captured_frame;
always@(posedge clk)begin #1;if(rst)begin
 if(accepted)actual_accepts=actual_accepts+1;
 if(dut.frame_valid)begin
  valid_frames=valid_frames+1;captured_frame=dut.frame;last_rate_good=dut.frame_rates_good;
 end
 if(check_stream&&dut.rx_rate_word_valid)begin
  if(stream_fb||dut.rx_rate_channel!=stream_words||dut.rx_rate_word!==active_data[1279-32*stream_words -:32])$fatal(1,"SPI admission word/channel not actual current physical frame");
  stream_words=stream_words+1;
 end
end end
function[1407:0] reseal(input[1407:0] raw,input bit usefb);
reg[15:0] crc;reg[1407:0] copy;integer b,body;begin
crc=16'hffff;body=usefb?1392:752;
for(b=0;b<body;b=b+1)begin if(crc[15]^raw[1407-b])crc={crc[14:0],1'b0}^16'h1021;else crc={crc[14:0],1'b0};end
copy=raw;if(usefb)copy[15:0]=crc;else copy[655:640]=crc;reseal=copy;end endfunction
task wire_frame(input bit usefb,input[1407:0] data,input integer bits,input bit expected_transport_valid,input bit expected_rate_good);
integer b,before_valid;begin
ticks(12);active_data=data;stream_fb=usefb;stream_words=0;check_stream=1;before_valid=valid_frames;
if(usefb)fb=0;else cmd=0;#160;
check(!dut.frame_rates_good&&!dut.rate_frame_good&&dut.rate_channel_good==0&&!dut.rate_busy,"physical new CS clears previous admission transaction");
for(b=0;b<bits;b=b+1)begin mosi=b<1408?data[1407-b]:0;#80;sck=1;#80;sck=0;end
#160;fb=1;cmd=1;ticks(12);check_stream=0;
check(!oe,"actual MISO released after arbitrary frame");
check(valid_frames==before_valid+expected_transport_valid,"exact transport validity bound to current frame");
if(expected_transport_valid)begin
if(last_rate_good!=expected_rate_good)$display("BINDING_DIAGNOSTIC op%h input_rate0%h expected%h actual%h engine_mask%h busy%h poison%h channels%0d cases%0d",data[1367:1360],data[1279 -:32],expected_rate_good,last_rate_good,dut.rate_channel_good,dut.rate_busy,dut.rate_poisoned,dut.admission.expected_channel,cases);
check(captured_frame==(usefb?data:{data[1407:640],640'd0}),"completed metadata references exact current frame bytes");
check(last_rate_good==expected_rate_good,"rate admission latched only on current CRC valid release");
end else check(!dut.frame_rates_good,"rejected physical transaction cannot retain prior admitted flag");
check(stream_words==(usefb?0:(bits>=512?12:(bits>128?(bits-128)/32:0))),"actual physical current-frame twelve-word capture count");
end endtask
task begin_case;
begin hostsession=hostsession+1;workframe=sync;workframe[1343 -:32]=hostsession;
wire_frame(0,reseal(workframe,0),768,1,1);check(fault==0&&session==hostsession,"real new session clears recoverable fault");
workframe=arm;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=1;
wire_frame(0,reseal(workframe,0),768,1,1);check(am==12'hfff&&seq==1&&en_n==0,"real measured-proof ARM before rate case");
end endtask
task make_update(input[31:0] v,input integer ch);
begin workframe=update;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=2;workframe[1279 -:384]=0;
if(ch==12)for(n=0;n<12;n=n+1)workframe[1279-32*n -:32]=n%2?-v:v;
else workframe[1279-32*ch -:32]=v;
workframe=reseal(workframe,0);end endtask
task rate_case(input[31:0] v,input integer ch,input bit allowed);
begin begin_case();make_update(v,ch);base_accepts=actual_accepts;
wire_frame(0,workframe,768,1,allowed);cases=cases+1;
if(allowed)begin
check(actual_accepts==base_accepts+1&&seq==2&&am==12'hfff&&fault==0&&dut.rates==workframe[1279 -:384],"good actual frame atomically commits exact12 rates once");
workframe=disarm;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=3;
wire_frame(0,reseal(workframe,0),768,1,1);ticks(2400);check(am==0&&!mreq&&fault==0,"actual timed clean stop after good rate");
end else begin
check(actual_accepts==base_accepts&&seq==1&&am==0&&dut.rates==0&&!pm&&fault[0],"invalid actual streamed rate cannot commit sequence progress or rates");
check(en_n==12'hfff&&!permit,"rejected rate never receives physical output authority");end
end endtask
task abort_case(input integer bits,input bit usefb,input bit corruptcrc);
begin begin_case();make_update(32'h00800000,12);base_accepts=actual_accepts;base_valid=valid_frames;
if(corruptcrc)workframe=workframe^(1408'd1<<640);
// A sealed96-byte command followed by80 zero bytes has a zero full-length
// CRC remainder on CS_FB: transport accepts those bytes, the real static
// validator rejects the wrong-CS opcode. Neither event admits its rate tuple.
wire_frame(usefb,workframe,bits,usefb&&bits==1408&&!corruptcrc,0);
check(actual_accepts==base_accepts&&seq==1&&am==0&&dut.rates==0&&!pm&&fault[0],"abort CRC wrongCS cannot borrow prior rate authorization");
end endtask
initial begin
file=$fopen("responses.txt","w");ticks(5);rst=1;ticks(2200);
workframe=cfg;
for(n=0;n<12;n=n+1)begin
workframe[1215-64*n -:16]=100;workframe[1199-64*n -:16]=100;
workframe[1183-64*n -:16]=100;workframe[1167-64*n -:16]=100;
end
transaction("configure",1,reseal(workframe,1));
check(dut.high=={12{16'd100}}&&dut.low=={12{16'd100}},"actual configured100tick profile matches independent boundary test");
transaction("sync",0,sync);watchdog(0);watchdog(1);check(tests==3,"both real watchdog observations retained");
// Each physical word position is exercised at both signs/global boundaries.
for(selected=0;selected<12;selected=selected+1)begin
rate_case(32'h01000000,selected,1);rate_case(-32'h01000000,selected,1);
rate_case(32'h01000001,selected,0);rate_case(-32'h01000001,selected,0);
rate_case(32'h80000000,selected,0);
end
rate_case(32'h00800000,12,1);abort_case(96,0,0);rate_case(0,12,1);
abort_case(175,0,0);abort_case(511,0,0);abort_case(512,0,0);abort_case(768,0,1);abort_case(1408,1,0);abort_case(769,0,0);
rate_case(32'h00800000,12,1);
// Real CONFIGURE changes actual timing, then endpoint rejects floor+1.
workframe=cfg;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=4;
for(n=0;n<12;n=n+1)begin workframe[1215-64*n -:16]=1023;workframe[1199-64*n -:16]=1023;end
wire_frame(1,reseal(workframe,1),1408,1,0);check(cfgv&&session==0,"real timing configuration commits and resets session");
rate_case(2098176,12,1);rate_case(-2098176,0,1);rate_case(2098177,0,0);rate_case(-2098177,11,0);
// Reset destroys both a previously good transaction and an in-flight one.
begin_case();make_update(0,12);wire_frame(0,workframe,768,1,1);
rst=0;ticks(2);check(!dut.frame_rates_good&&!dut.rate_frame_good&&dut.rate_channel_good==0&&seq==0&&am==0,"reset destroys prior completed frame metadata and motion state");
rst=1;ticks(2200);ticks(12);cmd=0;#160;check(!dut.frame_rates_good,"new physicalCS reset state safe");
for(n=0;n<170;n=n+1)begin mosi=workframe[1407-n];#80;sck=1;#80;sck=0;end
rst=0;ticks(2);check(!dut.frame_rates_good&&!dut.rate_frame_good&&dut.rate_channel_good==0,"reset mid current word destroys pending admission");cmd=1;sck=0;rst=1;ticks(20);
$fclose(file);$display("SPI_ADMISSION_BINDING_PASS checks=%0d actual_rate_cases=%0d actual_accepts=%0d actual_frame_releases=%0d",checks,cases,actual_accepts,valid_frames);$finish;
end
endmodule
