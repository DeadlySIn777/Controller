`timescale 1ns/1ps
module tb_cnc_endpoint;
    reg clk=0; always #10 clk=~clk;
    reg reset_n=0, inhibit_n=1, cs_n=1, sclk=0, mosi=0;
    reg [1:0] enc_a=0, enc_b=0, enc_z=0;
    wire miso, miso_oe, enabled, ready, link_fault, watchdog_fault, inhibit_fault, timing_fault;
    wire wdi;
    wire [5:0] steps, dirs;
    cnc_endpoint #(.WATCHDOG_CYCLES(20000)) dut (
        .clk(clk), .reset_n(reset_n), .inhibit_n(inhibit_n),
        .spi_cs_n(cs_n), .spi_sclk(sclk), .spi_mosi(mosi),
        .spi_miso(miso), .spi_miso_oe(miso_oe),
        .enc_a(enc_a), .enc_b(enc_b), .enc_z(enc_z),
        .step_out(steps), .dir_out(dirs), .motion_enable(enabled), .endpoint_ready(ready),
        .link_fault(link_fault), .watchdog_fault(watchdog_fault),
        .inhibit_fault(inhibit_fault), .timing_fault(timing_fault),
        .progress_wdi(wdi)
    );
    // Standalone generator at the documented fault-free rate bound (production timing defaults).
    reg bound_en=0;
    reg signed [31:0] bound_rate=0;
    wire bound_step, bound_dir, bound_fault;
    wire signed [31:0] bound_count;
    cnc_stepgen bound_gen (.clk(clk), .rst_n(reset_n), .enable(bound_en), .rate(bound_rate),
        .step(bound_step), .dir(bound_dir), .count(bound_count), .timing_fault(bound_fault));
    reg [511:0] tx, rx, previous_rx;
    reg [511:0] golden [0:2];
    reg [31:0] session=32'h10203040;
    integer tests=0, cycle=0, k, before_count, snap_count;
    integer spi_half_ns=100;
    integer status_fd;
    integer last_rise[0:5], last_fall[0:5], last_dir[0:5], observed_steps[0:5];
    reg [5:0] old_steps=0, old_dirs=0, old_raw=0;
    reg was_enabled=0;
    // Useful-progress WDI toggle accounting (sampled on the inactive clock edge).
    integer wdi_toggles=0, wdi_mark=0;
    reg old_wdi=1'bx;
    // Signed count of internal generator rising edges, for pulse-counter accounting.
    integer raw_edges[0:5];
    // Standalone bound generator: pulses and minimum rising-edge period.
    integer bound_pulses=0, bound_last_rise=-1, bound_min_period=1000000;
    reg old_bound_step=0;
    // MISO turnaround monitor: data setup before, and hold after, each SCLK rise.
    realtime last_miso_change=0, last_sclk_rise=-1;
    realtime min_setup=1.0e9, min_hold=1.0e9, window_setup=1.0e9, window_hold=1.0e9;
    integer spi_skew_ns=0, sampled_rises=0;
    function [15:0] crc;
        input [495:0] payload;
        reg [15:0] c;
        integer n;
        begin
            c=16'hffff;
            for(n=495;n>=0;n=n-1) begin
                if(c[15]^payload[n]) c={c[14:0],1'b0}^16'h1021;
                else c={c[14:0],1'b0};
            end
            crc=c;
        end
    endfunction
    function [511:0] command;
        input [7:0] op;
        input [5:0] mask;
        input [31:0] sid, seq;
        input signed [31:0] rate;
        reg [511:0] f;
        integer n;
        begin
            f=0; f[511:480]=32'h434e4331; f[479:472]=1; f[471:464]=op;
            f[461:456]=mask; f[447:416]=sid; f[415:384]=seq;
            for(n=0;n<6;n=n+1) if(mask[n]) f[383-n*32 -:32]=rate;
            f[15:0]=crc(f[511:16]); command=f;
        end
    endfunction
    task check;
        input condition; input [8*120-1:0] label;
        begin
            tests=tests+1;
            if(condition !== 1'b1) begin $display("FAIL %0s at %0t", label, $time); $fatal(1); end
            $display("PASS %0s", label);
        end
    endtask
    task wdi_expect;
        input integer delta; input [8*120-1:0] label;
        begin
            check(wdi_toggles-wdi_mark==delta && wdi===wdi_toggles[0], label);
            wdi_mark=wdi_toggles;
        end
    endtask
    task transfer;
        input [511:0] data;
        input integer nbits;
        output reg [511:0] response;
        integer n;
        begin
            response=0;
            @(negedge clk); cs_n=0; sclk=0;
            repeat(8) @(negedge clk);
            // Optional skew so SCLK edges do not align with core-clock edges.
            if(spi_skew_ns>0) #(spi_skew_ns);
            for(n=0;n<nbits;n=n+1) begin
                mosi=(n<512) ? data[511-n] : 0;
                #(spi_half_ns); sclk=1; #1;
                if(n<512) response={response[510:0],miso};
                #(spi_half_ns-1); sclk=0;
            end
            repeat(8) @(negedge clk);
            cs_n=1; mosi=0;
            repeat(10) @(negedge clk);
        end
    endtask
    task send;
        input [511:0] data;
        begin
            transfer(data,512,rx);
            check(rx[511:480]==32'h434e5331 && rx[479:472]==1, "status magic/version");
            check(rx[15:0]==crc(rx[511:16]), "status CRC");
        end
    endtask
    task sync_new;
        begin
            session=session+1;
            send(command(1,0,session,0,0));
            check(ready && !enabled && !link_fault && !watchdog_fault && !inhibit_fault,
                "fresh disarmed SYNC clears faults");
        end
    endtask
    task arm;
        begin
            send(command(2,63,session,1,0));
            check(enabled && steps==0, "ARM is zero-speed and enabled");
        end
    endtask
    task encoder_state;
        input [1:0] a, b, z;
        begin
            @(negedge clk); enc_a=a; enc_b=b; enc_z=z;
            repeat(8) @(negedge clk);
        end
    endtask
    // MISO data must be stable before each SCLK rise (setup) and must not change
    // until well after it (hold). Measured only while CS is asserted.
    always @(negedge cs_n) last_sclk_rise=-1;
    always @(posedge sclk) if(!cs_n) begin
        if($realtime-last_miso_change<min_setup) min_setup=$realtime-last_miso_change;
        if($realtime-last_miso_change<window_setup) window_setup=$realtime-last_miso_change;
        last_sclk_rise=$realtime; sampled_rises=sampled_rises+1;
    end
    always @(miso) if(!cs_n) begin
        if(last_sclk_rise>=0 && $realtime-last_sclk_rise<min_hold) min_hold=$realtime-last_sclk_rise;
        if(last_sclk_rise>=0 && $realtime-last_sclk_rise<window_hold) window_hold=$realtime-last_sclk_rise;
        last_miso_change=$realtime;
    end
    // Check all six emitted channels continuously, including rate changes.
    always @(negedge clk) begin
        cycle=cycle+1;
        if(old_wdi!==1'bx && wdi!==old_wdi) wdi_toggles=wdi_toggles+1;
        old_wdi=wdi;
        for(integer n=0;n<6;n=n+1) begin
            if(!dut.rst_n) raw_edges[n]=0;
            else if(dut.steps_raw[n] && !old_raw[n]) raw_edges[n]=raw_edges[n]+(dut.dirs_raw[n] ? -1 : 1);
        end
        old_raw=dut.steps_raw;
        if(bound_step && !old_bound_step) begin
            if(bound_last_rise>=0 && cycle-bound_last_rise<bound_min_period) bound_min_period=cycle-bound_last_rise;
            bound_last_rise=cycle; bound_pulses=bound_pulses+1;
        end
        old_bound_step=bound_step;
        for(integer n=0;n<6;n=n+1) begin
            if(enabled && was_enabled) begin
                if(dirs[n]!=old_dirs[n]) begin
                    if(last_rise[n]>=0 && cycle-last_rise[n]<100) $fatal(1,"DIR hold violation");
                    last_dir[n]=cycle;
                end
                if(steps[n] && !old_steps[n]) begin
                    if(last_fall[n]>=0 && cycle-last_fall[n]<100) $fatal(1,"STEP low width violation");
                    if(last_dir[n]>=0 && cycle-last_dir[n]<100) $fatal(1,"DIR setup violation");
                    last_rise[n]=cycle; observed_steps[n]=observed_steps[n]+1;
                end
                if(!steps[n] && old_steps[n]) begin
                    if(cycle-last_rise[n]!=100) $fatal(1,"STEP high width violation");
                    last_fall[n]=cycle;
                end
            end else begin
                last_rise[n]=-1; last_fall[n]=-1; last_dir[n]=-1;
            end
        end
        if(!enabled && steps!=0) $fatal(1,"STEP active while disabled");
        old_steps=steps; old_dirs=dirs; was_enabled=enabled;
    end
    initial begin
        for(k=0;k<6;k=k+1) begin last_rise[k]=-1; last_fall[k]=-1; last_dir[k]=-1; observed_steps[k]=0; raw_edges[k]=0; end
        $readmemh("tests/vectors.hex",golden);
        check(command(0,0,0,0,0)==golden[0], "independent Python CRC golden NOP");
        check(command(1,0,32'h10203041,0,0)==golden[1], "independent Python SYNC vector");
        check(command(2,63,32'h10203041,1,0)==golden[2], "independent Python ARM vector");
        repeat(10) @(negedge clk); reset_n=1;
        repeat(10) @(negedge clk);
        check(!enabled && !ready && steps==0 && !miso_oe, "reset is disarmed and MISO released");
        check(wdi===0 && wdi_toggles==0, "progress WDI is clear after reset");
        // Fault-free DDS bound: minimum STEP period is PULSE+SPACE+1 core ticks.
        check({32'd0, dut.MAX_RATE} <= (64'd1<<32)/(dut.PULSE_CYCLES+dut.SPACE_CYCLES+1),
            "configured MAX_RATE <= floor(2^32/(PULSE+SPACE+1))");
        repeat(5000) @(negedge clk);
        wdi_expect(0, "free-running clock does not toggle progress WDI");
        send(command(2,63,session,1,0));
        check(link_fault && !enabled, "ARM without SYNC rejected");
        sync_new(); arm();
        wdi_expect(0, "rejected ARM, SYNC and ARM do not toggle progress WDI");
        send(command(3,63,session,2,32'h01000000));
        wdi_expect(1, "accepted UPDATE toggles progress WDI exactly once");
        repeat(2048) @(negedge clk);
        check(enabled && !timing_fault && dut.step_counts[0]>=7, "six-axis positive DDS motion");
        for(k=0;k<6;k=k+1) check(observed_steps[k]>0, "every step output has emitted pulses");
        wdi_expect(0, "armed free-running motion does not toggle progress WDI");
        before_count=dut.step_counts[0];
        send(command(3,63,session,3,-32'h01000000));
        wdi_expect(1, "accepted UPDATE toggles progress WDI exactly once");
        before_count=dut.step_counts[0];
        repeat(2048) @(negedge clk);
        check(dirs==63 && dut.step_counts[0]<before_count && !timing_fault, "reverse obeys direction guards");
        send(command(4,0,session,4,0));
        check(!enabled && steps==0, "explicit DISARM disables all outputs");
        wdi_expect(0, "DISARM does not toggle progress WDI");
        spi_half_ns=80;
        send(command(0,0,0,0,0));
        check(!link_fault, "SPI core/8 maximum reference clock passes");
        // Core/8 at three SCLK-to-core-clock phases: MISO must change after the
        // rise and be stable for at least three core ticks before the next rise.
        window_setup=1.0e9; window_hold=1.0e9;
        spi_skew_ns=7; send(command(0,0,0,0,0));
        spi_skew_ns=13; send(command(0,0,0,0,0));
        spi_skew_ns=0; send(command(0,0,0,0,0));
        check(!link_fault && window_setup>=60.0 && window_hold>=40.0,
            "core/8 MISO setup >= 3 and hold >= 2 core ticks at three clock phases");
        wdi_expect(0, "NOP status reads do not toggle progress WDI");
        spi_half_ns=100;
        sync_new(); arm(); send(command(3,63,session,2,32'h01000000));
        wdi_expect(1, "accepted UPDATE toggles progress WDI exactly once");
        transfer(command(3,63,session,3,0),400,rx);
        check(link_fault && !enabled && steps==0, "truncated UPDATE disables active motion");
        wdi_expect(0, "truncated UPDATE does not toggle progress WDI");
        sync_new();
        transfer(command(2,63,session,1,0),400,rx);
        check(link_fault && !enabled, "truncated ARM never enables");
        sync_new();
        tx=command(2,63,session,1,0); tx[0]=~tx[0]; send(tx);
        check(link_fault && !enabled, "bad CRC never enables");
        sync_new();
        transfer(command(2,63,session,1,0),513,rx);
        check(link_fault && !enabled, "overlong ARM never enables");
        sync_new();
        tx=command(2,63,session,1,0); tx[100]=1; tx[15:0]=crc(tx[511:16]); send(tx);
        check(link_fault && !enabled, "nonzero reserved payload rejected");
        sync_new(); send(command(8,63,session,1,0));
        check(link_fault && !enabled, "unknown opcode rejected");
        sync_new(); send(command(2,63,session+1,1,0));
        check(link_fault && !enabled, "wrong session rejected");
        wdi_expect(0, "rejected ARM frames do not toggle progress WDI");
        sync_new(); arm(); send(command(3,63,session+1,2,0));
        check(link_fault && !enabled, "wrong-session UPDATE disarms");
        wdi_expect(0, "wrong-session UPDATE does not toggle progress WDI");
        sync_new(); arm();
        tx=command(3,63,session,2,32'h01000000); tx[0]=~tx[0]; send(tx);
        check(link_fault && !enabled, "bad-CRC UPDATE disarms");
        wdi_expect(0, "bad-CRC UPDATE does not toggle progress WDI");
        sync_new(); arm(); send(command(3,63,session,1,0));
        check(link_fault && !enabled, "duplicate sequence disarms");
        wdi_expect(0, "replayed UPDATE does not toggle progress WDI");
        sync_new(); arm(); send(command(3,63,session,3,0));
        check(link_fault && !enabled, "out-of-order sequence disarms");
        wdi_expect(0, "out-of-order UPDATE does not toggle progress WDI");
        sync_new(); arm(); send(command(3,63,session,2,32'h01000001));
        check(link_fault && !enabled, "out-of-range rate rejected");
        wdi_expect(0, "over-rate UPDATE does not toggle progress WDI");
        sync_new(); arm(); send(command(3,1,session,2,0));
        check(link_fault && !enabled, "UPDATE cannot change arm mask");
        wdi_expect(0, "mask-changing UPDATE does not toggle progress WDI");
        sync_new(); send(command(2,63,session,1,1));
        check(link_fault && !enabled, "nonzero ARM velocity rejected");
        sync_new(); arm(); send(command(3,63,session,2,32'h01000000));
        wdi_expect(1, "accepted UPDATE toggles progress WDI exactly once");
        repeat(20010) @(negedge clk);
        check(watchdog_fault && !enabled && steps==0, "watchdog expires and disables");
        wdi_expect(0, "progress WDI is constant through watchdog expiry");
        send(command(3,63,session,3,0));
        check(!enabled && watchdog_fault && link_fault, "UPDATE cannot auto-rearm after timeout");
        wdi_expect(0, "UPDATE after watchdog timeout does not toggle progress WDI");
        sync_new(); arm();
        // Four NOP transfers exceed the 20,000-clock watchdog; reads cannot keep motion armed.
        repeat(4) send(command(0,0,0,0,0));
        check(watchdog_fault && !enabled, "NOP status reads do not feed watchdog");
        wdi_expect(0, "armed NOP reads do not toggle progress WDI");
        sync_new(); arm(); send(command(3,63,session,2,32'h01000000));
        wdi_expect(1, "accepted UPDATE toggles progress WDI exactly once");
        repeat(600) @(negedge clk);
        @(negedge clk); #2 inhibit_n=0; #1;
        check(!enabled && steps==0, "external inhibit gates asynchronously");
        #2 inhibit_n=1;
        // Synchronous consumers see the inhibit through the two-flop synchronizer.
        repeat(3) @(posedge clk); #1;
        check(!dut.permit_sync && !dut.endpoint_ready &&
            !dut.axes[0].stepgen.enable && !dut.axes[1].stepgen.enable && !dut.axes[2].stepgen.enable &&
            !dut.axes[3].stepgen.enable && !dut.axes[4].stepgen.enable && !dut.axes[5].stepgen.enable &&
            dut.status_payload[448]==0 && dut.status_payload[449]==0 && dut.status_payload[434]==1,
            "stepgen enables and status permission drop within three core clocks of inhibit");
        repeat(12) @(negedge clk);
        check(inhibit_fault && !enabled, "sub-clock inhibit pulse is latched");
        check(raw_edges[0]==dut.step_counts[0] && raw_edges[1]==dut.step_counts[1] &&
            raw_edges[2]==dut.step_counts[2] && raw_edges[3]==dut.step_counts[3] &&
            raw_edges[4]==dut.step_counts[4] && raw_edges[5]==dut.step_counts[5],
            "pulse counters equal internal STEP rising edges across inhibit");
        send(command(3,63,session,3,32'h01000000));
        check(!enabled && link_fault && inhibit_fault, "UPDATE after inhibit pulse cannot resume motion");
        wdi_expect(0, "UPDATE after inhibit does not toggle progress WDI");
        inhibit_n=0;
        send(command(1,0,session+1,0,0));
        check(inhibit_fault && !enabled && !ready, "SYNC cannot clear asserted inhibit");
        inhibit_n=1; repeat(10) @(negedge clk); sync_new();
        // Encoders keep counting when disarmed; both index channels latch position.
        encoder_state(0,3,0); encoder_state(3,3,0); encoder_state(3,0,0); encoder_state(0,0,0);
        check(dut.enc_counts[0]==4 && dut.enc_counts[1]==4, "both quadrature encoders count forward disarmed");
        encoder_state(0,0,3);
        check(dut.index_counts[0]==4 && dut.index_counts[1]==4 && dut.index_seen==3, "both index positions latch");
        encoder_state(3,0,0); encoder_state(3,3,0); encoder_state(0,3,0); encoder_state(0,0,0);
        check(dut.enc_counts[0]==0 && dut.enc_counts[1]==0, "both encoders count backward");
        encoder_state(3,3,0);
        check(dut.enc_invalid==3 && dut.enc_counts[0]==0, "invalid two-bit quadrature transition detected");
        send(command(0,0,0,0,0));
        check(rx[159:128]==0 && rx[127:96]==0 && rx[95:64]==4 && rx[63:32]==4,
            "encoder and index status layout");
        check(rx[31:24]==8'h33, "encoder diagnostic flags layout");
        status_fd=$fopen("build/status_encoder.hex", "w");
        if(!status_fd) $fatal(1,"cannot write status evidence");
        $fwrite(status_fd,"%0128h\n",rx); $fclose(status_fd);
        arm(); send(command(3,63,session,2,32'h01000000));
        snap_count=dut.step_counts[0]; send(command(0,0,0,0,0));
        check($signed(rx[351:320])>=snap_count && $signed(rx[351:320])<dut.step_counts[0],
            "status is immutable snapshot from transaction start");
        check(rx[447:416]==session && rx[415:384]==2, "status reports accepted session and sequence");
        // Hold CS forever after one byte: incomplete transfer cannot feed watchdog.
        @(negedge clk); cs_n=0; repeat(8) @(negedge clk);
        repeat(8) begin #100; sclk=1; #100; sclk=0; end
        repeat(21000) @(negedge clk);
        check(watchdog_fault && !enabled, "held CS cannot defeat watchdog");
        cs_n=1; repeat(10) @(negedge clk);
        check(link_fault, "held incomplete frame faults when CS releases");
        wdi_expect(1, "held CS adds no toggle beyond the accepted UPDATE");
        // Leave the WDI high, then prove FPGA reset clears it.
        sync_new(); arm(); send(command(3,63,session,2,0)); send(command(4,0,session,3,0));
        wdi_expect(1, "accepted UPDATE toggles progress WDI exactly once");
        check(wdi===1, "progress WDI is high before reset case");
        check(raw_edges[0]==dut.step_counts[0] && raw_edges[1]==dut.step_counts[1] &&
            raw_edges[2]==dut.step_counts[2] && raw_edges[3]==dut.step_counts[3] &&
            raw_edges[4]==dut.step_counts[4] && raw_edges[5]==dut.step_counts[5],
            "pulse counters equal internal STEP rising edges for the whole run");
        sync_new();
        // Reset in the middle of an ARM transaction; subsequent suffix cannot arm.
        @(negedge clk); cs_n=0; repeat(8) @(negedge clk);
        tx=command(2,63,session,1,0);
        for(k=511;k>=256;k=k-1) begin mosi=tx[k]; #100; sclk=1; #100; sclk=0; end
        reset_n=0; repeat(8) @(negedge clk); reset_n=1; repeat(8) @(negedge clk);
        for(k=255;k>=0;k=k-1) begin mosi=tx[k]; #100; sclk=1; #100; sclk=0; end
        repeat(8) @(negedge clk); cs_n=1; repeat(10) @(negedge clk);
        check(!enabled && steps==0 && dut.session_id==0, "reset mid-frame cannot arm");
        check(wdi===0, "FPGA reset clears progress WDI");
        $display("MISO minimum setup %0.1f ns, minimum hold %0.1f ns over %0d SCLK rises", min_setup, min_hold, sampled_rises);
        check(sampled_rises>30000 && min_setup>=60.0 && min_hold>=40.0,
            "MISO setup >= 3 and hold >= 2 core ticks at every sampled SCLK rise");
        // Rate bound: the largest fault-free increment runs at the 201-tick period;
        // a 250 ksteps/s increment (200-tick average) latches a timing fault.
        bound_rate=32'h01460CBC; bound_en=1;
        repeat(201*400) @(negedge clk);
        check(!bound_fault && bound_pulses>=390 && bound_min_period==201,
            "largest fault-free increment 0x01460CBC holds the 201-tick minimum period");
        bound_en=0; @(negedge clk); bound_rate=32'h0147AE14; bound_en=1;
        repeat(1000) @(negedge clk);
        check(bound_fault, "250 ksteps/s increment latches timing fault at 100/100 timing");
        $display("ALL %0d CHECKS PASSED; pulse timing monitors passed on six channels", tests);
        $finish;
    end
    initial begin #100000000; $fatal(1,"testbench timeout"); end
endmodule
