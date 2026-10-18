`timescale 1ns/1ps
// Independent synthetic MCU peers. They accept actual 320-clock SPI commands,
// validate CRC/header/peer_sequence and prepare the *previous* command's response.
// This is no target-MCU firmware or analogue watchdog model.
module iol1_readonly_test_peer #(
    parameter [7:0] CLASS_ID = 8'h11,
    parameter [3:0] SLOT = 0
) (
    input wire reset_n, cs_n, sclk, mosi,
    input wire [3:0] injected_error,
    output reg miso,
    output integer bad_commands, output integer command_count
);
    reg [319:0] command_shift, response, wire_response;
    reg [15:0] epoch, peer_sequence;
    integer bits;
    function [31:0] crc32;
        input [287:0] body;
        reg [31:0] c; reg [7:0] b; integer i,j;
        begin
            c = 32'hffffffff;
            for(i=0;i<36;i=i+1) begin
                b=body[287-i*8 -:8];
                for(j=0;j<8;j=j+1)
                    c = (c[0]^b[j]) ? ((c>>1)^32'h82f63b78) : (c>>1);
            end
            crc32 = c ^ 32'hffffffff;
        end
    endfunction
    function [319:0] packet;
        input [15:0] ep,seq;
        reg [319:0] f;
        begin
            f=0; f[319:312]=8'h7a; f[311:304]=1;
            f[303:296]=CLASS_ID; f[295:288]={4'h1,SLOT};
            f[287:272]=ep;f[271:256]=seq;f[255:248]=ep==0 ? 0 : 8'h21;
            if(CLASS_ID==8'h31)f[119:112]=8'h0f;
            f[31:0]=crc32(f[319:32]); packet=f;
        end
    endfunction
    always @* begin
        wire_response=response;
        case(injected_error)
        1: wire_response[0]=~response[0];
        2: wire_response[303:296]=8'h7f;
        3: wire_response[291:288]=SLOT^4'h1;
        4: wire_response[287:272]=epoch+1;
        5: wire_response[271:256]=0; // fixed stale SYNC reply during sequenced polls
        6: wire_response[255:248]=8'h61;
        7: if(CLASS_ID==8'h11)wire_response[191:176]=441;
           else if(CLASS_ID==8'h21)wire_response[175:160]=441;
           else wire_response[143:128]=441;
        8: if(CLASS_ID!=8'h31)wire_response[159:112]=1;
           else wire_response[239:208]=1;
        9: wire_response[319:312]=0;
        10: wire_response[311:304]=2;
        11: wire_response[255:248]=8'h39; // output permission/enabled is forbidden
        12: if(CLASS_ID==8'h21)wire_response[239:232]=1;
            else if(CLASS_ID==8'h31)wire_response[119:112]=0;
            else wire_response[239:232]=response[239:232];
        13: wire_response=0; // actual disconnected/unprogrammed MISO LOW
        default: begin end
        endcase
        // Except explicit CRC corruption, errors have a correct CRC. The
        // receiver must reject semantics rather than relying only on CRC.
        if(injected_error>1 && injected_error!=13)wire_response[31:0]=crc32(wire_response[319:32]);
    end
    always @(negedge reset_n) begin
        epoch=0;peer_sequence=0;bits=0;command_shift=0;response=packet(0,0);
        bad_commands=0;command_count=0;miso=0;
    end
    initial begin
        epoch=0;peer_sequence=0;bits=0;command_shift=0;response=packet(0,0);
        bad_commands=0;command_count=0;miso=0;
    end
    always @(negedge cs_n) begin bits=0;command_shift=0;miso=wire_response[319];end
    always @(posedge sclk) if(!cs_n)begin command_shift={command_shift[318:0],mosi};bits=bits+1;end
    always @(negedge sclk) if(!cs_n && bits<320)miso=wire_response[319-bits];
    always @(posedge cs_n) if(reset_n && bits>0) begin
        command_count=command_count+1;
        if(bits!=320 || command_shift[319:304]!=16'ha701 ||
           command_shift[303:296]!=CLASS_ID || command_shift[295:288]!={4'b0,SLOT} ||
           command_shift[287:272]==0 || command_shift[247:240]!=8'hff ||
           command_shift[239:32]!=0 || command_shift[31:0]!=crc32(command_shift[319:32]) ||
           (command_shift[255:248]!=0 && command_shift[255:248]!=1))bad_commands=bad_commands+1;
        else if(command_shift[255:248]==1 && command_shift[271:256]==0)begin
            epoch=command_shift[287:272];peer_sequence=0;response=packet(epoch,peer_sequence);
        end else if(command_shift[255:248]==0 && command_shift[287:272]==epoch &&
                    command_shift[271:256]==(peer_sequence==16'hffff ? 16'h0001 : peer_sequence+1))begin
            peer_sequence=command_shift[271:256];response=packet(epoch,peer_sequence);
        end else bad_commands=bad_commands+1;
    end
endmodule

module tb_motherboard_watchdogs;
    reg clk=0;always #10 clk=~clk;
    reg reset_n=0, inhibit_n=1, rails_ok=1;
    reg cs=1,sclk=0,mosi=0;
    wire miso,miso_oe,ready,request_m,request_o,wdi_m,wdi_o;
    wire [11:0] steps,dirs,en_n;
    wire [3:0] io_cs,io_clk,io_cmd,io_rsp,io_fault;
    wire [1:0] pwm,pen;
    wire permit_req,lamp,link_fault,wd_fault,inh_fault,timing_fault;
    reg [3:0] injected[0:3];
    wire [31:0] bad[0:3],commands[0:3];
    cnc_motherboard_watchdog_bringup #(.IOL1_EPOCH(16'h51a7)) dut(
        .clk(clk),.reset_n(reset_n),.inhibit_n(inhibit_n),.rails_ok(rails_ok),
        .spi_cs_n(cs),.spi_sclk(sclk),.spi_mosi(mosi),.spi_miso(miso),.spi_miso_oe(miso_oe),
        .enc_a(2'b0),.enc_b(2'b0),.enc_z(2'b0),
        .step_out(steps),.dir_out(dirs),.enable_n(en_n),
        .motion_request(request_m),.endpoint_ready(ready),.output_request(request_o),
        .progress_m(wdi_m),.progress_o(wdi_o),
        .iol1_cs_n(io_cs),.iol1_sclk(io_clk),.iol1_mosi(io_cmd),.iol1_miso(io_rsp),
        .io_fault(io_fault),.pwm(pwm),.process_request(pen),
        .permit_out_request(permit_req),.arm_lamp_request(lamp),
        .link_fault(link_fault),.watchdog_fault(wd_fault),
        .inhibit_fault(inh_fault),.timing_fault(timing_fault)
    );
    genvar g;
    generate for(g=0;g<4;g=g+1)begin: peer
        iol1_readonly_test_peer #(.CLASS_ID(g==0?8'h11:g==3?8'h31:8'h21),.SLOT(g)) card(
            .reset_n(reset_n),.cs_n(io_cs[g]),.sclk(io_clk[g]),.mosi(io_cmd[g]),
            .injected_error(injected[g]),.miso(io_rsp[g]),
            .bad_commands(bad[g]),.command_count(commands[g])
        );
    end endgenerate
    integer checks=0,m_falls=0,o_falls=0,m_widths=0,o_widths=0;
    integer saved_m,saved_o,i,k;
    realtime m_start,o_start;
    always @(posedge wdi_m) if(reset_n)m_start=$realtime;
    always @(posedge wdi_o) if(reset_n)o_start=$realtime;
    always @(negedge wdi_m) if(reset_n)begin
        m_falls=m_falls+1;
        if($realtime-m_start!=1000.0)$fatal(1,"M width %0f ns",$realtime-m_start);
        m_widths=m_widths+1;
    end
    always @(negedge wdi_o) if(reset_n)begin
        o_falls=o_falls+1;
        if($realtime-o_start!=1000.0)$fatal(1,"O width %0f ns",$realtime-o_start);
        o_widths=o_widths+1;
    end
    task ck;
        input bit condition;input string label;
        begin checks=checks+1;if(!condition)$fatal(1,"FAIL %s",label);$display("PASS %s",label);end
    endtask
    function [15:0] crc16;
        input [495:0] f;reg [15:0] c;integer n;
        begin c=16'hffff;for(n=495;n>=0;n=n-1)c=(c[15]^f[n])?({c[14:0],1'b0}^16'h1021):{c[14:0],1'b0};crc16=c;end
    endfunction
    function [511:0] command;
        input [7:0] op;input [31:0] seq;
        reg [511:0] f;
        begin f=0;f[511:480]=32'h434e4331;f[479:472]=1;f[471:464]=op;
            if(op==2 || op==3)f[461:456]=63;
            if(op!=0)f[447:416]=32'h10203040;
            f[415:384]=seq;f[15:0]=crc16(f[511:16]);command=f;
        end
    endfunction
    task send;
        input [511:0] f;integer b;
        begin
            @(negedge clk);cs=0;repeat(8)@(negedge clk);
            for(b=511;b>=0;b=b-1)begin mosi=f[b];#100;sclk=1;#100;sclk=0;end
            repeat(8)@(negedge clk);cs=1;mosi=0;#2000;
        end
    endtask
    task fresh;
        begin reset_n=0;#200;reset_n=1;for(i=0;i<4;i=i+1)injected[i]=0;#400000;end
    endtask
    initial begin
        for(i=0;i<4;i=i+1)injected[i]=0;
        #100;ck(!wdi_m && !wdi_o && io_cs==15 && io_clk==0,"reset defaults WDI LOW / links deselected");
        reset_n=1;#600000;
        ck(o_falls>=3 && io_fault==0,"full physical four-port IOL1 acceptance produces O falling edges");
        ck(m_falls==0 && !wdi_m,"IOL1 replies cannot feed motion watchdog");
        ck(!request_o && pwm==0 && pen==0 && !permit_req && !lamp,"diagnostic traffic grants no process/output authority");
        ck(steps[11:6]==0 && dirs[11:6]==0 && en_n[11:6]==63,"unused six fitted motor channels stay electrically inactive");
        for(i=0;i<4;i=i+1)ck(bad[i]==0 && commands[i]>3,"physical command header/CRC/zero image validated independently");
        saved_m=m_falls;send(command(1,0));ck(m_falls==saved_m,"SYNC does not feed motion watchdog");
        send(command(2,1));ck(m_falls==saved_m+1 && request_m,"accepted ARM feeds exactly one falling edge");
        send(command(3,2));send(command(3,3));ck(m_falls==saved_m+3,"each accepted UPDATE feeds one edge, not every second frame");
        saved_m=m_falls;send(command(0,0));ck(m_falls==saved_m,"NOP has no useful progress");
        send(command(3,3));ck(m_falls==saved_m && !request_m,"replayed peer_sequence is rejected and cannot feed watchdog");
        fresh();send(command(1,0));send(command(2,1));saved_m=m_falls;
        send(command(3,2)^512'h1);ck(m_falls==saved_m && !request_m,"bad-CRC motion frame cannot feed WDI");
        // One valid peer cannot replace the complete-cycle criterion.
        for(k=1;k<=13;k=k+1)begin
            fresh();
            if(k==1)begin send(command(1,0));send(command(2,1));ck(request_m,"valid four-link diagnostics permit the separate deliberate motion ARM");end
            saved_o=o_falls;injected[1]=k;#500000;
            ck(io_fault[1] && o_falls==saved_o,"semantic/CRC/stale single-port failure withholds complete-cycle progress");
            if(k==1)ck(!request_m && steps==0,"IOL1 fault disarms motion-critical bench authority as well as O progress");
            saved_o=o_falls;injected[1]=0;#200000;
            ck(io_fault[1] && o_falls==saved_o,"fault recovery alone cannot restart a failed IOL1 link");
            ck(commands[0]>commands[1],"failed link cannot block other physical masters");
        end
        fresh();saved_o=o_falls;rails_ok=0;#300000;
        ck(!wdi_o && io_cs==15 && io_fault==15,"rail loss deselects links and records interrupted epochs");
        rails_ok=1;#200000;ck(o_falls==saved_o,"rail recovery cannot silently restart polling epoch");
        inhibit_n=0;#1;ck(!request_m && steps==0,"asynchronous motion inhibit remains independent of IOL1 activity");
        ck(m_widths==m_falls && o_widths==o_falls,"every completed accepted WDI pulse is exactly1000ns");
        $display("PASS motherboard watchdog bringup checks=%0d M_pulses=%0d O_pulses=%0d; synthetic peers, not target firmware",checks,m_widths,o_widths);
        $finish;
    end
    initial begin #20000000;$fatal(1,"test deadline");end
endmodule
