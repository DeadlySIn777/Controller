import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'cm-terminal-native-rule-coupons-r3/net-diagnostic-r4'
if OUT.exists():raise ValueError('Fresh diagnostic required')
OUT.mkdir();source=H/'cm-terminal-native-rule-coupons-r3/proposed-profile/board.kicad_pcb';helper=H/'diagnose_coupon_native_nets_r4.py'
pins={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),source,source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_dru'),helper]}
(OUT/'inputs.json').write_text(json.dumps(pins,indent=1)+'\n',encoding='utf-8')
cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper.resolve()),str(source.resolve()),str((OUT/'native-nets.json').resolve())]
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
with (OUT/'native.log').open('w',encoding='utf-8') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
for p,h in pins.items():
    if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise ValueError('Frozen coupon changed')
print((OUT/'native-nets.json').read_text(encoding='utf-8') if (OUT/'native-nets.json').exists() else (OUT/'native.log').read_text(encoding='utf-8'));raise SystemExit(r.returncode)
