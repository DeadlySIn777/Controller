from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out,baseline):
 if out.exists():raise RuntimeError('Fresh output required')
 proof=json.loads((baseline/'receipt.json').read_text());assert proof['status']=='PASS' and proof['source_unchanged']
 for p,h in proof['source_hashes'].items():assert sha(Path(p))==h
 out.mkdir(parents=True)
 original=(HERE/'cnc3_motion_state.v').read_text()
 mutations=[
 ('unmeasured-selftest-ARM','selftest_passed==2\'b11 && wd_m_ok','1\'b1 && wd_m_ok','ARM refuses untested watchdogs'),
 ('instant-selftest-flag','begin selftest_state<=1;selftest_passed[0]<=0;end','begin selftest_state<=1;selftest_passed[0]<=1;end','no instant SELFTEST flag'),
 ('immediate-DISARM','if(armed_mask!=0 && !arming)stopping<=1;','if(armed_mask!=0 && !arming)begin armed_mask<=0;stopping<=0;end','request retained while actual pulse drains'),
 ('retain-fault-continuity','pos_continuity<=pos_continuity&~armed_mask;','pos_continuity<=pos_continuity;','fault clears all armed continuity at ZERO rate'),
 ('ignore-reset-release','wd_m_ok && wd_o_ok && reset_arm_ready && !reset_arm_held','wd_m_ok && wd_o_ok && 1\'b1 && !reset_arm_held','missing reset release blocks ARM'),
 ('late-at-one-period','{1\'b0,update_interval_ticks}*33\'d2>{17\'d0,servo_period_us}*33\'d150','{1\'b0,update_interval_ticks}*33\'d2>{17\'d0,servo_period_us}*33\'d100','below1.5 period is not late'),
 ('lose-OPI-fall-proof',"else if(disarm_age>=OPI_DROP_TICKS-10'd1)begin disarm_proof<=0;fault_cut(F_STUCK);end","else if(disarm_age>=OPI_DROP_TICKS-10'd1)begin disarm_proof<=0;end",'actual stuck OPI after request drop faults at10us')]
 rows=[]
 for label,old,new,message in mutations:
  if original.count(old)!=1:raise RuntimeError('Mutation anchor nonunique: '+label)
  folder=out/label;folder.mkdir()
  for name in ['cnc3_stepgen_runtime.v','cnc3_rate_admission_serial.v','cnc3_command_validate.v','state.sv']:shutil.copyfile(baseline/name,folder/name)
  source=folder/'cnc3_motion_state.v';source.write_text(original.replace(old,new,1),encoding='utf8',newline='\n')
  command=f"cd '{unix(folder)}' && iverilog -g2012 -s tb -o state.vvp cnc3_motion_state.v cnc3_stepgen_runtime.v cnc3_rate_admission_serial.v cnc3_command_validate.v state.sv && vvp state.vvp"
  r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh','-c',command],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=600)
  text=r.stdout+r.stderr;(folder/'actual.log').write_text(text,encoding='utf8',newline='\n')
  passed=r.returncode!=0 and 'FATAL:' in text and message in text and 'STATEFUL_MOTION_PASS' not in text
  rows.append({'name':label,'compiled_mutation_sha256':sha(source),'rejected_at_expected_runtime_assertion':passed,'expected_assertion':message,'exit_code':r.returncode,'log_sha256':sha(folder/'actual.log'),'log_tail':text[-1000:]})
 unchanged=all(sha(Path(p))==h for p,h in proof['source_hashes'].items())
 receipt={'status':'PASS' if all(row['rejected_at_expected_runtime_assertion'] for row in rows) and unchanged else 'FAIL','baseline_receipt':str(baseline/'receipt.json'),'baseline_receipt_sha256':sha(baseline/'receipt.json'),'actual_original_positive_input_hashes':proof['source_hashes'],'original_sources_unchanged':unchanged,'controls':rows,'evidence_type':'actual independently compiled stateful RTL mutations and runtime assertion rejection','vendor_fit_hardware_safety_qualification':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--baseline',required=True,type=Path);a=ap.parse_args();raise SystemExit(main(a.out.resolve(),a.baseline.resolve()))
