#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/family-synthesis-r02'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/cnc3-transport-dccd6dcafa5d"
cp '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/'*.v "$rootfs/work/cnc3-transport-dccd6dcafa5d/"
cp synth.ys "$rootfs/work/cnc3-transport-dccd6dcafa5d/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/cnc3-transport-dccd6dcafa5d; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/cnc3-transport-dccd6dcafa5d/"*.json "$rootfs/work/cnc3-transport-dccd6dcafa5d/"*.log "$rootfs/work/cnc3-transport-dccd6dcafa5d/"*.txt .
test "$result" -eq 0
