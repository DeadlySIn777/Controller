"""Initial SIM2 state-machine implementation; historical inputs stay immutable."""
from pathlib import Path
p=Path(__file__).resolve().parents[3]/"gateware/v3/runtime/cnc3_runtime_state.v"
s=p.read_text()
def change(old,new):
 global s
 assert s.count(old)==1, old
 s=s.replace(old,new)
change("module cnc3_motion_state (", "module cnc3_runtime_state (")
change(" output wire io_enabled\n", """ output reg io_enabled,output reg io_config_valid,
 output reg [7:0] io_config_generation,
 output reg [15:0] dout_image,dout_enable_mask,din_stale_limit_us,
 output reg [431:0] io_page1,
 input wire provider_ready,input wire provider_fault,
 input wire [15:0] provider_output_faults,
 input wire [31:0] expected_configuration_hash,
 input wire limit_active
""")
change(" reg [5:0] progress_left;", """ reg [5:0] progress_left,output_progress_left;
 reg [17:0] io_watchdog_age;
 reg io_page1_valid;
 wire [15:0] command_dout=request_frame[1407-64*8 -:16];
 wire [15:0] command_index=request_frame[1407-68*8 -:16];
 wire [7:0] command_probe=request_frame[1407-70*8 -:8];
 wire io_payload_ok=(io_enabled ? (command_dout&~dout_enable_mask)==0 : command_dout==0) &&
  request_frame[1407-66*8 -:16]==0 && (command_index&16'hfff0)==0 &&
  (command_probe&8'hfc)==0 && request_frame[1407-72*8 -:80]==0 &&
  ((command_index==0 && command_probe==0) || io_config_valid);
 wire command_outputs=request_valid && (op==8'h03 || op==8'h09);
 wire output_conditions=provider_ready && !provider_fault && provider_output_faults==0 &&
  inhibit_n && wd_o_ok;
""")
change("  mask==armed_mask && request_frame[895 -:240]==0 && request_rates_valid;", "  mask==armed_mask && io_payload_ok && request_rates_valid;")
change(" wire motion_runtime_fault=!inhibit_n || !wd_m_ok || !motion_critical_ports_valid ||", " wire motion_runtime_fault=!inhibit_n || !wd_m_ok || !motion_critical_ports_valid || !provider_ready || provider_fault || limit_active ||")
change(" assign io_enabled=1'b0; // No pretend IOL1/output-session authority in this scope.\n", "")
change(" assign progress_o=1'b0;", " assign progress_o=output_progress_left!=0;")
change(" assign output_request=selftest_state==3;", " assign output_request=io_enabled || selftest_state==3;")
change(" assign state_bits={4'b0000,config_valid,qualification_latched,(qualification_latched && fault_word==0),motion_effective};", " assign state_bits={2'b00,io_enabled,io_config_valid,config_valid,qualification_latched,(qualification_latched && fault_word==0),motion_effective};")
change("   disarm_proof<=0;\n  end\n endtask", "   disarm_proof<=0;io_enabled<=0;dout_image<=0;output_progress_left<=0;\n  end\n endtask")
change("   session<=0;last_sequence<=0;ticks<=0;fault_word<=0;", """   session<=0;last_sequence<=0;ticks<=0;fault_word<=0;
   io_enabled<=0;io_config_valid<=0;io_config_generation<=0;io_page1_valid<=0;
   dout_image<=0;dout_enable_mask<=0;din_stale_limit_us<=440;io_page1<=0;
   output_progress_left<=0;io_watchdog_age<=0;""")
change("   if(progress_left!=0)progress_left<=progress_left-1'b1;", """   if(progress_left!=0)progress_left<=progress_left-1'b1;
   if(output_progress_left!=0)output_progress_left<=output_progress_left-1'b1;
   if(io_enabled && io_watchdog_age<WATCHDOG_TICKS)io_watchdog_age<=io_watchdog_age+1'b1;
""")
change("if(idle && qualification_latched && qualification_complete && !qualification_changed && inhibit_n", "if(idle && !io_enabled && qualification_latched && qualification_complete && !qualification_changed && inhibit_n")
change("if(idle && cfg_session && cfg_semantic)begin", "if(idle && !io_enabled && cfg_session && cfg_semantic && request_frame[447 -:32]==expected_configuration_hash)begin")
change("      config_valid<=1;session<=0;last_sequence<=0;accepted_pulse<=1;", "      config_valid<=1;io_config_valid<=0;io_page1_valid<=0;session<=0;last_sequence<=0;accepted_pulse<=1;")
change("if(next_sequence && idle && fault_word==0 && config_valid && mask==required_mask &&", "if(next_sequence && idle && io_enabled && io_config_valid && fault_word==0 && config_valid && mask==required_mask &&")
change("      progress_left<=50;accepted_pulse<=1;", "      progress_left<=50;accepted_pulse<=1;\n      if(io_enabled)begin dout_image<=command_dout;io_watchdog_age<=0;output_progress_left<=50;end")
change("    8'h0b:begin\n     if(next_sequence)begin last_sequence<=rx_seq;accepted_pulse<=1;end", """    8'h07:begin
     // Explicit SIM2 integrated provider profile. No legacy card-class claims.
     if(idle && !io_enabled && cfg_session && config_valid && provider_ready &&
        request_frame[1279 -:8]==1 &&
        request_frame[1407-41*8 -:16]==0 && request_frame[1407-48*8 -:16]==0 &&
        request_frame[1407-51*8 -:32]==0)begin
      io_page1<=request_frame[1279 -:432];io_page1_valid<=1;io_config_valid<=0;
      if(session!=0)last_sequence<=rx_seq;accepted_pulse<=1;
     end else if(idle && !io_enabled && cfg_session && config_valid && provider_ready &&
        io_page1_valid && request_frame[1279 -:8]==0 &&
        request_frame[1407-17*8 -:48]==0 && request_frame[1407-25*8 -:8]==0 &&
        request_frame[1407-26*8 -:32]==config_hash)begin
      dout_enable_mask<=request_frame[1407-23*8 -:16];
      din_stale_limit_us<=request_frame[1407-30*8 -:16];io_config_valid<=1;
      io_config_generation<=(io_config_generation==255)?1:io_config_generation+1'b1;
      if(session!=0)last_sequence<=rx_seq;accepted_pulse<=1;
     end else begin io_config_valid<=0;fault_cut(32'h00020000);last_reject<=8'h87;end
    end
    8'h0a:begin
     if(next_sequence && idle && !io_enabled && io_config_valid && fault_word==0 &&
        output_conditions && selftest_passed[1])begin
      io_enabled<=1;dout_image<=0;io_watchdog_age<=0;output_progress_left<=50;
      last_sequence<=rx_seq;accepted_pulse<=1;
     end else begin fault_cut(32'h00020000);last_reject<=8'h8a;end
    end
    8'h09:begin
     if(next_sequence && armed_mask==0 && io_enabled && output_conditions && io_payload_ok && fault_word==0)begin
      dout_image<=command_dout;io_watchdog_age<=0;output_progress_left<=50;
      last_sequence<=rx_seq;accepted_pulse<=1;
     end else begin fault_cut(F_LINK);last_reject<=8'h89;end
    end
    8'h0b:begin
     if(next_sequence)begin last_sequence<=rx_seq;accepted_pulse<=1;io_enabled<=0;dout_image<=0;output_progress_left<=0;end""")
change("if(next_sequence && idle && qualification_latched && wd_m_ok", "if(next_sequence && idle && !io_enabled && qualification_latched && wd_m_ok")
change("   if(reject_pulse)begin", """   if(io_enabled && (!output_conditions || (io_watchdog_age>=WATCHDOG_TICKS-1 &&
      !(command_outputs && io_payload_ok && next_sequence && fault_word==0))))begin
    fault_cut(!output_conditions?32'h00802000:32'h00004000);
   end
   if(provider_fault)begin io_config_valid<=0;fault_cut(32'h00002000);end
   if(armed_mask!=0 && limit_active)fault_cut(32'h00002000);
   if(reject_pulse)begin
    if(request_frame[1367:1360]==7)io_config_valid<=0;""")
change("// Report-local bounded CNC3 motion-authority candidate.", "// Versioned SIM2 runtime state derivative. Simulation authority only.")
s=s.replace("// General I/O is deliberately disabled until its actual IOL1/config/epoch\n// implementation exists. Physical qualification and safety inputs are providers.", "// Integrated virtual providers implement bounded DI/DO and provenance/freshness.\n// This does not grant physical IOL1/output or production authority.")
p.write_text(s)
