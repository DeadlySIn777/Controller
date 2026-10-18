#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-integrated-records-20261002/timing-width-motion-full-r02/family_synthesis_lint'
verilator --lint-only --top-module cnc3_motion_spi -Wall --Wno-fatal cnc3_alarm_filter.v cnc3_encoder_runtime.v cnc3_motion_spi.v cnc3_motion_state.v cnc3_rate_admission_serial.v cnc3_spi_transport_stateful.v cnc3_stepgen_runtime.v cnc3_spi_transport.v cnc3_command_validate.v > lint.log 2>&1
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-motion-f1591fbd6d"
cp *.v synth.ys "$rootfs/work/cnc3-motion-f1591fbd6d/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-motion-f1591fbd6d; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-motion-f1591fbd6d/"*.json "$rootfs/work/cnc3-motion-f1591fbd6d/"*.log "$rootfs/work/cnc3-motion-f1591fbd6d/"*.txt .
test "$result" -eq 0
