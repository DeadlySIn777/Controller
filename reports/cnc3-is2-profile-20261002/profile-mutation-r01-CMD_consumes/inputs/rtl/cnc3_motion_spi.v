`timescale 1ns/1ps
// Bounded real motion integration, report-local. Exact frozen transport/static
// validator, twelve actual DDS generators, four actual quadrature algorithms.
// A provider must implement the remaining safety qualifier/IOL1/pages/events.
// No general output authority is granted by this candidate.
module cnc3_motion_spi (
 input wire clk,input wire rst_n,
 input wire spi_cs_fb_n,spi_cs_cmd_n,spi_sclk,spi_mosi,
 output wire spi_miso,spi_miso_oe,
 input wire qualification_complete,input wire[11:0] installed_input,
 input wire[7:0] installed_module_class,
 input wire inhibit_n,wd_m_ok,wd_o_ok,
 input wire reset_arm_ready,reset_arm_held,contactor_deenergized,sto_arm_expected,
 input wire motion_critical_ports_valid,
 input wire[3:0] gate_high,opi_ok,
 input wire[11:0] alarm_current_raw,
 input wire[3:0] encoder_a,encoder_b,encoder_z,
 input wire[3:0] encoder_installed,encoder_port_valid,
 input wire[31:0] external_fault_word,input wire motion_critical_io_fault,
 // These must be supplied by real acquisition/event/diagnostic providers.
 // This scope overwrites all fields it owns and always marks DI/AI stale.
 input wire[1391:0] provider_feedback,input wire[751:0] provider_status,
 input wire[31:0] physical_safety_power_word,
 output wire[11:0] step_out,dir_out,enable_n,
 output wire motion_request,output_request,permit_out_req,progress_m,progress_o,
 output wire[3:0] opi_rearm,output wire reset_arm_consumed,
 output wire[31:0] session,last_sequence,fault_word,
 output wire[11:0] armed_mask,pos_continuity,
 output wire config_valid,output wire[1:0] selftest_passed,
 output wire[2:0] selftest_state,output wire accepted_pulse,
 output wire[7:0] last_reject,
 output wire[1391:0] actual_feedback_payload,output wire[751:0] actual_status_payload
);
 // This profile is intentionally incomplete until real full producer and
 // independent physical qualification providers are implemented. Inventory
 // support cannot be used as machine readiness or installed qualification.
 localparam IS2_PROFILE_COMPLETE=1'b0;
 wire page_request_accepted;
 reg page_pending,page_in_flight;
 wire[1391:0] cap3_payload;
 wire[1391:0] transport_feedback_payload=page_pending?cap3_payload:actual_feedback_payload;
 wire[1407:0] frame;wire frame_valid,frame_bad,frame_fb,innergood;
 wire[7:0] validation_result;
 wire snapshot_start,snapshot_fb;
 wire rate_frame_good,frame_rates_good,rx_rate_word_valid,rate_busy,rate_poisoned;
 wire[3:0] rx_rate_channel;wire[31:0] rx_rate_word;wire[11:0] rate_channel_good;
 wire rejection_header_valid,rejection_header_cs_fb;wire[47:0] rejection_header;
 cnc3_spi_transport_stateful transport(.clk(clk),.rst_n(rst_n),.spi_cs_fb_n(spi_cs_fb_n),.spi_cs_cmd_n(spi_cs_cmd_n),.spi_sclk(spi_sclk),.spi_mosi(spi_mosi),.feedback_payload(transport_feedback_payload),.status_payload(actual_status_payload),.spi_miso(spi_miso),.spi_miso_oe(spi_miso_oe),.frame(frame),.frame_cs_fb(frame_fb),.frame_valid(frame_valid),.frame_bad(frame_bad),.embedded_crc_good(innergood),.snapshot_start(snapshot_start),.snapshot_cs_fb(snapshot_fb),.rejection_header_valid(rejection_header_valid),.rejection_header(rejection_header),.rejection_header_cs_fb(rejection_header_cs_fb),.rate_frame_good(rate_frame_good),.frame_rates_good(frame_rates_good),.rx_rate_word_valid(rx_rate_word_valid),.rx_rate_channel(rx_rate_channel),.rx_rate_word(rx_rate_word));
 cnc3_command_validate validate(frame,frame_fb,frame_fb?9'd176:9'd96,1'b1,innergood,validation_result);
 // frame_valid is only raised by the actual streamed CRC-checked transport.
 wire req_valid=frame_valid && validation_result==0;
 wire rejected=frame_bad || (frame_valid && validation_result!=0);
 // Raw-header sideband can only invalidate recognizable CONFIGURE. It never
 // commits, changes session/sequence/generation, or emits progress/permission.
 wire rejected_config=(frame_valid && validation_result!=0 &&
  frame[1407:1376]==32'h434e4333 && frame[1375:1368]==3 && frame[1367:1360]==6) ||
  (frame_bad && rejection_header_valid && rejection_header[47:16]==32'h434e4333 &&
   rejection_header[15:8]==3 && rejection_header[7:0]==6);
 wire[11:0] installed_mask,required_mask,timing_latched,alarm_latched,required_encoders;
 wire[11:0] gen_enable,quiet,step_raw,dir_raw,timing_fault,alarms;
 wire alarm_valid,stop,sync_clear,io,effective,request_ready;
 wire[31:0] ticks,config_hash;
 wire[15:0] config_crc,servo_period,interval,late;
 wire[7:0] config_generation,state,mpg;
 wire[3:0] encoder_filter;
 wire[191:0] high,low,setup,hold;wire[383:0] rates;
 cnc3_rate_admission_serial admission(clk,rst_n,snapshot_start,rx_rate_word_valid,rx_rate_channel,rx_rate_word,high,low,rate_frame_good,rate_busy,rate_poisoned,rate_channel_good);
 wire signed[31:0] step_counts[0:11],encoder_counts[0:3],index_counts[0:3];
 wire[3:0] encoder_illegal,index_seen,index_pulse;
 wire[11:0] valid_encoders={8'd0,encoder_port_valid&encoder_installed&~encoder_illegal};
 cnc3_alarm_filter alarm_filter(clk,rst_n,alarm_current_raw,alarms,alarm_valid);
 cnc3_motion_state state_machine(.clk(clk),.rst_n(rst_n),.request_valid(req_valid),.request_frame(frame),.reject_pulse(rejected),.rejected_configure(rejected_config),.request_rates_valid(frame_rates_good),.qualification_complete(qualification_complete&&alarm_valid&&IS2_PROFILE_COMPLETE),.installed_input(installed_input),.installed_module_class(installed_module_class),.inhibit_n(inhibit_n),.wd_m_ok(wd_m_ok),.wd_o_ok(wd_o_ok),.reset_arm_ready(reset_arm_ready),.reset_arm_held(reset_arm_held),.contactor_deenergized(contactor_deenergized),.sto_arm_expected(sto_arm_expected),.motion_critical_ports_valid(motion_critical_ports_valid),.encoder_valid_mask(valid_encoders),.encoder_installed_mask({8'd0,encoder_installed}),.encoder_expansion_class(8'd0),.alarm_levels(alarms),.timing_faults(timing_fault),.external_fault_word(external_fault_word),.motion_critical_io_fault(motion_critical_io_fault),.gate_high(gate_high),.opi_ok(opi_ok),.generator_quiescent(quiet),.request_ready(request_ready),.session(session),.last_sequence(last_sequence),.ticks(ticks),.fault_word(fault_word),.installed_mask(installed_mask),.required_mask(required_mask),.armed_mask(armed_mask),.pos_continuity(pos_continuity),.step_timing_latched(timing_latched),.alarm_trip_latched(alarm_latched),.config_valid(config_valid),.config_generation(config_generation),.config_hash(config_hash),.config_crc(config_crc),.servo_period_us(servo_period),.required_encoder_mask(required_encoders),.encoder_filter_ticks(encoder_filter),.mpg_config(mpg),.pulse_ticks(high),.space_ticks(low),.setup_ticks(setup),.hold_ticks(hold),.rates(rates),.generator_enable(gen_enable),.generator_stop(stop),.motion_request(motion_request),.output_request(output_request),.permit_out_req(permit_out_req),.progress_m(progress_m),.progress_o(progress_o),.opi_rearm(opi_rearm),.reset_arm_consumed(reset_arm_consumed),.selftest_passed(selftest_passed),.selftest_state(selftest_state),.page_request_accepted(page_request_accepted),.accepted_pulse(accepted_pulse),.sync_clear(sync_clear),.last_reject(last_reject),.last_update_interval_us(interval),.late_update_count(late),.motion_effective(effective),.state_bits(state),.io_enabled(io));
 // Only a complete validated read-only FB frame with matching session can
 // consume the snapshot. CMD, corrupt/truncated/wrong-session transactions
 // leave the pending page intact. A newly accepted READ_PAGE queues the next.
 wire read_session=frame[1343:1312]==0 || frame[1343:1312]==session;
 wire page_consume=req_valid && frame_fb && page_in_flight && read_session &&
  armed_mask==0 && selftest_state==0 && frame[1311:1280]==0 &&
  (frame[1367:1360]==8'h10 || (frame[1367:1360]==8'h05 && frame[1279 -:8]==0));
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin page_pending<=0;page_in_flight<=0;end
  else begin
   if(snapshot_start)begin page_in_flight<=snapshot_fb && page_pending;if(!snapshot_fb)page_pending<=0;end
   if(page_consume)page_pending<=0;
   if(page_request_accepted)page_pending<=1;
  end
 end
 cnc3_is2_cap3_page0 capabilities(.installed_mask(installed_mask),
  .encoder_installed(encoder_installed & {4{IS2_PROFILE_COMPLETE}}),.payload(cap3_payload));
 genvar g;
 generate for(g=0;g<12;g=g+1)begin:motors
  cnc3_stepgen_runtime generator(clk,rst_n,gen_enable[g],stop,$signed(rates[383-32*g -:32]),high[191-16*g -:16],low[191-16*g -:16],setup[191-16*g -:16],hold[191-16*g -:16],step_raw[g],dir_raw[g],step_counts[g],timing_fault[g],quiet[g]);
 end endgenerate
 generate for(g=0;g<4;g=g+1)begin:encoders
  cnc3_encoder_runtime encoder(clk,rst_n,encoder_a[g],encoder_b[g],encoder_z[g],encoder_filter,sync_clear,encoder_counts[g],index_counts[g],index_seen[g],encoder_illegal[g],index_pulse[g]);
 end endgenerate
 assign step_out=step_raw&gen_enable;
 assign dir_out=dir_raw&gen_enable;
 assign enable_n=~gen_enable;
 reg[1391:0] fb;
 reg[751:0] status;
 reg[31:0] safety;
 integer i;
 always@*begin
  safety=physical_safety_power_word;
  safety[21]=selftest_passed[0];safety[22]=selftest_passed[1];
  fb=provider_feedback;
  fb[1391 -:32]=32'h434e4633;fb[1359 -:8]=3;fb[1351 -:8]=state;
  fb[1343 -:16]={4'd0,armed_mask};fb[1327 -:32]=session;fb[1295 -:32]=last_sequence;
  fb[1263 -:32]=ticks;fb[1231 -:32]=fault_word;fb[1199 -:16]={4'd0,installed_mask};
  fb[1183 -:16]={4'd0,timing_latched};fb[1167 -:16]={4'd0,alarms};
  fb[1151 -:16]={4'd0,alarm_latched};fb[1135 -:16]={4'd0,gen_enable};
  fb[1119 -:16]={4'd0,pos_continuity};
  for(i=0;i<12;i=i+1)fb[1103-24*i -:24]=step_counts[i][23:0];
  for(i=0;i<4;i=i+1)fb[815-24*i -:24]=encoder_installed[i]?encoder_counts[i][23:0]:24'd0;
  for(i=4;i<12;i=i+1)fb[815-24*i -:24]=0;
  fb[527 -:16]={4'd0,valid_encoders};fb[511 -:16]={12'd0,encoder_illegal};
  fb[495 -:16]={12'd0,encoder_installed&~encoder_port_valid};
  // One-shot index/event transport is not yet implemented; do not claim armed.
  fb[479 -:16]=0;
  fb[279 -:8]=8'hff; // DI stale/no IOL1 acquisition authority in this scope.
  fb[239 -:8]=0;fb[231 -:8]=0; // process/PWM/AO commands disabled.
  fb[159 -:8]=0;fb[151 -:8]=8'hff; // AI invalid/stale.
  fb[79 -:32]=safety;fb[47 -:8]=config_generation;fb[39 -:8]=0;
  status=provider_status;
  status[751 -:32]=32'h434e5333;status[719 -:8]=3;status[711 -:8]=state;
  status[703 -:16]={4'd0,armed_mask};status[687 -:32]=session;status[655 -:32]=last_sequence;
  status[623 -:32]=ticks;status[591 -:32]=fault_word;status[559 -:16]=0;
  status[511 -:32]=safety;status[479 -:16]={4'd0,pos_continuity};
  status[303 -:8]=8'hff; // telemetry source unavailable.
  status[279 -:8]=0; // telemetry validity unavailable.
  status[63:0]=0; // Frozen CNS3 bytes86..93 are reserved ZERO.
  status[127 -:16]=interval;status[111 -:16]=late;
 end
 assign actual_feedback_payload=fb;assign actual_status_payload=status;
endmodule
