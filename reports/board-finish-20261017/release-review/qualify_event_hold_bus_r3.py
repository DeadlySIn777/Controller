"""Actual four-state selector exhaustion and strict event boundary differential."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;OUT=H/'event-hold-disabled-bus-r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    prefix=(OUT/'boundary_tb.sv').read_text().split(' initial begin\n')[0].replace('module event_dispatch_diff_tb;', 'module event_selector_tb;')
    bench=OUT/'selector_tb.sv'
    bench.write_text(prefix+''' reg [7:0] selector;
 integer profile,pattern,bitno,selector_checks=0,unknown_checks=0;
 reg [23:0] previous_result;
 initial begin
  reset;
  for(profile=0;profile<3;profile=profile+1)begin
   case(profile)
    0:begin step_counts=288'h0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789;encoder_counts=96'hf123456789abcdef01234567;end
    1:begin step_counts={12{24'hz0x123}};encoder_counts={4{24'hx12z45}};end
    2:begin step_counts={12{24'h5az0x9}};encoder_counts={4{24'hz12x45}};end
   endcase
   for(pattern=0;pattern<65536;pattern=pattern+1)begin
    for(bitno=0;bitno<8;bitno=bitno+1)begin
     case((pattern>>(2*bitno))&3)
      0:selector[bitno]=0;1:selector[bitno]=1;2:selector[bitno]=1'bx;3:selector[bitno]=1'bz;
     endcase
    end
    #1;
    if(old.capture(selector)!==dut.capture(selector))$fatal(1,"capture selector differs profile=%0d pattern=%0d selector=%b",profile,pattern,selector);
    if($isunknown(selector))begin
     unknown_checks=unknown_checks+1;
     if(dut.capture(selector)!==24'd0)$fatal(1,"unknown selector did not return zero");
    end else if((selector>=12 && selector<16) || selector>=20)begin
     if(dut.capture(selector)!==24'd0)$fatal(1,"invalid known selector did not return zero");
    end
    selector_checks=selector_checks+1;
   end
  end
  $display("EVENT_SELECTOR_EXHAUSTION_PASS checks=%0d unknown_selector_checks=%0d profiles=3 all256known_values=PASS all65536four_state_values=PASS literal_payload_XZ=PASS",selector_checks,unknown_checks);$finish;
 end
endmodule
''')
    paths=[OUT/'original_diff.v',OUT/'candidate_diff.v',H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v']
    executions=[]
    for name,top,tb in [('selector','event_selector_tb',bench),('boundary','event_dispatch_diff_tb',OUT/'boundary_tb.sv')]:
        for phase,args in [('compile',['iverilog','-g2012','-s',top,'-o',linux(OUT/(name+'.vvp')),*map(linux,paths),linux(tb)]),('execute',['vvp',linux(OUT/(name+'.vvp'))])]:
            argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
            r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
            log=OUT/(name+'-'+phase+'.log');log.write_bytes(r.stdout)
            row={'name':name+'-'+phase,'argv':argv,'exit':r.returncode,'log_SHA256':sha(log)};executions.append(row)
            print(json.dumps(row),flush=True);print(r.stdout.decode(errors='replace')[-1500:],flush=True)
            if r.returncode:break
        if executions[-1]['exit']:break
    prep=json.loads((OUT/'preparation-receipt.json').read_bytes())
    source=H.parents[2]/'gateware/v3/runtime/cnc3_runtime_events.v';assert sha(source)==prep['canonical_reference_SHA256']
    record={'status':'CAPTURE_HELD_DISABLED_BUS_MASKED_BOUNDARY_DIFFERENTIAL_PASS' if len(executions)==4 and all(r['exit']==0 for r in executions) else 'FAIL','executions':executions,'selector_patterns_per_profile':65536,'payload_profiles':3,'known_invalid_selectors':'12..15 and20..255 return0','unknown_selectors':'all65280X/Z-containing8-bit patterns perprofile return0','boundary_cases':55296,'boundary_comparison':'full write_enable plus enabled-bank address/data equality; public outputs and queue state exact; disabled bus differences explicitly counted; same seeded-state and30000externalstress scope as r1','canonical_sources_unchanged':True,'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'input_SHA256':{str(p):sha(p) for p in [Path(__file__),*paths,bench,OUT/'boundary_tb.sv']},'adopted':False,'formal_equivalence':'NOT_RUN','physical_wrapper_fit_timing':'OPEN'}
    (OUT/'behavior-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':record['status']}),flush=True)
    return 0 if record['status']!='FAIL' else 1
if __name__=='__main__':raise SystemExit(main())
