from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'gateware/v3/runtime/cnc3_runtime_sim.v'
s=p.read_text()
def change(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
change('module cnc3_motion_spi (','module cnc3_runtime_sim (')
change(' input wire qualification_complete,input wire[11:0] installed_input,\n input wire[7:0] installed_module_class,',''' input wire sim_context,input wire[31:0] sim_expected_session,sim_expected_config_hash,
 input wire provider_strobe,input wire[31:0] provider_tag,input wire[7:0] provider_abi,
 input wire[31:0] provider_session,provider_config_hash,provider_sequence,
 input wire[7:0] provider_valid_mask,input wire[31:0] provider_faults,
 input wire[23:0] di_raw,input wire[15:0] do_applied,do_fault,
 input wire[1:0] probe_raw,input wire[11:0] home_raw,limit_low_raw,limit_high_raw,''')
change(' input wire motion_critical_ports_valid,\n','')
change(' input wire[3:0] encoder_installed,encoder_port_valid,',' input wire[3:0] encoder_port_valid,')
change(' input wire[31:0] external_fault_word,input wire motion_critical_io_fault,',' input wire[31:0] external_fault_word,')
change(' input wire[1391:0] provider_feedback,input wire[751:0] provider_status,\n','')
change(' output wire[1391:0] actual_feedback_payload,output wire[751:0] actual_status_payload',''' output wire[1391:0] actual_feedback_payload,output wire[751:0] actual_status_payload,
 output wire[15:0] dout_request,output wire sim_ready,provider_error,
 output wire[31:0] provider_accepted_sequence,
 output wire physical_authority,production_profile_complete''')
start=s.index(' // This profile is intentionally incomplete')
end=s.index(' wire page_request_accepted;',start)
s=s[:start]+''' // This top can drive a disconnected virtual plant only. No physical authority
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
 assign dout_request=(io && sim_ready && inhibit_n && wd_o_ok && fault_word==0)?dout_image:16'd0;
 always@(posedge clk or negedge rst_n)begin
  if(!rst_n)begin output_mismatch<=0;mismatch_age<=0;end
  else if(sync_clear)begin output_mismatch<=0;mismatch_age<=0;end
  else if(io && applied!=dout_request)begin
   if(mismatch_age>=49999)output_mismatch<=1;
   else mismatch_age<=mismatch_age+1'b1;
  end else mismatch_age<=0;
 end
''' +s[end:]
change(' cnc3_command_validate validate(', ' cnc3_runtime_validate validate(')
change(' cnc3_motion_state state_machine(', ' cnc3_runtime_state state_machine(')
change('.qualification_complete(qualification_complete&&alarm_valid&&IS2_PROFILE_COMPLETE),.installed_input(installed_input),.installed_module_class(installed_module_class)', '.qualification_complete(sim_ready&&alarm_valid),.installed_input(12\'hfff),.installed_module_class(8\'d0)')
change('.motion_critical_ports_valid(motion_critical_ports_valid)', '.motion_critical_ports_valid(sim_ready)')
change('.external_fault_word(external_fault_word),.motion_critical_io_fault(motion_critical_io_fault)', '.external_fault_word(runtime_faults),.motion_critical_io_fault(provider_error)')
change('.state_bits(state),.io_enabled(io));', '''.state_bits(state),.io_enabled(io),.io_config_valid(io_config_valid),.io_config_generation(io_generation),
  .dout_image(dout_image),.dout_enable_mask(dout_enable_mask),.din_stale_limit_us(din_limit),.io_page1(io_page1),
  .provider_ready(sim_ready),.provider_fault(provider_error),.provider_output_faults(output_faults),
  .expected_configuration_hash(sim_expected_config_hash),.limit_active(|limit_low || |limit_high));''')
change(' cnc3_is2_cap3_page0 capabilities(.installed_mask(installed_mask),\n  .encoder_installed(encoder_installed & {4{IS2_PROFILE_COMPLETE}}),.payload(cap3_payload));', ''' cnc3_runtime_cap3 capabilities(.ready(sim_ready&&alarm_valid),.payload(cap3_payload));
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
  .probe_status(probe_status),.overflow(event_overflow));''')
change('  fb=provider_feedback;', '  fb=0;')
change('  // One-shot index/event transport is not yet implemented; do not claim armed.\n  fb[479 -:16]=0;\n  fb[279 -:8]=8\'hff; // DI stale/no IOL1 acquisition authority in this scope.', '''  fb[479 -:16]={12'd0,index_armed};
  fb[1391-120*8 -:8]=probe_status;fb[1391-121*8 -:8]=event_status;
  fb[1391-136*8 -:24]=sim_ready?din:24'd0;fb[279 -:8]=din_age;
  fb[1391-140*8 -:16]=applied;fb[1391-142*8 -:16]=output_faults;''')
change("fb[47 -:8]=config_generation;fb[39 -:8]=0;", "fb[47 -:8]=config_generation;fb[39 -:8]=io_generation;")
change('  status=provider_status;', '  status=0;')
change("status[559 -:16]=0;", "status[559 -:16]=dout_image;\n  status[751-26*8 -:16]=applied;status[751-28*8 -:16]=output_faults;\n  status[751-36*8 -:160]=event_head;")
s=s.replace('// Bounded real motion integration, report-local.', '// Current versioned SIM2 runtime integration, disconnected only.')
s=s.replace('// No general output authority is granted by this candidate.', '// General outputs are virtual-plant application only; physical authority is LOW.')
p.write_text(s)
