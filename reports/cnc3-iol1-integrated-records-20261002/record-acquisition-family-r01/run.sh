#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-integrated-records-20261002/record-acquisition-family-r01'
verilator --lint-only --top-module cnc3_motion_acquisition_composition -Wall --Wno-fatal cnc_iol1_record_master.v cnc_iol1_record_acquisition.v cnc_mbr2_stream_checker.v cnc3_alarm_filter.v cnc3_encoder_runtime.v cnc3_motion_spi.v cnc3_motion_state.v cnc3_rate_admission_serial.v cnc3_spi_transport_stateful.v cnc3_stepgen_runtime.v cnc3_spi_transport.v cnc3_command_validate.v cnc3_motion_acquisition_composition.v > lint.log 2>&1
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/iol1-acquire-fb331a1220"
cp *.v synth.ys "$rootfs/work/iol1-acquire-fb331a1220/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/iol1-acquire-fb331a1220; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/iol1-acquire-fb331a1220/"*.json "$rootfs/work/iol1-acquire-fb331a1220/"*.log "$rootfs/work/iol1-acquire-fb331a1220/"*.txt .
test "$result" -eq 0
