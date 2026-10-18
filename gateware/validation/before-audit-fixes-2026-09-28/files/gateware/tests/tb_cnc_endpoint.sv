`timescale 1ns/1ps
module tb_cnc_endpoint;
    reg clk=0; always #10 clk=~clk;
    reg reset_n=0, inhibit_n=1, cs_n=1, sclk=0, mosi=0;
    reg [1:0] enc_a=0, enc_b=0, enc_z=0;
    wire miso, miso_oe, enabled, ready, link_fault, watchdog_fault, inhibit_fault, timing_fault;
    wire [5:0] steps, dirs;
    cnc_endpoint #(.WATCHDOG_CYCLES(20000)) dut (
        .clk(clk), .reset_n(reset_n), .inhibit_n(inhibit_n),
        .spi_cs_n(cs_n), .spi_sclk(sclk), .spi_mosi(mosi),
        .spi_miso(miso), .spi_miso_oe(miso_oe),
        .enc_a(enc_a), .enc_b(enc_b), .enc_z(enc_z),
        .step_out(steps), .dir_out(dirs), .motion_enable(enabled), .endpoint_ready(ready),
        .link_fault(link_fault), .watchdog_fault(watchdog_fault),
        .inhibit_fault(inhibit_fault), .timing_fault(timing_fault)
    );
    reg [511:0] tx, rx, previous_rx;
    reg [511:0] golden [0:2];
    reg [31:0] session=32'h10203040;
    integer tests=0, cycle=0, k, before_count, snap_count;
    integer spi_half_ns=100;
    integer status_fd;
    integer last_rise[0:5], last_fall[0:5], last_dir[0:5], observed_steps[0:5];
    reg [5:0] old_steps=0, old_dirs=0;
    reg was_enabled=0;
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
    task transfer;
        input [511:0] data;
        input integer nbits;
        output reg [511:0] response;
        integer n;
        begin
            response=0;
            @(negedge clk); cs_n=0; sclk=0;
            repeat(8) @(negedge clk);
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
    // Check all six emitted channels continuously, including rate changes.
    always @(negedge clk) begin
        cycle=cycle+1;
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
        for(k=0;k<6;k=k+1) begin last_rise[k]=-1; last_fall[k]=-1; last_dir[k]=-1; observed_steps[k]=0; end
        $readmemh("tests/vectors.hex",golden);
        check(command(0,0,0,0,0)==golden[0], "independent Python CRC golden NOP");
        check(command(1,0,32'h10203041,0,0)==golden[1], "independent Python SYNC vector");
        check(command(2,63,32'h10203041,1,0)==golden[2], "independent Python ARM vector");
        repeat(10) @(negedge clk); reset_n=1;
        repeat(10) @(negedge clk);
        check(!enabled && !ready && steps==0 && !miso_oe, "reset is disarmed and MISO released");
        send(command(2,63,session,1,0));
        check(link_fault && !enabled, "ARM without SYNC rejected");
        sync_new(); arm();
        send(command(3,63,session,2,32'h01000000));
        repeat(2048) @(negedge clk);
        check(enabled && !timing_fault && dut.step_counts[0]>=7, "six-axis positive DDS motion");
        for(k=0;k<6;k=k+1) check(observed_steps[k]>0, "every step output has emitted pulses");
        before_count=dut.step_counts[0];
        send(command(3,63,session,3,-32'h01000000));
        before_count=dut.step_counts[0];
        repeat(2048) @(negedge clk);
        check(dirs==63 && dut.step_counts[0]<before_count && !timing_fault, "reverse obeys direction guards");
        send(command(4,0,session,4,0));
        check(!enabled && steps==0, "explicit DISARM disables all outputs");
        spi_half_ns=80;
        send(command(0,0,0,0,0));
        check(!link_fault, "SPI core/8 maximum reference clock passes");
        spi_half_ns=100;
        sync_new(); arm(); send(command(3,63,session,2,32'h01000000));
        transfer(command(3,63,session,3,0),400,rx);
        check(link_fault && !enabled && steps==0, "truncated UPDATE disables active motion");
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
        sync_new(); arm(); send(command(3,63,session,1,0));
        check(link_fault && !enabled, "duplicate sequence disarms");
        sync_new(); arm(); send(command(3,63,session,3,0));
        check(link_fault && !enabled, "out-of-order sequence disarms");
        sync_new(); arm(); send(command(3,63,session,2,32'h01000001));
        check(link_fault && !enabled, "out-of-range rate rejected");
        sync_new(); arm(); send(command(3,1,session,2,0));
        check(link_fault && !enabled, "UPDATE cannot change arm mask");
        sync_new(); send(command(2,63,session,1,1));
        check(link_fault && !enabled, "nonzero ARM velocity rejected");
        sync_new(); arm(); send(command(3,63,session,2,32'h01000000));
        repeat(20010) @(negedge clk);
        check(watchdog_fault && !enabled && steps==0, "watchdog expires and disables");
        send(command(3,63,session,3,0));
        check(!enabled && watchdog_fault && link_fault, "UPDATE cannot auto-rearm after timeout");
        sync_new(); arm();
        // Four NOP transfers exceed the 20,000-clock watchdog; reads cannot keep motion armed.
        repeat(4) send(command(0,0,0,0,0));
        check(watchdog_fault && !enabled, "NOP status reads do not feed watchdog");
        sync_new(); arm(); send(command(3,63,session,2,32'h01000000));
        @(negedge clk); #2 inhibit_n=0; #1;
        check(!enabled && steps==0, "external inhibit gates asynchronously");
        #2 inhibit_n=1;
        repeat(12) @(negedge clk);
        check(inhibit_fault && !enabled, "sub-clock inhibit pulse is latched");
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
        sync_new();
        // Reset in the middle of an ARM transaction; subsequent suffix cannot arm.
        @(negedge clk); cs_n=0; repeat(8) @(negedge clk);
        tx=command(2,63,session,1,0);
        for(k=511;k>=256;k=k-1) begin mosi=tx[k]; #100; sclk=1; #100; sclk=0; end
        reset_n=0; repeat(8) @(negedge clk); reset_n=1; repeat(8) @(negedge clk);
        for(k=255;k>=0;k=k-1) begin mosi=tx[k]; #100; sclk=1; #100; sclk=0; end
        repeat(8) @(negedge clk); cs_n=1; repeat(10) @(negedge clk);
        check(!enabled && steps==0 && dut.session_id==0, "reset mid-frame cannot arm");
        $display("ALL %0d CHECKS PASSED; pulse timing monitors passed on six channels", tests);
        $finish;
    end
    initial begin #100000000; $fatal(1,"testbench timeout"); end
endmodule
