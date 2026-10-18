"""Capture final immutable host-control/runner identities, never launch KiCad."""
import hashlib,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
import compose_two as C
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    files=[HERE/'compose_two.py',HERE/'measure_two.py',HERE/'audit_two.py',HERE/'audit.json',HERE/'construction.json',HERE/'r07-two-zero-via.kicad_pcb']
    initial={str(p):sha(p) for p in files}
    logs=[]
    for path in (HERE/'test_two.py',HERE.parent/'test_geometry_controls.py'):
        result=subprocess.run([sys.executable,str(path)],capture_output=True,text=True)
        log=HERE/(path.stem+'-final.log');log.write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise ValueError('Hostcontrolfailed:'+str(path))
        logs.append({'test_source':str(path),'sha256':sha(path),'log':str(log),'log_sha256':sha(log),'exit_code':result.returncode})
    checked=C.validate_construction(HERE/'construction.json',HERE/'r07-two-zero-via.kicad_pcb')
    for path,expected in initial.items():
        if sha(Path(path))!=expected:raise ValueError('Frozeninputchangedduringcontrols:'+path)
    derivation=json.loads((HERE/'runner-derivation.json').read_text())
    derivation['initial_derivative_sha256']=derivation['derived_sha256']
    derivation['derived_sha256']=sha(HERE/'measure_two.py')
    derivation['post_derivation_changes']=['Bind frozen r07/r06 baseline reports and measured copies before/after',
                                         'Check r06 raw native DRC/version independently','Explicit combined dual-baseline verdict helper for rejection control']
    (HERE/'runner-derivation.json').write_text(json.dumps(derivation,indent=1)+'\n',encoding='utf-8')
    ready={'schema':'r07-two-signal-ready-host-v1','source_files_sha256':initial,'tests':logs,'controls_passed':14,
      'construction_check':checked,'runner_derivation_sha256':sha(HERE/'runner-derivation.json'),
      'native_launched':False,'native_gate':'OPEN;mustpassBOTHlive/r07andr06','adopted':False,'manufacturing_ready':False,
      'synthetic_guard_control':'Actual saved r07 plus onlytwo simulated pad joins:live+2/-0PASS,r06loss15FAIL. This is a host rejection fixture, not native candidate evidence'}
    (HERE/'ready.json').write_text(json.dumps(ready,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'ready':str(HERE/'ready.json'),'ready_sha256':sha(HERE/'ready.json'),'pins':initial,'controls_passed':14},indent=1))

if __name__=='__main__':main()
