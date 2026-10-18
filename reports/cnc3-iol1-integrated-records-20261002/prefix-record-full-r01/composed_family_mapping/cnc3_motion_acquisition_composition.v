module cnc3_motion_acquisition_composition (
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
 output wire[1391:0] actual_feedback_payload,output wire[751:0] actual_status_payload,
 input wire diagnostic_enable,input wire[3:0]iol1_miso,
 output wire[3:0]iol1_cs_n,iol1_sclk,iol1_mosi,iol1_fault,iol1_accepted,
 output wire[3:0]diagnostic_sample_valid,diagnostic_transport_seen,
 output wire[3:0]commercial_active,factory_identity_verified,analog_valid,
 output wire[511:0]last_valid_realtime,last_integrity_realtime,
 output wire[63:0]sample_age_us,last_reply_sequence,analog_codes,
 output wire[11:0]last_reply_state,
 output wire[23:0]diagnostic_filtered_di,diagnostic_raw_di,
 output wire[15:0]diagnostic_do_applied,
 output wire[3:0] record_integrity_observed,record_failed,chunk_accepted,
 output wire[511:0]observed_board_serial,output wire[383:0]observed_mcu_uid,
 output wire[127:0]observed_generation,output wire[23:0]chunk_index,output wire[255:0]chunk_data,
 output wire dic_configuration_echo_valid,signature_authenticated,output wire[31:0]dic_configuration_crc
);
// Composition counts retained exact motion + real acquisition. Diagnostic data
// cannot substitute for the absent qualified factory/provider inputs of motion.
cnc3_motion_spi motion(.*);
cnc_iol1_record_acquisition diagnostic(.clk(clk),.reset_n(rst_n),.enable(diagnostic_enable),.miso(iol1_miso),.cs_n(iol1_cs_n),.sclk(iol1_sclk),.mosi(iol1_mosi),.fault_latched(iol1_fault),.accepted(iol1_accepted),.diagnostic_sample_valid(diagnostic_sample_valid),.diagnostic_transport_seen(diagnostic_transport_seen),.commercial_active(commercial_active),.factory_identity_verified(factory_identity_verified),.last_valid_realtime(last_valid_realtime),.last_integrity_realtime(last_integrity_realtime),.sample_age_us(sample_age_us),.last_reply_sequence(last_reply_sequence),.last_reply_state(last_reply_state),.diagnostic_filtered_di(diagnostic_filtered_di),.diagnostic_raw_di(diagnostic_raw_di),.diagnostic_do_applied(diagnostic_do_applied),.analog_valid(analog_valid),.analog_codes(analog_codes),.record_integrity_observed(record_integrity_observed),.record_failed(record_failed),.chunk_accepted(chunk_accepted),.chunk_index(chunk_index),.chunk_data(chunk_data),.observed_board_serial(observed_board_serial),.observed_mcu_uid(observed_mcu_uid),.observed_generation(observed_generation),.dic_configuration_echo_valid(dic_configuration_echo_valid),.dic_configuration_crc(dic_configuration_crc),.signature_authenticated(signature_authenticated));
endmodule
