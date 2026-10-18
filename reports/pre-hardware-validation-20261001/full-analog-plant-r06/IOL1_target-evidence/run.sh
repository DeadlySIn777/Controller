#!/bin/sh
set -eu
cd "$(dirname "$0")"
clang --version > clang-version.txt
ld.lld --version > linker-version.txt
gcc --version > host-gcc-version.txt
iverilog -V > iverilog-version.txt 2>&1
verilator --version > verilator-version.txt
flags="--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -O2 -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections"
clang $flags -c inputs/firmware/motherboard_iol1_readonly/iol1.c -o iol1.o
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c inputs/firmware/motherboard_iol1_readonly/startup.S -o startup.o
for slot in 0 1 2 3
do
 clang $flags -Iinputs/firmware/motherboard_iol1_readonly/vendor/ST -Iinputs/firmware/motherboard_iol1_readonly/vendor/ARM -DNODE_SLOT=$slot -c inputs/firmware/motherboard_iol1_readonly/target.c -o target$slot.o
 clang $flags -S -Iinputs/firmware/motherboard_iol1_readonly/vendor/ST -Iinputs/firmware/motherboard_iol1_readonly/vendor/ARM -DNODE_SLOT=$slot inputs/firmware/motherboard_iol1_readonly/target.c -o target$slot.s
 ld.lld -T inputs/firmware/motherboard_iol1_readonly/stm32g031.ld --gc-sections -Map=node$slot.map startup.o iol1.o target$slot.o -o node$slot.elf
 readelf -h -l -S -s node$slot.elf > node$slot-elf-review.txt
 size node$slot.elf >> sizes.txt
 objcopy -I elf32-little -O binary node$slot.elf node$slot.bin
done
gcc -O2 -std=c11 -Wall -Wextra -Werror inputs/firmware/motherboard_iol1_readonly/iol1.c inputs/firmware/motherboard_iol1_readonly/test_protocol.c -o host-protocol
./host-protocol > host-protocol.log
gcc -O1 -g -fsanitize=undefined,address -fno-omit-frame-pointer -std=c11 -Wall -Wextra -Werror inputs/firmware/motherboard_iol1_readonly/iol1.c inputs/firmware/motherboard_iol1_readonly/test_protocol.c -o sanitized-protocol
./sanitized-protocol > sanitized-protocol.log
mkdir vpi-include
cp inputs/firmware/motherboard_iol1_readonly/vendor/Icarus/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' inputs/firmware/motherboard_iol1_readonly/vendor/Icarus/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include -Iinputs/firmware/motherboard_iol1_readonly inputs/firmware/motherboard_iol1_readonly/peer_vpi.c inputs/firmware/motherboard_iol1_readonly/iol1.c -o peer_vpi.vpi > vpi-build.log 2>&1
verilator --lint-only -Wall --top-module cnc_motherboard_iol1_target_bringup inputs/gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v inputs/gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v > lint.log 2>&1
iverilog -g2005 -Wall -s cnc_motherboard_iol1_target_bringup -o elaborated inputs/gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v inputs/gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v > verilog2005.log 2>&1
iverilog -g2012 -Wall -s tb_iol1_target_c -o simulation inputs/gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v inputs/gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v inputs/gateware/motherboard_iol1_target_bringup/tb_iol1_target_c.sv > simulation-build.log 2>&1
vvp -M. -mpeer_vpi simulation > simulation.log 2>&1
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$task_root/work/iol1-target-d6e22fd3c690"
mkdir "$task_root/work/iol1-target-d6e22fd3c690/rtl"
cp inputs/gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v inputs/gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v "$task_root/work/iol1-target-d6e22fd3c690/rtl/"
cp synth.ys "$task_root/work/iol1-target-d6e22fd3c690/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/iol1-target-d6e22fd3c690; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
synth_result=$?
set -e
for artifact in "$task_root/work/iol1-target-d6e22fd3c690/"*
do
 if [ -f "$artifact" ]; then cp "$artifact" .; fi
done
test "$synth_result" -eq 0
