#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/shared-package-final-r02/family-synthesis'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-d4a94517bef1"
cp inputs/rtl/*.v "$rootfs/work/cnc3-transport-d4a94517bef1/"
cp synth.ys "$rootfs/work/cnc3-transport-d4a94517bef1/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-d4a94517bef1; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-d4a94517bef1/"*.json "$rootfs/work/cnc3-transport-d4a94517bef1/"*.log "$rootfs/work/cnc3-transport-d4a94517bef1/"*.txt .
test "$result" -eq 0
