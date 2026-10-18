from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('p3',ROOT/'gateware/v3/frozen/protocol_v3.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p._SPEC=p.Spec(str(ROOT/'gateware/v3/frozen/spec/protocol.json'))
 def cmd(op,seq=0,mask=0,**fields):return p.encode_command(op,session=0x11223344 if op not in (0,16) else 0,sequence=seq,channel_mask=mask,fields=fields)[1]
 frames={'cfg':p.encode_configure(expected_module_class=1,required_mask=0xfff,alarm_trip_mask=0xfff,encoder_filter_ticks=4,required_encoder_mask=15),
 'sync':cmd(1),'testm':cmd(13,1,rate_0=0x01000000),'testo':cmd(13,2,rate_0=0x02000000),
 'clear':cmd(14,3,0xfff),'arm':cmd(2,4,0xfff),'update':p.encode_update(session=0x11223344,sequence=5,rates=[(-1 if k%2 else 1)*0x800000 for k in range(12)],channel_mask=0xfff),
 'disarm':cmd(4,6),'arm2':cmd(2,7,0xfff),'zero':p.encode_update(session=0x11223344,sequence=8,rates=[0]*12,channel_mask=0xfff),
 'nop':cmd(0),'read':p.encode_fb_read(),'unsupported_page':p.encode_command(5)[1]}
 declarations=[]
 for name,b in frames.items():declarations.append(f"localparam[1407:0] {name}=1408'h{(b+bytes(176-len(b))).hex()};")
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,fb=1,cmd=1,sck=0,mosi=0;wire miso,oe;
reg wm=1,wo=1,inhibit=1;reg[3:0] opi=0;wire[3:0] rearm;
reg[3:0] ea=0,eb=0,ez=0;wire[11:0] steps,dirs,en_n,am,cont;
wire mreq,oreq,permit,pm,po,consume,cfgv,accepted;wire[31:0] session,seq,fault;
wire[1:0] tests;wire[2:0] teststate;wire[7:0] rejected;
wire[1391:0] actualfb;wire[751:0] actualstatus;
wire[3:0] gates={4{mreq&&inhibit}};
cnc3_motion_spi dut(.clk(clk),.rst_n(rst),.spi_cs_fb_n(fb),.spi_cs_cmd_n(cmd),.spi_sclk(sck),.spi_mosi(mosi),.spi_miso(miso),.spi_miso_oe(oe),.qualification_complete(1'b1),.installed_input(12'hfff),.installed_module_class(8'd1),.inhibit_n(inhibit),.wd_m_ok(wm),.wd_o_ok(wo),.reset_arm_ready(1'b1),.reset_arm_held(1'b0),.contactor_deenergized(1'b1),.sto_arm_expected(1'b1),.motion_critical_ports_valid(1'b1),.gate_high(gates),.opi_ok(opi),.alarm_current_raw(12'd0),.encoder_a(ea),.encoder_b(eb),.encoder_z(ez),.encoder_installed(4'hf),.encoder_port_valid(4'hf),.external_fault_word(32'd0),.motion_critical_io_fault(1'b0),.provider_feedback(1392'd0),.provider_status(752'd0),.physical_safety_power_word(32'd0),.step_out(steps),.dir_out(dirs),.enable_n(en_n),.motion_request(mreq),.output_request(oreq),.permit_out_req(permit),.progress_m(pm),.progress_o(po),.opi_rearm(rearm),.reset_arm_consumed(consume),.session(session),.last_sequence(seq),.fault_word(fault),.armed_mask(am),.pos_continuity(cont),.config_valid(cfgv),.selftest_passed(tests),.selftest_state(teststate),.accepted_pulse(accepted),.last_reject(rejected),.actual_feedback_payload(actualfb),.actual_status_payload(actualstatus));
// Explicit ideal physical gate/OPI test fixture. These are ports in production.
always@(posedge clk)if(!mreq||!inhibit)opi<=0;else opi<=opi|rearm;
integer checks=0,file,j,core_cycles=0,progress_start=0,progress_pulses=0;reg[1407:0] reply;reg oldprogress=0;
always@(posedge clk)begin
#1;core_cycles=core_cycles+1;
if(pm&&!oldprogress)progress_start=core_cycles;
if(!pm&&oldprogress)begin
if(core_cycles-progress_start!=50)$fatal(1,"actual accepted motion progress is not50ticks");
progress_pulses=progress_pulses+1;
end
oldprogress=pm;
end
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
task check(input bit good,input string message);begin checks=checks+1;if(!good)$fatal(1,"%s seq%0d fault%h",message,seq,fault);end endtask
task transaction(input string name,input bit usefb,input[1407:0] data);
integer i,bits;begin
bits=usefb?1408:768;ticks(12);if(usefb)fb=0;else cmd=0;#160;reply=0;
for(i=0;i<bits;i=i+1)begin mosi=data[1407-i];#80;sck=1;reply={reply[1406:0],miso};#80;sck=0;end
#160;fb=1;cmd=1;ticks(12);$fdisplay(file,"%s %0d %h",name,bits/8,reply);
check(!oe,"MISO released after actual transaction");
end endtask
task watchdog(input bit outputtest);begin
transaction(outputtest?"testO":"testM",0,outputtest?testo:testm);
check(teststate==(outputtest?3:1),"actual SPI starts selected selftest");
ticks(500000);check(en_n==12'hfff && steps==0 && dirs==0 && permit==0 && pm==0 && po==0,"actual SPI selftest field containment");
check(outputtest?!tests[1]:!tests[0],"SPI no instant selftest pass");
if(outputtest)wo=0;else wm=0;ticks(5);check(teststate==(outputtest?4:2),"actual SPI observed external fall");
ticks(100);if(outputtest)wo=1;else wm=1;ticks(5);check(teststate==0,"SPI recovery observed");
end endtask
initial begin
file=$fopen("responses.txt","w");ticks(5);rst=1;ticks(2200);
transaction("configure",1,cfg);check(cfgv && session==0,"actual CONFIGURE commits after CS release");
transaction("sync",0,sync);check(fault==0 && session==32'h11223344,"actual SYNC");
watchdog(0);watchdog(1);check(tests==3,"actual SPI both measured watchdog tests");
transaction("continuity",0,clear);check(cont==12'hfff,"actual continuity witness");
transaction("arm",0,arm);check(am==12'hfff && en_n==0,"actual SPI all12 permission");
transaction("update",0,update);check(seq==5 && fault==0,"actual SPI atomic twelve UPDATE");
ticks(20000);
// Drive four real quadrature algorithms through ten positive cycles each.
for(j=0;j<10;j=j+1)begin eb=15;ticks(20);ea=15;ticks(20);eb=0;ticks(20);ea=0;ticks(20);end
transaction("moving_feedback",1,read);check(fault==0,"actual counts feedback read");
transaction("clean_disarm",0,disarm);ticks(500);check(am==0 && !mreq && cont==12'hfff,"actual SPI clean drain");
transaction("stopped_feedback",1,read);
transaction("rearm",0,arm2);transaction("zero_update",0,zero);
// Corrupt physical bytes rather than injecting a semantic rejection flag.
transaction("bad_crc",0,nop ^ (1408'd1<<640));
check(fault[0] && am==0 && cont==0 && en_n==12'hfff,"actual SPI CRC fault clears zero-rate continuity");
transaction("fault_feedback",1,read);
check(progress_pulses==4,"actual ARM/UPDATE only four1us watchdog pulses");
$fclose(file);$display("ACTUAL_STATEFUL_SPI_PASS checks=%0d",checks);$finish;
end
endmodule
'''
 tb=tb.replace('module tb;','module tb;\n'+'\n'.join(declarations))
 (out/'spi_motion.sv').write_text(tb,encoding='utf8',newline='\n')
 sources=[*sorted(HERE.glob('cnc3_*.v')),HERE/'inputs/workspace/gateware/v3/rtl/cnc3_spi_transport.v',HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 before={q.as_posix():sha(q) for q in sources}
 for q in sources:shutil.copyfile(q,out/q.name)
 args=' '.join(q.name for q in sources)
 script=f"cd '{unix(out)}' && iverilog -g2012 -s tb -o spi_motion.vvp {args} spi_motion.sv && vvp spi_motion.vvp"
 result=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh','-c',script],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=600)
 log=result.stdout+result.stderr;(out/'actual-iverilog.log').write_text(log,encoding='utf8',newline='\n')
 decoded={};checks=[]
 try:
  if result.returncode or 'ACTUAL_STATEFUL_SPI_PASS' not in log:raise RuntimeError(log[-3000:])
  for line in (out/'responses.txt').read_text().splitlines():
   name,n,hextext=line.split();n=int(n);data=int(hextext,16).to_bytes(n,'big');cs='CS_FB' if n==176 else 'CS_CMD';decoded[name]=p.decode_response(cs,data)
  moving=decoded['moving_feedback'];stopped=decoded['stopped_feedback'];fault=decoded['fault_feedback']
  checks.append(('snapshot-before-commit',decoded['update']['last_sequence']==4 and moving['last_sequence']==5))
  checks.append(('actual-twelve-step-counters',all(moving[f'step_count_{k}']!=0 for k in range(12))))
  checks.append(('actual-four-encoder-counters',all(moving[f'encoder_count_{k}']==40 for k in range(4))))
  checks.append(('eight-unimplemented-encoder-slots-zero-invalid',all(moving[f'encoder_count_{k}']==0 for k in range(4,12)) and moving['encoder_valid_mask']==15))
  checks.append(('actual-CRC-fault',fault['fault_word']&1 and fault['armed_mask']==0 and fault['pos_continuity']==0))
  checks.append(('clean-stop-continuity',stopped['armed_mask']==0 and stopped['pos_continuity']==0xfff))
  checks.append(('unavailable-IOL1-explicit',moving['din_age']==255 and moving['ain_age']==255 and moving['ain_status']==0))
  if not all(v for _,v in checks):raise RuntimeError('Actual frozen response decoding assertions failed')
  status='PASS'
 except Exception as e:status='FAIL';log+='\n'+str(e)
 (out/'decoded-responses.json').write_text(json.dumps(decoded,indent=2,default=lambda x:x.hex() if isinstance(x,bytes) else str(x))+'\n',encoding='utf8',newline='\n')
 unchanged=all(sha(Path(q))==h for q,h in before.items())
 receipt={'status':status if unchanged else 'FAIL','source_hashes':before,'source_unchanged':unchanged,'evidence_type':'actual Icarus frozen SPI transport +stateful motion +12 runtime stepgens +4 filtered quadrature counters','response_codec':'unchanged frozen protocol_v3 decode/CRC','response_checks':dict(checks),'external_providers':'explicit ideal simulation inputs, not physical qualification','HAL_IOL1_events_pages_full_twelve_machine':False,'detail':log[-3300:]}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);raise SystemExit(main(ap.parse_args().out.resolve()))
