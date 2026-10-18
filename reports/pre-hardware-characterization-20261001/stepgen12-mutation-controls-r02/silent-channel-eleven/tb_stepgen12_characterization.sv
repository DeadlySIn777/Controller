`timescale 1ns/1ps
// Isolated characterization of twelve instances of the actual unchanged RTL.
// This is NOT a twelve-channel endpoint, CNC3 implementation or vendor timing run.
module tb_stepgen12_characterization;
    parameter integer HIGH = 12;
    parameter integer LOW = 12;
    parameter integer SETUP = 12;
    parameter integer HOLD = 12;
    reg clk = 0;
    always #10 clk = !clk;  // Assumed 50 MHz, not a measured/fitted clock.
    reg rst_n = 0, enable = 0;
    reg signed [31:0] rate = 0;
    reg seed_load = 0;
    reg [31:0] seed_phase = 0;
    wire [11:0] step, dir, fault;
    wire signed [31:0] count [0:11];
    genvar g;
    generate for (g=0; g<12; g=g+1) begin : channels
        cnc_stepgen #(.PULSE_CYCLES(HIGH), .SPACE_CYCLES(LOW),
            .DIR_SETUP_CYCLES(SETUP), .DIR_HOLD_CYCLES(HOLD)) dut (
            .clk(clk), .rst_n(rst_n), .enable(enable), .rate(g == 11 ? 32'sd0 : rate),
            .step(step[g]), .dir(dir[g]), .count(count[g]), .timing_fault(fault[g]));
        // Explicit test-fixture phase injection. The chosen phase belongs to
        // the reset-reachable DDS subgroup; this exposes rare short periods
        // without pretending that a finite reset-only sample proves a bound.
        always @(negedge clk) if (seed_load) channels[g].dut.phase = seed_phase;
    end endgenerate

    integer j, tick, rows = 0, checks = 0;
    integer rises [0:11], signed_edges [0:11], last_rise [0:11], last_fall [0:11];
    reg [11:0] previous_step;
    reg [31:0] inc;
    reg [63:0] safe_increment, scale = 64'h100000000;
    integer cycles;

    function automatic [31:0] reachable_phase(input [31:0] word_value);
        reg [31:0] gcd_power_two;
        begin
            gcd_power_two = word_value & (~word_value + 1);
            reachable_phase = 0 - gcd_power_two;
        end
    endfunction

    task automatic exercise(input [31:0] word_value, input integer reverse,
                            input integer adversarial, input integer sample_cycles);
        reg [63:0] expected_wraps, phase_total;
        reg [31:0] seed;
        integer observed_fault, expected_fault, requested_direction;
        begin
            @(negedge clk); rst_n=0; enable=0; rate=0; seed_load=0;
            repeat (3) @(negedge clk);
            rst_n=1;
            repeat (2) @(negedge clk);
            enable=1;
            repeat (SETUP+HIGH+LOW+HOLD+5) @(negedge clk);
            if (reverse != 0) begin
                rate = -$signed(word_value);
                repeat (SETUP+1) begin @(posedge clk); #1; end
            end
            // Drive seed controls before the falling edge, avoiding a fixture race.
            @(posedge clk); #1;
            seed = adversarial != 0 ? reachable_phase(word_value) : 0;
            seed_phase=seed; seed_load=1;
            rate = reverse != 0 ? -$signed(word_value) : $signed(word_value);
            @(negedge clk); #1; seed_load=0;
            for (j=0;j<12;j=j+1) begin
                if (count[j] != 0 || step[j] || fault[j]) $fatal(1,"Dirty start state channel %0d",j);
                rises[j]=0; signed_edges[j]=0; last_rise[j]=-1; last_fall[j]=-1;
            end
            previous_step=step;
            for (tick=0;tick<sample_cycles;tick=tick+1) begin
                @(posedge clk); #1;
                for (j=0;j<12;j=j+1) begin
                    if (step[j] && !previous_step[j]) begin
                        if (dir[j] != (reverse != 0)) $fatal(1,"Wrong STEP direction");
                        if (last_fall[j]>=0 && tick-last_fall[j]<LOW) $fatal(1,"STEP-low violation");
                        rises[j]=rises[j]+1;
                        signed_edges[j]=signed_edges[j]+(reverse != 0 ? -1 : 1);
                        last_rise[j]=tick;
                    end
                    if (!step[j] && previous_step[j]) begin
                        if (last_rise[j]<0 || tick-last_rise[j]<HIGH) $fatal(1,"STEP-high violation");
                        last_fall[j]=tick;
                    end
                    if (count[j] != signed_edges[j]) $fatal(1,"Actual emitted-edge/count mismatch");
                    checks=checks+1;
                end
                previous_step=step;
            end
            phase_total={32'b0,seed}+{32'b0,word_value}*sample_cycles;
            expected_wraps=phase_total >> 32;
            observed_fault=(fault != 0);
            expected_fault=(adversarial != 0 && {32'b0,word_value}>safe_increment);
            if (expected_fault && fault != 12'hfff) $fatal(1,"Worst reachable phase failed to expose all twelve timing faults");
            if ({32'b0,word_value}<=safe_increment && observed_fault) $fatal(1,"Fault below the analytical safe boundary");
            if (!observed_fault) begin
                for (j=0;j<12;j=j+1)
                    if (rises[j] != expected_wraps) $fatal(1,"DDS requested/emitted pulse mismatch");
            end
            $display("{\"increment\":%0d,\"reverse\":%0d,\"adversarial_reachable_phase\":%0d,\"seed_phase\":%0d,\"sample_cycles\":%0d,\"channels\":12,\"timing_fault\":%0d,\"fault_mask\":%0d,\"requested_wraps_per_channel\":%0d,\"emitted_rises_per_channel\":%0d}",word_value,reverse,adversarial,seed,sample_cycles,observed_fault,fault,expected_wraps,rises[0]);
            rows=rows+1;
            @(negedge clk); enable=0;
            @(posedge clk); #1;
            if (step != 0 || dir != 0) $fatal(1,"Disabled pulse-generator output did not clear");
            // Outer endpoint permission/no-restart behavior is a separate test.
        end
    endtask

    integer rates_hz [0:9];
    integer k, direction, phase_case;
    reg [63:0] wide;
    initial begin
        cycles=4096;
        if ($value$plusargs("cycles=%d",cycles)) begin end
        if (cycles<512 || cycles>10000000) $fatal(1,"Invalid bounded sample duration");
        if (HIGH<1 || LOW<1 || SETUP<1 || HOLD<1) $fatal(1,"Invalid timing profile");
        safe_increment=scale/(HIGH+LOW+1);
        rates_hz[0]=100000; rates_hz[1]=250000; rates_hz[2]=500000;
        rates_hz[3]=1000000; rates_hz[4]=2000000; rates_hz[5]=2200000;
        rates_hz[6]=2400000; rates_hz[7]=3000000; rates_hz[8]=3800000; rates_hz[9]=4000000;
        for (k=0;k<12;k=k+1) begin
            if (k<10) begin wide=scale*rates_hz[k]; inc=wide/50000000; end
            else if (k==10) inc=safe_increment[31:0];
            else inc=safe_increment[31:0]+1;
            for (direction=0;direction<2;direction=direction+1)
                for (phase_case=0;phase_case<2;phase_case=phase_case+1)
                    exercise(inc,direction,phase_case,cycles);
        end
        $display("SUMMARY rows=%0d edge_counter_checks=%0d high=%0d low=%0d setup=%0d hold=%0d safe_increment=%0d",rows,checks,HIGH,LOW,SETUP,HOLD,safe_increment);
        $finish;
    end
endmodule
