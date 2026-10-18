"""Immutable disconnected RTL/lint/synthesis receipt for fitted watchdog bring-up.

Historical six/two endpoint regressions run against byte-preserved original files.
This does not invoke hardware, flash firmware or claim vendor place/route.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=[
 'gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v',
 'gateware/motherboard_bringup/cnc_iol1_readonly_master.v',
 'gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v',
 'gateware/motherboard_bringup/tb_motherboard_watchdogs.sv',
 'gateware/motherboard_bringup/README.md',
 'gateware/rtl/cnc_endpoint.v','gateware/rtl/cnc_spi_frame.v',
 'gateware/rtl/cnc_stepgen.v','gateware/rtl/cnc_encoder.v',
 'gateware/board_review/tb_permission_connection.sv',
 'gateware/tests/tb_cnc_endpoint.sv','gateware/tests/tb_cnc_endpoint_v2.sv',
 'gateware/tools/run_tests.sh','gateware/tools/protocol.py',
 'tools/hardware_check_motherboard_watchdog_rtl.py']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-dir',required=True,type=Path);a=ap.parse_args();out=a.output_dir.resolve()
 if out.exists():raise SystemExit('Immutable run directory already exists')
 raw={n:(ROOT/n).read_bytes() for n in NAMES}
 for p in (ROOT/'gateware/tests').iterdir():
  if p.suffix in ('.hex','.json'):raw[p.relative_to(ROOT).as_posix()]=p.read_bytes()
 out.mkdir(parents=True)
 for n,b in raw.items():p=out/'inputs'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 work='motherboard-watchdog-'+uuid.uuid4().hex[:12]
 sources='inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v inputs/gateware/motherboard_bringup/cnc_iol1_readonly_master.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v'
 script=f'''#!/bin/sh
set -eu
cd "$(dirname "$0")"
iverilog -V > iverilog-version.txt 2>&1
verilator --version > verilator-version.txt
verilator --lint-only -Wall --top-module cnc_motherboard_watchdog_bringup {sources} > lint.log 2>&1
iverilog -g2005 -Wall -s cnc_motherboard_watchdog_bringup -o elaborated {sources} > verilog2005.log 2>&1
iverilog -g2012 -Wall -s tb_motherboard_watchdogs -o simulation {sources} inputs/gateware/motherboard_bringup/tb_motherboard_watchdogs.sv > build.log 2>&1
vvp simulation > run.log 2>&1
sh inputs/gateware/tools/run_tests.sh > historical-regression.log 2>&1
iverilog -g2012 -Wall -s tb_permission_connection -o historical-permission inputs/gateware/rtl/cnc_endpoint.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v inputs/gateware/board_review/tb_permission_connection.sv > historical-permission-build.log 2>&1
vvp historical-permission > historical-permission.log 2>&1
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
test -x "$task_root/usr/bin/yosys"
mkdir "$task_root/work/{work}"
mkdir "$task_root/work/{work}/rtl"
cp inputs/gateware/motherboard_bringup/*.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v "$task_root/work/{work}/rtl/"
cp synth.ys "$task_root/work/{work}/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{work}; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
synth_result=$?
set -e
for artifact in "$task_root/work/{work}/"*
do
    if [ -f "$artifact" ]
    then
        cp "$artifact" .
    fi
done
test "$synth_result" -eq 0
'''
 (out/'run.sh').write_text(script,newline='\n')
 synth='''read_verilog rtl/cnc_motherboard_motion_bringup.v rtl/cnc_motherboard_watchdog_bringup.v rtl/cnc_iol1_readonly_master.v rtl/cnc_spi_frame.v rtl/cnc_stepgen.v rtl/cnc_encoder.v
hierarchy -check -top cnc_motherboard_watchdog_bringup
proc
check -assert
select -assert-none t:$dlatch t:$adlatch t:$dlatchsr
tee -o structural-stat.json stat -json
synth_efinix -top cnc_motherboard_watchdog_bringup
delete t:$scopeinfo
check -assert -mapped
select -assert-none t:EFX_LATCH t:$_DLATCH_* t:$dlatch t:$adlatch t:$dlatchsr
tee -o mapped-stat.json stat -json
write_json motherboard_watchdog_bringup_efinix.json
write_edif motherboard_watchdog_bringup_efinix.edif
'''
 (out/'synth.ys').write_text(synth,newline='\n')
 unix='/mnt/'+str(out)[0].lower()+str(out)[2:].replace('\\','/')+'/run.sh'
 run=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',unix],capture_output=True,text=True,timeout=240)
 (out/'launcher.log').write_text(run.stdout+run.stderr)
 log=(out/'run.log').read_text() if (out/'run.log').exists() else ''
 m=re.search(r'PASS motherboard watchdog bringup checks=(\d+) M_pulses=(\d+) O_pulses=(\d+);',log)
 changed=[n for n,b in raw.items() if (ROOT/n).read_bytes()!=b or (out/'inputs'/n).read_bytes()!=b]
 result={'schema_version':1,'scope':'current fitted-waveform diagnostic RTL, synthetic MCU peers, byte-preserved six-axis/two-encoder historical regressions; family synthesis only',
  'passed':run.returncode==0 and bool(m) and int(m[1])==58 and not changed,
  'checks':int(m[1]) if m else 0,'motion_pulses':int(m[2]) if m else 0,'output_pulses':int(m[3]) if m else 0,
  'exit_code':run.returncode,'source_changed_during_run':changed,'source_sha256':{n:sha(b) for n,b in raw.items()},
  'manufacturing_ready':False,'target_MCU_firmware':False,'twelve_axis_runtime':False,'physical_20ms_proof':False,
  'vendor_package_fit':False,'vendor_routed_timing':False,'physical_pin_assignment_from_native_schematic_requires_separate_review':True}
 result['artifact_sha256']={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','artifact_sha256')},indent=2));return not result['passed']
if __name__=='__main__':raise SystemExit(main())
