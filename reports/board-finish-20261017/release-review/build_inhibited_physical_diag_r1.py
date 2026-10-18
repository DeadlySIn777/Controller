"""Build an exact-pin, explicitly unqualified read-only diagnostic candidate."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,re,shutil
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017'
OUT=BASE/'release-review/inhibited-physical-diag-r1';OUT.mkdir(exist_ok=False)
RTL=OUT/'rtl';RTL.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pinfile=BASE/'release-review/R299-actual-256-ball-source-pinmap.csv'
pins=[r for r in csv.DictReader(pinfile.open(newline='',encoding='utf-8-sig')) if r['assigned_user_ball'].lower()=='true']
assert len(pins)==135
acq=ROOT/'reports/cnc3-iol1-integrated-records-20261002/prefix-record-full-r01/composed_family_mapping'
source_files=[acq/n for n in ['cnc_iol1_record_acquisition.v','cnc_iol1_record_master.v','cnc_mbr2_stream_checker.v']]
source_files += [BASE/'release-review/transport-cmd-alignment-r1/cnc3_spi_transport_stateful.v']
source_files += [ROOT/'gateware/v3/runtime'/n for n in ['cnc3_alarm_filter.v','cnc3_encoder_runtime.v']]
for p in source_files:shutil.copyfile(p,RTL/p.name)

body=r'''
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
'''
observed=[p['logical_signal'] for p in pins if p['direction']=='input' and p['logical_signal']!='FPGA_CLK_50M']
declarations=[f" {p['direction']} wire {p['logical_signal']}" for p in pins]
header='`timescale 1ns/1ps\n// Report-local unqualified diagnostic: NO motion/output/permit authority.\nmodule cnc3_physical_inhibited_diag(\n'+',\n'.join(declarations)+'\n);\n'
assignments=[];outputs=[]
for p in pins:
 if p['direction']!='output':continue
 name=p['logical_signal'];source=''
 if re.fullmatch(r'EN\d+_N_FPGA',name):value="1'b1";reason='HIGH inactive; actual EN_N pull-up (R5063..R5074), noninverting buffer path'
 elif re.fullmatch(r'(STEP|DIR)\d+_FPGA',name):value="1'b0";reason='LOW defined STEP/DIR idle; all individual enables held inactive'
 elif name.startswith('IOL1_'):
  lane=int(name[6]);kind=name[8:]
  if kind=='CS_N':value=f"(raw_reset_n && reset_released)?iol1_cs[{lane}]:1'b1";reason='Mode0 active-low select; reset/default HIGH'
  else:
   signal='iol1_sclk' if kind=='SCLK' else 'iol1_mosi'
   value=f"(raw_reset_n && reset_released)?{signal}[{lane}]:1'b0";reason='Mode0 clock/data reset LOW; source-master reset values retained'
 elif name=='HOST_SPI_MISO':value="(raw_reset_n && reset_released && host_miso_oe)?host_miso:1'bz";reason='Tri-state unless exactly one CS active and reset released; raw-CS/reset OE from verified transport'
 elif name=='FAST_SR_LOAD_N':value="1'b1";reason='R14078 pull-up: idle load released HIGH; no FAST_SR qualification claimed'
 elif name in ['FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT']:
  value="1'b1";reason='Active-HIGH assertion per historical implemented fault outputs; exact board TP22001..4 only. Diagnostic-image refusal policy, not measured subsystem fault/qualification'
 else:
  assert name in ['ARM_LAMP_FPGA','FPGA_OUTPUT_REQUEST','FPGA_PROGRESS_O','OPI_REARM_M','OPI_REARM_O',
   'PERMIT_OUT_REQ','PWM0_FPGA','PWM1_FPGA','FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','WATCHDOG_TRIP_CLEAR',
   'FPGA_PROGRESS_M','FAST_SR_CLK','FAST_PORTS_ENABLE','XF_POWER_ENABLE','PEN0_CMD','PEN1_CMD'],name
  value="1'b0";reason='LOW inactive source-backed request/strobe/enable or endpoint-not-ready; see electrical-idle-evidence.json'
 assignments.append(f' assign {name}={value};')
 outputs.append({**p,'safe_drive':value,'basis':reason})
observation='\n localparam integer OBS_WIDTH='+str(len(observed))+';\n wire[OBS_WIDTH-1:0] raw_input_observations={'+','.join(reversed(observed))+'};\n reg[OBS_WIDTH-1:0] obs0,obs1,input_observations;\n always@(posedge FPGA_CLK_50M or negedge raw_reset_n)\n  if(!raw_reset_n)begin obs0<=0;obs1<=0;input_observations<=0;end\n  else begin obs0<=raw_input_observations;obs1<=obs0;input_observations<=obs1;end\n'
early=[" wire raw_reset_n=FPGA_USER_RESET_N && RAILS_OK_FPGA;",' reg reset_meta,reset_released;',
       ' wire[3:0] iol1_cs,iol1_sclk,iol1_mosi;',' wire host_miso,host_miso_oe;']
for declaration in early:
 assert body.count(declaration)==1;body=body.replace(declaration,'')
top=RTL/'cnc3_physical_inhibited_diag.v';top.write_text(header+'\n'.join(early)+observation+'\n'.join(assignments)+body,encoding='utf-8')

evidence={
 'authority_clamp':{'source':'hardware/mc_permission/design.json','components':['U3','U4','U5','U6','U7','U8','R1'],
  'fact':'Endpoint LOW holds both physical latch clears LOW; motion/output request LOW also blocks final permission gates. No useful-progress/rearm/clear pulse is generated.'},
 'motor_idle':{'source':'hardware/motherboard/design.json','components':['U5001','R5063'],
  'fact':'Noninverting LVC244 STEP/DIR/EN_N path; EN_N default pull-up, all12 HIGH inactive. Existing current runtime uses enable_n=~gen_enable.'},
 'process':{'source':'hardware/motherboard_process/design.json','components':['U14403','R14408','R14409','R14410','R14411'],
  'fact':'PWM/PEN AND gated with physical permission, FPGA inputs default LOW.'},
 'port_power':{'source':'hardware/motherboard_operator/design.json','components':['R14025','R14026','U14015','U14016'],
  'fact':'LOW request/default keeps frontend/accessory protected port switches OFF.'},
 'shift_idle':{'source':'hardware/motherboard_operator/design.json','components':['R14077','R14078'],
  'fact':'Clock LOW pulldown; load_n HIGH pullup. Reader unimplemented in this bounded wrapper.'},
 'common_controls':{'source':'hardware/motherboard_control_bridges/design.json','components':['R12001','R12002','R12003','R12004','R12005','R12006'],
  'fact':'OPI motor rearm and active-HIGH watchdog clear have LOW common-stem defaults; no strobe emitted. OUT independent rearm held LOW.'},
 'arm_lamp':{'source':'hardware/motherboard/design.json','components':['U19017'],
  'fact':'ISO7720F command path default LOW. Lamp request remains LOW.'},
 'fault_test_pins':{'source':'hardware/motherboard/design.json','components':['TP22001','TP22002','TP22003','TP22004'],
  'fact':'Bare diagnostic test points only, no field/motion authority. Historical cnc_motherboard_motion_bringup defines active-HIGH faults; four asserted pins explicitly identify unqualified diagnostic image.'},
 'SPI':{'source':'selected cnc3_spi_transport_stateful.v and cnc_iol1_record_master.v',
  'fact':'Existing mode0 masters reset CS high, SCLK/MOSI low. Host MISO raw reset/CS-dependent OE retained, inferred top tri-state requires later vendor IO implementation review.'},
}
(OUT/'electrical-idle-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
(OUT/'output-safe-drive-manifest.json').write_text(json.dumps(outputs,indent=2)+'\n')
(OUT/'input-observation-order.json').write_text(json.dumps({str(i):name for i,name in enumerate(observed)},indent=2)+'\n')
shutil.copyfile(pinfile,OUT/pinfile.name)
receipt={'status':'HDL_CANDIDATE_EMITTED_NOT_YET_COMPILED_OR_QUALIFIED','created_utc':datetime.now(timezone.utc).isoformat(),
 'top':'cnc3_physical_inhibited_diag','actual_top_ports':len(pins),'top_input_count':sum(p['direction']=='input' for p in pins),
 'top_output_count':len(outputs),'all_ports_match_actual135_pin_contract':True,
 'reused_RTL_SHA256':{str(p):sha(p) for p in source_files},'emitted_RTL_SHA256':{p.name:sha(p) for p in RTL.iterdir()},
 'pin_contract_SHA256':sha(pinfile),'electrical_inputs_SHA256':{str(ROOT/p):sha(ROOT/p) for p in ['hardware/mc_permission/design.json','hardware/motherboard/design.json','hardware/motherboard_process/design.json','hardware/motherboard_operator/design.json','hardware/motherboard_control_bridges/design.json','gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v']},
 'fitted_design_counts':{'motors':12,'ABZ':4,'DI':24,'DO':16},'qualification_claim':False,
 'physical_authority':False,'production_adopted':False,'canonical_sources_settings_archive_modified':False,
 'notes':['Distinct DGF1/DGS1 framing is unqualified read-only diagnostic data, not CNC3/SIM2 capabilities.',
  'Acquisition sends inherited diagnostic DIC CONFIG_WRITE and IDENT/polls; no output authority commands.',
  'Inherited record checker tests proposed MBR2 source lineage6ec697f7…; CRC/UID/shape observations are not current factory trust or authentication.',
  'No selftest or physical-safety/provider health values are invented. Actual raw GPIO observations are labelled individually.',
  'FAST_SR and protected port power requests remain idle; raw encoder counts remain unqualified. No standalone full production wrapper/fit proof.']}
(OUT/'construction-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'ports':len(pins),'outputs':len(outputs),'top_SHA256':sha(top)}))
