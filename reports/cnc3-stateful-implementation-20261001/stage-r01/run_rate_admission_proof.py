from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out,baseline):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('p3',ROOT/'gateware/v3/frozen/protocol_v3.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p._SPEC=p.Spec(str(ROOT/'gateware/v3/frozen/spec/protocol.json'))
 profiles=[(100,100),(100,155),(1023,1023),(101,900),(1023,100)]
 rows=[];declarations=[]
 for i,(h,l) in enumerate(profiles):
  timing={f'timing_{ch}':[h,l,100,100] for ch in range(12)}
  raw=p.encode_configure(expected_module_class=1,required_mask=0xfff,**timing)
  declarations.append(f"localparam[1407:0] profile{i}=1408'h{raw.hex()};")
  rows.append({'high':h,'low':l,'actual_generator_period':h+l+1,'timing_cap':(1<<32)//(h+l+1),'admission_cap':min(0x01000000,(1<<32)//(h+l+1))})
 prefix=(baseline/'state.sv').read_text().split('initial begin\ncold();')[0]
 prefix=prefix.replace('module tb;','module tb;\n'+'\n'.join(declarations),1)
 tb=prefix+r'''
reg[31:0] hostsession=32'h55667788,sessioncounter=32'h90000000,hostseq=2;
reg[1407:0] workframe;integer profile,channel,cases=0;reg[31:0] cap;
function[1407:0] reseal(input[1407:0] raw,input bit usefb);
reg[15:0] crc;reg[1407:0] copy;integer b,body;begin
crc=16'hffff;body=usefb?1392:752;
for(b=0;b<body;b=b+1)begin
if(crc[15]^raw[1407-b])crc={crc[14:0],1'b0}^16'h1021;else crc={crc[14:0],1'b0};end
copy=raw;if(usefb)copy[15:0]=crc;else copy[655:640]=crc;reseal=copy;end endfunction
task config_profile(input[1407:0] raw);
begin workframe=raw;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=hostsession?hostseq+1:0;
send(reseal(workframe,1));check(cfgv&&sess==0,"valid timing profile commits atomically");hostsession=0;hostseq=0;end endtask
task begin_case;
begin sessioncounter=sessioncounter+1;hostsession=sessioncounter;
workframe=sync2;workframe[1343 -:32]=hostsession;send(reseal(workframe,0));check(fw==0,"explicit new SYNC before independent case");
workframe=arm;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=1;send(reseal(workframe,0));hostseq=1;ticks(8);
check(am==12'hfff&&enable==12'hfff,"real observed ARM for admission case");end endtask
task rate_case(input[31:0] value,input integer selected,input bit allowed);
begin begin_case();workframe=update;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=2;workframe[1279 -:384]=0;
if(selected==12)begin for(j=0;j<12;j=j+1)workframe[1279-32*j -:32]=j%2?-value:value;end
else workframe[1279-32*selected -:32]=value;
workframe=reseal(workframe,0);send(workframe);cases=cases+1;
if(allowed)begin
check(am==12'hfff&&seq==2&&accepted&&rates==workframe[1279 -:384]&&pm,"valid host rate admitted atomically");hostseq=2;
workframe=disarm;workframe[1343 -:32]=hostsession;workframe[1311 -:32]=3;send(reseal(workframe,0));hostseq=3;ticks(2300);
check(am==0&&!mreq&&!fw[3],"actual clean no-timing-fault stop");
end else begin
check(am==0&&seq==1&&!accepted&&rates==0&&!pm&&fw[0]&&cfgv,"bad rate rejected atomically before admission");
check(enable==0&&!permit,"bad rate never receives actuator authority");end
end endtask
initial begin
cold();send(cfg);send(sync2);test_watchdog(0);test_watchdog(1);
for(profile=0;profile<5;profile=profile+1)begin
case(profile)
0:begin config_profile(profile0);cap=32'd16777216;end
1:begin config_profile(profile1);cap=32'd16777216;end
2:begin config_profile(profile2);cap=32'd2098176;end
3:begin config_profile(profile3);cap=32'd4286394;end
4:begin config_profile(profile4);cap=32'd3821145;end
endcase
rate_case(cap,12,1);
for(channel=0;channel<12;channel=channel+1)begin
rate_case(cap,channel,1);rate_case(-cap,channel,1);
rate_case(cap+1,channel,0);rate_case(-(cap+1),channel,0);
rate_case(32'h80000000,channel,0);rate_case(0,channel,1);
end
end
$display("RATE_ADMISSION_PASS checks=%0d actual_cases=%0d actual_generators=12",checks,cases);$finish;
end
endmodule
'''
 (out/'rate.sv').write_text(tb,encoding='utf8',newline='\n')
 paths=[HERE/'cnc3_motion_state.v',HERE/'cnc3_stepgen_runtime.v',HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v'];hashes={q.as_posix():sha(q) for q in paths}
 original=paths[0].read_text();controls=[]
 variants=[('baseline',None,None),('removed-global-clamp',"magnitude<=32'h01000000 &&","1'b1 &&"),('removed-timing-validity',"period_product<=36'd4294967296","1'b1")]
 for label,old,new in variants:
  folder=out/label;folder.mkdir()
  for q in paths:shutil.copyfile(q,folder/q.name)
  shutil.copyfile(out/'rate.sv',folder/'rate.sv')
  if old:
   assert original.count(old)==1
   (folder/'cnc3_motion_state.v').write_text(original.replace(old,new,1),encoding='utf8',newline='\n')
  command=f"cd '{unix(folder)}' && iverilog -g2012 -s tb -o rate.vvp cnc3_motion_state.v cnc3_stepgen_runtime.v cnc3_command_validate.v rate.sv && vvp rate.vvp"
  r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh','-c',command],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=600)
  log=r.stdout+r.stderr;(folder/'actual.log').write_text(log,encoding='utf8',newline='\n')
  passed=(r.returncode==0 and 'RATE_ADMISSION_PASS' in log) if not old else (r.returncode!=0 and 'bad rate rejected atomically before admission' in log)
  controls.append({'name':label,'passed':passed,'actual_compiled_source_sha256':sha(folder/'cnc3_motion_state.v'),'log_sha256':sha(folder/'actual.log'),'detail':log[-1000:]})
 unchanged=all(sha(Path(q))==h for q,h in hashes.items())
 receipt={'status':'PASS' if all(c['passed'] for c in controls) and unchanged else 'FAIL','input_hashes':hashes,'source_unchanged':unchanged,'cases':rows,'controls':controls,'global_protocol_MAX_RATE':16777216,'global_protocol_cap_pps_at_50MHz':195312.5,'timing_validity':'unsigned abs32; validated high/low100..1023; exact36-bit magnitude25*(high+low+1)11<=2^32','drive_machine_limits_remain_host_duty':True,'no_ABI_rate_or_hardware_rating_change':True,'vendor_fit_physical_or_full_HAL_qualification':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--baseline',required=True,type=Path);a=ap.parse_args();raise SystemExit(main(a.out.resolve(),a.baseline.resolve()))
