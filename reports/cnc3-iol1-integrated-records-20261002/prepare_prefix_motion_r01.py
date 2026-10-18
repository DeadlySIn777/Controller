from pathlib import Path
import hashlib,json,shutil,subprocess
H=Path(__file__).resolve().parent;D=H/'prefix-motion-candidate-r01';src=H/'timing-width-motion-candidate-r02'
if D.exists():raise RuntimeError('fresh candidate required')
shutil.copytree(src,D,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile(H/'prefix-arithmetic-stage-r01/cnc3_stepgen_runtime.v',D/'cnc3_stepgen_runtime.v')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(D/'prefix-arithmetic-provenance.json').write_text(json.dumps({'prior_candidate':str(src),'prefix_formal_receipt':str(H/'prefix-arithmetic-stage-r01/receipt.json'),'only_delta':'modulo32-bit count +/-1 and two-complement magnitude boolean prefix implementation; formally equal for all32-bit data, no output timing/rate changes'},indent=2)+'\n')
m=json.loads((D/'bundle-manifest.json').read_text());m['files']={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','freeze-receipt.json')};(D/'bundle-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
T=H/'prefix-cycle-equivalence-r01';T.mkdir()
for fn in ('cnc3_stepgen_runtime_reference.v','tb_timer_equivalence.sv'):shutil.copyfile(H/'timer-share-stage-r01'/fn,T/fn)
shutil.copyfile(D/'cnc3_stepgen_runtime.v',T/'cnc3_stepgen_runtime.v')
before={str(p):sha(p) for p in T.glob('*.v')};u='/mnt/'+T.drive[0].lower()+T.as_posix()[2:]
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','bash','-lc',f"cd '{u}' && iverilog -g2012 -s tb_timer_equivalence -o cycle.vvp cnc3_stepgen_runtime_reference.v cnc3_stepgen_runtime.v tb_timer_equivalence.sv && vvp cycle.vvp"],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90)
(T/'execute.log').write_text(r.stdout+r.stderr,newline='\n');passed=r.returncode==0 and 'PASS exact timer sharing cycles=1200029 edges=4332 profiles=12' in r.stdout and all(sha(Path(p))==h for p,h in before.items());(T/'receipt.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','cycles':1200029,'edges':4332,'profiles':12,'exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'scope':'actual compiled original16-bit timers/count/DDS vs combined Boolean arithmetic +sharedtimerdefault16; all32-bit rate extremes/all16-bit timing, midrunconfig/reset/stop','physical_fit_claim':False},indent=2)+'\n');assert passed
print(D,sha(D/'bundle-manifest.json'))
