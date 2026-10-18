"""Three compile-success/behavior-failure controls on frozen isolated FIFO RTL."""
from pathlib import Path
import hashlib,json,shutil,subprocess
H=Path(__file__).resolve().parent;BASE=H/'producer-fifo-independent-supplement-r1';OUT=BASE/'mutations'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    assert not OUT.exists();OUT.mkdir()
    baseline=json.loads((BASE/'receipt.json').read_bytes());assert baseline['status']=='PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS'
    original=(BASE/'candidate_diff.v').read_text()
    cases=[('drop_global_prefetch','count!=0 && prefetched_rd==rd && |producer_head_valid','count!=0 && |producer_head_valid','public/global/filter event state differs'),
      ('sequence_as_global_tag','{temp_wr,temp_sequence,kind,origin,flags,ticks,data}','{temp_sequence,temp_sequence,kind,origin,flags,ticks,data}','normalized admitted record differs'),
      ('capacity_255','if(temp_count<256)begin','if(temp_count<255)begin','public/global/filter event state differs')]
    records=[]
    for name,before,after,marker in cases:
        assert original.count(before)==1,name
        d=OUT/name;d.mkdir();(d/'candidate_diff.v').write_text(original.replace(before,after))
        for f in ['original_diff.v','cnc3_event_bank.v','supplement_tb.sv']:shutil.copyfile(BASE/f,d/f)
        paths=[d/'original_diff.v',d/'candidate_diff.v',d/'cnc3_event_bank.v',d/'supplement_tb.sv'];runs=[]
        for phase,args in [('compile',['iverilog','-g2012','-s','producer_fifo_supplement_tb','-o',linux(d/'mutation.vvp'),*map(linux,paths)]),('execute',['vvp',linux(d/'mutation.vvp')])]:
            argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
            result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
            log=d/(phase+'.log');log.write_bytes(result.stdout);runs.append({'phase':phase,'exit':result.returncode,'argv':argv,'log_SHA256':sha(log)})
            print(name,phase,result.returncode,result.stdout.decode(errors='replace')[-1500:],flush=True)
            if phase=='compile' and result.returncode:break
        detected=len(runs)==2 and runs[0]['exit']==0 and runs[1]['exit']!=0 and marker in (d/'execute.log').read_text()
        record={'mutation':name,'status':'EXPECTED_BEHAVIORAL_REGRESSION_DETECTED' if detected else 'FAIL','successful_compile_required':True,'expected_failure_marker':marker,'executions':runs,'changed_expression':{'before':before,'after':after},'input_SHA256':{str(p):sha(p) for p in paths}}
        (d/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
    frozen_still_same=all(sha(Path(p))==digest for p,digest in baseline['input_SHA256'].items())
    record={'status':'THREE_FIFO_SEMANTIC_MUTATIONS_COMPILE_AND_FAIL_BEHAVIOR_AS_REQUIRED' if all(r['status']=='EXPECTED_BEHAVIORAL_REGRESSION_DETECTED' for r in records) and frozen_still_same else 'FAIL','controls':records,'frozen_supplement_and_live_inputs_unchanged':frozen_still_same,'baseline_PASS_receipt_SHA256':sha(BASE/'receipt.json'),'script_SHA256':sha(Path(__file__)),'adopted':False}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':record['status']}))
    return 0 if record['status']!='FAIL' else 1
if __name__=='__main__':raise SystemExit(main())
