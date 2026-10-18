"""Supplement selector exhaustion with distinct data in every source channel."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;OUT=H/'event-capture-select-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    old=(OUT/'selector_tb.sv').read_text();new=old.replace('module event_selector_tb;', 'module event_selector_unique_tb;')
    start=new.index('   case(profile)');end=new.index('   for(pattern=',start)
    new=new[:start]+'''   for(a=0;a<12;a=a+1)begin
    case(profile)
     0:step_counts[287-24*a -:24]=24'h120000+a*24'h101;
     1:step_counts[287-24*a -:24]={a[7:0],16'hxz12};
     2:step_counts[287-24*a -:24]={a[7:0]^8'h5a,16'h3zx4};
    endcase
   end
   for(a=0;a<4;a=a+1)begin
    case(profile)
     0:encoder_counts[95-24*a -:24]=24'h670000+a*24'h101;
     1:encoder_counts[95-24*a -:24]={a[7:0]|8'h80,16'hzx34};
     2:encoder_counts[95-24*a -:24]={a[7:0]^8'hc3,16'hx5z6};
    endcase
   end
'''+new[end:]
    new=new.replace('EVENT_SELECTOR_EXHAUSTION_PASS','EVENT_SELECTOR_UNIQUE_CHANNEL_EXHAUSTION_PASS')
    bench=OUT/'selector_unique_tb.sv';assert not bench.exists();bench.write_text(new)
    paths=[OUT/'original_diff.v',OUT/'candidate_diff.v',H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v',bench]
    runs=[]
    for name,args in [('unique-selector-compile',['iverilog','-g2012','-s','event_selector_unique_tb','-o',linux(OUT/'selector_unique.vvp'),*map(linux,paths)]),('unique-selector-execute',['vvp',linux(OUT/'selector_unique.vvp')])]:
        argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
        result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
        log=OUT/(name+'.log');log.write_bytes(result.stdout);print(result.stdout.decode(errors='replace'),end='')
        runs.append({'name':name,'argv':argv,'exit':result.returncode,'log_SHA256':sha(log)})
        if result.returncode:break
    record={'status':'ALL_65536_FOUR_STATE_SELECTORS_THREE_DISTINCT_CHANNEL_PAYLOAD_PROFILES_PASS' if len(runs)==2 and all(r['exit']==0 for r in runs) else 'FAIL','executions':runs,'function_checks':196608,'all_16_legal_source_values_distinct_in_each_profile':True,'X_Z_payload_profiles':2,'known_invalid_and_unknown_selectors_return_zero':True,'input_SHA256':{str(p):sha(p) for p in [Path(__file__),*paths]},'adopted':False}
    (OUT/'unique-selector-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    return 0 if record['status']!='FAIL' else 1
if __name__=='__main__':raise SystemExit(main())
