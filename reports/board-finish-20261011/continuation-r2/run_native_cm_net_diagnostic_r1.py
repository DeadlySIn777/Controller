"""Use the existing test-only slot for one frozen native net observation."""
import hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
stage=HERE/'combined-reset-cm-native-r4';out=stage/'net-diagnostic-r1'
if out.exists():raise ValueError('Fresh diagnostic required')
out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
helper=HERE/'diagnose_native_cm_net_assignment_r1.py'
board=stage/'copy/board.kicad_pcb';spec=stage/'native-via-spec.json'
command=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper.resolve()),str(board.resolve()),str((out/'native.json').resolve()),str(spec.resolve())]
pins={str(p.resolve()):sha(p) for p in [Path(__file__),helper,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),spec]}
(out/'inputs.json').write_text(json.dumps({'pins':pins,'command':command,'no_new_slots':True},indent=1)+'\n',encoding='utf-8')
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
with (out/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
if any(sha(Path(p))!=h for p,h in pins.items()):raise ValueError('Frozen diagnostic input changed')
print(json.dumps({'exit_code':run.returncode,'log':str(out/'native.log'),'output':str(out/'native.json')}),flush=True)
