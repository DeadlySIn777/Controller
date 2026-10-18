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
mkdir "$task_root/work/motherboard-watchdog-2e6332c1544f"
mkdir "$task_root/work/motherboard-watchdog-2e6332c1544f/rtl"
cp inputs/gateware/motherboard_bringup/*.v inputs/gateware/rtl/cnc_spi_frame.v inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v "$task_root/work/motherboard-watchdog-2e6332c1544f/rtl/"
cp synth.ys "$task_root/work/motherboard-watchdog-2e6332c1544f/synth.ys"
chroot "$task_root" sh -c 'cd /work/motherboard-watchdog-2e6332c1544f; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1'
cp "$task_root/work/motherboard-watchdog-2e6332c1544f/"*.json "$task_root/work/motherboard-watchdog-2e6332c1544f/"*.edif "$task_root/work/motherboard-watchdog-2e6332c1544f/"*.log "$task_root/work/motherboard-watchdog-2e6332c1544f/"*.txt .
