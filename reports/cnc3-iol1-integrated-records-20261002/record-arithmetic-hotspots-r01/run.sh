#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-integrated-records-20261002/record-arithmetic-hotspots-r01'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/record-hotspots-d17712e6"
cp *.v synth.ys "$rootfs/work/record-hotspots-d17712e6/"
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/record-hotspots-d17712e6; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
cp "$rootfs/work/record-hotspots-d17712e6/"*.json "$rootfs/work/record-hotspots-d17712e6/"*.log "$rootfs/work/record-hotspots-d17712e6/"*.txt .
