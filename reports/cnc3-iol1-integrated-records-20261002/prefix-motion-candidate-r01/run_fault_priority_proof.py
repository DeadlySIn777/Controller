import os
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out,baseline,expect_failure):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('p3',HERE/'inputs/workspace/gateware/v3/frozen/protocol_v3.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p._SPEC=p.Spec(str(HERE/'inputs/workspace/gateware/v3/frozen/spec/protocol.json'))
 def cmd(op,seq,mask=0):return p.encode_command(op,session=0x55667788,sequence=seq,channel_mask=mask)[1]
 frames={'edgearm':cmd(2,3,0xfff),'edgeupdate':p.encode_update(session=0x55667788,sequence=4,rates=[0x800000]*12,channel_mask=0xfff)}
 declarations='\n'.join(f"localparam[1407:0] {n}=1408'h{(b+bytes(176-len(b))).hex()};" for n,b in frames.items())
 original=(baseline/'state.sv').read_text();assert original.count('initial begin\ncold();')==1
 prefix=original.split('initial begin\ncold();')[0].replace('module tb;','module tb;\n'+declarations,1)
 tb=prefix+r'''initial begin
cold();send(cfg);send(sync2);test_watchdog(0);test_watchdog(1);
autoopi=0;opi=0;send(edgearm);check(am==12'hfff && d.arming,"real pending ARM without final OPI");
scan_admission(edgeupdate);check(admission_good,"real serial admission completed before fault edge");
while(d.arming_age!=499)@(negedge clk);
frame=edgeupdate;#1;check(structural==0,"real exact-edge UPDATE structural acceptance");rv=1;
@(negedge clk);rv=0;#1;
check(fw[10] && am==0 && enable==0,"arming timeout physical fault dominates UPDATE");
check(rates==0 && pm==0 && !accepted && seq==3,"fault cannot be overwritten by UPDATE acceptance/progress/rates");
cold();send(cfg);check(cfgv && gen==1,"new qualified config");
installed=12'h0ff;send(cfg);
check(fw[5] && im==0 && !accepted && !cfgv && rm==0,"same-cycle qualification loss cannot accept CONFIGURE");
check(gen==1 && chash==32'haabbccdd && ccrc==cfg[15:0],"rejected qualification CONFIGURE retains diagnostic identity");
$display("FAULT_PRIORITY_PASS checks=%0d",checks);$finish;
end
endmodule
'''
 (out/'state.sv').write_text(tb,encoding='utf8',newline='\n')
 paths=[HERE/'cnc3_motion_state.v',HERE/'cnc3_stepgen_runtime.v',HERE/'cnc3_rate_admission_serial.v',HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 hashes={q.as_posix():sha(q) for q in paths}
 for q in paths:shutil.copyfile(q,out/q.name)
 command=f"cd '{unix(out)}' && iverilog -g2012 -s tb -o state.vvp cnc3_motion_state.v cnc3_stepgen_runtime.v cnc3_rate_admission_serial.v cnc3_command_validate.v state.sv && vvp state.vvp"
 r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh','-c',command],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=600)
 log=r.stdout+r.stderr;(out/'actual.log').write_text(log,encoding='utf8',newline='\n')
 observed_bug=r.returncode!=0 and 'fault cannot be overwritten by UPDATE acceptance/progress/rates' in log
 passed=observed_bug if expect_failure else r.returncode==0 and 'FAULT_PRIORITY_PASS' in log
 unchanged=all(sha(Path(q))==h for q,h in hashes.items())
 receipt={'status':'PASS' if passed and unchanged else 'FAIL','baseline_has_actual_confirmed_fault_priority_bug':observed_bug,'expected_historical_failure':expect_failure,'actual_fixed_edge_controls_pass':passed and not expect_failure,'input_hashes':hashes,'source_unchanged':unchanged,'testbench_sha256':sha(out/'state.sv'),'detail':log[-2000:],'hardware_vendor_HAL_qualification':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--baseline',required=True,type=Path);ap.add_argument('--expect-historical-failure',action='store_true');a=ap.parse_args();raise SystemExit(main(a.out.resolve(),a.baseline.resolve(),a.expect_historical_failure))
