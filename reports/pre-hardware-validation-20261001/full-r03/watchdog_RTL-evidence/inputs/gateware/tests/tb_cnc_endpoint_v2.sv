`timescale 1ns/1ps
// Opt-in ABI v2 (ENABLE_DISCOVERY=1) build with production default parameters:
// capability page contents, one-shot consumption (including by rejected
// transactions), version enforcement and armed capability requests.
module tb_cnc_endpoint_v2;
    reg clk=0; always #10 clk=~clk;
    reg reset_n=0, inhibit_n=1, cs_n=1, sclk=0, mosi=0;
    reg [1:0] enc_a=0, enc_b=0, enc_z=0;
    wire miso, miso_oe, enabled, ready, link_fault, watchdog_fault, inhibit_fault, timing_fault, wdi;
    wire [5:0] steps, dirs;
    cnc_endpoint #(.ENABLE_DISCOVERY(1)) dut (
        .clk(clk), .reset_n(reset_n), .inhibit_n(inhibit_n),
        .spi_cs_n(cs_n), .spi_sclk(sclk), .spi_mosi(mosi),
        .spi_miso(miso), .spi_miso_oe(miso_oe),
        .enc_a(enc_a), .enc_b(enc_b), .enc_z(enc_z),
        .step_out(steps), .dir_out(dirs), .motion_enable(enabled), .endpoint_ready(ready),
        .link_fault(link_fault), .watchdog_fault(watchdog_fault),
        .inhibit_fault(inhibit_fault), .timing_fault(timing_fault),
        .progress_wdi(wdi)
    );
    reg [511:0] tx, rx;
    reg [31:0] session=32'h20304050;
    integer tests=0;
    reg wdi_before;
    // Counts every progress_wdi change after reset release, so an even number of
    // spurious toggles (which would restore the level) is still detected.
    integer wdi_toggles=0;
    always @(wdi) if (reset_n) wdi_toggles=wdi_toggles+1;
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
        input [7:0] version;
        input [7:0] op;
        input [5:0] mask;
        input [31:0] sid, seq;
        input signed [31:0] rate;
        reg [511:0] f;
        integer n;
        begin
            f=0; f[511:480]=32'h434e4331; f[479:472]=version; f[471:464]=op;
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
                #100; sclk=1; #1;
                if(n<512) response={response[510:0],miso};
                #99; sclk=0;
            end
            repeat(8) @(negedge clk);
            cs_n=1; mosi=0;
            repeat(10) @(negedge clk);
        end
    endtask
    // Complete transfer whose response must be ordinary v2 status.
    task send;
        input [511:0] data;
        begin
            transfer(data,512,rx);
            check(rx[511:480]==32'h434e5331 && rx[479:472]==2 && rx[15:0]==crc(rx[511:16]),
                "v2 ordinary status magic/version/CRC");
        end
    endtask
    function is_caps;
        input [511:0] r;
        begin
            is_caps = r[511:480]==32'h434e4332 && r[479:472]==2 && r[15:0]==crc(r[511:16]);
        end
    endfunction
    initial begin
        repeat(10) @(negedge clk); reset_n=1;
        repeat(10) @(negedge clk);
        check(!enabled && !ready && steps==0 && wdi===0, "v2 reset is disarmed with progress WDI clear");
        send(command(2,0,0,0,0,0));
        check(!link_fault, "v2 NOP accepted");
        // Discovery: opcode 5's own response is the prior snapshot; the next NOP is the page.
        send(command(2,5,0,0,0,0));
        check(!link_fault && !enabled, "capability request accepted while disarmed");
        transfer(command(2,0,0,0,0,0),512,rx);
        check(is_caps(rx), "next transaction returns the CNC2 capability page");
        check(rx[471:464]==6 && rx[463:456]==2 && rx[455:448]==0 && rx[447:416]==32'h0000001f &&
            rx[415:384]==50000000 && rx[383:352]==32'h01000000 &&
            rx[351:336]==100 && rx[335:320]==100 && rx[319:304]==100 && rx[303:288]==100 &&
            rx[287:256]==250000 && rx[255:16]==0,
            "capability page reports production parameters and zero reserved bytes");
        send(command(2,0,0,0,0,0));
        check(!link_fault, "ordinary status resumes after one capability page");
        // A rejected transaction consumes the pending page.
        send(command(2,5,0,0,0,0));
        tx=command(2,0,0,0,0,0); tx[0]=~tx[0];
        transfer(tx,512,rx);
        check(is_caps(rx) && link_fault, "bad-CRC frame after request receives the page and latches link fault");
        transfer(command(2,0,0,0,0,0),512,rx);
        check(!is_caps(rx) && rx[511:480]==32'h434e5331 && rx[15:0]==crc(rx[511:16]),
            "rejected transaction consumes the pending capability page");
        // A truncated transaction (early CS release) also consumes it.
        send(command(2,5,0,0,0,0));
        transfer(command(2,0,0,0,0,0),400,rx);
        transfer(command(2,0,0,0,0,0),512,rx);
        check(!is_caps(rx) && rx[511:480]==32'h434e5331 && rx[15:0]==crc(rx[511:16]),
            "truncated transaction consumes the pending capability page");
        check(wdi===0 && wdi_toggles==0,
            "disarmed capability requests and page reads do not toggle progress WDI");
        // Version enforcement.
        session=session+1;
        send(command(2,1,0,session,0,0));
        check(ready && !link_fault && !enabled, "v2 SYNC clears faults");
        send(command(1,0,0,0,0,0));
        check(link_fault && !ready, "v1 command rejected by v2 endpoint");
        // Capability request while armed is a protocol fault and serves no page.
        session=session+1;
        send(command(2,1,0,session,0,0));
        send(command(2,2,63,session,1,0));
        check(enabled && steps==0, "v2 ARM is zero-speed and enabled");
        wdi_before=wdi;
        send(command(2,3,63,session,2,32'h00800000));
        check(enabled && wdi===~wdi_before, "v2 accepted UPDATE toggles progress WDI");
        wdi_before=wdi;
        send(command(2,5,0,0,0,0));
        check(link_fault && !enabled && steps==0 && wdi===wdi_before,
            "armed capability request disarms without toggling progress WDI");
        transfer(command(2,0,0,0,0,0),512,rx);
        check(!is_caps(rx) && rx[511:480]==32'h434e5331 && link_fault,
            "armed capability request serves no capability page");
        $display("ALL %0d V2 CHECKS PASSED", tests);
        $finish;
    end
    initial begin #20000000; $fatal(1,"v2 testbench timeout"); end
endmodule
