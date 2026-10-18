import os
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out,baseline):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True)
 prefix=(baseline/'spi_motion.sv').read_text().split('initial begin\nfile=$fopen')[0]
 # The inherited monitor checks accepted pulse width while reset is released.
 # A deliberate asynchronous reset during that pulse must instead immediately
 # remove progress; the explicit final cold-state assertions check that path.
 old='if(core_cycles-progress_start!=50)$fatal'
 if prefix.count(old)!=1:raise RuntimeError('Progress monitor anchor not unique')
 prefix=prefix.replace(old,'if(rst && core_cycles-progress_start!=50)$fatal',1)
 tb=prefix+r'''
reg[1407:0] workframe,active_data;
reg[31:0] hostsession=32'h22000000,value;
integer actual_accepts=0,valid_frames=0,stream_words=0,base_accepts,base_valid,cases=0,selected,n;
bit check_stream=0,stream_fb=0,last_rate_good=0;
reg[1407:0] captured_frame;
always@(posedge clk)begin #1;if(rst)begin
 if(accepted)actual_accepts=actual_accepts+1;
 if(dut.frame_valid)begin
  valid_frames=valid_frames+1;captured_frame=dut.frame;last_rate_good=dut.frame_rates_good;
 end
 if(check_stream&&dut.rx_rate_word_valid)begin
  if(stream_fb||dut.rx_rate_channel!=stream_words||dut.rx_rate_word!==active_data[1279-32*stream_words -:32])$fatal(1,"SPI admission word/channel not actual current physical frame");
  stream_words=stream_words+1;
 end
end end
function[1407:0] reseal(input[1407:0] raw,input bit usefb);
reg[15:0] crc;reg[1407:0] copy;integer b,body;begin
crc=16'hffff;body=usefb?1392:752;
for(b=0;b<body;b=b+1)begin if(crc[15]^raw[1407-b])crc={crc[14:0],1'b0}^16'h1021;else crc={crc[14:0],1'b0};end
copy=raw;if(usefb)copy[15:0]=crc;else copy[655:640]=crc;reseal=copy;end endfunction
task wire_frame(input bit usefb,input[1407:0] data,input integer bits,input bit expected_transport_valid,input bit expected_rate_good);
integer b,before_valid;begin
ticks(12);active_data=data;stream_fb=usefb;stream_words=0;check_stream=1;before_valid=valid_frames;
if(usefb)fb=0;else cmd=0;#160;
check(!dut.frame_rates_good&&!dut.rate_frame_good&&dut.rate_channel_good==0&&!dut.rate_busy,"physical new CS clears previous admission transaction");
for(b=0;b<bits;b=b+1)begin mosi=b<1408?data[1407-b]:0;#80;sck=1;#80;sck=0;end
#160;fb=1;cmd=1;ticks(12);check_stream=0;
check(!oe,"actual MISO released after arbitrary frame");
check(valid_frames==before_valid+expected_transport_valid,"exact transport validity bound to current frame");
if(expected_transport_valid)begin
if(last_rate_good!=expected_rate_good)$display("BINDING_DIAGNOSTIC op%h input_rate0%h expected%h actual%h engine_mask%h busy%h poison%h channels%0d cases%0d",data[1367:1360],data[1279 -:32],expected_rate_good,last_rate_good,dut.rate_channel_good,dut.rate_busy,dut.rate_poisoned,dut.admission.expected_channel,cases);
check(captured_frame==(usefb?data:{data[1407:640],640'd0}),"completed metadata references exact current frame bytes");
check(last_rate_good==expected_rate_good,"rate admission latched only on current CRC valid release");
end else check(!dut.frame_rates_good,"rejected physical transaction cannot retain prior admitted flag");
check(stream_words==(usefb?0:(bits>=512?12:(bits>128?(bits-128)/32:0))),"actual physical current-frame twelve-word capture count");
end endtask
task begin_case;
begin hostsession=hostsession+1;workframe=sync;workframe[1343 -:32]=hostsession;
wire_frame(0,reseal(workframe,0),768,1,1);check(fault==0&&session==hostsession,"real new session clears recoverable fault");
workframe=arm;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=1;
wire_frame(0,reseal(workframe,0),768,1,1);check(am==12'hfff&&seq==1&&en_n==0,"real measured-proof ARM before rate case");
end endtask
task make_update(input[31:0] v,input integer ch);
begin workframe=update;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=2;workframe[1279 -:384]=0;
if(ch==12)for(n=0;n<12;n=n+1)workframe[1279-32*n -:32]=n%2?-v:v;
else workframe[1279-32*ch -:32]=v;
workframe=reseal(workframe,0);end endtask
task rate_case(input[31:0] v,input integer ch,input bit allowed);
begin begin_case();make_update(v,ch);base_accepts=actual_accepts;
wire_frame(0,workframe,768,1,allowed);cases=cases+1;
if(allowed)begin
check(actual_accepts==base_accepts+1&&seq==2&&am==12'hfff&&fault==0&&dut.rates==workframe[1279 -:384],"good actual frame atomically commits exact12 rates once");
workframe=disarm;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=3;
wire_frame(0,reseal(workframe,0),768,1,1);ticks(2400);check(am==0&&!mreq&&fault==0,"actual timed clean stop after good rate");
end else begin
check(actual_accepts==base_accepts&&seq==1&&am==0&&dut.rates==0&&!pm&&fault[0],"invalid actual streamed rate cannot commit sequence progress or rates");
check(en_n==12'hfff&&!permit,"rejected rate never receives physical output authority");end
end endtask
task abort_case(input integer bits,input bit usefb,input bit corruptcrc);
begin begin_case();make_update(32'h00800000,12);base_accepts=actual_accepts;base_valid=valid_frames;
if(corruptcrc)workframe=workframe^(1408'd1<<640);
// A sealed96-byte command followed by80 zero bytes has a zero full-length
// CRC remainder on CS_FB: transport accepts those bytes, the real static
// validator rejects the wrong-CS opcode. Neither event admits its rate tuple.
wire_frame(usefb,workframe,bits,usefb&&bits==1408&&!corruptcrc,0);
check(actual_accepts==base_accepts&&seq==1&&am==0&&dut.rates==0&&!pm&&fault[0],"abort CRC wrongCS cannot borrow prior rate authorization");
end endtask
initial begin
file=$fopen("responses.txt","w");ticks(5);rst=1;ticks(2200);
workframe=cfg;
for(n=0;n<12;n=n+1)begin
workframe[1215-64*n -:16]=100;workframe[1199-64*n -:16]=100;
workframe[1183-64*n -:16]=100;workframe[1167-64*n -:16]=100;
end
transaction("configure",1,reseal(workframe,1));
check(dut.high=={12{16'd100}}&&dut.low=={12{16'd100}},"actual configured100tick profile matches independent boundary test");
transaction("sync",0,sync);watchdog(0);watchdog(1);check(tests==3,"both real watchdog observations retained");
// Each physical word position is exercised at both signs/global boundaries.
for(selected=0;selected<12;selected=selected+1)begin
rate_case(32'h01000000,selected,1);rate_case(-32'h01000000,selected,1);
rate_case(32'h01000001,selected,0);rate_case(-32'h01000001,selected,0);
rate_case(32'h80000000,selected,0);
end
rate_case(32'h00800000,12,1);abort_case(96,0,0);rate_case(0,12,1);
abort_case(175,0,0);abort_case(511,0,0);abort_case(512,0,0);abort_case(768,0,1);abort_case(1408,1,0);abort_case(769,0,0);
rate_case(32'h00800000,12,1);
// Real CONFIGURE changes actual timing, then endpoint rejects floor+1.
workframe=cfg;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=4;
for(n=0;n<12;n=n+1)begin workframe[1215-64*n -:16]=1023;workframe[1199-64*n -:16]=1023;end
wire_frame(1,reseal(workframe,1),1408,1,0);check(cfgv&&session==0,"real timing configuration commits and resets session");
rate_case(2098176,12,1);rate_case(-2098176,0,1);rate_case(2098177,0,0);rate_case(-2098177,11,0);
// Reset destroys both a previously good transaction and an in-flight one.
begin_case();make_update(0,12);wire_frame(0,workframe,768,1,1);
rst=0;ticks(2);check(!dut.frame_rates_good&&!dut.rate_frame_good&&dut.rate_channel_good==0&&seq==0&&am==0,"reset destroys prior completed frame metadata and motion state");
rst=1;ticks(2200);ticks(12);cmd=0;#160;check(!dut.frame_rates_good,"new physicalCS reset state safe");
for(n=0;n<170;n=n+1)begin mosi=workframe[1407-n];#80;sck=1;#80;sck=0;end
rst=0;ticks(2);check(!dut.frame_rates_good&&!dut.rate_frame_good&&dut.rate_channel_good==0,"reset mid current word destroys pending admission");cmd=1;sck=0;rst=1;ticks(20);
$fclose(file);$display("SPI_ADMISSION_BINDING_PASS checks=%0d actual_rate_cases=%0d actual_accepts=%0d actual_frame_releases=%0d",checks,cases,actual_accepts,valid_frames);$finish;
end
endmodule
'''
 (out/'binding.sv').write_text(tb,encoding='utf8',newline='\n')
 sources=[*sorted(HERE.glob('cnc3_*.v')),HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 hashes={str(q):sha(q) for q in sources};rows=[]
 mutations=[('baseline',None,None,None),('admission-unbound-true',HERE/'cnc3_spi_transport_stateful.v',('frame_rates_good<=!selected_fb && rate_frame_good;',"frame_rates_good<=!selected_fb;"),'rate admission latched only on current CRC valid release'),('no-new-CS-clear',HERE/'cnc3_spi_transport_stateful.v',('active<=1;selected_fb<=fb_start;frame_rates_good<=0;','active<=1;selected_fb<=fb_start;frame_rates_good<=frame_rates_good;'),'physical new CS clears previous admission transaction')]
 for label,path,delta,assertion in mutations:
  folder=out/label;folder.mkdir()
  for q in sources:shutil.copyfile(q,folder/q.name)
  shutil.copyfile(out/'binding.sv',folder/'binding.sv')
  if delta:
   body=path.read_text();assert body.count(delta[0])==1;(folder/path.name).write_text(body.replace(*delta,1),encoding='utf8',newline='\n')
  files=' '.join(q.name for q in sources)
  cmd=f"cd '{unix(folder)}' && iverilog -g2012 -s tb -o binding.vvp {files} binding.sv && vvp binding.vvp"
  r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh','-c',cmd],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
  log=r.stdout+r.stderr;(folder/'actual.log').write_text(log,encoding='utf8',newline='\n')
  ok=r.returncode==0 and 'SPI_ADMISSION_BINDING_PASS' in log if delta is None else r.returncode!=0 and 'FATAL:' in log and assertion in log
  rows.append({'name':label,'passed':ok,'expected_runtime_assertion':assertion,'log_sha256':sha(folder/'actual.log'),'detail':log[-1600:]})
 unchanged=all(sha(Path(q))==h for q,h in hashes.items())
 receipt={'status':'PASS' if unchanged and all(x['passed'] for x in rows) else 'FAIL','source_hashes':hashes,'source_unchanged':unchanged,'baseline_prefix_sha256':hashlib.sha256(prefix.encode()).hexdigest(),'controls':rows,'evidence_type':'actual synchronized mode0 SPI reception, CRC/CS release, current-word shared serial admission, stateful commit and actual12 generators','request_backpressure_queue_integrated':False,'request_processing':'actual one-core-cycle accept/reject; every request_ready is true because no multi-cycle pending consumer exists in this motion scope','public_structural_endpoint_queue_is_separate':True,'physical_provider_inputs':'explicit ideal simulation only','HAL_full_IO_pages_vendor_fit_physical_qualification':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);a=ap.parse_args();raise SystemExit(main(a.out.resolve(),a.baseline.resolve()))
