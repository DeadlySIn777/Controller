"""Preserve exact failed or passing actual-SPI differential artifacts."""
from pathlib import Path
import hashlib,json,subprocess,time
H=Path(__file__).resolve().parent;OUT=H/'transport-cmd-alignment-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
def main():
    prep=json.loads((OUT/'preparation-receipt.json').read_bytes())
    paths=[OUT/'original_diff.v',OUT/'candidate_diff.v',H/'transport_alignment_diff_tb.sv']
    inputs={str(p):sha(p) for p in [Path(__file__),*paths]};runs=[];started=time.time()
    for name,args in [('compile',['iverilog','-g2012','-s','transport_alignment_diff_tb','-o',linux(OUT/'differential.vvp'),*map(linux,paths)]),('execute',['vvp',linux(OUT/'differential.vvp')])]:
        argv=['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17',*args]
        result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
        log=OUT/(name+'.log');assert not log.exists();log.write_bytes(result.stdout)
        row={'name':name,'argv':argv,'exit':result.returncode,'log_SHA256':sha(log)};runs.append(row)
        print(json.dumps(row),flush=True);print(result.stdout.decode(errors='replace')[-3000:],flush=True)
        if result.returncode:break
    assert all(sha(Path(p))==digest for p,digest in inputs.items())
    assert sha(Path(prep['source']))==prep['canonical_SHA256']
    record={'status':'ACTUAL_SPI_OLD_NEW_TRANSPORT_ALIGNMENT_DIFFERENTIAL_PASS' if len(runs)==2 and all(r['exit']==0 for r in runs) else 'FAIL','executions':runs,'elapsed_seconds':time.time()-started,'candidate_SHA256':sha(OUT/'cnc3_spi_transport_stateful.v'),'canonical_sources_unchanged':True,'input_SHA256':inputs,'scope':'all public outputs including held frames/rejection headers/rate words/MISO/OE; all internal protocol/CRC/timer/snapshot state exact, RX compared under explicit CMD-upper768 normalization; checked before/after core edges and asynchronous reset pulses','vectors':'32valid CRC16frames including16CMD×12ratewords andFBgood/badinnerCRC; malformedCRC,truncation/header/overrun boundaries,overlap,timing,reset,180000binarywirefuzzcycles,3000fourstatewirefuzzcycles','formal_equivalence':'NOT_RUN','physical_fit_timing':'OPEN','adopted':False,'manufacturing_ready':False}
    (OUT/'behavior-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':record['status'],'elapsed_seconds':record['elapsed_seconds']}),flush=True)
    return 0 if record['status']!='FAIL' else 1
if __name__=='__main__':raise SystemExit(main())
