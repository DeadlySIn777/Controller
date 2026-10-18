from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil, subprocess
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p): return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists(): raise RuntimeError('Fresh output directory required')
 out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('p3',ROOT/'gateware/v3/frozen/protocol_v3.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p._SPEC=p.Spec(str(ROOT/'gateware/v3/frozen/spec/protocol.json'))
 cfg=p.encode_configure(expected_module_class=1,required_mask=0xfff,alarm_trip_mask=0xfff,alarm_on_no_current=0xfff,config_hash=0xaabbccdd)
 update=p.encode_update(session=0x12345678,sequence=1,rates=[0]*12,channel_mask=0xfff)
 declarations='\n'.join(f"localparam[1407:0] {n}=1408'h{(b+bytes(176-len(b))).hex()};" for n,b in [('cfg',cfg),('update',update)])
 tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst=0,fb=1,cmd=1,sck=0,mosi=0;wire miso,oe;
wire cfgv;wire[31:0] session,seq,fault;
wire[11:0] steps,dirs,en_n;
cnc3_motion_spi dut(.clk(clk),.rst_n(rst),.spi_cs_fb_n(fb),.spi_cs_cmd_n(cmd),.spi_sclk(sck),.spi_mosi(mosi),.spi_miso(miso),.spi_miso_oe(oe),.qualification_complete(1'b1),.installed_input(12'hfff),.installed_module_class(8'd1),.inhibit_n(1'b1),.wd_m_ok(1'b1),.wd_o_ok(1'b1),.reset_arm_ready(1'b0),.reset_arm_held(1'b1),.contactor_deenergized(1'b0),.sto_arm_expected(1'b0),.motion_critical_ports_valid(1'b1),.gate_high(4'd0),.opi_ok(4'd0),.alarm_current_raw(12'd0),.encoder_a(4'd0),.encoder_b(4'd0),.encoder_z(4'd0),.encoder_installed(4'd0),.encoder_port_valid(4'd0),.external_fault_word(32'd0),.motion_critical_io_fault(1'b0),.provider_feedback(1392'd0),.provider_status(752'd0),.physical_safety_power_word(32'd0),.step_out(steps),.dir_out(dirs),.enable_n(en_n),.session(session),.last_sequence(seq),.fault_word(fault),.config_valid(cfgv));
// Compare every original transport output on the identical physical bus. The
// extension must not alter the original command/snapshot/CRC validity behavior.
wire omiso,ooe,ofv,ofbad,ofcs,oinner,osnap,osnapcs;wire[1407:0] oframe;
cnc3_spi_transport original(.clk(clk),.rst_n(rst),.spi_cs_fb_n(fb),.spi_cs_cmd_n(cmd),.spi_sclk(sck),.spi_mosi(mosi),.feedback_payload(dut.actual_feedback_payload),.status_payload(dut.actual_status_payload),.spi_miso(omiso),.spi_miso_oe(ooe),.frame(oframe),.frame_cs_fb(ofcs),.frame_valid(ofv),.frame_bad(ofbad),.embedded_crc_good(oinner),.snapshot_start(osnap),.snapshot_cs_fb(osnapcs));
integer cycles=0,checks=0,headers=0;reg[47:0] lastheader;reg lastcs;
always@(posedge clk)begin #1;if(rst)begin
cycles=cycles+1;
if({omiso,ooe,ofv,ofbad,ofcs,oinner,osnap,osnapcs,oframe}!=={miso,oe,dut.frame_valid,dut.frame_bad,dut.frame_fb,dut.innergood,dut.snapshot_start,dut.snapshot_fb,dut.frame})$fatal(1,"original transport behavior changed");
if(dut.rejection_header_valid)begin
if(!dut.frame_bad||dut.frame_valid)$fatal(1,"rejection sideband authorized frame");
headers=headers+1;lastheader=dut.rejection_header;lastcs=dut.rejection_header_cs_fb;
end
end end
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
task check(input bit condition,input string message);begin checks=checks+1;if(!condition)$fatal(1,"%s cfg%h fault%h",message,cfgv,fault);end endtask
task transaction(input bit usefb,input[1407:0] data,input integer bits);
integer i;begin ticks(12);if(usefb)fb=0;else cmd=0;#160;
for(i=0;i<bits;i=i+1)begin mosi=i<1408?data[1407-i]:0;#80;sck=1;#80;sck=0;end
#160;fb=1;cmd=1;ticks(12);check(!oe,"physical MISO release");end endtask
task setup;
begin rst=0;fb=1;cmd=1;sck=0;ticks(5);rst=1;ticks(2200);transaction(1,cfg,1408);
check(cfgv && dut.required_mask==12'hfff,"accepted fresh actual CONFIGURE");
check(dut.state_machine.alarm_trip_mask==12'hfff && dut.state_machine.alarm_on_no_current==12'hfff,"configured both alarm masks");
check(dut.config_generation==1 && dut.config_hash==32'haabbccdd,"accepted diagnostics");headers=0;end endtask
task rejected;
begin check(!cfgv && dut.required_mask==0 && dut.state_machine.alarm_trip_mask==0 && dut.state_machine.alarm_on_no_current==0,"recognizable rejected CONFIGURE clears all validity/masks");
check(dut.config_generation==1 && dut.config_hash==32'haabbccdd && dut.config_crc==cfg[15:0],"rejection retains accepted generation/hash/CRC");
check(session==0 && seq==0 && en_n==12'hfff && steps==0 && dirs==0 && dut.permit_out_req==0 && dut.progress_m==0 && dut.progress_o==0,"rejection cannot authorize/sequence/progress");
check(headers==1 && lastheader==48'h434e43330306,"captured exact physical recognizable header");end endtask
initial begin
setup();transaction(1,cfg^1408'd1,1408);rejected();check(lastcs,"bad CRC physical CS_FB provenance");
setup();transaction(1,cfg,48);rejected();
setup();transaction(1,cfg,80);rejected();
setup();transaction(1,cfg,1409);rejected();
setup();transaction(0,cfg,768);rejected();check(!lastcs,"wrong CS physical metadata retained");
setup();transaction(1,cfg^(1408'd1<<1400),1408);check(cfgv && dut.required_mask==12'hfff,"unknown magic cannot classify as CONFIGURE");
setup();transaction(1,cfg^(1408'd1<<1368),1408);check(cfgv,"wrong ABI cannot classify as CONFIGURE");
setup();transaction(1,cfg,47);check(cfgv && headers==0,"missing sixth header byte cannot classify");
setup();transaction(0,update^(1408'd1<<640),768);check(cfgv && dut.required_mask==12'hfff && fault[0],"bad UPDATE cuts LINK but preserves configuration");
$display("REJECTION_HEADER_PASS checks=%0d exact_transport_cycle_comparisons=%0d",checks,cycles);$finish;
end
endmodule
'''.replace('module tb;','module tb;\n'+declarations)
 sources=[*sorted(HERE.glob('cnc3_*.v')),HERE/'inputs/workspace/gateware/v3/rtl/cnc3_spi_transport.v',HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 hashes={q.as_posix():sha(q) for q in sources}
 for q in sources:shutil.copyfile(q,out/q.name)
 (out/'rejection.sv').write_text(tb,encoding='utf8',newline='\n')
 files=' '.join(q.name for q in sources)
 log='';controls={}
 for label,mutate in [('baseline',False),('removed-rejection-sideband',True)]:
  folder=out/label;folder.mkdir()
  for q in sources:shutil.copyfile(out/q.name,folder/q.name)
  shutil.copyfile(out/'rejection.sv',folder/'rejection.sv')
  if mutate:
   q=folder/'cnc3_spi_transport_stateful.v';s=q.read_text();assert 'rejection_header_valid<=1;' in s;s=s.replace('rejection_header_valid<=1;','rejection_header_valid<=0;');q.write_text(s,encoding='utf8',newline='\n')
  command=f"cd '{unix(folder)}' && iverilog -g2012 -s tb -o rejection.vvp {files} rejection.sv && vvp rejection.vvp"
  r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh','-c',command],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=120)
  body=r.stdout+r.stderr;(folder/'actual.log').write_text(body,encoding='utf8',newline='\n');log+=label+'\n'+body
  controls[label]=(r.returncode==0 and 'REJECTION_HEADER_PASS' in body) if not mutate else (r.returncode!=0 and 'recognizable rejected CONFIGURE clears all validity/masks' in body)
 unchanged=all(sha(Path(q))==h for q,h in hashes.items())
 receipt={'status':'PASS' if all(controls.values()) and unchanged else 'FAIL','input_hashes':hashes,'source_unchanged':unchanged,'controls':controls,'evidence_type':'actual SPI RTL rejection metadata, original-transport cycle equivalence and compiled removal mutation','metadata_is_invalidation_only':True,'hardware_HAL_complete_endpoint_qualification':False,'detail':log[-3500:]}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);raise SystemExit(main(ap.parse_args().out.resolve()))
