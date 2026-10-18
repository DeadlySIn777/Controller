`timescale 1ns/1ps
// Report-local unqualified diagnostic: NO motion/output/permit authority.
module cnc3_physical_inhibited_diag(
 output wire STEP0_FPGA,
 output wire ARM_LAMP_FPGA,
 output wire DIR0_FPGA,
 output wire FPGA_OUTPUT_REQUEST,
 output wire FPGA_PROGRESS_O,
 output wire STEP1_FPGA,
 output wire DIR1_FPGA,
 output wire STEP2_FPGA,
 output wire DIR2_FPGA,
 output wire STEP3_FPGA,
 output wire OPI_REARM_M,
 output wire OPI_REARM_O,
 output wire DIR3_FPGA,
 output wire STEP4_FPGA,
 input wire FPGA_CLK_50M,
 output wire DIR4_FPGA,
 output wire STEP5_FPGA,
 output wire DIR5_FPGA,
 output wire STEP6_FPGA,
 output wire DIR6_FPGA,
 output wire STEP7_FPGA,
 output wire PEN0_CMD,
 output wire PEN1_CMD,
 output wire DIR7_FPGA,
 output wire STEP8_FPGA,
 output wire DIR8_FPGA,
 output wire STEP9_FPGA,
 output wire DIR9_FPGA,
 output wire STEP10_FPGA,
 output wire PERMIT_OUT_REQ,
 output wire PWM0_FPGA,
 output wire DIR10_FPGA,
 output wire STEP11_FPGA,
 output wire DIR11_FPGA,
 input wire HOST_SPI_CS_FB_N,
 input wire HOST_SPI_SCLK,
 input wire HOST_SPI_MOSI,
 output wire HOST_SPI_MISO,
 input wire FPGA_USER_RESET_N,
 input wire RAW_INHIBIT_N,
 output wire FPGA_ENDPOINT_READY,
 output wire FPGA_MOTION_REQUEST,
 output wire PWM1_FPGA,
 output wire WATCHDOG_TRIP_CLEAR,
 output wire FPGA_PROGRESS_M,
 input wire TX_PERMIT,
 output wire FPGA_LINK_FAULT,
 output wire FPGA_WATCHDOG_FAULT,
 output wire FPGA_INHIBIT_FAULT,
 output wire FPGA_TIMING_FAULT,
 input wire ENC0_A_FPGA,
 input wire ENC0_B_FPGA,
 input wire ENC0_Z_FPGA,
 input wire ENC1_A_FPGA,
 input wire ENC1_B_FPGA,
 output wire FAST_SR_CLK,
 output wire FAST_SR_LOAD_N,
 input wire ENC1_Z_FPGA,
 input wire ENC2_A_FPGA,
 input wire ENC2_B_FPGA,
 input wire ENC2_Z_FPGA,
 input wire ENC3_A_FPGA,
 output wire IOL1_L0_CS_N,
 output wire IOL1_L0_MOSI,
 input wire ENC3_B_FPGA,
 input wire ENC3_Z_FPGA,
 output wire IOL1_L0_SCLK,
 output wire IOL1_L1_CS_N,
 output wire IOL1_L1_MOSI,
 output wire IOL1_L1_SCLK,
 input wire ALM0_FPGA,
 output wire IOL1_L2_CS_N,
 output wire IOL1_L2_MOSI,
 input wire ALM1_FPGA,
 input wire ALM2_FPGA,
 input wire ALM3_FPGA,
 input wire ALM4_FPGA,
 input wire ALM5_FPGA,
 input wire ALM6_FPGA,
 output wire IOL1_L2_SCLK,
 output wire IOL1_L3_CS_N,
 input wire ALM7_FPGA,
 input wire ALM8_FPGA,
 input wire ALM9_FPGA,
 input wire ALM10_FPGA,
 input wire ALM11_FPGA,
 input wire PRB0_FPGA,
 output wire IOL1_L3_MOSI,
 output wire IOL1_L3_SCLK,
 input wire PRB1_FPGA,
 input wire EXT_PERMIT_FPGA,
 output wire EN0_N_FPGA,
 output wire EN1_N_FPGA,
 output wire EN2_N_FPGA,
 output wire EN3_N_FPGA,
 output wire EN4_N_FPGA,
 output wire EN5_N_FPGA,
 output wire EN6_N_FPGA,
 output wire EN7_N_FPGA,
 output wire EN8_N_FPGA,
 output wire EN9_N_FPGA,
 output wire EN10_N_FPGA,
 output wire EN11_N_FPGA,
 input wire CONTACTOR_FB_FPGA,
 input wire FREQ0_FPGA,
 input wire FREQ1_FPGA,
 input wire HOST_SPI_CS_CMD_N,
 input wire MPG_A_FPGA,
 input wire MPG_B_FPGA,
 input wire OPI_OK_A,
 input wire OPI_OK_B,
 input wire OPI_OK_BOE,
 input wire OPI_OK_OUT,
 input wire OPI_OK_TX,
 input wire OUT_PERMIT,
 input wire PROCESS_PERMIT_FPGA,
 input wire PROC_PERMIT,
 input wire RESET_ARM_FPGA,
 input wire SAFETY_STATUS_FPGA,
 input wire STO_FB_FPGA,
 input wire WATCHDOG_TRIP_M,
 input wire WATCHDOG_TRIP_O,
 input wire WD_M_OK,
 input wire WD_O_OK,
 input wire FAST_SR_DATA,
 input wire IOL1_L0_MISO,
 input wire IOL1_L1_MISO,
 input wire IOL1_L2_MISO,
 input wire IOL1_L3_MISO,
 input wire MOTION_A_PGOOD,
 input wire MOTION_B_PGOOD,
 input wire RAILS_OK_FPGA,
 input wire TAMPER_CLEAR_N,
 output wire FAST_PORTS_ENABLE,
 output wire XF_POWER_ENABLE
);
 assign STEP0_FPGA=1'b0;
 assign ARM_LAMP_FPGA=1'b0;
 assign DIR0_FPGA=1'b0;
 assign FPGA_OUTPUT_REQUEST=1'b0;
 assign FPGA_PROGRESS_O=1'b0;
 assign STEP1_FPGA=1'b0;
 assign DIR1_FPGA=1'b0;
 assign STEP2_FPGA=1'b0;
 assign DIR2_FPGA=1'b0;
 assign STEP3_FPGA=1'b0;
 assign OPI_REARM_M=1'b0;
 assign OPI_REARM_O=1'b0;
 assign DIR3_FPGA=1'b0;
 assign STEP4_FPGA=1'b0;
 assign DIR4_FPGA=1'b0;
 assign STEP5_FPGA=1'b0;
 assign DIR5_FPGA=1'b0;
 assign STEP6_FPGA=1'b0;
 assign DIR6_FPGA=1'b0;
 assign STEP7_FPGA=1'b0;
 assign PEN0_CMD=1'b0;
 assign PEN1_CMD=1'b0;
 assign DIR7_FPGA=1'b0;
 assign STEP8_FPGA=1'b0;
 assign DIR8_FPGA=1'b0;
 assign STEP9_FPGA=1'b0;
 assign DIR9_FPGA=1'b0;
 assign STEP10_FPGA=1'b0;
 assign PERMIT_OUT_REQ=1'b0;
 assign PWM0_FPGA=1'b0;
 assign DIR10_FPGA=1'b0;
 assign STEP11_FPGA=1'b0;
 assign DIR11_FPGA=1'b0;
 assign HOST_SPI_MISO=(raw_reset_n && reset_released && host_miso_oe)?host_miso:1'bz;
 assign FPGA_ENDPOINT_READY=1'b0;
 assign FPGA_MOTION_REQUEST=1'b0;
 assign PWM1_FPGA=1'b0;
 assign WATCHDOG_TRIP_CLEAR=1'b0;
 assign FPGA_PROGRESS_M=1'b0;
 assign FPGA_LINK_FAULT=1'b1;
 assign FPGA_WATCHDOG_FAULT=1'b1;
 assign FPGA_INHIBIT_FAULT=1'b1;
 assign FPGA_TIMING_FAULT=1'b1;
 assign FAST_SR_CLK=1'b0;
 assign FAST_SR_LOAD_N=1'b1;
 assign IOL1_L0_CS_N=(raw_reset_n && reset_released)?iol1_cs[0]:1'b1;
 assign IOL1_L0_MOSI=(raw_reset_n && reset_released)?iol1_mosi[0]:1'b0;
 assign IOL1_L0_SCLK=(raw_reset_n && reset_released)?iol1_sclk[0]:1'b0;
 assign IOL1_L1_CS_N=(raw_reset_n && reset_released)?iol1_cs[1]:1'b1;
 assign IOL1_L1_MOSI=(raw_reset_n && reset_released)?iol1_mosi[1]:1'b0;
 assign IOL1_L1_SCLK=(raw_reset_n && reset_released)?iol1_sclk[1]:1'b0;
 assign IOL1_L2_CS_N=(raw_reset_n && reset_released)?iol1_cs[2]:1'b1;
 assign IOL1_L2_MOSI=(raw_reset_n && reset_released)?iol1_mosi[2]:1'b0;
 assign IOL1_L2_SCLK=(raw_reset_n && reset_released)?iol1_sclk[2]:1'b0;
 assign IOL1_L3_CS_N=(raw_reset_n && reset_released)?iol1_cs[3]:1'b1;
 assign IOL1_L3_MOSI=(raw_reset_n && reset_released)?iol1_mosi[3]:1'b0;
 assign IOL1_L3_SCLK=(raw_reset_n && reset_released)?iol1_sclk[3]:1'b0;
 assign EN0_N_FPGA=1'b1;
 assign EN1_N_FPGA=1'b1;
 assign EN2_N_FPGA=1'b1;
 assign EN3_N_FPGA=1'b1;
 assign EN4_N_FPGA=1'b1;
 assign EN5_N_FPGA=1'b1;
 assign EN6_N_FPGA=1'b1;
 assign EN7_N_FPGA=1'b1;
 assign EN8_N_FPGA=1'b1;
 assign EN9_N_FPGA=1'b1;
 assign EN10_N_FPGA=1'b1;
 assign EN11_N_FPGA=1'b1;
 assign FAST_PORTS_ENABLE=1'b0;
 assign XF_POWER_ENABLE=1'b0;
 localparam integer OBS_WIDTH=63;
 wire[OBS_WIDTH-1:0] raw_input_observations={TAMPER_CLEAR_N,RAILS_OK_FPGA,MOTION_B_PGOOD,MOTION_A_PGOOD,IOL1_L3_MISO,IOL1_L2_MISO,IOL1_L1_MISO,IOL1_L0_MISO,FAST_SR_DATA,WD_O_OK,WD_M_OK,WATCHDOG_TRIP_O,WATCHDOG_TRIP_M,STO_FB_FPGA,SAFETY_STATUS_FPGA,RESET_ARM_FPGA,PROC_PERMIT,PROCESS_PERMIT_FPGA,OUT_PERMIT,OPI_OK_TX,OPI_OK_OUT,OPI_OK_BOE,OPI_OK_B,OPI_OK_A,MPG_B_FPGA,MPG_A_FPGA,HOST_SPI_CS_CMD_N,FREQ1_FPGA,FREQ0_FPGA,CONTACTOR_FB_FPGA,EXT_PERMIT_FPGA,PRB1_FPGA,PRB0_FPGA,ALM11_FPGA,ALM10_FPGA,ALM9_FPGA,ALM8_FPGA,ALM7_FPGA,ALM6_FPGA,ALM5_FPGA,ALM4_FPGA,ALM3_FPGA,ALM2_FPGA,ALM1_FPGA,ALM0_FPGA,ENC3_Z_FPGA,ENC3_B_FPGA,ENC3_A_FPGA,ENC2_Z_FPGA,ENC2_B_FPGA,ENC2_A_FPGA,ENC1_Z_FPGA,ENC1_B_FPGA,ENC1_A_FPGA,ENC0_Z_FPGA,ENC0_B_FPGA,ENC0_A_FPGA,TX_PERMIT,RAW_INHIBIT_N,FPGA_USER_RESET_N,HOST_SPI_MOSI,HOST_SPI_SCLK,HOST_SPI_CS_FB_N};
 reg[OBS_WIDTH-1:0] obs0,obs1,input_observations;
 always@(posedge FPGA_CLK_50M or negedge raw_reset_n)
  if(!raw_reset_n)begin obs0<=0;obs1<=0;input_observations<=0;end
  else begin obs0<=raw_input_observations;obs1<=obs0;input_observations<=obs1;end

 // raw_reset_n is a source pin conjunction, not a fabricated rail-health flag.
 // RAILS_OK_FPGA binds /FPGA_CRESET_N in the exact physical manifest.
 wire raw_reset_n=FPGA_USER_RESET_N && RAILS_OK_FPGA;
 reg reset_meta,reset_released;
 always @(posedge FPGA_CLK_50M or negedge raw_reset_n)
  if(!raw_reset_n)begin reset_meta<=0;reset_released<=0;end
  else begin reset_meta<=1;reset_released<=reset_meta;end
 wire[3:0] iol1_cs,iol1_sclk,iol1_mosi;
 wire[3:0] iol1_miso={IOL1_L3_MISO,IOL1_L2_MISO,IOL1_L1_MISO,IOL1_L0_MISO};
 wire[3:0] lane_fault,accepted,diagnostic_sample_valid,diagnostic_transport_seen;
 wire[3:0] commercial_active,factory_identity_verified,analog_valid;
 wire[511:0] last_valid_realtime,last_integrity_realtime,observed_board_serial;
 wire[383:0] observed_mcu_uid;
 wire[127:0] observed_generation;
 wire[63:0] sample_age_us,last_reply_sequence,analog_codes;
 wire[11:0] last_reply_state;
 wire[23:0] diagnostic_filtered_di,diagnostic_raw_di,chunk_index;
 wire[15:0] diagnostic_do_applied;
 wire[3:0] record_integrity_observed,record_failed,chunk_accepted;
 wire[255:0] chunk_data;
 wire dic_configuration_echo_valid,signature_authenticated;
 wire[31:0] dic_configuration_crc;
 // Preserved diagnostic policy: DIC filter CONFIG_WRITE, IDENT then polls.
 // This is not an output-capable or authenticated/ACTIVE acquisition image.
 cnc_iol1_record_acquisition acquisition(
  .clk(FPGA_CLK_50M),.reset_n(reset_released),.enable(reset_released),.miso(iol1_miso),
  .cs_n(iol1_cs),.sclk(iol1_sclk),.mosi(iol1_mosi),.fault_latched(lane_fault),.accepted(accepted),
  .diagnostic_sample_valid(diagnostic_sample_valid),.diagnostic_transport_seen(diagnostic_transport_seen),
  .commercial_active(commercial_active),.factory_identity_verified(factory_identity_verified),
  .last_valid_realtime(last_valid_realtime),.last_integrity_realtime(last_integrity_realtime),
  .sample_age_us(sample_age_us),.last_reply_sequence(last_reply_sequence),.last_reply_state(last_reply_state),
  .diagnostic_filtered_di(diagnostic_filtered_di),.diagnostic_raw_di(diagnostic_raw_di),
  .diagnostic_do_applied(diagnostic_do_applied),.analog_valid(analog_valid),.analog_codes(analog_codes),
  .record_integrity_observed(record_integrity_observed),.record_failed(record_failed),
  .chunk_accepted(chunk_accepted),.chunk_index(chunk_index),.chunk_data(chunk_data),
  .observed_board_serial(observed_board_serial),.observed_mcu_uid(observed_mcu_uid),
  .observed_generation(observed_generation),.dic_configuration_echo_valid(dic_configuration_echo_valid),
  .dic_configuration_crc(dic_configuration_crc),.signature_authenticated(signature_authenticated));
 wire[11:0] alarm_filtered;wire alarm_filter_sample_ready;
 cnc3_alarm_filter alarm_samples(.clk(FPGA_CLK_50M),.rst_n(reset_released),
  .raw({ALM11_FPGA,ALM10_FPGA,ALM9_FPGA,ALM8_FPGA,ALM7_FPGA,ALM6_FPGA,
        ALM5_FPGA,ALM4_FPGA,ALM3_FPGA,ALM2_FPGA,ALM1_FPGA,ALM0_FPGA}),
  .level(alarm_filtered),.valid(alarm_filter_sample_ready));
 wire[3:0] encoder_a={ENC3_A_FPGA,ENC2_A_FPGA,ENC1_A_FPGA,ENC0_A_FPGA};
 wire[3:0] encoder_b={ENC3_B_FPGA,ENC2_B_FPGA,ENC1_B_FPGA,ENC0_B_FPGA};
 wire[3:0] encoder_z={ENC3_Z_FPGA,ENC2_Z_FPGA,ENC1_Z_FPGA,ENC0_Z_FPGA};
 wire[127:0] encoder_observed,index_observed;
 wire[3:0] encoder_index_seen,encoder_illegal,encoder_index_pulse;
 genvar e;
 generate for(e=0;e<4;e=e+1)begin:encoders
  cnc3_encoder_runtime counter(.clk(FPGA_CLK_50M),.rst_n(reset_released),
   .a(encoder_a[e]),.b(encoder_b[e]),.z(encoder_z[e]),.filter_ticks(4'd1),.clear_observations(1'b0),
   .count(encoder_observed[32*e+:32]),.index_count(index_observed[32*e+:32]),
   .index_seen(encoder_index_seen[e]),.invalid_transition(encoder_illegal[e]),.index_capture(encoder_index_pulse[e]));
 end endgenerate
 // Counts are raw observations. Port power remains OFF, so no encoder-valid
 // or physical position/continuity/qualification assertion is made.
 reg[31:0] clock_observation,host_complete_frames,host_bad_frames,host_ignored_requests;
 reg[1:0] selected_region;
 wire[1407:0] host_frame;
 wire host_frame_valid,host_frame_bad,host_frame_fb;
 wire host_inner_good,host_snapshot,host_snapshot_fb,host_rejection_valid,host_rejection_fb;
 wire[47:0] host_rejection_header;
 wire host_frame_rates_good,host_rate_valid;wire[3:0]host_rate_channel;wire[31:0]host_rate_word;
 wire host_miso,host_miso_oe;
 reg[1391:0] feedback;
 reg[751:0] status;
 cnc3_spi_transport_stateful host_wire(
  .clk(FPGA_CLK_50M),.rst_n(reset_released),.spi_cs_fb_n(HOST_SPI_CS_FB_N),
  .spi_cs_cmd_n(HOST_SPI_CS_CMD_N),.spi_sclk(HOST_SPI_SCLK),.spi_mosi(HOST_SPI_MOSI),
  .feedback_payload(feedback),.status_payload(status),.spi_miso(host_miso),.spi_miso_oe(host_miso_oe),
  .frame(host_frame),.frame_cs_fb(host_frame_fb),.frame_valid(host_frame_valid),.frame_bad(host_frame_bad),
  .embedded_crc_good(host_inner_good),.snapshot_start(host_snapshot),.snapshot_cs_fb(host_snapshot_fb),
  .rejection_header_valid(host_rejection_valid),.rejection_header(host_rejection_header),
  .rejection_header_cs_fb(host_rejection_fb),.rate_frame_good(1'b0),.frame_rates_good(host_frame_rates_good),
  .rx_rate_word_valid(host_rate_valid),.rx_rate_channel(host_rate_channel),.rx_rate_word(host_rate_word));
 // Only a CRC-complete96-byte DGR1/read-region request changes a diagnostic
 // page selector. It cannot configure, arm, rearm, clear or refresh a watchdog.
 wire select_request=host_frame_valid && !host_frame_fb &&
  host_frame[1407:1376]==32'h44475231 && host_frame[1375:1368]==1 &&
  host_frame[1367:1360]==8'h10 && host_frame[1359:1352]<4 && host_frame[1351:656]==0;
 always @(posedge FPGA_CLK_50M or negedge raw_reset_n)begin
  if(!raw_reset_n)begin clock_observation<=0;host_complete_frames<=0;host_bad_frames<=0;host_ignored_requests<=0;selected_region<=0;end
  else if(!reset_released)begin clock_observation<=0;host_complete_frames<=0;host_bad_frames<=0;host_ignored_requests<=0;selected_region<=0;end
  else begin
   clock_observation<=clock_observation+1'b1;
   if(host_frame_valid)host_complete_frames<=host_complete_frames+1'b1;
   if(host_frame_bad)host_bad_frames<=host_bad_frames+1'b1;
   if(select_request)selected_region<=host_frame[1353:1352];
   else if(host_frame_valid && !host_frame_fb)host_ignored_requests<=host_ignored_requests+1'b1;
  end
 end
 always @*begin
  feedback=0;status=0;
  feedback[1391-0*8-:32]=32'h44474631; // DGF1, not CNC3/SIM2.
  feedback[1391-4*8-:8]=1;feedback[1391-5*8-:8]=1; // version1,inhibited diagnostic
  feedback[1391-6*8-:16]=174;
  feedback[1391-8*8-:32]=32'h0c041810; // fitted design counts12/4/24/16, not qualified counts
  feedback[1391-12*8-:32]=clock_observation;
  feedback[1391-16*8-:64]={{(64-OBS_WIDTH){1'b0}},input_observations};
  feedback[1391-24*8-:32]=host_complete_frames;feedback[1391-28*8-:32]=host_bad_frames;
  feedback[1391-32*8-:16]={4'd0,alarm_filtered};
  feedback[1391-34*8-:8]={7'd0,alarm_filter_sample_ready};
  feedback[1391-35*8-:8]={7'd0,reset_released};
  feedback[1391-36*8-:128]=encoder_observed;feedback[1391-52*8-:128]=index_observed;
  feedback[1391-68*8-:8]={4'd0,encoder_illegal};feedback[1391-69*8-:8]={4'd0,encoder_index_seen};
  feedback[1391-70*8-:8]={4'd0,encoder_index_pulse};
  feedback[1391-72*8-:8]={4'd0,lane_fault};feedback[1391-73*8-:8]={4'd0,diagnostic_sample_valid};
  feedback[1391-74*8-:8]={4'd0,diagnostic_transport_seen};feedback[1391-75*8-:8]={4'd0,record_integrity_observed};
  feedback[1391-76*8-:8]={4'd0,record_failed};feedback[1391-77*8-:8]={4'd0,chunk_accepted};
  feedback[1391-78*8-:8]={7'd0,dic_configuration_echo_valid};
  feedback[1391-79*8-:8]={7'd0,signature_authenticated}; // existing acquisition observation, remains false
  feedback[1391-80*8-:64]=sample_age_us;feedback[1391-88*8-:64]=last_reply_sequence;
  feedback[1391-96*8-:16]={4'd0,last_reply_state};
  feedback[1391-98*8-:8]={4'd0,commercial_active};feedback[1391-99*8-:8]={4'd0,factory_identity_verified};
  feedback[1391-100*8-:24]=diagnostic_raw_di;feedback[1391-103*8-:24]=diagnostic_filtered_di;
  feedback[1391-106*8-:16]=diagnostic_do_applied; // target SW_STATE observations, not terminal voltage
  feedback[1391-108*8-:8]={4'd0,analog_valid};feedback[1391-109*8-:64]=analog_codes;
  feedback[1391-117*8-:32]=dic_configuration_crc;feedback[1391-121*8-:128]=observed_generation;
  feedback[1391-137*8-:96]=observed_mcu_uid[96*selected_region+:96];
  feedback[1391-149*8-:128]=observed_board_serial[128*selected_region+:128];
  feedback[1391-165*8-:8]={6'd0,selected_region};feedback[1391-166*8-:32]=host_ignored_requests;
  status[751-0*8-:32]=32'h44475331; // DGS1
  status[751-4*8-:8]=1;status[751-5*8-:8]=1;status[751-6*8-:16]=94;
  status[751-8*8-:32]=32'h0c041810;status[751-12*8-:32]=clock_observation;
  status[751-16*8-:64]={{(64-OBS_WIDTH){1'b0}},input_observations};
  status[751-24*8-:32]=host_complete_frames;status[751-28*8-:32]=host_bad_frames;
  status[751-32*8-:32]=host_ignored_requests;
  status[751-36*8-:64]=sample_age_us;status[751-44*8-:64]=last_reply_sequence;
  status[751-52*8-:8]={4'd0,lane_fault};status[751-53*8-:8]={4'd0,diagnostic_sample_valid};
  status[751-54*8-:8]={4'd0,record_integrity_observed};status[751-55*8-:8]={4'd0,record_failed};
  status[751-56*8-:8]={6'd0,selected_region};
  status[751-57*8-:96]=observed_mcu_uid[96*selected_region+:96];
  status[751-69*8-:128]=observed_board_serial[128*selected_region+:128];
  status[751-85*8-:32]=observed_generation[32*selected_region+:32];
  status[751-89*8-:32]=dic_configuration_crc;
  status[751-93*8-:8]={7'd0,dic_configuration_echo_valid};
 end
endmodule
