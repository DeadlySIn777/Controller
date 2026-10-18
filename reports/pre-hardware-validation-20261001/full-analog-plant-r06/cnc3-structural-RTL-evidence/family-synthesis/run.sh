#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/pre-hardware-validation-20261001/full-analog-plant-r06/cnc3-structural-RTL-evidence/family-synthesis'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-0ea9324213ae"
cp inputs/rtl/*.v "$rootfs/work/cnc3-transport-0ea9324213ae/"
cp synth.ys "$rootfs/work/cnc3-transport-0ea9324213ae/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-0ea9324213ae; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-0ea9324213ae/"*.json "$rootfs/work/cnc3-transport-0ea9324213ae/"*.log "$rootfs/work/cnc3-transport-0ea9324213ae/"*.txt .
test "$result" -eq 0
