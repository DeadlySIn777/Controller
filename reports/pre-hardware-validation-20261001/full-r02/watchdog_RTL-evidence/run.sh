#!/bin/sh
set -eu
cd "$(dirname "$0")"
iverilog -V > iverilog-version.txt 2>&1
verilator --version > verilator-version.txt
verilator --lint-only -Wall --top-module cnc_motherboard_watchdog_bringup inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v inputs/gateware/motherboard_bringup/cnc_iol1_readonly_master.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v > lint.log 2>&1
iverilog -g2005 -Wall -s cnc_motherboard_watchdog_bringup -o elaborated inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v inputs/gateware/motherboard_bringup/cnc_iol1_readonly_master.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v > verilog2005.log 2>&1
iverilog -g2012 -Wall -s tb_motherboard_watchdogs -o simulation inputs/gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v inputs/gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v inputs/gateware/motherboard_bringup/cnc_iol1_readonly_master.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v inputs/gateware/motherboard_bringup/tb_motherboard_watchdogs.sv > build.log 2>&1
vvp simulation > run.log 2>&1
sh inputs/gateware/tools/run_tests.sh > historical-regression.log 2>&1
iverilog -g2012 -Wall -s tb_permission_connection -o historical-permission inputs/gateware/rtl/cnc_endpoint.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v inputs/gateware/board_review/tb_permission_connection.sv > historical-permission-build.log 2>&1
vvp historical-permission > historical-permission.log 2>&1
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
test -x "$task_root/usr/bin/yosys"
mkdir "$task_root/work/motherboard-watchdog-d22a9114bffc"
mkdir "$task_root/work/motherboard-watchdog-d22a9114bffc/rtl"
cp inputs/gateware/motherboard_bringup/*.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v "$task_root/work/motherboard-watchdog-d22a9114bffc/rtl/"
cp synth.ys "$task_root/work/motherboard-watchdog-d22a9114bffc/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/motherboard-watchdog-d22a9114bffc; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
synth_result=$?
set -e
for artifact in "$task_root/work/motherboard-watchdog-d22a9114bffc/"*
do
    if [ -f "$artifact" ]
    then
        cp "$artifact" .
    fi
done
test "$synth_result" -eq 0
