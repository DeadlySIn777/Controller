#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-integrated-records-20261002/timer-share-formal-r01'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/timer-proof-r01"
cp *.v prove.ys "$rootfs/work/timer-proof-r01/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/timer-proof-r01; yosys -V > version.txt; yosys -Q -T -s prove.ys > proof.log 2>&1"'
rc=$?
set -e
cp "$rootfs/work/timer-proof-r01/"*.txt "$rootfs/work/timer-proof-r01/"*.log .
exit "$rc"
