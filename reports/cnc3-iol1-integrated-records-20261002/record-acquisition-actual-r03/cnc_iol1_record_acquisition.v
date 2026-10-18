`timescale 1ns/1ps
// Read-only observations from actual physical IOL1 response bits.
// SYNCED diagnostic binding is NEVER commercial ACTIVE/factory qualification.
module cnc_iol1_record_acquisition #(
    parameter [3:0] HARDWARE_MAJOR=1,
    parameter [15:0] EPOCH = 16'h51a7,
    parameter integer STALE_US = 440
) (
    input wire clk, input wire reset_n, input wire enable,
    input wire [3:0] miso,
    output wire [3:0] cs_n, sclk, mosi,
    output wire [3:0] fault_latched, accepted,
    output reg [3:0] diagnostic_sample_valid,
    output reg [3:0] diagnostic_transport_seen,
    output wire [3:0] commercial_active,
    output wire [3:0] factory_identity_verified,
    output reg [511:0] last_valid_realtime,
    output reg [511:0] last_integrity_realtime,
    output reg [63:0] sample_age_us,
    output reg [63:0] last_reply_sequence,
    output reg [11:0] last_reply_state,
    output wire [23:0] diagnostic_filtered_di, diagnostic_raw_di,
    output wire [15:0] diagnostic_do_applied,
    output wire [3:0] analog_valid,
    output wire [63:0] analog_codes,
    output wire [3:0] record_integrity_observed,record_failed,
    output wire [511:0] observed_board_serial,output wire [383:0] observed_mcu_uid,
    output wire [127:0] observed_generation,
    output wire [3:0] chunk_accepted,output wire [23:0] chunk_index,output wire [255:0] chunk_data,
    output reg dic_configuration_echo_valid,output reg[31:0] dic_configuration_crc,
    output wire signature_authenticated
);
    assign commercial_active=0;
    assign factory_identity_verified=0;
    // This actual image observes held-reset ADC/DAC. No cached zero is valid.
    assign analog_valid=0;
    assign analog_codes=0;
    assign diagnostic_filtered_di={last_valid_realtime[495:488],last_valid_realtime[503:496],last_valid_realtime[511:504]};
    assign diagnostic_raw_di={last_valid_realtime[471:464],last_valid_realtime[479:472],last_valid_realtime[487:480]};
    assign diagnostic_do_applied={last_valid_realtime[255:248],last_valid_realtime[383:376]};
    wire [3:0] frame_seen,header_good,synced;
    wire [7:0] failures;
    wire [319:0] frames[0:3];
    wire[3:0] operation_sent;wire[7:0] sent_control[0:3],accepted_control[0:3];wire[5:0] accepted_chunk[0:3];
    reg[7:0] request_control[0:3];wire[207:0] request_payload[0:3];reg[6:0] next_request[0:3];reg[3:0] config_sent;
    localparam[207:0] DIC_CONFIG={8'd0,8'd1,8'd1,8'd2,8'd3,168'd0};
    function[31:0] config_crc;input[191:0] blob;reg[31:0] c;integer n,k;reg[7:0] b;
      begin c=32'hffffffff;for(n=0;n<24;n=n+1)begin b=blob[191-n*8-:8];for(k=0;k<8;k=k+1)c=(c[0]^b[k])?((c>>1)^32'h82f63b78):(c>>1);end config_crc=c^32'hffffffff;end
    endfunction
    localparam[31:0] EXPECTED_CONFIG_CRC=config_crc({8'd1,8'd1,8'd2,8'd3,160'd0});
    integer sched;
    always @*for(integer n=0;n<4;n=n+1)begin
      if(n==0&&!config_sent[0])request_control[n]=8'h10;
      else if(next_request[n]<64)request_control[n]=8'h08;
      else request_control[n]=0;
    end
    genvar g;
    generate for(g=0;g<4;g=g+1)begin: lane
        cnc_iol1_record_master #(.HARDWARE_MAJOR(HARDWARE_MAJOR),.CLASS_ID(g==0?8'h11:g==3?8'h31:8'h21),.SLOT_ID(g),.EPOCH(EPOCH)) master(
            .clk(clk),.reset_n(reset_n),.enable(enable),.miso(miso[g]),
            .request_control(request_control[g]),.request_payload(request_payload[g]),
            .operation_sent(operation_sent[g]),.sent_control(sent_control[g]),
            .accepted_control(accepted_control[g]),.accepted_chunk(accepted_chunk[g]),
            .cs_n(cs_n[g]),.sclk(sclk[g]),.mosi(mosi[g]),.accepted(accepted[g]),.fault_latched(fault_latched[g]),
            .frame_seen(frame_seen[g]),.header_crc_good(header_good[g]),.checked_frame(frames[g]),
            .link_synced(synced[g]),.failed_polls(failures[g*2+:2]));
        assign request_payload[g]=(g==0&&!config_sent[0])?DIC_CONFIG:next_request[g]<64?{2'b0,next_request[g][5:0],200'd0}:208'd0;
        assign chunk_accepted[g]=accepted[g]&&accepted_control[g]==8'h08;
        assign chunk_index[g*6+:6]=accepted_chunk[g];
        assign chunk_data[g*64+:64]=frames[g][95:32];
    end endgenerate
    cnc_mbr2_stream_checker #(.HARDWARE_MAJOR(HARDWARE_MAJOR)) record_check(
      .clk(clk),.reset_n(reset_n),.enable(enable),.lane_fault(fault_latched),
      .chunk_accepted(chunk_accepted),.chunk_index(chunk_index),.chunk_data(chunk_data),
      .record_integrity_observed(record_integrity_observed),.record_failed(record_failed),
      .observed_board_serial(observed_board_serial),.observed_mcu_uid(observed_mcu_uid),.observed_generation(observed_generation),
      .signature_authenticated(signature_authenticated),.factory_identity_verified(),.commercial_active());
    always @(posedge clk or negedge reset_n)begin
      if(!reset_n)begin
        config_sent<=0;dic_configuration_echo_valid<=0;dic_configuration_crc<=0;
        for(sched=0;sched<4;sched=sched+1)next_request[sched]<=0;
      end else begin
        for(sched=0;sched<4;sched=sched+1)if(operation_sent[sched])begin
          if(sent_control[sched]==8'h10)config_sent[sched]<=1;
          else if(sent_control[sched]==8'h08&&next_request[sched]<64)next_request[sched]<=next_request[sched]+1;
        end
        if(accepted[0]&&accepted_control[0]==8'h10)begin
          dic_configuration_crc<=frames[0][63:32];dic_configuration_echo_valid<=frames[0][63:32]==EXPECTED_CONFIG_CRC;
        end
        if(!enable||fault_latched[0])dic_configuration_echo_valid<=0;
      end
    end
    // One shared exact 50 MHz -> microsecond timebase; no four-way division.
    reg [5:0] us_div;
    
    reg [3:0] previous_cs;
    reg [15:0] residence_us[0:3],reply_elapsed_us[0:3];
    reg [3:0] release_seen;
    reg [15:0] age[0:3];
    wire [15:0] reported_age[0:3];
    wire [16:0] age_sum[0:3];
    generate for(genvar a=0;a<4;a=a+1)begin: ages_calc
        assign reported_age[a]=a==0?frames[a][191:176]:a==3?frames[a][143:128]:frames[a][175:160];
        assign age_sum[a]={1'b0,reported_age[a]}+{1'b0,reply_elapsed_us[a]};
    end endgenerate
    integer i;
    always @* begin
        for(integer k=0;k<4;k=k+1)sample_age_us[k*16+:16]=age[k];
    end
    always @(posedge clk or negedge reset_n)begin
        if(!reset_n)begin
            us_div<=0;previous_cs<=15;release_seen<=0;
            diagnostic_sample_valid<=0;diagnostic_transport_seen<=0;
            last_valid_realtime<=0;last_integrity_realtime<=0;last_reply_sequence<=0;last_reply_state<=0;
            for(i=0;i<4;i=i+1)begin age[i]<=16'hffff;residence_us[i]<=16'hffff;reply_elapsed_us[i]<=16'hffff;end
        end else begin
            if(us_div==49)begin us_div<=0;end
            else us_div<=us_div+1;
            previous_cs<=cs_n;
            for(i=0;i<4;i=i+1)begin
                // Target prepares this reply only after the PREVIOUS CS release.
                // Add the measured residence+wire interval, plus one us for
                // phase quantization. Initial/preboot sample cannot qualify.
                if(us_div==49&&residence_us[i]!=16'hffff)residence_us[i]<=residence_us[i]+1;
                if(cs_n[i]&&!previous_cs[i])begin
                    reply_elapsed_us[i]<=release_seen[i]&&residence_us[i]!=16'hffff ? residence_us[i]+16'd1 : 16'hffff;
                    residence_us[i]<=0;release_seen[i]<=1;
                end
                if(us_div==49&&age[i]!=16'hffff)age[i]<=age[i]+1;
                if({16'b0,age[i]}>STALE_US||(us_div==49&&{16'b0,age[i]}>=STALE_US))diagnostic_sample_valid[i]<=0;
                if(frame_seen[i]&&header_good[i])begin
                    diagnostic_transport_seen[i]<=1;
                    last_integrity_realtime[511-i*128-:128]<=frames[i][239:112];
                    last_reply_sequence[i*16+:16]<=frames[i][271:256];
                    last_reply_state[i*3+:3]<=frames[i][250:248];
                    // Trusted fault/power/unavailable observation invalidates
                    // immediately, not after a third CRC rejection.
                    if(!accepted[i])diagnostic_sample_valid[i]<=0;
                end
                if(accepted[i])begin
                    last_valid_realtime[511-i*128-:128]<=frames[i][239:112];
                    age[i]<=age_sum[i]>=17'd65535 ? 16'hffff : age_sum[i][15:0];
                    diagnostic_sample_valid[i]<=i!=3&&(i!=0||dic_configuration_echo_valid)&&release_seen[i]&&{15'b0,age_sum[i]}<=STALE_US&&STALE_US>=250&&STALE_US<=440;
                end
                if(!enable||fault_latched[i])begin
                    diagnostic_sample_valid[i]<=0;diagnostic_transport_seen[i]<=0;
                end
            end
        end
    end
endmodule
