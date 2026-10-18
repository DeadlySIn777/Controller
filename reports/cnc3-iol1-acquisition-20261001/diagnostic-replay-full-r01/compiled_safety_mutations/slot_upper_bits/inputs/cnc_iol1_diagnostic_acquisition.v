`timescale 1ns/1ps
// Read-only observations from actual physical IOL1 response bits.
// SYNCED diagnostic binding is NEVER commercial ACTIVE/factory qualification.
module cnc_iol1_diagnostic_acquisition #(
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
    output wire [63:0] analog_codes
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
    genvar g;
    generate for(g=0;g<4;g=g+1)begin: lane
        cnc_iol1_acquisition_master #(.CLASS_ID(g==0?8'h11:g==3?8'h31:8'h21),.SLOT_ID(g),.EPOCH(EPOCH)) master(
            .clk(clk),.reset_n(reset_n),.enable(enable),.miso(miso[g]),
            .cs_n(cs_n[g]),.sclk(sclk[g]),.mosi(mosi[g]),.accepted(accepted[g]),.fault_latched(fault_latched[g]),
            .frame_seen(frame_seen[g]),.header_crc_good(header_good[g]),.checked_frame(frames[g]),
            .link_synced(synced[g]),.failed_polls(failures[g*2+:2]));
    end endgenerate
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
                    diagnostic_sample_valid[i]<=i!=3&&release_seen[i]&&{15'b0,age_sum[i]}<=STALE_US&&STALE_US>=250&&STALE_US<=440;
                end
                if(!enable||fault_latched[i])begin
                    diagnostic_sample_valid[i]<=0;diagnostic_transport_seen[i]<=0;
                end
            end
        end
    end
endmodule
