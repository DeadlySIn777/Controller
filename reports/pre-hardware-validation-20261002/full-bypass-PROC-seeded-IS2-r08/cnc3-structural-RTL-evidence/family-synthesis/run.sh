#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/cnc3-structural-RTL-evidence/family-synthesis'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-a2f2627c3156"
cp inputs/rtl/*.v "$rootfs/work/cnc3-transport-a2f2627c3156/"
cp synth.ys "$rootfs/work/cnc3-transport-a2f2627c3156/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-a2f2627c3156; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-a2f2627c3156/"*.json "$rootfs/work/cnc3-transport-a2f2627c3156/"*.log "$rootfs/work/cnc3-transport-a2f2627c3156/"*.txt .
test "$result" -eq 0
