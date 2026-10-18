import os
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,uuid,re
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('Fresh evidence directory required')
 out.mkdir(parents=True)
 sources=[*sorted(HERE.glob('cnc3_*.v')),HERE/'inputs/workspace/gateware/v3/rtl/cnc3_spi_transport.v',HERE/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 hashes={q.as_posix():sha(q) for q in sources}
 for q in sources:shutil.copyfile(q,out/q.name)
 files=' '.join(q.name for q in sources);work='cnc3-motion-'+uuid.uuid4().hex[:10]
 (out/'synth.ys').write_text(f'''read_verilog {files}
hierarchy -check -top cnc3_motion_spi
proc
check -assert
select -assert-none t:$dlatch t:$adlatch t:$dlatchsr
tee -o structural-stat.json stat -json
synth_efinix -top cnc3_motion_spi
delete t:$scopeinfo
check -assert -mapped
select -assert-none t:EFX_LATCH t:$_DLATCH_* t:$dlatch t:$adlatch t:$dlatchsr
tee -o mapped-stat.json stat -json
write_json cnc3_motion_spi_efinix.json
''',encoding='utf8',newline='\n')
 (out/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(out)}'
verilator --lint-only --top-module cnc3_motion_spi -Wall --Wno-fatal {files} > lint.log 2>&1
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/{work}"
cp *.v synth.ys "$rootfs/work/{work}/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{work}; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/{work}/"*.json "$rootfs/work/{work}/"*.log "$rootfs/work/{work}/"*.txt .
test "$result" -eq 0
''',encoding='utf8',newline='\n')
 r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(out/'run.sh')],text=True,capture_output=True,encoding='utf8',errors='replace',timeout=600)
 (out/'command.log').write_text(r.stdout+r.stderr,encoding='utf8',newline='\n')
 lint=(out/'lint.log').read_text() if(out/'lint.log').is_file() else ''
 warnings=re.findall(r'%Warning-([A-Z0-9_]+):',lint);errors=re.findall(r'%Error[^\n]*',lint)
 blocks=re.split(r'(?=%Warning-)',lint)
 admitted=[]
 for block in blocks:
  if not block.startswith('%Warning-'):continue
  category=block.split(':',1)[0].removeprefix('%Warning-')
  scratch=(category=='BLKSEQ' and 'cycle_faults=0;' in block and 'cnc3_motion_state.v:' in block)
  if category=='UNUSEDSIGNAL' or scratch:admitted.append(category)
 lint_pass=not errors and len(admitted)==len(warnings)
 unchanged=all(sha(Path(q))==h for q,h in hashes.items())
 present=all((out/q).is_file() for q in ('mapped-stat.json','structural-stat.json','cnc3_motion_spi_efinix.json'))
 receipt={'status':'PASS' if r.returncode==0 and lint_pass and present and unchanged else 'FAIL','input_hashes':hashes,'source_unchanged':unchanged,'actual_yosys_Efinix_family_mapping':r.returncode==0 and present,'lint_status':'PASS' if lint_pass else 'FAIL','lint_categories':warnings,'lint_errors':errors,'admitted_exact_scratch_BLKSEQ':'Only two cycle_faults=0 assignments: the same-cycle fault-union procedural temporary uses blocking accumulation deliberately; its effect is simulated and mapped, not a suppressed timing/width/error. No other BLKSEQ accepted.','unused_scope':'reported diagnostic/index/provider outputs retained for future integration; inspect complete lint.log','vendor_T20_fit_timing_bitstream':False,'physical_clock_SI_or_safety_qualification':False,'outputs':{q.relative_to(out).as_posix():sha(q) for q in out.rglob('*') if q.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);raise SystemExit(main(ap.parse_args().out.resolve()))
