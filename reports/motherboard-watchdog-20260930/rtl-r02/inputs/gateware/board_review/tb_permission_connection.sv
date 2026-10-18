`timescale 1ns/1ps
// Digital connection model of the external permission circuit. This is not a
// transistor model, watchdog timer simulation, device fit or safety proof.
module permission_connection_model (
    input wire local_reset_n, cdone, external_permit, watchdog_ok,
    input wire endpoint_ready, motion_request,
    output wire inhibit_n, tx_permit, arm_latched
);
    assign inhibit_n = local_reset_n && cdone && external_permit && watchdog_ok;
    wire clear_n = inhibit_n && endpoint_ready;
    reg latch;
    always @(posedge motion_request or negedge clear_n)
        if (!clear_n) latch <= 1'b0;
        else latch <= 1'b1;
    assign arm_latched = latch;
    assign tx_permit = inhibit_n && latch && motion_request;
endmodule

module tb_permission_connection;
    reg clk=0, run_clock=1;
    always #10 if(run_clock) clk=~clk;
    reg local_reset_n=0, user_reset_n=0, cdone=0, external_permit=0, watchdog_ok=0;
    reg cs_n=1, sclk=0, mosi=0;
    wire inhibit_n, tx_permit, arm_latched, motion, ready, miso, miso_oe;
    wire link_fault, wd_fault, inhibit_fault, timing_fault, wdi;
    wire [5:0] steps,dirs;
    wire [5:0] driver_command = steps & {6{tx_permit}};
    cnc_endpoint dut (
        .clk(clk),.reset_n(user_reset_n),.inhibit_n(inhibit_n),
        .spi_cs_n(cs_n),.spi_sclk(sclk),.spi_mosi(mosi),.spi_miso(miso),.spi_miso_oe(miso_oe),
        .enc_a(2'b0),.enc_b(2'b0),.enc_z(2'b0),.step_out(steps),.dir_out(dirs),
        .motion_enable(motion),.endpoint_ready(ready),.link_fault(link_fault),
        .watchdog_fault(wd_fault),.inhibit_fault(inhibit_fault),.timing_fault(timing_fault),.progress_wdi(wdi)
    );
    permission_connection_model board (
        .local_reset_n(local_reset_n),.cdone(cdone),
        .external_permit(external_permit),.watchdog_ok(watchdog_ok),
        .endpoint_ready(ready),.motion_request(motion),.inhibit_n(inhibit_n),
        .tx_permit(tx_permit),.arm_latched(arm_latched)
    );
    integer tests=0, pulse_count=0, wdi_falls=0, saved_count, saved_falls;
    reg [31:0] session=32'h82000000;
    reg [511:0] rx;
    always @(posedge driver_command[0]) pulse_count=pulse_count+1;
    always @(negedge wdi) if(local_reset_n && user_reset_n) wdi_falls=wdi_falls+1;
    function [15:0] crc;
        input [495:0] data;
        reg [15:0] c;
        integer i;
        begin c=16'hffff;
            for(i=495;i>=0;i=i-1) c=(c[15]^data[i])?({c[14:0],1'b0}^16'h1021):{c[14:0],1'b0};
            crc=c;
        end
    endfunction
    function [511:0] command;
        input [7:0] op;
        input [5:0] mask;
        input [31:0] sid,seq;
        input signed [31:0] rate;
        reg [511:0] f;
        integer i;
        begin
            f=0;f[511:480]=32'h434e4331;f[479:472]=1;f[471:464]=op;
            f[461:456]=mask;f[447:416]=sid;f[415:384]=seq;
            for(i=0;i<6;i=i+1) if(mask[i]) f[383-i*32 -:32]=rate;
            f[15:0]=crc(f[511:16]);command=f;
        end
    endfunction
    task check;
        input condition;input [8*140-1:0] label;
        begin tests=tests+1;
            if(condition!==1'b1) begin $display("FAIL %0s at %0t",label,$time);$fatal(1);end
            $display("PASS %0s",label);
        end
    endtask
    task send;
        input [511:0] data;
        integer i;
        begin
            @(negedge clk);cs_n=0;sclk=0;repeat(8)@(negedge clk);rx=0;
            for(i=511;i>=0;i=i-1) begin
                mosi=data[i];#100;sclk=1;#1;rx={rx[510:0],miso};#99;sclk=0;
            end
            repeat(8)@(negedge clk);cs_n=1;mosi=0;repeat(10)@(negedge clk);
            check(rx[511:480]==32'h434e5331 && rx[15:0]==crc(rx[511:16]),"actual endpoint status CRC/magic");
        end
    endtask
    task fresh_arm;
        begin
            session=session+1;
            send(command(1,0,session,0,0));
            check(ready && !motion && !tx_permit,"fresh SYNC establishes ready while hardware stays disarmed");
            send(command(2,63,session,1,0));
            check(motion && tx_permit && arm_latched && driver_command==0,"zero-rate ARM edge sets independent latch without a pulse");
        end
    endtask
    task start_motion;
        begin
            saved_falls=wdi_falls;
            send(command(3,63,session,2,32'h00800000));
            send(command(3,63,session,3,32'h00800000));
            check(wdi_falls==saved_falls+1,"two accepted UPDATE toggles provide one watchdog falling edge");
            saved_count=pulse_count;#40000;
            check(pulse_count>saved_count && tx_permit,"actual stepgen pulses cross the external permit gate");
        end
    endtask
    initial begin
        #200;
        local_reset_n=1;cdone=1;external_permit=1;
        #1000;
        check(!inhibit_n && !tx_permit,"unhealthy external watchdog inhibits startup");
        watchdog_ok=1;#1000;
        check(inhibit_n && !user_reset_n && !ready && !motion && !tx_permit,"CDONE high cannot release user logic while post-configuration reset is held");
        user_reset_n=1;#1000;
        check(inhibit_n && !motion && !tx_permit,"watchdog release alone cannot arm");
        fresh_arm();start_motion();
        // Clock-stall test: watchdog output injection is independent of FPGA clk.
        @(negedge clk);run_clock=0;#37;watchdog_ok=0;#1;
        check(!tx_permit && !arm_latched && driver_command==0,"watchdog fault clears physical gate while FPGA clock is stopped");
        saved_count=pulse_count;#100000;watchdog_ok=1;#100000;
        check(!tx_permit && pulse_count==saved_count,"watchdog auto-release cannot restart a stalled FPGA");
        run_clock=1;#1000;
        check(!motion && !ready && !tx_permit,"resumed FPGA clock retains inhibit authorization loss");
        send(command(3,63,session,4,32'h00800000));
        check(!tx_permit && !ready,"old-session UPDATE is rejected after external fault");
        fresh_arm();start_motion();
        // A pulse shorter than one FPGA cycle must clear asynchronous authorization.
        @(negedge clk);#2;external_permit=0;#2;external_permit=1;#1;
        check(!tx_permit && !arm_latched,"brief external permit drop clears board latch");
        #1000;check(!motion && !ready,"brief external permit loss remains latched in actual RTL");
        fresh_arm();
        send(command(4,0,session,2,0));
        check(!motion && !tx_permit,"DISARM withdraws hardware permission");
        // No reset required; a new deliberate ARM edge can restore it.
        send(command(2,63,session,3,0));
        check(tx_permit && motion,"new deliberate ARM after DISARM is accepted");
        cdone=0;#1;
        check(!tx_permit && !arm_latched,"configuration-done loss inhibits hardware asynchronously");
        cdone=1;#1000;
        check(!tx_permit && !ready,"configuration recovery cannot restore motion authority");
        fresh_arm();
        local_reset_n=0;user_reset_n=0;#1;
        check(!tx_permit && driver_command==0,"service/configuration reset inhibits actual outputs");
        #100;local_reset_n=1;#1000;
        check(!tx_permit && !ready,"reset release requires fresh protocol session and ARM");
        user_reset_n=1;#1000;
        check(!tx_permit && !ready,"user reset release still requires fresh protocol session and ARM");
        fresh_arm();
        // Leave SPI idle with clock running. Actual production5ms RTL watchdog fires.
        #5100000;
        check(wd_fault && !motion && !tx_permit,"actual5ms RTL watchdog independently clears board permit");
        check(!link_fault,"idle timeout is classified as watchdog rather than CRC/link failure");
        $display("PASS permission connection checks=%0d; six-channel production RTL plus idealized board gates; no timing qualification",tests);
        $finish;
    end
    initial begin #20000000;$fatal(1,"test timeout");end
endmodule
