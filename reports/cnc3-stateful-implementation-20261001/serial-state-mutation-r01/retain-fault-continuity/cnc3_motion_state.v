`timescale 1ns/1ps
// Report-local bounded CNC3 motion-authority candidate. The input frame is a
// complete CRC/static-validated frozen 96/176-byte frame, not arbitrary bytes.
// General I/O is deliberately disabled until its actual IOL1/config/epoch
// implementation exists. Physical qualification and safety inputs are providers.
module cnc3_motion_state (
 input wire clk,input wire rst_n,
 input wire request_valid,input wire [1407:0] request_frame,
 input wire reject_pulse,input wire rejected_configure,input wire request_rates_valid,
 input wire qualification_complete,input wire [11:0] installed_input,
 input wire [7:0] installed_module_class,
 input wire inhibit_n,input wire wd_m_ok,input wire wd_o_ok,
 input wire reset_arm_ready,input wire reset_arm_held,
 input wire contactor_deenergized,input wire sto_arm_expected,
 input wire motion_critical_ports_valid,
 input wire [11:0] encoder_valid_mask,input wire [11:0] encoder_installed_mask,
 input wire [7:0] encoder_expansion_class,
 input wire [11:0] alarm_levels,input wire [11:0] timing_faults,
 input wire [31:0] external_fault_word,input wire motion_critical_io_fault,
 // Physical final gate and sticky OPI readbacks: TX,A,B,BOE in bits0..3.
 input wire [3:0] gate_high,input wire [3:0] opi_ok,
 input wire [11:0] generator_quiescent,
 output wire request_ready,
 output reg [31:0] session,output reg [31:0] last_sequence,
 output reg [31:0] ticks,output reg [31:0] fault_word,
 output reg [11:0] installed_mask,output reg [11:0] required_mask,
 output reg [11:0] armed_mask,output reg [11:0] pos_continuity,
 output reg [11:0] step_timing_latched,output reg [11:0] alarm_trip_latched,
 output reg config_valid,output reg [7:0] config_generation,
 output reg [31:0] config_hash,output reg [15:0] config_crc,
 output reg [15:0] servo_period_us,
 output reg [11:0] required_encoder_mask,output reg [3:0] encoder_filter_ticks,
 output reg [7:0] mpg_config,
 output reg [191:0] pulse_ticks,space_ticks,setup_ticks,hold_ticks,
 output reg [383:0] rates,
 output wire [11:0] generator_enable,output wire generator_stop,
 output wire motion_request,output wire output_request,output wire permit_out_req,
 output wire progress_m,output wire progress_o,
 output reg [3:0] opi_rearm,output reg reset_arm_consumed,
 output reg [1:0] selftest_passed,output reg [2:0] selftest_state,
 output reg accepted_pulse,output reg sync_clear,output reg [7:0] last_reject,
 output reg [15:0] last_update_interval_us,output reg [15:0] late_update_count,
 output wire motion_effective,output wire [7:0] state_bits,
 output wire io_enabled
);
 localparam [31:0] F_LINK=32'h00000001,F_WATCHDOG=32'h00000002,
  F_INHIBIT=32'h00000004,F_TIMING=32'h00000008,F_ALARM=32'h00000010,
  F_CHANGED=32'h00000020,F_INVALID=32'h00000040,F_CONFIG=32'h00000080,
  F_OPI=32'h00000200,F_STUCK=32'h00000400,
  F_SELFTEST=32'h00000800,F_ENCODER=32'h00080000,F_ARM=32'h08000000;
 localparam [31:0] POWER_CYCLE=F_CHANGED|F_INVALID;
 localparam [17:0] WATCHDOG_TICKS=18'd250000;
 localparam [19:0] TEST_MIN_TICKS=20'd453000,TEST_MAX_TICKS=20'd668500;
 localparam [9:0] OPI_DROP_TICKS=10'd500;
 // ARM response settling is a bounded engineering candidate, NOT a frozen
 // physical timing guarantee. DISARM's 500-tick fall bound is normative.
 localparam [9:0] ARM_SETTLE_TICKS=10'd500;
 // I/O-only bits14..18,22/23 and a noncritical slot/link fault do not cut motion.
 localparam [31:0] MOTION_EXTERNAL=32'h0e38127f;
 reg [31:0] cycle_faults;
 reg [11:0] alarm_trip_mask,alarm_on_no_current;
 reg [7:0] expected_module_class;
 reg qualification_latched;
 reg [7:0] qualification_class;
 reg arming,arming_rearmed,stopping,disarm_proof;
 reg [9:0] arming_age,disarm_age;
 reg [3:0] proof_domains;
 reg [17:0] watchdog_age;
 reg [19:0] test_age;
 reg [5:0] progress_left;
 reg [31:0] last_update_tick;
 reg [15:0] update_us_age;
 reg [5:0] update_subtick;
 wire [7:0] op=request_frame[1367:1360];
 wire [11:0] mask=request_frame[1355:1344];
 wire [31:0] rx_session=request_frame[1343:1312];
 wire [31:0] rx_seq=request_frame[1311:1280];
 wire next_sequence=(session!=0 && rx_session==session && last_sequence!=32'hffffffff && rx_seq==last_sequence+1'b1 && rx_seq!=0);
 wire readonly_session=rx_session==0 || rx_session==session;
 wire [3:0] active_domains=(|armed_mask[11:8])?4'b1111:4'b0011;
 wire [11:0] asserted_alarm=(alarm_levels^alarm_on_no_current)&alarm_trip_mask;
 wire [11:0] cmd_required=request_frame[1259 -: 12];
 wire [7:0] cmd_class=request_frame[1271 -: 8];
 wire [11:0] cmd_enc_required=request_frame[379 -: 12];
 wire [7:0] cmd_enc_class=request_frame[399 -: 8];
 wire cfg_session=(session==0)?(rx_session==0 && rx_seq==0):next_sequence;
 wire idle=(armed_mask==0 && !arming && !stopping && !disarm_proof && selftest_state==0);
 wire qualification_changed=qualification_latched &&
  (!qualification_complete || installed_input!=installed_mask || installed_module_class!=qualification_class);
 wire cfg_semantic=qualification_latched && qualification_complete && !qualification_changed && ((fault_word|external_fault_word)&POWER_CYCLE)==0 &&
  cmd_required!=0 && (cmd_required&~installed_mask)==0 &&
  (cmd_class==0 || (cmd_class==1 && qualification_class==1 && |installed_mask[11:8])) &&
  ((cmd_required&12'hf00)==0 || cmd_class==1) &&
  (cmd_enc_required&~encoder_installed_mask)==0 &&
  (cmd_enc_class==0 || (cmd_enc_class==1 && encoder_expansion_class==1)) &&
  ((cmd_enc_required&12'hff0)==0 || cmd_enc_class==1);
 wire clean_disarm_accept=request_valid && op==8'h04 && next_sequence;
 wire [31:0] update_interval_ticks=ticks-last_update_tick;
 // Capture this cycle's complete50-tick interval without a large combinational
 // divider. This is telemetry only; watchdog and late threshold use exact ticks.
 wire [15:0] update_interval_us=(update_subtick==49 && update_us_age!=65535)?update_us_age+16'd1:update_us_age;
 wire motion_runtime_fault=!inhibit_n || !wd_m_ok || !motion_critical_ports_valid ||
  ((external_fault_word&MOTION_EXTERNAL)!=0) || motion_critical_io_fault ||
  ((required_encoder_mask&~encoder_valid_mask)!=0) || (|timing_faults) ||
  ((asserted_alarm&armed_mask)!=0) ||
  (!arming && ((opi_ok&active_domains)!=active_domains));
 // Real serial admission is bound to this completed CRC-checked frame by the
 // transport. It enforces global MAX and actual high+low+1 before acceptance.
 wire update_admissible=next_sequence && armed_mask!=0 && !stopping &&
  !motion_runtime_fault && !qualification_changed && fault_word==0 &&
  mask==armed_mask && request_frame[895 -:240]==0 && request_rates_valid;
 assign request_ready=1'b1;
 assign io_enabled=1'b0; // No pretend IOL1/output-session authority in this scope.
 assign progress_m=progress_left!=0;
 assign progress_o=1'b0;
 assign motion_request=(armed_mask!=0) || selftest_state==1;
 assign output_request=selftest_state==3;
 assign permit_out_req=armed_mask!=0;
 assign motion_effective=(armed_mask!=0 && !arming && !motion_runtime_fault);
 assign generator_enable=motion_effective?armed_mask:12'd0;
 // Combinational acceptance term prevents a new STEP on the DISARM commit edge.
 assign generator_stop=stopping || clean_disarm_accept;
 assign state_bits={4'b0000,config_valid,qualification_latched,(qualification_latched && fault_word==0),motion_effective};
 integer i;
 task fault_cut;
  input [31:0] bits;
  begin
   cycle_faults=cycle_faults|bits;
   pos_continuity<=pos_continuity;
   armed_mask<=0;rates<=0;arming<=0;stopping<=0;progress_left<=0;
   disarm_proof<=0;
  end
 endtask
 task config_reject;
  begin
   config_valid<=0;required_mask<=0;alarm_trip_mask<=0;alarm_on_no_current<=0;
   fault_cut(F_LINK|F_CONFIG);last_reject<=8'h86;
  end
 endtask
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n)begin
   session<=0;last_sequence<=0;ticks<=0;fault_word<=0;
   installed_mask<=0;required_mask<=0;armed_mask<=0;pos_continuity<=0;
   step_timing_latched<=0;alarm_trip_latched<=0;config_valid<=0;
   config_generation<=0;config_hash<=0;config_crc<=0;servo_period_us<=1000;
   required_encoder_mask<=0;encoder_filter_ticks<=0;mpg_config<=0;
   alarm_trip_mask<=0;alarm_on_no_current<=0;expected_module_class<=0;
   qualification_latched<=0;qualification_class<=0;
   arming<=0;arming_rearmed<=0;stopping<=0;disarm_proof<=0;
   arming_age<=0;disarm_age<=0;proof_domains<=0;watchdog_age<=0;
   test_age<=0;progress_left<=0;last_update_tick<=0;update_us_age<=0;update_subtick<=0;
   rates<=0;opi_rearm<=0;reset_arm_consumed<=0;
   selftest_passed<=0;selftest_state<=0;accepted_pulse<=0;last_reject<=0;
   last_update_interval_us<=0;late_update_count<=0;sync_clear<=0;cycle_faults=0;
   for(i=0;i<12;i=i+1)begin
    pulse_ticks[191-16*i -:16]<=100;space_ticks[191-16*i -:16]<=100;
    setup_ticks[191-16*i -:16]<=100;hold_ticks[191-16*i -:16]<=100;
   end
  end else begin
   cycle_faults=0;
   ticks<=ticks+1'b1;accepted_pulse<=0;sync_clear<=0;opi_rearm<=0;reset_arm_consumed<=0;
   if(progress_left!=0)progress_left<=progress_left-1'b1;
   if(armed_mask!=0)begin
    watchdog_age<=watchdog_age+1'b1;
    if(update_subtick==49)begin update_subtick<=0;if(update_us_age!=65535)update_us_age<=update_us_age+1'b1;end
    else update_subtick<=update_subtick+1'b1;
   end
   if(!qualification_latched && qualification_complete && (fault_word&POWER_CYCLE)==0)begin
    if(installed_input==12'h0ff || installed_input==12'hfff)begin
     installed_mask<=installed_input;qualification_class<=installed_module_class;
     qualification_latched<=1;selftest_passed<=0;
    end else begin installed_mask<=0;fault_cut(F_INVALID);end
   end
   // Real observed WDO fall, then explicit recovery wait. Never instant flags.
   if(selftest_state==1 || selftest_state==3)begin
    test_age<=test_age+1'b1;
    if((selftest_state==1 && !wd_m_ok)||(selftest_state==3 && !wd_o_ok))begin
     if(test_age+20'd1>=TEST_MIN_TICKS && test_age+20'd1<=TEST_MAX_TICKS)begin
      if(selftest_state==1)begin selftest_passed[0]<=1;selftest_state<=2;end
      else begin selftest_passed[1]<=1;selftest_state<=4;end
     end else begin selftest_state<=0;selftest_passed<=0;fault_cut(F_SELFTEST);end
    end else if(test_age+20'd1>=TEST_MAX_TICKS)begin
     selftest_state<=0;selftest_passed<=0;fault_cut(F_SELFTEST);
    end
   end
   if(selftest_state==2 && wd_m_ok)selftest_state<=0;
   if(selftest_state==4 && wd_o_ok)selftest_state<=0;
   if(arming)begin
    arming_age<=arming_age+1'b1;
    if(!arming_rearmed && (gate_high&active_domains)==active_domains)begin
     opi_rearm<=active_domains;arming_rearmed<=1;
    end
    if(arming_rearmed && (opi_ok&active_domains)==active_domains)arming<=0;
    else if(arming_age>=ARM_SETTLE_TICKS-10'd1)fault_cut(F_STUCK);
   end
   if(stopping && (generator_quiescent&armed_mask)==armed_mask)begin
    proof_domains<=active_domains;disarm_proof<=1;disarm_age<=0;
    armed_mask<=0;rates<=0;stopping<=0;
   end
   if(disarm_proof)begin
    disarm_age<=disarm_age+1'b1;
    if((opi_ok&proof_domains)==0)disarm_proof<=0;
    else if(disarm_age>=OPI_DROP_TICKS-10'd1)begin disarm_proof<=0;fault_cut(F_STUCK);end
   end
   if(request_valid && cycle_faults==0)begin
    case(op)
    8'h00,8'h10:begin
     if(readonly_session)accepted_pulse<=1;
     else begin fault_cut(F_LINK);last_reject<=8'h81;end
    end
    8'h01:begin
     if(idle && qualification_latched && qualification_complete && !qualification_changed && inhibit_n && ((fault_word|external_fault_word)&POWER_CYCLE)==0 && rx_session!=0 && rx_session!=session)begin
      session<=rx_session;last_sequence<=0;step_timing_latched<=0;alarm_trip_latched<=0;
      fault_word<=config_valid?32'd0:F_CONFIG;late_update_count<=0;last_reject<=0;accepted_pulse<=1;sync_clear<=1;
     end else begin fault_cut(F_LINK);last_reject<=8'h81;end
    end
    8'h06:begin
     if(idle && cfg_session && cfg_semantic)begin
      required_mask<=cmd_required;alarm_trip_mask<=request_frame[1243 -:12];
      alarm_on_no_current<=request_frame[1227 -:12];expected_module_class<=cmd_class;
      for(i=0;i<12;i=i+1)begin
       pulse_ticks[191-16*i -:16]<=request_frame[1215-64*i -:16];
       space_ticks[191-16*i -:16]<=request_frame[1199-64*i -:16];
       setup_ticks[191-16*i -:16]<=request_frame[1183-64*i -:16];
       hold_ticks[191-16*i -:16]<=request_frame[1167-64*i -:16];
      end
      config_hash<=request_frame[447 -:32];servo_period_us<=request_frame[415 -:16];
      required_encoder_mask<=cmd_enc_required;encoder_filter_ticks<=request_frame[387 -:4];
      mpg_config<=request_frame[367 -:8];config_crc<=request_frame[15:0];
      config_generation<=(config_generation==255)?8'd1:config_generation+1'b1;
      config_valid<=1;session<=0;last_sequence<=0;accepted_pulse<=1;
     end else config_reject();
    end
    8'h02:begin
     if(next_sequence && idle && fault_word==0 && config_valid && mask==required_mask &&
       (mask&~installed_mask)==0 && mask!=0 && inhibit_n && qualification_complete &&
       selftest_passed==2'b11 && wd_m_ok && wd_o_ok && reset_arm_ready && !reset_arm_held &&
       contactor_deenergized && sto_arm_expected && motion_critical_ports_valid && external_fault_word==0 && !motion_critical_io_fault &&
       (required_encoder_mask&~encoder_valid_mask)==0 && (asserted_alarm&mask)==0 &&
       ((mask&12'hf00)==0 || expected_module_class==qualification_class))begin
      last_sequence<=rx_seq;armed_mask<=mask;rates<=0;watchdog_age<=0;last_update_tick<=ticks;update_us_age<=0;update_subtick<=0;
      progress_left<=50;reset_arm_consumed<=1;arming<=1;arming_rearmed<=0;arming_age<=0;accepted_pulse<=1;
     end else begin
      if(next_sequence)last_sequence<=rx_seq;
      if(mask!=required_mask)config_reject();
      fault_cut(F_ARM|(!next_sequence?F_LINK:32'd0));last_reject<=8'h82;
     end
    end
    8'h03:begin
     if(update_admissible)begin
      rates<=request_frame[1279 -:384];last_sequence<=rx_seq;watchdog_age<=0;
      progress_left<=50;accepted_pulse<=1;
      last_update_interval_us<=update_interval_us;update_us_age<=0;update_subtick<=0;
      if({1'b0,update_interval_ticks}*33'd2>{17'd0,servo_period_us}*33'd150 && late_update_count!=65535)late_update_count<=late_update_count+1'b1;
      last_update_tick<=ticks;
     end else begin fault_cut(F_LINK);last_reject<=8'h83;end
    end
    8'h04:begin
     if(next_sequence)begin
      last_sequence<=rx_seq;rates<=0;accepted_pulse<=1;
      if(armed_mask!=0 && !arming)stopping<=1;
      else begin proof_domains<=active_domains;armed_mask<=0;arming<=0;disarm_proof<=1;disarm_age<=0;end
     end else begin fault_cut(F_LINK);last_reject<=8'h84;end
    end
    8'h0b:begin
     if(next_sequence)begin last_sequence<=rx_seq;accepted_pulse<=1;end
     else begin fault_cut(F_LINK);last_reject<=8'h8b;end
    end
    8'h0d:begin
     if(next_sequence && idle && qualification_latched && wd_m_ok && wd_o_ok && (fault_word&POWER_CYCLE)==0)begin
      last_sequence<=rx_seq;rates<=0;progress_left<=0;test_age<=0;accepted_pulse<=1;
      if(request_frame[1279 -:8]==1)begin selftest_state<=1;selftest_passed[0]<=0;end
      else begin selftest_state<=3;selftest_passed[1]<=0;end
     end else begin fault_cut(F_SELFTEST);last_reject<=8'h8d;end
    end
    8'h0e:begin
     if(next_sequence && idle && (mask&~installed_mask)==0)begin
      last_sequence<=rx_seq;pos_continuity<=pos_continuity|mask;accepted_pulse<=1;
     end else begin fault_cut(F_LINK);last_reject<=8'h8e;end
    end
    // Pages/events/IOL1/output authority require their actual implementations.
    // Reject unsupported functionality explicitly; never report a fake success.
    default:begin fault_cut(F_LINK);last_reject<=8'hfd;end
    endcase
   end
   // A recognized CONFIGURE rejected by an already observed same-cycle fault
   // still invalidates the old configuration; it never commits diagnostics.
   if(request_valid && cycle_faults!=0 && op==8'h06)config_reject();
   // Last priority: actual physical faults win over every command acceptance.
   if(external_fault_word!=0)fault_word<=fault_word|external_fault_word;
   if(armed_mask!=0 && motion_runtime_fault)begin
    if(!inhibit_n)fault_cut(F_INHIBIT);
    else if(!wd_m_ok)fault_cut(F_WATCHDOG);
    else if((required_encoder_mask&~encoder_valid_mask)!=0)fault_cut(F_ENCODER);
    else if(|timing_faults)begin step_timing_latched<=step_timing_latched|timing_faults;fault_cut(F_TIMING);end
    else if((asserted_alarm&armed_mask)!=0)begin alarm_trip_latched<=alarm_trip_latched|(asserted_alarm&armed_mask);fault_cut(F_ALARM);end
    else if(!arming && (opi_ok&active_domains)!=active_domains)fault_cut(F_OPI);
    else fault_cut(external_fault_word|((motion_critical_io_fault || !motion_critical_ports_valid)?32'h00002000:32'd0));
   end
   // An accepted UPDATE on the exact expiry edge restarts the watchdog.
   if(armed_mask!=0 && watchdog_age>=WATCHDOG_TICKS-18'd1 && !(request_valid && op==8'h03 && update_admissible))fault_cut(F_WATCHDOG);
   if(reject_pulse)begin
    if(rejected_configure)config_reject();
    else begin fault_cut(F_LINK);last_reject<=8'hfe;end
   end
   if(qualification_changed)begin
    installed_mask<=0;selftest_passed<=0;selftest_state<=0;pos_continuity<=0;fault_cut(F_CHANGED);
   end
   if(cycle_faults!=0)begin
    fault_word<=fault_word|cycle_faults|external_fault_word;
    rates<=0;progress_left<=0;accepted_pulse<=0;
   end
  end
 end
endmodule
