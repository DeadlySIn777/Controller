"""Compile four real G031 read-only targets and cross-test the same C protocol.

Runs disconnected compilers/HDL only. Immutable input copies separate actual
ARM compilation, host C execution, HDL/C protocol simulation and synthesis.
Never flashes a target or opens a machine interface.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,re
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();out=a.output_dir.resolve()
 if out.exists():raise SystemExit('Run directory already exists; do not overwrite evidence')
 names=[]
 for directory in ['firmware/motherboard_iol1_readonly','gateware/motherboard_iol1_target_bringup']:
  names.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.is_file())
 names+=['gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v','gateware/rtl/cnc_spi_frame.v','gateware/rtl/cnc_stepgen.v','gateware/rtl/cnc_encoder.v',Path(__file__).relative_to(ROOT).as_posix()]
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
flags="--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -Oz -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections"
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
iverilog-vpi -I{src} {src}/peer_vpi.c {src}/iol1.c > vpi-build.log 2>&1
verilator --lint-only -Wall --top-module cnc_motherboard_iol1_target_bringup {sources} > lint.log 2>&1
iverilog -g2005 -Wall -s cnc_motherboard_iol1_target_bringup -o elaborated {sources} > verilog2005.log 2>&1
iverilog -g2012 -Wall -s tb_iol1_target_c -o simulation {sources} {rtl}/tb_iol1_target_c.sv > simulation-build.log 2>&1
vvp -M. -mpeer_vpi simulation > simulation.log 2>&1
'''
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
    HDL_C_cross_test=(out/'simulation.log').read_text().splitlines()[-2:],target_sizes=(out/'sizes.txt').read_text())
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2));raise SystemExit(proc.returncode)
if __name__=='__main__':main()
