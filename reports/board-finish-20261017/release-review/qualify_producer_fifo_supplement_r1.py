"""Independent focused producer-FIFO commit/head/wrap supplement, frozen inputs."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time
H=Path(__file__).resolve().parent;RUN=H.parent/'event-producer-fifo-r1';OUT=H/'producer-fifo-independent-supplement-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    assert not OUT.exists();OUT.mkdir()
    prep=json.loads((RUN/'preparation-receipt.json').read_bytes())
    selected=RUN/'cnc3_runtime_events.v';assert sha(selected)==prep['candidate_SHA256']=='4d21b8af4ca2decc10d872361fb033fcaecb939b14ff4d62d959609cdc2f30d6'
    assert (RUN/'candidate_diff.v').read_text().replace('module cnc3_runtime_events_candidate(', 'module cnc3_runtime_events(')==selected.read_text()
    canonical=H.parents[2]/'gateware/v3/runtime/cnc3_runtime_events.v'
    assert sha(canonical)==prep['original_SHA256']
    assert (RUN/'original_diff.v').read_text().replace('module cnc3_runtime_events_original(', 'module cnc3_runtime_events(')==canonical.read_text()
    for f in ['original_diff.v','candidate_diff.v','cnc3_runtime_events.v']:shutil.copyfile(RUN/f,OUT/f)
    bank=H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v';shutil.copyfile(bank,OUT/'cnc3_event_bank.v')
    harness=RUN/'boundary_tb.sv';prefix=harness.read_text().split(' initial begin\n')[0].replace('module event_dispatch_diff_tb;', 'module producer_fifo_supplement_tb;')
    prefix=prefix.replace('integer ledger_checks=0,admission_checks=0;', 'integer ledger_checks=0,admission_checks=0,stop_pending=0,postcommit_checks=0;')
    token='  if(seed_mode==0)p=6;else p=s%7;'
    assert prefix.count(token)==1
    prefix=prefix.replace(token,'  if(seed_mode==0)p=6;else if(seed_mode>=2 && seed_mode<=8)p=seed_mode-2;else if(seed_mode>=9)p=(s+seed_mode-9)%7;else p=s%7;')
    token='  queue_check;index_pulse=0;fault_word=0;ack_commit=0;tick;tick;'
    assert prefix.count(token)==1
    prefix=prefix.replace(token,'  queue_check;index_pulse=0;fault_word=0;ack_commit=0;if(!stop_pending)begin tick;tick;queue_check;postcommit_checks=postcommit_checks+1;end')
    tail=''' task drain_all;
 integer q,starting;
 begin
  starting=old.count;
  for(q=0;q<starting;q=q+1)begin
   if(oh[159:152]===8'd0)$fatal(1,"head unexpectedly masked before delivery");
   cmd_snapshot=1;tick;cmd_snapshot=0;cmd_complete=1;tick;cmd_complete=0;
   ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;queue_check;postcommit_checks=postcommit_checks+1;
  end
  if(old.count!==0 || dut.count!==0)$fatal(1,"focused queue did not drain");
 end endtask
 task external_seven_pending;
 begin
  index_request=0;probe_request=0;arm_commit=1;probe_raw=0;fault_word=0;index_pulse=0;tick;arm_commit=0;tick;tick;tick;
  index_request=15;probe_request=3;arm_commit=1;tick;arm_commit=0;
  probe_raw=3;tick;tick;index_pulse=15;fault_word=1;tick;
  if(old.count!==7 || $countones(dut.write_enable)!==7)$fatal(1,"focused external seven producers were not pending");
  queue_check;index_pulse=0;fault_word=0;
 end endtask
 integer producer,rotate;
 initial begin
  // Each producer alone holds all256 entries, including same-producer
  // full pop+append at every near-wrap local read/write alignment.
  for(producer=0;producer<7;producer=producer+1)begin
   seed_mode=producer+2;
   for(wb=0;wb<8;wb=wb+1)begin
    mask=1<<producer;free_slots=0;seq_value=255;ackcase=1;
    boundary_case(mask,wb,free_slots,seq_value,ackcase);
    if(wb==0)drain_all;
   end
  end
  // Every producer becomes global head; drain across all seven cached RAM
  // heads and local wrap positions, with new seven-way admission mixed in.
  for(rotate=0;rotate<7;rotate=rotate+1)begin
   seed_mode=9+rotate;
   for(wb=0;wb<8;wb=wb+1)begin
    mask=127;free_slots=248;seq_value=254;ackcase=1;
    boundary_case(mask,wb,free_slots,seq_value,ackcase);drain_all;
   end
  end
  // Empty producers must mask stale tags, before/after physical commit.
  for(producer=0;producer<7;producer=producer+1)begin
   seed_mode=producer+2;mask=1<<producer;wb=7;free_slots=256;seq_value=1;ackcase=0;
   boundary_case(mask,wb,free_slots,seq_value,ackcase);drain_all;
  end
  seed_mode=9;mask=127;wb=7;free_slots=256;seq_value=255;ackcase=0;
  boundary_case(mask,wb,free_slots,seq_value,ackcase);drain_all;
  // Real external stimulus: clear while seven RAM writes are pending.
  // Their stale tag0..6 contents remain physically present after clear.
  reset;external_seven_pending;clear=1;tick;clear=0;tick;tick;queue_check;
  external_seven_pending;tick;tick;queue_check;postcommit_checks=postcommit_checks+1;drain_all;
  // Repeat through asynchronous reset while writes are pending, with
  // literal X/Z payload bits and no RAM array reset.
  reset;step_counts={12{24'hz0x123}};index_counts={4{24'hx12z45}};encoder_counts={4{24'hz123x5}};
  external_seven_pending;rst_n=0;#1;compare;tick;rst_n=1;tick;
  external_seven_pending;tick;tick;queue_check;postcommit_checks=postcommit_checks+1;drain_all;
  $display("PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS cycles=%0d boundary_cases=%0d postcommit_checks=%0d live_record_checks=%0d admission_checks=%0d all7producer_full_pop_append=PASS rotated_head_drains=PASS empty_stale_clear_reset=PASS",cycles,cases,postcommit_checks,ledger_checks,admission_checks);$finish;
 end
endmodule
'''
    bench=OUT/'supplement_tb.sv';bench.write_text(prefix+tail)
    paths=[OUT/'original_diff.v',OUT/'candidate_diff.v',OUT/'cnc3_event_bank.v',bench]
    inputs={str(p):sha(p) for p in [Path(__file__),selected,harness,*paths]};runs=[];started=time.time()
    for name,args in [('compile',['iverilog','-g2012','-s','producer_fifo_supplement_tb','-o',linux(OUT/'supplement.vvp'),*map(linux,paths)]),('execute',['vvp',linux(OUT/'supplement.vvp')])]:
        argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
        r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
        log=OUT/(name+'.log');log.write_bytes(r.stdout);row={'name':name,'argv':argv,'exit':r.returncode,'log_SHA256':sha(log)};runs.append(row)
        print(json.dumps(row),flush=True);print(r.stdout.decode(errors='replace')[-2000:],flush=True)
        if r.returncode:break
    selected_still_same=sha(selected)==prep['candidate_SHA256']
    rec={'status':'PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS' if len(runs)==2 and all(r['exit']==0 for r in runs) else 'FAIL','executions':runs,'elapsed_seconds':time.time()-started,'selected_candidate_SHA256':prep['candidate_SHA256'],'candidate_diff_normalization_equals_selected_source':True,'original_diff_normalization_equals_canonical':True,'selected_live_source_still_same':selected_still_same,'canonical_unchanged':sha(canonical)==prep['original_SHA256'],'scope':'frozen independent copy; per-producer full256 ACK+append, post-commit physical live ledgers, every producer head/interleaved drain and local pointer wrap, empty/stale-tag clear/reset with pending seven writes, X/Z payloads','main110592matrix_duplicated':False,'input_SHA256':inputs,'adopted':False,'physical_fit_timing':'OPEN'}
    (OUT/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'status':rec['status'],'elapsed_seconds':rec['elapsed_seconds']}),flush=True)
    return 0 if rec['status']!='FAIL' else 1
if __name__=='__main__':raise SystemExit(main())
