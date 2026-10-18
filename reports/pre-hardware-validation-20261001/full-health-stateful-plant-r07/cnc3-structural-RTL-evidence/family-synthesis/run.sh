#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/pre-hardware-validation-20261001/full-health-stateful-plant-r07/cnc3-structural-RTL-evidence/family-synthesis'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-f29dfe8e1b52"
cp inputs/rtl/*.v "$rootfs/work/cnc3-transport-f29dfe8e1b52/"
cp synth.ys "$rootfs/work/cnc3-transport-f29dfe8e1b52/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-f29dfe8e1b52; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-f29dfe8e1b52/"*.json "$rootfs/work/cnc3-transport-f29dfe8e1b52/"*.log "$rootfs/work/cnc3-transport-f29dfe8e1b52/"*.txt .
test "$result" -eq 0
