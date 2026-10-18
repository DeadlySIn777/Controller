from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('Fresh evidence required')
 out.mkdir(parents=True)
 mod=importlib.util.spec_from_file_location('p3',ROOT/'gateware/v3/frozen/protocol_v3.py');p=importlib.util.module_from_spec(mod);mod.loader.exec_module(p);p._SPEC=p.Spec(str(ROOT/'gateware/v3/frozen/spec/protocol.json'))
 def cfg(**kw):return p.encode_configure(expected_module_class=1,required_mask=0xfff,alarm_trip_mask=0xfff,config_hash=0xaabbccdd,**kw)
 def cmd(op,session=0,sequence=0,mask=0,**fields):return p.encode_command(op,session=session,sequence=sequence,channel_mask=mask,fields=fields)[1]
 configs={f'timing_{k}':[100+k,110+k,120+k,130+k] for k in range(12)}
 frames={'cfg':cfg(**configs),'cfg2':cfg(session=0x55667788,sequence=1,**configs),
  'sync1':cmd(1,0x11223344),'sync2':cmd(1,0x55667788),'sync3':cmd(1,0x778899aa),
  'arm1':cmd(2,0x11223344,1,0xfff),'testm':cmd(13,0x55667788,1,rate_0=0x01000000),
  'testo':cmd(13,0x55667788,2,rate_0=0x02000000),'clear':cmd(14,0x55667788,3,0xfff),
  'arm':cmd(2,0x55667788,4,0xfff),'update':p.encode_update(session=0x55667788,sequence=5,rates=[(-1 if k%2 else 1)*(0x800000+k*997) for k in range(12)],channel_mask=0xfff),
  'disarm':cmd(4,0x55667788,9),'nop':cmd(0),'fbread':p.encode_fb_read(),
  'arm2':cmd(2,0x55667788,10,0xfff),'zero':p.encode_update(session=0x55667788,sequence=11,rates=[0]*12,channel_mask=0xfff),
  'staletest':cmd(13,0x778899aa,1,rate_0=0x01000000),'earlytest':cmd(13,0x778899aa,1,rate_0=0x01000000),
  'fresharm':cmd(2,0x778899aa,1,0xfff)}
 # Structurally valid wrong-session CONFIGURE must clear current config.
 frames['badcfg']=cfg(session=0x12340000,sequence=10,**configs)
 for seq in (6,7,8):frames['late'+str(seq)]=p.encode_update(session=0x55667788,sequence=seq,rates=[(-1 if k%2 else 1)*(0x800000+k*997) for k in range(12)],channel_mask=0xfff)
 frames['guardcfg']=cfg(session=0x55667788,sequence=5,required_encoder_mask=1,**configs)
 for k in range(10):
  sess=0xabc00000+k
  frames['guard_sync'+str(k)]=cmd(1,sess)
  frames['guard_arm'+str(k)]=cmd(2,sess,1,0xfff)
  frames['guard_disarm'+str(k)]=cmd(4,sess,2)
 declarations=[]
 for name,b in frames.items():
  declarations.append(f"localparam[1407:0] {name}=1408'h{(b+bytes(176-len(b))).hex()};")
 (out/'frames.json').write_text(json.dumps({k:v.hex() for k,v in frames.items()},indent=2)+'\n',encoding='utf8')
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,rv=0,reject=0,rejectedcfg=0;reg[1407:0] frame=0;wire[7:0] structural;
reg qual=0;reg[11:0] installed=12'hfff;reg[7:0] moduleclass=1;
reg inhibit=1,wm=1,wo=1,ready=1,held=0,contactor=1,sto=1,ports=1;
reg[11:0] ev=0,ei=0,alarms=0;reg[31:0] extfault=0;reg criticalio=0;
reg[3:0] opi=0;reg autoopi=1;wire[3:0] rearm;
wire[11:0] enable,quiet,steps,dirs,timing;
wire[31:0] sess,seq,tick,fw,chash;wire[11:0] im,rm,am,continuity,st,al,rem;
wire cfgv;wire[7:0] gen,mpg,state,lastrej;wire[15:0] ccrc,servo,interval,late;
wire[3:0] ef;wire[191:0] high,low,setup,hold;wire[383:0] rates;
wire stop,mreq,oreq,permit,pm,po,consumed,accepted,effective,io;wire[1:0] tests;wire[2:0] teststate;
wire signed[31:0] counts[0:11];
wire[3:0] gates={4{mreq&&inhibit}};
cnc3_command_validate validate(frame,frame[1367:1360]==6,frame[1367:1360]==6?9'd176:9'd96,1'b1,1'b1,structural);
cnc3_motion_state d(.clk(clk),.rst_n(rst),.request_valid(rv),.request_frame(frame),.reject_pulse(reject),.rejected_configure(rejectedcfg),.qualification_complete(qual),.installed_input(installed),.installed_module_class(moduleclass),.inhibit_n(inhibit),.wd_m_ok(wm),.wd_o_ok(wo),.reset_arm_ready(ready),.reset_arm_held(held),.contactor_deenergized(contactor),.sto_arm_expected(sto),.motion_critical_ports_valid(ports),.encoder_valid_mask(ev),.encoder_installed_mask(ei),.encoder_expansion_class(8'd0),.alarm_levels(alarms),.timing_faults(timing),.external_fault_word(extfault),.motion_critical_io_fault(criticalio),.gate_high(gates),.opi_ok(opi),.generator_quiescent(quiet),.request_ready(),.session(sess),.last_sequence(seq),.ticks(tick),.fault_word(fw),.installed_mask(im),.required_mask(rm),.armed_mask(am),.pos_continuity(continuity),.step_timing_latched(st),.alarm_trip_latched(al),.config_valid(cfgv),.config_generation(gen),.config_hash(chash),.config_crc(ccrc),.servo_period_us(servo),.required_encoder_mask(rem),.encoder_filter_ticks(ef),.mpg_config(mpg),.pulse_ticks(high),.space_ticks(low),.setup_ticks(setup),.hold_ticks(hold),.rates(rates),.generator_enable(enable),.generator_stop(stop),.motion_request(mreq),.output_request(oreq),.permit_out_req(permit),.progress_m(pm),.progress_o(po),.opi_rearm(rearm),.reset_arm_consumed(consumed),.selftest_passed(tests),.selftest_state(teststate),.accepted_pulse(accepted),.last_reject(lastrej),.last_update_interval_us(interval),.late_update_count(late),.motion_effective(effective),.state_bits(state),.io_enabled(io));
genvar k;generate for(k=0;k<12;k=k+1)begin:g
cnc3_stepgen_runtime sg(clk,rst,enable[k],stop,$signed(rates[383-32*k -:32]),high[191-16*k -:16],low[191-16*k -:16],setup[191-16*k -:16],hold[191-16*k -:16],steps[k],dirs[k],counts[k],timing[k],quiet[k]);
end endgenerate
always@(posedge clk)if(autoopi)begin
if(!mreq || !inhibit)opi<=0;else opi<=opi|rearm;
end
integer checks=0,j,elapsed;reg[11:0] savedcontinuity;reg signed[31:0] savedcounts[0:11];
task check(input bit yes,input string message);begin checks=checks+1;if(!yes)$fatal(1,"%s tick%0d fault%h",message,tick,fw);end endtask
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
task send(input[1407:0] value);begin
@(negedge clk);frame=value;#1;
// FB_READ also uses CS_FB. This bench's static checker chip-select is corrected
// explicitly for the two readonly frame classes used here.
if(value[1367:1360]!=16)check(structural==0,"actual frozen static frame acceptance");
rv=1;@(negedge clk);rv=0;#1;
end endtask
task send_at_delta(input[1407:0] value,input integer delta);begin
while(tick-d.last_update_tick<delta)@(negedge clk);
frame=value;#1;check(structural==0,"late interval real static validation");rv=1;
@(negedge clk);rv=0;#1;
end endtask
task cold;begin rst=0;rv=0;wm=1;wo=1;qual=0;inhibit=1;autoopi=1;opi=0;installed=12'hfff;held=0;ready=1;ports=1;extfault=0;ticks(4);rst=1;ticks(2);qual=1;ticks(3);end endtask
task test_watchdog(input bit output_test);begin
send(output_test?testo:testm);
check(teststate==(output_test?3:1),"real selftest start");
for(elapsed=0;elapsed<500000;elapsed=elapsed+1)begin
ticks(1);
if(elapsed%4096==0)begin
check(enable==0 && steps==0 && dirs==0 && permit==0 && pm==0 && po==0 && rates==0 && io==0,"selftest containment");
check(output_test?(oreq&&!mreq):(mreq&&!oreq),"only selected watchdog request");
end
end
check(output_test?!tests[1]:!tests[0],"no instant SELFTEST flag");
if(output_test)wo=0;else wm=0;ticks(2);
check(teststate==(output_test?4:2),"measured fall enters recovery wait");
check(output_test?tests[1]:tests[0],"only observed timely fall passed");
check(!mreq&&!oreq,"selftest request low after fall");
ticks(200);check(teststate!=(0),"must wait actual WDO recovery");
if(output_test)wo=1;else wm=1;ticks(3);check(teststate==0,"recovery observed");
end endtask
initial begin
cold();check(am==0 && rates==0 && enable==0 && tests==0 && !cfgv,"cold defaults");
send(cfg);check(cfgv && gen==1 && sess==0 && chash==32'haabbccdd,"atomic configure/session clear");
for(j=0;j<12;j=j+1)check(high[191-16*j -:16]==100+j && low[191-16*j -:16]==110+j && setup[191-16*j -:16]==120+j && hold[191-16*j -:16]==130+j,"all12 native timings");
send(sync1);check(sess==32'h11223344 && fw==0,"SYNC recovery");
send(arm1);check(am==0 && fw[27] && tests==0,"ARM refuses untested watchdogs");
send(sync2);check(fw==0,"new session clears ARM refusal");
test_watchdog(0);test_watchdog(1);check(tests==3,"both independent measured selftests");
send(clear);check(continuity==12'hfff,"explicit host re-reference witness");
send(arm);check(am==12'hfff && consumed && permit,"ARM consumes release");
ticks(100);check(effective && enable==12'hfff,"actual OPI rearm handshake");
send(update);check(rates==update[1279 -:384] && seq==5,"atomic12 update");
ticks(20000);for(j=0;j<12;j=j+1)check(counts[j]!=0,"all12 actual emitted counters");
send_at_delta(late6,74999);check(late==0 && interval==1499,"below1.5 period is not late");
send_at_delta(late7,75000);check(late==0 && interval==1500,"equal1.5 period is not late");
send_at_delta(late8,75001);check(late==1 && interval==1500,"one tick above1.5 period late");
while(steps==0)ticks(1);
send(disarm);for(j=0;j<12;j=j+1)savedcounts[j]=counts[j];
check(mreq && stop && am==12'hfff,"request retained while actual pulse drains");
ticks(1500);check(am==0 && !mreq && !permit && continuity==12'hfff,"clean stopped continuity");
for(j=0;j<12;j=j+1)check(counts[j]==savedcounts[j],"no post-DISARM rising edges");
send(arm2);ticks(8);send(zero);check(rates==0 && am!=0,"armed zero rate");
inhibit=0;ticks(2);check(am==0 && continuity==0 && fw[2],"fault clears all armed continuity at ZERO rate");
inhibit=1;ticks(2);send(sync3);check(fw==0 && am==0,"no automatic rearm after inhibit recovery");
send(badcfg);check(!cfgv && rm==0 && fw[7] && chash==32'haabbccdd && gen==1,"EVERY recognized CONFIG reject clears validity but retains diagnosis");
// Fresh startup: actual early fall must fail, and no-fall must fail.
cold();send(cfg);send(sync3);send(earlytest);ticks(100);wm=0;ticks(2);check(fw[11] && tests==0 && !mreq,"early external WDO fail");
cold();send(cfg);send(sync3);send(staletest);ticks(668510);check(fw[11] && tests==0 && !mreq,"missing external WDO fail");
// Readonly traffic never feeds the exact fixed5ms watchdog.
cold();send(cfg);send(sync2);test_watchdog(0);test_watchdog(1);send(clear);send(arm);ticks(8);
for(j=0;j<100;j=j+1)begin ticks(2497);send(nop);end
ticks(500);check(fw[1] && am==0 && continuity==0,"NOP does not feed motion watchdog");
// Real provider preconditions remain required after passing both real tests.
ei=1;ev=1;send(guardcfg);check(cfgv && sess==0 && rem==1,"required encoder committed");
ready=0;send(guard_sync0);send(guard_arm0);check(am==0 && fw[27],"missing reset release blocks ARM");ready=1;
held=1;send(guard_sync1);send(guard_arm1);check(am==0 && fw[27],"held reset blocks ARM");held=0;
contactor=0;send(guard_sync2);send(guard_arm2);check(am==0 && fw[27],"energized contactor blocks ARM");contactor=1;
sto=0;send(guard_sync3);send(guard_arm3);check(am==0 && fw[27],"unexpected STO blocks ARM");sto=1;
ports=0;send(guard_sync4);send(guard_arm4);check(am==0 && fw[27],"missing critical port blocks ARM");ports=1;
wo=0;send(guard_sync5);send(guard_arm5);check(am==0 && fw[27],"WDO not recovered blocks ARM");wo=1;
ev=0;send(guard_sync6);send(guard_arm6);check(am==0 && fw[27],"required encoder invalid blocks ARM");ev=1;
alarms=1;send(guard_sync7);send(guard_arm7);check(am==0 && fw[27],"tripping alarm blocks ARM");alarms=0;
send(guard_sync8);send(guard_arm8);ticks(8);check(am==12'hfff,"fully observed conditions allow ARM");
autoopi=0;opi=15;send(guard_disarm8);ticks(510);check(fw[10] && am==0,"actual stuck OPI after request drop faults at10us");
autoopi=1;opi=0;send(guard_sync9);send(guard_arm9);ticks(8);check(am!=0,"deliberate rearm after service");
ev=0;ticks(2);check(am==0 && fw[19],"runtime required encoder loss cuts motion");ev=1;
// Presence change remains power-cycle sticky and zeros installed population.
installed=12'h0ff;ticks(2);check(fw[5] && im==0 && tests==0,"qualified population change power-cycle fault");
send(sync3);check(fw[5] && im==0,"SYNC cannot clear population-change fault");
$display("STATEFUL_MOTION_PASS checks=%0d actual_generators=12 ticks=%0d",checks,tick);$finish;
end
endmodule
'''
 tb=tb.replace('module tb;','module tb;\n'+'\n'.join(declarations))
 (out/'state.sv').write_text(tb,encoding='utf8',newline='\n')
 sourcepaths=[HERE/'cnc3_motion_state.v',HERE/'cnc3_stepgen_runtime.v',HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 before={q.as_posix():sha(q) for q in sourcepaths}
 for q in sourcepaths:shutil.copyfile(q,out/q.name)
 command=f"cd '{unix(out)}' && iverilog -g2012 -s tb -o state.vvp cnc3_motion_state.v cnc3_stepgen_runtime.v cnc3_command_validate.v state.sv && vvp state.vvp"
 result=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh','-c',command],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=600)
 log=result.stdout+result.stderr;(out/'actual-iverilog.log').write_text(log,encoding='utf8',newline='\n')
 unchanged=all(sha(Path(q))==h for q,h in before.items())
 receipt={'status':'PASS' if result.returncode==0 and 'STATEFUL_MOTION_PASS' in log and unchanged else 'FAIL','evidence_type':'actual Icarus stateful CNC3 motion +12 runtime DDS simulations','source_hashes':before,'source_unchanged':unchanged,'codecs':'actual frozen command builders and static RTL validator','external_physical_gates_and_WDO':'explicit ideal testbench observations; no hardware qualification','CNC3_SPI_full_HAL_IO_plant_included':False,'detail':log[-3500:]}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);raise SystemExit(main(ap.parse_args().out.resolve()))
