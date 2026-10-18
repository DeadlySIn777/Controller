"""Generic Efinix-family screen of the functional SIM top, never a vendor fit."""
import argparse,hashlib,json,subprocess,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
args=argparse.ArgumentParser();args.add_argument('--out',required=True);a=args.parse_args()
out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=False);copied=out/'inputs';copied.mkdir()
inventory=[]
for p in sorted((ROOT/'reports/deeper-runtime-20261004/rtl/serialized-candidate-r02/source').glob('*.v')):
 (copied/p.name).write_bytes(p.read_bytes());inventory.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
script='read_verilog '+' '.join('inputs/'+p.name for p in sorted(copied.glob('*.v')))+'\nhierarchy -check -top cnc3_runtime_sim\nsynth_efinix -top cnc3_runtime_sim\nstat\nwrite_json mapped.json\n'
(out/'synth.ys').write_text(script)
name='sim2-map-'+uuid.uuid4().hex[:12]
shell=f'''#!/bin/sh
set -eu
cd '{unix(out)}'
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$task_root/work/{name}"
mkdir "$task_root/work/{name}/inputs"
cp inputs/*.v "$task_root/work/{name}/inputs/"
cp synth.ys "$task_root/work/{name}/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{name}; yosys -V > yosys-version.txt; timeout -k 5 600 yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
for artifact in "$task_root/work/{name}/"*
do
 if [ -f "$artifact" ]; then cp "$artifact" .; fi
done
exit "$result"
'''
(out/'run.sh').write_text(shell,encoding='utf-8',newline='\n')
receipt={'started_utc':datetime.now(timezone.utc).isoformat(),'inputs':inventory,'top':'cnc3_runtime_sim','vendor_fit':False,'physical_measurements':0}
try:
 r=subprocess.run(['wsl.exe','-d','GarciaMechBuilder','--','sh',unix(out/'run.sh')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=630)
 (out/'launcher.log').write_bytes(r.stdout);receipt['exit']=r.returncode
except subprocess.TimeoutExpired:receipt['error']='bounded630s launcher timeout'
receipt['completed_utc']=datetime.now(timezone.utc).isoformat();receipt['sources_unchanged']=all(sha(ROOT/i['path'])==i['sha256'] for i in inventory)
receipt['artifacts']={p.name:sha(p) for p in out.iterdir() if p.is_file()}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
