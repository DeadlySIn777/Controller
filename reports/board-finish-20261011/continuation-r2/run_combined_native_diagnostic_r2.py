"""Read the frozen combined board again with pre-gate exact via diagnostics."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIOR=HERE/'combined-power-source-native-r1';OUT=HERE/'combined-power-native-diagnostic-r2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if OUT.exists():raise ValueError('Fresh diagnostic directory required')
    pins=json.loads((PRIOR/'inputs.json').read_bytes())
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Prior frozen input changed '+p)
    prior=json.loads((PRIOR/'invocation.json').read_bytes());cmd=prior['command'];old=str((HERE/'native_entry_width_r3.py').resolve());new=str((HERE/'native_entry_diagnostic_r4.py').resolve())
    if cmd.count(old)!=1:raise ValueError('One exact entry helper expected')
    cmd[cmd.index(old)]=new;cmd[-1]=str((OUT/'native-parity.json').resolve());OUT.mkdir()
    extra={str(p.resolve()):sha(p) for p in [Path(__file__),HERE/'native_entry_diagnostic_r4.py',HERE/'native-via-diagnostic-derivation-r4.json',PRIOR/'receipt.json']}
    (OUT/'inputs.json').write_text(json.dumps({'inherited_pins':pins,'extra':extra,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'new_heavy_slots':0},indent=1)+'\n',encoding='utf-8')
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONUTF8='1')
    with (OUT/'native.log').open('w',encoding='utf-8') as f:run=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
    for p,h in {**pins,**extra}.items():
        if sha(p)!=h:raise ValueError('Diagnostic input changed '+p)
    api=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {};ok=run.returncode==0 and api.get('summary',{}).get('parity_defects')==0 and api.get('added_via_annuli',{}).get('verdict')=='PASS'
    result={'verdict':'PASS_SOURCE_NATIVE_API_ONLY' if ok else 'FAIL_EXACT_VIA_GATE','native_exit_code':run.returncode,'native_summary':api.get('summary'),'observed_vias':str(OUT/'native-parity.json.actual-vias.json'),'refill_DRC_connectivity':'NOT_EXECUTED','adopted':False}
    (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
