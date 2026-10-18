"""Compile four real G031 read-only targets and cross-test the same C protocol.

Runs disconnected compilers/HDL only. Immutable input copies separate actual
ARM compilation, host C execution, HDL/C protocol simulation and synthesis.
Never flashes a target or opens a machine interface.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,re,uuid
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();out=a.output_dir.resolve()
 if out.exists():raise SystemExit('Run directory already exists; do not overwrite evidence')
 names=[]
 for directory in ['firmware/motherboard_iol1_readonly','gateware/motherboard_iol1_target_bringup']:
  names.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.is_file())
 names+=['gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v','gateware/rtl/cnc_spi_frame.v','gateware/rtl/cnc_stepgen.v','gateware/rtl/cnc_encoder.v',Path(__file__).relative_to(ROOT).as_posix()]
 work='iol1-target-'+uuid.uuid4().hex[:12]
 raw={n:(ROOT/n).read_bytes() for n in names};out.mkdir(parents=True)
 for n,b in raw.items():p=out/'inputs'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 src='inputs/firmware/motherboard_iol1_readonly';rtl='inputs/gateware/motherboard_iol1_target_bringup'
 sources=f'{rtl}/cnc_iol1_readonly_target_master.v {rtl}/cnc_motherboard_iol1_target_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v'
 script=f'''#!/bin/sh
set -eu
cd "$(dirname "$0")"
clang --version > clang-version.txt
ld.lld --version > linker-version.txt
gcc --version > host-gcc-version.txt
iverilog -V > iverilog-version.txt 2>&1
verilator --version > verilator-version.txt
flags="--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -O2 -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections"
clang $flags -c {src}/iol1.c -o iol1.o
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c {src}/startup.S -o startup.o
for slot in 0 1 2 3
do
 clang $flags -I{src}/vendor/ST -I{src}/vendor/ARM -DNODE_SLOT=$slot -c {src}/target.c -o target$slot.o
 clang $flags -S -I{src}/vendor/ST -I{src}/vendor/ARM -DNODE_SLOT=$slot {src}/target.c -o target$slot.s
 ld.lld -T {src}/stm32g031.ld --gc-sections -Map=node$slot.map startup.o iol1.o target$slot.o -o node$slot.elf
 readelf -h -l -S -s node$slot.elf > node$slot-elf-review.txt
 size node$slot.elf >> sizes.txt
 objcopy -I elf32-little -O binary node$slot.elf node$slot.bin
done
gcc -O2 -std=c11 -Wall -Wextra -Werror {src}/iol1.c {src}/test_protocol.c -o host-protocol
./host-protocol > host-protocol.log
gcc -O1 -g -fsanitize=undefined,address -fno-omit-frame-pointer -std=c11 -Wall -Wextra -Werror {src}/iol1.c {src}/test_protocol.c -o sanitized-protocol
./sanitized-protocol > sanitized-protocol.log
mkdir vpi-include
cp {src}/vendor/Icarus/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' {src}/vendor/Icarus/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include -I{src} {src}/peer_vpi.c {src}/iol1.c -o peer_vpi.vpi > vpi-build.log 2>&1
verilator --lint-only -Wall --top-module cnc_motherboard_iol1_target_bringup {sources} > lint.log 2>&1
iverilog -g2005 -Wall -s cnc_motherboard_iol1_target_bringup -o elaborated {sources} > verilog2005.log 2>&1
iverilog -g2012 -Wall -s tb_iol1_target_c -o simulation {sources} {rtl}/tb_iol1_target_c.sv > simulation-build.log 2>&1
vvp -M. -mpeer_vpi simulation > simulation.log 2>&1
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$task_root/work/{work}"
mkdir "$task_root/work/{work}/rtl"
cp {sources} "$task_root/work/{work}/rtl/"
cp synth.ys "$task_root/work/{work}/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{work}; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
synth_result=$?
set -e
for artifact in "$task_root/work/{work}/"*
do
 if [ -f "$artifact" ]; then cp "$artifact" .; fi
done
test "$synth_result" -eq 0
'''
 (out/'synth.ys').write_text('read_verilog '+ ' '.join('rtl/'+Path(n).name for n in sources.split()) + '\nhierarchy -check -top cnc_motherboard_iol1_target_bringup\nsynth_efinix -top cnc_motherboard_iol1_target_bringup\ncheck -assert\nstat\nwrite_json synthesized.json\n',newline='\n')
 (out/'run.sh').write_text(script,newline='\n')
 path='/mnt/'+out.drive[0].lower()+'/'+out.as_posix()[3:]+'/run.sh'
 proc=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',path],capture_output=True,text=True)
 (out/'build.log').write_text(proc.stdout+proc.stderr)
 receipt={'tool_exit':proc.returncode,'inputs':[{'path':n,'sha256':sha(b)} for n,b in raw.items()],
   'inputs_unchanged':all((ROOT/n).read_bytes()==b for n,b in raw.items()),'hardware_accessed':False,
   'target_compilation':proc.returncode==0,'target_execution':False,'factory_options_provisioned':False,
   'physical_timing_qualification':False,'production_firmware':False,'manufacturing_ready':False}
 if proc.returncode==0:
  receipt.update(host_C_checks=int(re.search(r'PASS (\d+)',(out/'host-protocol.log').read_text()).group(1)),
    backend_synthesis=True,vendor_fit_timing_bitstream=False,HDL_C_cross_test=(out/'simulation.log').read_text().splitlines()[-2:],target_sizes=(out/'sizes.txt').read_text())
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({k:v for k,v in receipt.items() if k!='inputs'},indent=2));raise SystemExit(proc.returncode)
if __name__=='__main__':main()
