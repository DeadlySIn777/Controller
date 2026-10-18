#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/rev-a-integration-20261004/vendor/structural-family-r01'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-66a8b94b1be0"
cp inputs/rtl/*.v "$rootfs/work/cnc3-transport-66a8b94b1be0/"
cp synth.ys "$rootfs/work/cnc3-transport-66a8b94b1be0/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-66a8b94b1be0; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-66a8b94b1be0/"*.json "$rootfs/work/cnc3-transport-66a8b94b1be0/"*.log "$rootfs/work/cnc3-transport-66a8b94b1be0/"*.txt .
test "$result" -eq 0
