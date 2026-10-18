#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/family-synthesis-r01'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-b378c595cff4"
cp '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/'*.v "$rootfs/work/cnc3-transport-b378c595cff4/"
cp synth.ys "$rootfs/work/cnc3-transport-b378c595cff4/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-b378c595cff4; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-b378c595cff4/"*.json "$rootfs/work/cnc3-transport-b378c595cff4/"*.log "$rootfs/work/cnc3-transport-b378c595cff4/"*.txt .
test "$result" -eq 0
