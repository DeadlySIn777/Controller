from pathlib import Path
import argparse,hashlib,json,subprocess,uuid
BASE=Path(__file__).resolve().parent
OUT=BASE/'family-synthesis-r01';STAGE=BASE/'stage-r01'
a=argparse.ArgumentParser();a.add_argument('--out',type=Path);args=a.parse_args()
if args.out:OUT=args.out.resolve()
OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
work='cnc3-transport-'+uuid.uuid4().hex[:12]
script=f'''#!/bin/sh
set -eu
cd '{unix(OUT)}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/{work}"
cp '{unix(STAGE)}/rtl/'*.v "$rootfs/work/{work}/"
cp synth.ys "$rootfs/work/{work}/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{work}; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/{work}/"*.json "$rootfs/work/{work}/"*.log "$rootfs/work/{work}/"*.txt .
test "$result" -eq 0
'''
(OUT/'run.sh').write_text(script,newline='\n')
(OUT/'synth.ys').write_text('''read_verilog cnc3_command_validate.v cnc3_spi_transport.v cnc3_frame_endpoint.v cnc3_feedback_pack.v cnc3_status_pack.v
hierarchy -check -top cnc3_frame_endpoint
proc
check -assert
select -assert-none t:$dlatch t:$adlatch t:$dlatchsr
tee -o structural-stat.json stat -json
synth_efinix -top cnc3_frame_endpoint
delete t:$scopeinfo
check -assert -mapped
select -assert-none t:EFX_LATCH t:$_DLATCH_* t:$dlatch t:$adlatch t:$dlatchsr
tee -o mapped-stat.json stat -json
write_json cnc3_frame_endpoint_efinix.json
''',newline='\n')
before={str(f):sha(f) for f in (STAGE/'rtl').glob('*.v')}
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',unix(OUT/'run.sh')],text=True,capture_output=True,timeout=300)
(OUT/'command.log').write_text(r.stdout+r.stderr)
receipt={'status':'PASS' if r.returncode==0 else 'FAIL','source_hashes':before,'source_unchanged':all(sha(Path(f))==h for f,h in before.items()),'family_synthesis_only':True,'Efinity_fit_timing':False,'clock_frequency_qualified':False,'compiler_result':r.returncode,'outputs':{f.name:sha(f) for f in OUT.iterdir() if f.is_file()}}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));raise SystemExit(r.returncode)
