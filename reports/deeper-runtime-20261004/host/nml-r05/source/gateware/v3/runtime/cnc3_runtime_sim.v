`timescale 1ns/1ps
// Current versioned SIM2 runtime integration, disconnected only. Frozen transport,
// explicit integrated-class validator, twelve DDS generators and four ABZ counters.
// Physical IOL1 acquisition/qualification and additional pages remain outside scope.
// General outputs are virtual-plant application only; physical authority is LOW.
module cnc3_runtime_sim (
 input wire clk,input wire rst_n,
 input wire spi_cs_fb_n,spi_cs_cmd_n,spi_sclk,spi_mosi,
 output wire spi_miso,spi_miso_oe,
 input wire sim_context,input wire[31:0] sim_expected_session,sim_expected_config_hash,
 input wire provider_strobe,input wire[31:0] provider_tag,input wire[7:0] provider_abi,
 input wire[31:0] provider_session,provider_config_hash,provider_sequence,
 input wire[7:0] provider_valid_mask,input wire[31:0] provider_faults,
 input wire[23:0] di_raw,input wire[15:0] do_applied,do_fault,
 input wire[1:0] probe_raw,input wire[11:0] home_raw,limit_low_raw,limit_high_raw,
 input wire inhibit_n,wd_m_ok,wd_o_ok,
 input wire reset_arm_ready,reset_arm_held,contactor_deenergized,sto_arm_expected,
 input wire[3:0] gate_high,opi_ok,
 input wire output_gate_high,output_opi_ok,output wire output_opi_rearm,
 input wire[11:0] alarm_current_raw,
 input wire[3:0] encoder_a,encoder_b,encoder_z,
 input wire[3:0] encoder_port_valid,
 input wire[31:0] external_fault_word,
 // Explicit model safety observations; this input does not qualify real hardware.
 input wire[31:0] physical_safety_power_word,
 output wire[11:0] step_out,dir_out,enable_n,
 output wire motion_request,output_request,permit_out_req,progress_m,progress_o,
 output wire[3:0] opi_rearm,output wire reset_arm_consumed,
 output wire[31:0] session,last_sequence,fault_word,
 output wire[11:0] armed_mask,pos_continuity,
 output wire config_valid,output wire[1:0] selftest_passed,
 output wire[2:0] selftest_state,output wire accepted_pulse,
 output wire[7:0] last_reject,
 output wire[1391:0] actual_feedback_payload,output wire[751:0] actual_status_payload,
 output wire[15:0] dout_request,output wire sim_ready,provider_error,
 output wire[31:0] provider_accepted_sequence,
 output wire physical_authority,production_profile_complete
);
 // This top can drive a disconnected virtual plant only. No physical authority
 // or production completion output can be promoted by runtime inputs.
 assign physical_authority=1'b0;assign production_profile_complete=1'b0;
 wire[23:0] din;wire[15:0] applied,output_faults,dout_image,dout_enable_mask,din_limit;
 wire[11:0] home,limit_low,limit_high;
 wire[7:0] din_age,io_generation;wire io_config_valid;
 wire[431:0] io_page1;
 cnc3_runtime_provider provider(.clk(clk),.rst_n(rst_n),.sim_context(sim_context),
  .sim_expected_session(sim_expected_session),.sim_expected_config_hash(sim_expected_config_hash),
  .provider_strobe(provider_strobe),.provider_tag(provider_tag),.provider_abi(provider_abi),
  .provider_session(provider_session),.provider_config_hash(provider_config_hash),
  .provider_sequence(provider_sequence),.provider_valid_mask(provider_valid_mask),.provider_faults(provider_faults),
  .di_raw(di_raw),.do_applied(do_applied),.do_fault(do_fault),.home_raw(home_raw),
  .limit_low_raw(limit_low_raw),.limit_high_raw(limit_high_raw),.din_stale_limit_us(din_limit),
  .ready(sim_ready),.fault_latched(provider_error),.din(din),.applied(applied),.faults(output_faults),
  .home(home),.limit_low(limit_low),.limit_high(limit_high),.din_age(din_age),
  .accepted_sequence(provider_accepted_sequence));
 wire[3:0] encoder_installed={4{sim_ready}};
 wire event_overflow;wire[3:0] index_armed;wire[7:0] probe_status,event_status;
 wire[159:0] event_head;
 reg output_mismatch;reg[15:0] mismatch_age;
 wire[31:0] runtime_faults=external_fault_word | (provider_error?32'h00002000:32'd0) |
  ((output_mismatch || |output_faults)?32'h00010000:32'd0) |
  (event_overflow?32'h00040000:32'd0);
 wire output_effective;
 assign dout_request=(output_effective && sim_ready && inhibit_n && wd_o_ok && fault_word==0)?dout_image:16'd0;
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin output_mismatch<=0;mismatch_age<=0;end
  else if(sync_clear)begin output_mismatch<=0;mismatch_age<=0;end
  else if(io && applied!=dout_request)begin
   if(mismatch_age>=49999)output_mismatch<=1;
   else mismatch_age<=mismatch_age+1'b1;
  end else mismatch_age<=0;
 end
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
 cnc3_runtime_validate validate(frame,frame_fb,frame_fb?9'd176:9'd96,1'b1,innergood,validation_result);
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
 cnc3_runtime_state state_machine(.clk(clk),.rst_n(rst_n),.request_valid(req_valid),.request_frame(frame),.reject_pulse(rejected),.rejected_configure(rejected_config),.request_rates_valid(frame_rates_good),.qualification_complete(sim_ready&&alarm_valid),.installed_input(12'hfff),.installed_module_class(8'd0),.inhibit_n(inhibit_n),.wd_m_ok(wd_m_ok),.wd_o_ok(wd_o_ok),.reset_arm_ready(reset_arm_ready),.reset_arm_held(reset_arm_held),.contactor_deenergized(contactor_deenergized),.sto_arm_expected(sto_arm_expected),.motion_critical_ports_valid(sim_ready),.encoder_valid_mask(valid_encoders),.encoder_installed_mask({8'd0,encoder_installed}),.encoder_expansion_class(8'd0),.alarm_levels(alarms),.timing_faults(timing_fault),.external_fault_word(runtime_faults),.motion_critical_io_fault(provider_error),.gate_high(gate_high),.opi_ok(opi_ok),.generator_quiescent(quiet),.request_ready(request_ready),.session(session),.last_sequence(last_sequence),.ticks(ticks),.fault_word(fault_word),.installed_mask(installed_mask),.required_mask(required_mask),.armed_mask(armed_mask),.pos_continuity(pos_continuity),.step_timing_latched(timing_latched),.alarm_trip_latched(alarm_latched),.config_valid(config_valid),.config_generation(config_generation),.config_hash(config_hash),.config_crc(config_crc),.servo_period_us(servo_period),.required_encoder_mask(required_encoders),.encoder_filter_ticks(encoder_filter),.mpg_config(mpg),.pulse_ticks(high),.space_ticks(low),.setup_ticks(setup),.hold_ticks(hold),.rates(rates),.generator_enable(gen_enable),.generator_stop(stop),.motion_request(motion_request),.output_request(output_request),.permit_out_req(permit_out_req),.progress_m(progress_m),.progress_o(progress_o),.opi_rearm(opi_rearm),.reset_arm_consumed(reset_arm_consumed),.selftest_passed(selftest_passed),.selftest_state(selftest_state),.page_request_accepted(page_request_accepted),.accepted_pulse(accepted_pulse),.sync_clear(sync_clear),.last_reject(last_reject),.last_update_interval_us(interval),.late_update_count(late),.motion_effective(effective),.state_bits(state),.io_enabled(io),.io_config_valid(io_config_valid),.io_config_generation(io_generation),
  .dout_image(dout_image),.dout_enable_mask(dout_enable_mask),.din_stale_limit_us(din_limit),.io_page1(io_page1),
  .provider_ready(sim_ready),.provider_fault(provider_error),.provider_output_faults(output_faults | (output_mismatch?16'hffff:16'd0)),.provider_applied(applied),
  .expected_configuration_hash(sim_expected_config_hash),.limit_active(|limit_low || |limit_high),
  .output_gate_high(output_gate_high),.output_opi_ok(output_opi_ok),
  .output_opi_rearm(output_opi_rearm),.output_effective(output_effective));
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
   if(snapshot_start)page_in_flight<=snapshot_fb && page_pending;
   if(page_consume)page_pending<=0;
   if(page_request_accepted)page_pending<=1;
  end
 end
 cnc3_runtime_cap3 capabilities(.ready(sim_ready&&alarm_valid),.payload(cap3_payload));
 wire[287:0] event_steps;wire[95:0] event_encoders,event_indices;
 genvar c;
 generate for(c=0;c<12;c=c+1)begin:pack_steps
  assign event_steps[287-24*c -:24]=step_counts[c][23:0];
 end endgenerate
 generate for(c=0;c<4;c=c+1)begin:pack_encoders
  assign event_encoders[95-24*c -:24]=encoder_counts[c][23:0];
  assign event_indices[95-24*c -:24]=index_counts[c][23:0];
 end endgenerate
 cnc3_runtime_events events(.clk(clk),.rst_n(rst_n),.clear(sync_clear),.provider_ready(sim_ready),
  .ticks(ticks),.fault_word(fault_word),.safety_word(safety),.armed_mask(armed_mask),.pos_continuity(pos_continuity),
  .step_counts(event_steps),.encoder_counts(event_encoders),.index_counts(event_indices),.index_pulse(index_pulse),
  .probe_raw(probe_raw),.io_page1(io_page1),
  .arm_commit(accepted_pulse && frame[1367:1360]==3),
  .index_request(frame[1407-68*8-12 -:4]),.probe_request(frame[1407-70*8-6 -:2]),
  .cmd_snapshot(snapshot_start&&!snapshot_fb),.cmd_complete(frame_valid&&!frame_fb),
  .ack_commit(accepted_pulse && frame[1367:1360]==16),.ack(frame[1279 -:8]),
  .event_head(event_head),.event_status(event_status),.index_armed(index_armed),
  .probe_status(probe_status),.overflow(event_overflow));
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
  fb=0;
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
  fb[479 -:16]={12'd0,index_armed};
  fb[1391-120*8 -:8]=probe_status;fb[1391-121*8 -:8]=event_status;
  fb[1391-136*8 -:24]=sim_ready?din:24'd0;fb[279 -:8]=din_age;
  fb[1391-140*8 -:16]=applied;fb[1391-142*8 -:16]=output_faults;
  fb[239 -:8]=0;fb[231 -:8]=0; // process/PWM/AO commands disabled.
  fb[159 -:8]=0;fb[151 -:8]=8'hff; // AI invalid/stale.
  fb[79 -:32]=safety;fb[47 -:8]=config_generation;fb[39 -:8]=io_generation;
  status=0;
  status[751 -:32]=32'h434e5333;status[719 -:8]=3;status[711 -:8]=state;
  status[703 -:16]={4'd0,armed_mask};status[687 -:32]=session;status[655 -:32]=last_sequence;
  status[623 -:32]=ticks;status[591 -:32]=fault_word;status[559 -:16]=dout_image;
  status[751-26*8 -:16]=applied;status[751-28*8 -:16]=output_faults;
  status[751-36*8 -:160]=event_head;
  status[511 -:32]=safety;status[479 -:16]={4'd0,pos_continuity};
  status[303 -:8]=8'hff; // telemetry source unavailable.
  status[279 -:8]=0; // telemetry validity unavailable.
  status[63:0]=0; // Frozen CNS3 bytes86..93 are reserved ZERO.
  status[127 -:16]=interval;status[111 -:16]=late;
 end
 assign actual_feedback_payload=fb;assign actual_status_payload=status;
endmodule
