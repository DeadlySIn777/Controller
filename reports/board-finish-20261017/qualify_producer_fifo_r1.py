"""Compare different memory organizations by outputs, admission, and live records."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import psutil
H=Path(__file__).resolve().parent;OUT=H/'event-producer-fifo-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    source=H/'release-review/event-capture-select-r2/boundary_tb.sv'
    s=source.read_text()
    s=s.replace('integer mask,wb,free_slots,seqcase,ackcase,a,z,seq_value;',
     'integer mask,wb,free_slots,seqcase,ackcase,a,z,seq_value,seed_mode=0;\n integer ledger_checks=0,admission_checks=0;')
    a=s.index(' task compare;');b=s.index(' task tick;',a)
    s=s[:a]+''' function integer producer_of;
 input [159:0] value;
 begin
  case(value[151:144])
   1:producer_of=value[143:136];2:producer_of=2+value[143:136];3:producer_of=6;
   default:producer_of=-1;
  endcase
 end endfunction
 task compare;
 integer p,q,total,seen;reg[159:0] value;reg[7:0] tag;
 begin
  if({oh,os,oi,op,oo} !== {nh,ns,ni,np,no} ||
    {old.rd,old.wr,old.count,old.next_sequence,old.snapshot_sequence,old.delivered_sequence,old.prefetched_rd,
     old.index_level,old.probe_level,old.probe_armed,old.probe_overrun,old.probe_sync1,old.probe_sync2,old.filtered,
     old.stable[0],old.stable[1],old.previous_fault} !==
    {dut.rd,dut.wr,dut.count,dut.next_sequence,dut.snapshot_sequence,dut.delivered_sequence,dut.prefetched_rd,
     dut.index_level,dut.probe_level,dut.probe_armed,dut.probe_overrun,dut.probe_sync1,dut.probe_sync2,dut.filtered,
     dut.stable[0],dut.stable[1],dut.previous_fault})begin
   $display("FAIL cycle=%0d case=%0d mask=%0d offset=%0d free=%0d seq=%0d ACK=%0d seed=%0d oldcount=%0d newcount=%0d oldhead=%h newhead=%h oldrd=%0d newrd=%0d localvalid=%b",cycles,cases,mask,wb,free_slots,seq_value,ackcase,seed_mode,old.count,dut.count,oh,nh,old.rd,dut.rd,dut.producer_head_valid);
   $fatal(1,"public/global/filter event state differs");
  end
  total=0;
  for(p=0;p<7;p=p+1)begin
   total=total+dut.producer_count[p];
   if(dut.producer_wr[p] !== 8'(dut.producer_rd[p]+dut.producer_count[p]))
    $fatal(1,"local pointer/count invariant differs producer=%0d",p);
  end
  if(total!==int'(old.count))$fatal(1,"local/global occupancy differs");
  seen=0;
  for(q=0;q<8;q=q+1)if(old.write_enable[q])begin
   value=old.write_data[160*q +:160];tag={old.write_address[5*q +:5],3'(q)};
   p=producer_of(value);
   if(p<0 || p>6 || (seen&(1<<p)))$fatal(1,"invalid/duplicate admitted producer");
   seen=seen|(1<<p);
   if(dut.write_enable[p]!==1'b1 || dut.write_data[168*p +:168]!=={tag,value})
    $fatal(1,"normalized admitted record differs producer=%0d",p);
   admission_checks=admission_checks+1;
  end
  if(7'(seen)!==dut.write_enable)$fatal(1,"normalized admission enables differ");
 end endtask
'''+s[b:]
    a=s.index(' task memory_word;');b=s.index(' task boundary_case;',a)
    old_set='\n'.join(f' {i}:old.banks[{i}].memory.memory[slot/8]=value;' for i in range(8))
    old_get='\n'.join(f' {i}:old_word=old.banks[{i}].memory.memory[slot/8];' for i in range(8))
    new_set='\n'.join(f' {i}:dut.producers[{i}].memory.memory[address]=value;' for i in range(7))
    new_get='\n'.join(f' {i}:new_word=dut.producers[{i}].memory.memory[address];' for i in range(7))
    s=s[:a]+f''' task memory_word;
 input integer slot;input [159:0] value;
 begin case(slot%8)
{old_set}
 endcase end endtask
 function [159:0] old_word;
 input integer slot;
 begin
 case(slot%8)
{old_get}
 endcase
 if(old.write_enable[slot%8] && old.write_address[5*(slot%8) +:5]==5'(slot/8))
  old_word=old.write_data[160*(slot%8) +:160];
 end endfunction
 task producer_word;
 input integer producer,address;input[167:0]value;
 begin case(producer)
{new_set}
 endcase end endtask
 function [167:0] new_word;
 input integer producer,address;
 begin case(producer)
{new_get}
 endcase
 if(dut.write_enable[producer] && dut.write_address[8*producer +:8]==8'(address))
  new_word=dut.write_data[168*producer +:168];
 end endfunction
 task queue_check;
 integer seen[0:6];integer n,p,slot,address;reg[159:0]value;
 begin
 for(p=0;p<7;p=p+1)seen[p]=0;
 for(n=0;n<old.count;n=n+1)begin
  slot=(int'(old.rd)+n)%256;value=old_word(slot);p=producer_of(value);
  if(p<0 || p>6)$fatal(1,"invalid logical record");
  address=(int'(dut.producer_rd[p])+seen[p])%256;
  if(new_word(p,address)!=={{8'(slot),value}})
   $fatal(1,"normalized live queue differs offset=%0d producer=%0d address=%0d",n,p,address);
  seen[p]=seen[p]+1;ledger_checks=ledger_checks+1;
 end
 for(p=0;p<7;p=p+1)if(seen[p]!==int'(dut.producer_count[p]))
  $fatal(1,"normalized queue count differs producer=%0d",p);
 end endtask
 task seed_queue;
 input integer r,n,nextseq;
 integer p,s,slot,address;reg[159:0]value;
 begin
 for(p=0;p<7;p=p+1)begin
  dut.producer_rd[p]=8'(248+((seed_mode*37+p*31+wb)%8));
  dut.producer_prefetched_rd[p]=dut.producer_rd[p];
  dut.producer_wr[p]=dut.producer_rd[p];dut.producer_count[p]=0;
 end
 for(s=0;s<n;s=s+1)begin
  slot=(r+s)%256;value=record(slot,r,n,nextseq);
  if(seed_mode==0)p=6;else p=s%7;
  if(p<2)begin value[151:144]=1;value[143:136]=8'(p);end
  else if(p<6)begin value[151:144]=2;value[143:136]=8'(p-2);end
  else begin value[151:144]=3;value[143:136]=8'(slot);end
  memory_word(slot,value);address=dut.producer_wr[p];
  producer_word(p,address,{{8'(slot),value}});
  dut.producer_wr[p]=dut.producer_wr[p]+8'd1;
  dut.producer_count[p]=dut.producer_count[p]+9'd1;
 end
 end endtask
'''+s[b:]
    s=s.replace('  for(s=0;s<256;s=s+1)memory_word(s,record(s,r,n,nextseq));',
      '  seed_queue(r,n,nextseq);')
    s=s.replace('  index_pulse=0;fault_word=0;ack_commit=0;tick;tick;',
      '  queue_check;index_pulse=0;fault_word=0;ack_commit=0;tick;tick;')
    s=s.replace('  for(mask=0;mask<128;mask=mask+1)',
      '  for(seed_mode=0;seed_mode<2;seed_mode=seed_mode+1)\n  for(mask=0;mask<128;mask=mask+1)')
    s=s.replace('   ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;',
      '   ack=oh[159:152];ack_commit=1;tick;ack_commit=0;tick;queue_check;')
    s=s.replace('   tick;\n  end\n  $display(',
      '   tick;if(a%101==0)queue_check;\n  end\n  $display(')
    s=s.replace('EVENT_DISPATCH_DIFF_PASS boundary_cases=', 'PRODUCER_FIFO_DIFF_PASS boundary_cases=')
    s=s.replace('external_random_cycles=30000",cases,cycles,seven,acks,fulls,wraps)',
      'external_random_cycles=30000 live_record_checks=%0d admission_checks=%0d",cases,cycles,seven,acks,fulls,wraps,ledger_checks,admission_checks)')
    tb=OUT/'boundary_tb.sv';assert not tb.exists();tb.write_text(s)
    spec=importlib.util.spec_from_file_location('guard',H/'run_efinity_ram_inference_r1.py')
    A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);A.OUT=OUT
    paths=[OUT/'original_diff.v',OUT/'candidate_diff.v',H/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v',tb]
    rows=[]
    for phase,args in [('compile',['iverilog','-g2012','-s','event_dispatch_diff_tb','-o',linux(OUT/'boundary.vvp'),*map(linux,paths)]),('execute',['vvp',linux(OUT/'boundary.vvp')])]:
        argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
        result=A.run_guarded(argv,OUT,'boundary-'+phase)
        log=OUT/('boundary-'+phase+'.console.log');row={'phase':phase,'argv':argv,**result,'log_SHA256':sha(log)};rows.append(row)
        print(json.dumps(row),flush=True);print(log.read_text(errors='replace')[-2500:],flush=True)
        if result['exit']:break
    canonical=H.parent.parent/'gateware/v3/runtime/cnc3_runtime_events.v'
    prep=json.loads((OUT/'preparation-receipt.json').read_bytes())
    assert sha(canonical)==prep['original_SHA256']
    passed=len(rows)==2 and all(r['exit']==0 for r in rows) and 'PRODUCER_FIFO_DIFF_PASS' in log.read_text()
    rec={'status':'PRODUCER_FIFO_DIFFERENTIAL_PASS' if passed else 'FAIL','executions':rows,'scope':'110592 seeded boundary cases across two legal storage organizations; public/global/filter state; all admitted records; complete normalized live queue after each boundary; external-only capacity/overflow/delivery/clear/reset and30000stresscycles with payload/control X/Z','structural_organization':'seven independent256depth168bit tagged producer FIFOs; global256admission and original sequence/order preserved','not_claimed':['arbitrary illegal internal state equivalence','formal equivalence','device fit/timing','hardware'], 'input_SHA256':{str(p):sha(p) for p in [Path(__file__),source,*paths]},'canonical_unchanged':True,'adopted':False}
    (OUT/'behavior-receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'status':rec['status']}),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
