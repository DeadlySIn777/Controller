#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/bounded_CNC3_stateful_replay-evidence/family_synthesis_lint'
verilator --lint-only --top-module cnc3_motion_spi -Wall --Wno-fatal cnc3_alarm_filter.v cnc3_encoder_runtime.v cnc3_motion_spi.v cnc3_motion_state.v cnc3_rate_admission_serial.v cnc3_spi_transport_stateful.v cnc3_stepgen_runtime.v cnc3_spi_transport.v cnc3_command_validate.v > lint.log 2>&1
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-motion-8f74a6ee09"
cp *.v synth.ys "$rootfs/work/cnc3-motion-8f74a6ee09/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-motion-8f74a6ee09; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-motion-8f74a6ee09/"*.json "$rootfs/work/cnc3-motion-8f74a6ee09/"*.log "$rootfs/work/cnc3-motion-8f74a6ee09/"*.txt .
test "$result" -eq 0
